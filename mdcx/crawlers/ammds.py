#!/usr/bin/env python3
"""AMMDS 数据源爬虫 — V1 架构

检索流程:
  1. POST /api/v1/movie/lookup  → 查询库内是否已入库
  2. GET  /api/v1/movie/{id}    → Lookup 命中时获取完整元数据
  3. POST /api/v1/movie/search  → 保底方案，多数据源检索并合并
"""

import re
import time
import traceback
from typing import Any
from urllib.parse import urlparse

from ..config.manager import manager
from ..models.log_buffer import LogBuffer
from ..utils.language import is_japanese


# ============================================================
# 辅助函数
# ============================================================

def get_year(release: str) -> str:
    """从日期字符串中提取四位年份"""
    try:
        return re.findall(r"\d{4}", release)[0]
    except Exception:
        return ""


def get_actor_photo(actor: str) -> dict:
    """构建演员名 → 空照片 URL 的映射"""
    names = [a.strip() for a in actor.split(",") if a.strip()]
    return {name: "" for name in names}


def _check_response(res: Any, context: str) -> tuple[bool, str]:
    """校验 AMMDS API 统一响应格式: {code, message, data, timestamp}

    Returns:
        (ok, error_detail): ok=True 表示 code==200 且 data 有效 (非 None，非空数组)
    """
    if res is None:
        return False, f"{context}: 响应为空（网络请求失败）"
    if not isinstance(res, dict):
        return False, f"{context}: 响应格式异常，非 JSON 对象"
    code = res.get("code")
    message = res.get("message", "")
    data = res.get("data")
    if code is None:
        return False, f"{context}: 响应缺少 code 字段"
    if code != 200:
        return False, f"{context}: [{code}] {message}"
    if data is None:
        return False, f"{context}: data 为空"
    if isinstance(data, list) and not data:
        return False, f"{context}: data 为空数组（无结果）"
    return True, ""


# ============================================================
# Detail API 数据提取
# ============================================================

def _extract_actors(actors_data) -> str:
    """从 Detail API 的 actors 字段提取逗号分隔的演员名列表"""
    if isinstance(actors_data, dict):
        return ",".join(actors_data.keys())
    if isinstance(actors_data, list):
        return ",".join(actors_data)
    return ""


def _extract_directors(directors) -> str:
    if isinstance(directors, list):
        return ",".join(directors)
    return ""


def _extract_genres_tags(detail: dict) -> str:
    parts = []
    for key in ("genre", "tag"):
        val = detail.get(key, [])
        if isinstance(val, list):
            parts.extend(val)
    return ",".join(parts)


def _extract_studio(detail: dict) -> str:
    val = detail.get("studio", [])
    if isinstance(val, list):
        return ",".join(val)
    return ""


def _extract_publisher(detail: dict) -> str:
    val = detail.get("issueStudio", [])
    if isinstance(val, list):
        return ",".join(val)
    return ""


def _extract_series(detail: dict) -> str:
    sets = detail.get("sets", {})
    if isinstance(sets, dict):
        return sets.get("name", "")
    return ""


def _extract_mosaic(detail: dict) -> str:
    mosaic_val = detail.get("mpaa", "") or detail.get("mosaic", "")
    s = str(mosaic_val)
    if "无码" in s:
        return "无码"
    if "有码" in s:
        return "有码"
    return "有码"


# ============================================================
# 结果构建
# ============================================================

def _build_result(detail: dict, detail_url: str, number: str) -> dict:
    """从 Detail API 返回的完整元数据构建结果字典"""
    orig_title = detail.get("originalTitle", "") or ""
    title_cn = detail.get("titleCn", "") or ""
    title = orig_title or title_cn or ""

    plot = detail.get("plot", "") or ""
    plot_cn = detail.get("plotCn", "") or ""
    outline = plot_cn or plot or ""

    actor = _extract_actors(detail.get("actors", {}))
    director = _extract_directors(detail.get("director", []))
    release = detail.get("premiered", "") or ""
    year = get_year(release)

    runtime_val = detail.get("runtime", "")
    runtime = str(runtime_val) if runtime_val else ""

    score_val = detail.get("rating", "")
    score = str(score_val) if score_val else ""

    poster = detail.get("poster", "") or ""
    thumb = detail.get("thumb", "") or ""
    fanart = detail.get("fanart", "") or ""
    extrafanart_val = detail.get("extrafanart", "")

    extrafanart = []
    if fanart:
        extrafanart.append(fanart)
    if isinstance(extrafanart_val, str) and extrafanart_val:
        extrafanart.append(extrafanart_val)
    elif isinstance(extrafanart_val, list):
        extrafanart.extend(extrafanart_val)

    uniqueid = detail.get("uniqueid", number) or number
    tag = _extract_genres_tags(detail)
    studio = _extract_studio(detail)
    publisher = _extract_publisher(detail) or studio
    series = _extract_series(detail)
    mosaic = _extract_mosaic(detail)

    actor_photo = get_actor_photo(actor)

    return {
        "number": uniqueid,
        "title": title,
        "originaltitle": orig_title,
        "actor": actor,
        "all_actor": actor,
        "outline": outline,
        "originalplot": plot,
        "tag": tag,
        "release": release,
        "year": year,
        "runtime": runtime,
        "score": score,
        "series": series,
        "director": director,
        "studio": studio,
        "publisher": publisher,
        "source": "ammds",
        "actor_photo": actor_photo,
        "all_actor_photo": actor_photo,
        "thumb": thumb,
        "poster": poster,
        "extrafanart": extrafanart,
        "trailer": "",
        "image_download": False,
        "image_cut": "",
        "mosaic": mosaic,
        "website": detail_url,
        "wanted": "",
    }


def _build_result_from_search(search_items: list[dict], number: str) -> dict:
    """从多个数据源的搜索结果中合并构建结果（不调用 Detail API）

    合并策略:
      - 日文标题/简介优先（is_japanese 判定）
      - 演员/标签列表合并去重
      - 图片优先取可正常获取的来源（非 javbus.com 优先）
      - 所有字段补全，不留空值
    """
    if not search_items:
        return _empty_result(number)

    # --- 1. 筛选：size写匹配当前番号的条目 ---
    matched = []
    for item in search_items:
        item_num = (item.get("number") or "").upper()
        if item_num == number.upper():
            matched.append(item)

    if not matched:
        # 无精确匹配，取第一个结果兜底
        matched = [search_items[0]]

    # --- 2. 排序：日文标题优先 ---
    matched.sort(
        key=lambda x: is_japanese(str(x.get("title") or "")),
        reverse=True,
    )

    # --- 3-4. 标题 & 简介：日文优先 ---
    title = ""
    outline = ""
    for item in matched:
        t = item.get("title") or ""
        s = item.get("summary") or ""
        if not title:
            title = t
        elif is_japanese(t) and not is_japanese(title):
            title = t
        if not outline:
            outline = s
        elif is_japanese(s) and not is_japanese(outline):
            outline = s

    originaltitle = title

    # --- 5. 演员：合并去重 ---
    actors_list = []
    for item in matched:
        val = item.get("actors") or []
        if isinstance(val, list):
            for a in val:
                a_str = str(a).strip()
                if a_str and a_str not in actors_list:
                    actors_list.append(a_str)
    actor = ",".join(actors_list)

    # --- 6. 标签：合并 genres + tags，去重 ---
    all_tags = []
    for item in matched:
        for key in ("genres", "tags"):
            val = item.get(key) or []
            if isinstance(val, list):
                for v in val:
                    v_str = str(v).strip()
                    if v_str and v_str not in all_tags:
                        all_tags.append(v_str)
    tag = ",".join(all_tags)

    # --- 7. 导演/制作商/系列/厂牌：日文优先 → 首个非空 ---
    def _pick_str(items: list[dict], key: str) -> str:
        jp_val = ""
        first_val = ""
        for item in items:
            v = str(item.get(key) or "").strip()
            if not v:
                continue
            if not first_val:
                first_val = v
            if is_japanese(v):
                jp_val = v
                break
        return jp_val or first_val

    director = _pick_str(matched, "director")
    studio = _pick_str(matched, "studio")
    series = _pick_str(matched, "series")
    label = _pick_str(matched, "label")

    # --- 8. 发行日期：取首个非空 ---
    release = ""
    for item in matched:
        release = str(item.get("release") or "").strip()
        if release:
            break
    year = get_year(release)

    # --- 9. 时长 / 评分：取首个有效值 ---
    runtime = ""
    for item in matched:
        v = item.get("runtime")
        if v:
            runtime = str(v)
            break

    score = ""
    for item in matched:
        v = item.get("score")
        if v is not None and v != 0:
            score = str(v)
            break

    # --- 10. 图片：收集所有来源，优先可正常获取的 ---
    all_covers = []
    all_thumbs = []
    all_previews = []

    for item in matched:
        c = (item.get("cover") or "").strip()
        t = (item.get("thumb") or "").strip()
        if c and c not in all_covers:
            all_covers.append(c)
        if t and t not in all_thumbs:
            all_thumbs.append(t)
        previews = item.get("previewImages") or []
        if isinstance(previews, list):
            for p in previews:
                p_str = str(p).strip()
                if p_str and p_str not in all_previews:
                    all_previews.append(p_str)

    def _is_blocked_image(url: str) -> bool:
        """判断图片 URL 是否来自可能被屏蔽的域名"""
        return "javbus.com" in url

    # poster: 优先非 javbus cover → javbus cover → thumb → preview
    poster = ""
    for c in all_covers:
        if not _is_blocked_image(c):
            poster = c
            break
    if not poster:
        poster = all_covers[0] if all_covers else ""
    if not poster:
        poster = all_thumbs[0] if all_thumbs else ""
    if not poster:
        poster = all_previews[0] if all_previews else ""

    # thumb: 优先非 javbus thumb → 首个 cover
    thumb = ""
    for t in all_thumbs:
        if not _is_blocked_image(t):
            thumb = t
            break
    if not thumb:
        thumb = all_thumbs[0] if all_thumbs else (all_covers[0] if all_covers else "")

    # extrafanart: 合并所有 thumb + previewImages，排除已用作 poster/thumb 的首张
    extrafanart = []
    for t in all_thumbs:
        if t and t not in extrafanart:
            extrafanart.append(t)
    for p in all_previews:
        if p and p not in extrafanart:
            extrafanart.append(p)
    # 如果 poster 在 extrafanart 首位，移除避免重复
    if poster and extrafanart and extrafanart[0] == poster:
        extrafanart.pop(0)

    # --- 11. 马赛克 ---
    mosaic_raw = _pick_str(matched, "mosaic")
    mosaic = "有码"
    if mosaic_raw:
        m_lower = mosaic_raw.lower()
        if "无码" in m_lower or "uncensored" in m_lower:
            mosaic = "无码"

    # --- 12. Website URL ---
    website = ""
    for item in matched:
        u = (item.get("url") or "").strip()
        if u:
            website = u
            break

    # --- 13. 组装结果 ---
    actor_photo = get_actor_photo(actor)

    return {
        "number": number,
        "title": title,
        "originaltitle": originaltitle,
        "actor": actor,
        "all_actor": actor,
        "outline": outline,
        "originalplot": outline,
        "tag": tag,
        "release": release,
        "year": year,
        "runtime": runtime,
        "score": score,
        "series": series,
        "director": director,
        "studio": studio,
        "publisher": studio or label or "",
        "source": "ammds",
        "actor_photo": actor_photo,
        "all_actor_photo": actor_photo,
        "thumb": thumb,
        "poster": poster,
        "extrafanart": extrafanart,
        "trailer": "",
        "image_download": False,
        "image_cut": "",
        "mosaic": mosaic,
        "website": website,
        "wanted": "",
    }


def _empty_result(number: str) -> dict:
    """返回空结果字典，所有字段为空默认值"""
    return {
        "number": number,
        "title": "",
        "originaltitle": "",
        "actor": "",
        "all_actor": "",
        "outline": "",
        "originalplot": "",
        "tag": "",
        "release": "",
        "year": "",
        "runtime": "",
        "score": "",
        "series": "",
        "director": "",
        "studio": "",
        "publisher": "",
        "source": "ammds",
        "actor_photo": {},
        "all_actor_photo": {},
        "thumb": "",
        "poster": "",
        "extrafanart": [],
        "trailer": "",
        "image_download": False,
        "image_cut": "",
        "mosaic": "有码",
        "website": "",
        "wanted": "",
    }


# ============================================================
# 主入口
# ============================================================

async def main(
    number: str,
    appoint_url: str = "",
    file_path: str = "",
    **kwargs,
) -> dict:
    start_time = time.time()
    website_name = "ammds"
    LogBuffer.req().write(f"-> {website_name}")

    ammds_url = manager.config.ammds_url
    api_key = manager.config.ammds_api_key

    web_info = "\n       "
    debug_info = ""

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/111.0.0.202 Safari/537.36"
        ),
    }

    try:
        # --- API Key 检查 ---
        if not api_key:
            debug_info = "请添加 AMMDS API Key 后刮削！（「设置」-「网络」-「AMMDS API Key」）"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)

        parsed = urlparse(ammds_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # ============================================================
        # 路径 A: appoint_url — 指定地址直连
        # ============================================================
        if appoint_url:
            detail_url = appoint_url
            debug_info = f"指定地址: {detail_url}"
            LogBuffer.info().write(web_info + debug_info)

            t0 = time.time()
            res_detail, error = await manager.computed.async_client.get_json(
                detail_url, headers=headers
            )
            elapsed = time.time() - t0

            if res_detail is None:
                debug_info = f"请求失败 (耗时: {elapsed:.2f}s): {error}"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            ok, err = _check_response(res_detail, "详情")
            if not ok:
                debug_info = f"{err} (耗时: {elapsed:.2f}s)"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            detail = res_detail.get("data", {})
            if not isinstance(detail, dict) or not detail:
                debug_info = f"详情 data 无效 (耗时: {elapsed:.2f}s)"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            dic = _build_result(detail, detail_url, number)
            debug_info = f"数据获取成功！(耗时: {elapsed:.2f}s)"
            LogBuffer.info().write(web_info + debug_info)

            result = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
            LogBuffer.req().write(f"({round(time.time() - start_time)}s) ")
            return result

        # ============================================================
        # Step 1: Lookup — 查询库内是否已入库
        # ============================================================
        movie_id = None
        lookup_hit = False

        try:
            lookup_url = f"{base_url}/api/v1/movie/lookup"
            lookup_body = {"number": number}
            debug_info = f"[本地匹配] POST {lookup_url}"
            LogBuffer.info().write(web_info + debug_info)
            debug_info = f"           请求: {lookup_body}"
            LogBuffer.info().write(web_info + debug_info)

            t0 = time.time()
            res_lookup, error = await manager.computed.async_client.post_json(
                lookup_url, json_data=lookup_body, headers=headers
            )
            elapsed = time.time() - t0

            if res_lookup is None:
                debug_info = f"           网络错误 (耗时: {elapsed:.2f}s): {error}"
                LogBuffer.info().write(web_info + debug_info)
            else:
                ok, err = _check_response(res_lookup, "本地匹配")
                if ok:
                    movie_id = res_lookup.get("data")
                    if movie_id and isinstance(movie_id, str):
                        lookup_hit = True
                        debug_info = f"           命中影片 ID: {movie_id} (耗时: {elapsed:.2f}s)"
                        LogBuffer.info().write(web_info + debug_info)
                    else:
                        debug_info = f"           未命中 (data={movie_id}, 耗时: {elapsed:.2f}s)"
                        LogBuffer.info().write(web_info + debug_info)
                else:
                    debug_info = f"           未命中: {err} (耗时: {elapsed:.2f}s)"
                    LogBuffer.info().write(web_info + debug_info)
        except Exception as e:
            debug_info = f"           异常 (将回退到搜索): {e}"
            LogBuffer.info().write(web_info + debug_info)

        # ============================================================
        # Step 2: Detail — Lookup 命中时获取完整元数据
        # ============================================================
        detail_success = False
        if lookup_hit and movie_id:
            detail_url = f"{base_url}/api/v1/movie/{movie_id}"
            debug_info = f"[影片详情] GET {detail_url}"
            LogBuffer.info().write(web_info + debug_info)

            t0 = time.time()
            res_detail, error = await manager.computed.async_client.get_json(
                detail_url, headers=headers
            )
            elapsed = time.time() - t0

            if res_detail is not None:
                ok, err = _check_response(res_detail, "影片详情")
                if ok:
                    detail = res_detail.get("data", {})
                    if isinstance(detail, dict) and detail:
                        dic = _build_result(detail, detail_url, number)
                        debug_info = f"           数据获取成功！(耗时: {elapsed:.2f}s)"
                        LogBuffer.info().write(web_info + debug_info)
                        detail_success = True
                    else:
                        debug_info = f"           详情 data 无效 (将回退到搜索)"
                        LogBuffer.info().write(web_info + debug_info)
                else:
                    debug_info = f"           详情请求失败: {err} (将回退到搜索)"
                    LogBuffer.info().write(web_info + debug_info)
            else:
                debug_info = f"           详情网络错误 (将回退到搜索): {error}"
                LogBuffer.info().write(web_info + debug_info)

        # ============================================================
        # Step 3: Search — 保底方案，多数据源检索并合并
        # ============================================================
        if not detail_success:
            search_url = f"{base_url}/api/v1/movie/search"
            search_body = {"keyword": number}
            debug_info = f"[数据源检索] POST {search_url}"
            LogBuffer.info().write(web_info + debug_info)
            debug_info = f"             请求: {search_body}"
            LogBuffer.info().write(web_info + debug_info)

            t0 = time.time()
            res_search, error = await manager.computed.async_client.post_json(
                search_url, json_data=search_body, headers=headers
            )
            elapsed = time.time() - t0

            if res_search is None:
                debug_info = f"             网络错误 (耗时: {elapsed:.2f}s): {error}"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            code = res_search.get("code", 0)
            message = res_search.get("message", "")

            if code == 401:
                raise Exception("AMMDS API Key 无效或已过期，请在 AMMDS 管理面板重新生成")
            if code == 500:
                raise Exception(
                    f"AMMDS 数据源检索服务异常 ({message})。"
                    "请检查 AMMDS 管理面板 → 数据源设置，确保数据源已正确配置。"
                )

            ok, err = _check_response(res_search, "数据源检索")
            if not ok:
                if code == 200 and isinstance(res_search.get("data"), list):
                    # 空数组：搜索成功但无结果
                    debug_info = f"             未搜索到影片: {number} (耗时: {elapsed:.2f}s)"
                    LogBuffer.info().write(web_info + debug_info)
                    raise Exception(debug_info)
                debug_info = f"             {err} (耗时: {elapsed:.2f}s)"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(f"AMMDS 检索失败: {message} (code={code})")

            search_results = res_search.get("data", [])
            if not isinstance(search_results, list) or not search_results:
                debug_info = f"             未搜索到影片: {number} (耗时: {elapsed:.2f}s)"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            debug_info = (
                f"             搜索到 {len(search_results)} 条结果, "
                f"多源合并构建 (耗时: {elapsed:.2f}s)"
            )
            LogBuffer.info().write(web_info + debug_info)

            dic = _build_result_from_search(search_results, number)

    except Exception:
        print(traceback.format_exc())
        dic = _empty_result(number)

    result = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    LogBuffer.req().write(f"({round(time.time() - start_time)}s) ")
    return result
