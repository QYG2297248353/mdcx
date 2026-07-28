#!/usr/bin/env python3
import re
import time
import traceback
from typing import Any
from urllib.parse import urlparse

from ..config.manager import manager
from ..models.log_buffer import LogBuffer
from ..utils.language import is_japanese


def get_year(release):
    try:
        return re.findall(r"\d{4}", release)[0]
    except Exception:
        return ""


def get_actor_photo(actor):
    actor = actor.split(",")
    data = {}
    for i in actor:
        data[i] = ""
    return data


def _extract_mosaic(detail):
    mosaic_val = detail.get("mpaa", "")
    if not mosaic_val:
        mosaic_val = detail.get("mosaic", "")
    if "无码" in str(mosaic_val):
        return "无码"
    if "有码" in str(mosaic_val):
        return "有码"
    return "有码"


def _extract_actors(actors_data):
    if isinstance(actors_data, dict):
        return ",".join(actors_data.keys())
    if isinstance(actors_data, list):
        return ",".join(actors_data)
    return ""


def _extract_directors(directors):
    if isinstance(directors, list):
        return ",".join(directors)
    return ""


def _extract_genres_tags(detail):
    parts = []
    genres = detail.get("genre", [])
    if isinstance(genres, list):
        parts.extend(genres)
    tags = detail.get("tag", [])
    if isinstance(tags, list):
        parts.extend(tags)
    return ",".join(parts)


def _extract_studio(detail):
    studio_list = detail.get("studio", [])
    if isinstance(studio_list, list):
        return ",".join(studio_list)
    return ""


def _extract_publisher(detail):
    pub_list = detail.get("issueStudio", [])
    if isinstance(pub_list, list):
        return ",".join(pub_list)
    return ""


def _extract_series(detail):
    sets = detail.get("sets", {})
    if isinstance(sets, dict):
        return sets.get("name", "")
    return ""


def _build_result(detail, detail_url, number):
    orig_title = detail.get("originalTitle", "")
    title_cn = detail.get("titleCn", "")
    title = orig_title or title_cn or ""

    plot = detail.get("plot", "")
    plot_cn = detail.get("plotCn", "")
    outline = plot_cn or plot or ""

    actor = _extract_actors(detail.get("actors", {}))
    all_actor = actor

    director = _extract_directors(detail.get("director", []))

    release = detail.get("premiered", "")
    year = get_year(release)

    runtime_val = detail.get("runtime", "")
    runtime = str(runtime_val) if runtime_val else ""

    score_val = detail.get("rating", "")
    score = str(score_val) if score_val else ""

    poster = detail.get("poster", "")
    thumb = detail.get("thumb", "")
    fanart = detail.get("fanart", "")
    extrafanart_val = detail.get("extrafanart", "")

    extrafanart = []
    if fanart:
        extrafanart.append(fanart)
    if isinstance(extrafanart_val, str) and extrafanart_val:
        extrafanart.append(extrafanart_val)
    elif isinstance(extrafanart_val, list):
        extrafanart.extend(extrafanart_val)

    uniqueid = detail.get("uniqueid", number)

    tag = _extract_genres_tags(detail)
    studio = _extract_studio(detail)
    publisher = _extract_publisher(detail) or studio
    series = _extract_series(detail)
    mosaic = _extract_mosaic(detail)

    return {
        "number": uniqueid,
        "title": title,
        "originaltitle": orig_title,
        "actor": actor,
        "all_actor": all_actor,
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
        "actor_photo": get_actor_photo(actor),
        "all_actor_photo": get_actor_photo(all_actor),
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


def _build_result_from_search(matched_items, number):
    """从多个搜索结果条目中合并构建结果（不调用Detail API）"""
    if not matched_items:
        return None

    # 以第一个匹配条目为基础
    base = matched_items[0]

    def _get_first(items, key):
        """从多个条目中取首个非空值"""
        for item in items:
            val = item.get(key)
            if val is not None and val != "" and val != [] and val != {}:
                return val
        return base.get(key, "")

    def _get_first_jp(items, key):
        """优先取日文值，找不到日文则取首个非空值"""
        for item in items:
            val = item.get(key)
            if val is not None and val != "" and val != [] and val != {} and is_japanese(str(val)):
                return val
        return _get_first(items, key)

    def _collect_unique(items, key):
        """收集所有条目中指定字段的唯一非空值"""
        result = []
        for item in items:
            val = item.get(key)
            if val and val not in result:
                result.append(val)
        return result

    def _merge_list(items, key):
        """合并多个条目中的列表字段，去重"""
        result = []
        for item in items:
            val = item.get(key, [])
            if isinstance(val, (list, tuple)):
                for v in val:
                    if v and v not in result:
                        result.append(v)
        return result

    def _get_first_nonzero(items, key):
        """从多个条目中取首个非零数值"""
        for item in items:
            val = item.get(key)
            if val:
                return val
        return base.get(key, "")

    # 将日文标题的条目排在前面，确保日文优先
    matched_items = sorted(matched_items, key=lambda x: is_japanese(x.get("title", "") or ""), reverse=True)

    # 字符串字段：优先取日文值
    title = _get_first_jp(matched_items, "title") or ""
    summary = _get_first_jp(matched_items, "summary") or ""
    cover = _get_first(matched_items, "cover") or ""
    thumb = _get_first(matched_items, "thumb") or ""
    director = _get_first_jp(matched_items, "director") or ""
    studio = _get_first_jp(matched_items, "studio") or ""
    series = _get_first_jp(matched_items, "series") or ""
    release = _get_first(matched_items, "release") or ""
    label = _get_first_jp(matched_items, "label") or ""
    mosaic = _get_first_jp(matched_items, "mosaic") or ""
    url = _get_first(matched_items, "url") or ""

    # 列表字段：合并去重
    actors = _merge_list(matched_items, "actors")
    genres = _merge_list(matched_items, "genres")
    tags = _merge_list(matched_items, "tags")
    preview_images = _merge_list(matched_items, "previewImages")

    # 合并 all tags
    all_tag_parts = []
    all_tag_parts.extend(genres)
    all_tag_parts.extend(tags)

    # 数值字段：取首个非零
    runtime_val = _get_first_nonzero(matched_items, "runtime")
    runtime = str(runtime_val) if runtime_val else ""
    score_val = _get_first_nonzero(matched_items, "score")
    score_val = score_val if score_val else 0
    if isinstance(score_val, float) and score_val == 0:
        score = ""
    else:
        score = str(score_val) if score_val else ""

    # 演员
    actor = ",".join([a for a in actors if a])

    # 标签
    tag = ",".join(all_tag_parts)

    # 图片：收集所有数据源的全部唯一URL，实现多源fallback
    all_covers = _collect_unique(matched_items, "cover")
    all_thumbs = _collect_unique(matched_items, "thumb")
    all_previews = []
    for item in matched_items:
        previews = item.get("previewImages", [])
        if isinstance(previews, list):
            for p in previews:
                if p and p not in all_previews:
                    all_previews.append(p)

    # poster: 依次尝试全部 cover -> 全部 thumb -> 全部 preview 的首个
    poster = ""
    if all_covers:
        poster = all_covers[0]
    if not poster and all_thumbs:
        poster = all_thumbs[0]
    if not poster and all_previews:
        poster = all_previews[0]

    # thumb: 首个 thumb 或 cover
    thumb = all_thumbs[0] if all_thumbs else (all_covers[0] if all_covers else "")

    # extrafanart: 合并所有来源的 thumb + previewImages，去重，排除已用作 poster 的首张
    extrafanart = []
    for t in all_thumbs:
        if t and t not in extrafanart:
            extrafanart.append(t)
    for img in all_previews:
        if img and img not in extrafanart:
            extrafanart.append(img)
    # 如果 poster 在 extrafanart 中且是第一个，移除避免重复
    if poster and extrafanart and extrafanart[0] == poster:
        extrafanart.pop(0)

    # thumb 备选列表（供后续下载失败重试）
    thumb_fallback = all_thumbs[1:] if len(all_thumbs) > 1 else []

    year = get_year(release)

    # 马赛克判定
    mosaic_result = "有码"
    mosaic_lower = str(mosaic).lower() if mosaic else ""
    if "无码" in mosaic_lower or "uncensored" in mosaic_lower:
        mosaic_result = "无码"

    return {
        "number": _get_first(matched_items, "number") or number,
        "title": title,
        "originaltitle": title,
        "actor": actor,
        "all_actor": actor,
        "outline": summary,
        "originalplot": summary,
        "tag": tag,
        "release": release,
        "year": year,
        "runtime": runtime,
        "score": score,
        "series": series,
        "director": director,
        "studio": studio,
        "publisher": studio,
        "source": "ammds",
        "actor_photo": {},
        "all_actor_photo": {},
        "thumb": thumb,
        "poster": poster,
        "extrafanart": extrafanart,
        "trailer": "",
        "image_download": False,
        "image_cut": "",
        "mosaic": mosaic_result,
        "website": url,
        "wanted": "",
        "thumb_fallback": thumb_fallback,
    }


def _check_response(res: Any, context: str) -> tuple[bool, str]:
    """
    校验 AMMDS API 统一响应格式: {code, message, data, timestamp}

    Returns:
        (ok, error_detail): ok=True 表示 code==200 且 data 不为 None
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
    return True, ""


async def main(
    number,
    appoint_url="",
    file_path="",
    **kwargs,
):
    start_time = time.time()
    website_name = "ammds"
    LogBuffer.req().write(f"-> {website_name}")

    ammds_url = manager.config.ammds_url
    api_key = manager.config.ammds_api_key

    LogBuffer.info().write("\n    🌐 ammds")
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
        if not api_key:
            debug_info = "请添加 AMMDS API Key 后刮削！（「设置」-「网络」-「AMMDS API Key」）"
            LogBuffer.info().write(web_info + debug_info)
            raise Exception(debug_info)

        parsed = urlparse(ammds_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        movie_id = None

        # ---- appoint_url path ----
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
            try:
                dic = _build_result(detail, detail_url, number)
                debug_info = f"数据获取成功！(耗时: {elapsed:.2f}s)"
                LogBuffer.info().write(web_info + debug_info)
            except Exception as e:
                debug_info = f"数据生成出错: {str(e)}"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            result = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
            LogBuffer.req().write(f"({round(time.time() - start_time)}s) ")
            return result

        # ============================================================
        # Step 1: Lookup — 查询库内是否已入库
        # ============================================================
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
                    if movie_id:
                        lookup_hit = True
                        debug_info = f"           命中影片 ID: {movie_id} (耗时: {elapsed:.2f}s)"
                        LogBuffer.info().write(web_info + debug_info)
                else:
                    debug_info = f"           未命中 (耗时: {elapsed:.2f}s)"
                    LogBuffer.info().write(web_info + debug_info)
        except Exception as e:
            debug_info = f"           异常 (将回退到搜索): {str(e)}"
            LogBuffer.info().write(web_info + debug_info)

        # ============================================================
        # Step 2: Detail — 仅当 Lookup 命中时用库内 ID 获取详情
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
                        try:
                            dic = _build_result(detail, detail_url, number)
                            debug_info = f"           数据获取成功！(耗时: {elapsed:.2f}s)"
                            LogBuffer.info().write(web_info + debug_info)
                            detail_success = True
                        except Exception as e:
                            debug_info = f"           数据生成出错: {str(e)}"
                            LogBuffer.info().write(web_info + debug_info)
                    else:
                        debug_info = f"           详情 data 为空 (将回退到搜索)"
                        LogBuffer.info().write(web_info + debug_info)
                else:
                    debug_info = f"           详情请求失败: {err} (将回退到搜索)"
                    LogBuffer.info().write(web_info + debug_info)
            else:
                debug_info = f"           详情网络错误 (将回退到搜索): {error}"
                LogBuffer.info().write(web_info + debug_info)

        # ============================================================
        # Step 3: Search — 保底方案，搜索结果直接构建不调Detail
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

            ok, err = _check_response(res_search, "数据源检索")
            if not ok:
                debug_info = f"             {err} (耗时: {elapsed:.2f}s)"
                LogBuffer.info().write(web_info + debug_info)
                code = res_search.get("code", 0)
                message = res_search.get("message", "")
                if code == 401:
                    raise Exception("AMMDS API Key 无效或已过期，请在 AMMDS 管理面板重新生成")
                elif code == 500:
                    raise Exception(
                        f"AMMDS 数据源检索服务异常 ({message})。"
                        "请检查 AMMDS 管理面板 → 数据源设置，确保数据源已正确配置。"
                    )
                else:
                    raise Exception(f"AMMDS 检索失败: {message} (code={code})")

            search_results = res_search.get("data", [])
            if not isinstance(search_results, list) or not search_results:
                debug_info = f"             未搜索到影片: {number} (耗时: {elapsed:.2f}s)"
                LogBuffer.info().write(web_info + debug_info)
                raise Exception(debug_info)

            # 收集所有 number 匹配的条目
            matched_items = []
            for movie in search_results:
                movie_num = movie.get("number") or ""
                if movie_num.upper() == number.upper():
                    matched_items.append(movie)

            if not matched_items:
                # 无精确匹配，用第一个结果作为兜底
                matched_items = [search_results[0]]

            debug_info = (
                f"             搜索到 {len(search_results)} 条结果, "
                f"{len(matched_items)} 条精确匹配, 多源合并构建 (耗时: {elapsed:.2f}s)"
            )
            LogBuffer.info().write(web_info + debug_info)

            # 直接从搜索结果构建，不调Detail
            dic = _build_result_from_search(matched_items, number)

    except Exception:
        print(traceback.format_exc())
        dic = {
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

    result = {website_name: {"zh_cn": dic, "zh_tw": dic, "jp": dic}}
    LogBuffer.req().write(f"({round(time.time() - start_time)}s) ")
    return result
