#!/usr/bin/env python3
"""ammds.py 单元测试 — 验证搜索结果合并逻辑和边界情况"""

import json
import sys
import os

# 确保可以 import mdcx
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mdcx.crawlers.ammds import (
    _build_result_from_search,
    _empty_result,
    _build_result,
    _check_response,
    get_year,
    get_actor_photo,
)

# ============================================================
# 测试数据: DASD-750 搜索结果的简化版 (来自 AMMDS-API.md)
# ============================================================

DASD750_SEARCH_DATA = [
    {
        "source": "metatube",
        "actors": None,
        "cover": "https://www.javbus.com/pics/cover/7wub_b.jpg",
        "director": None,
        "genres": [],
        "id": "DASD-750",
        "label": None,
        "mosaic": None,
        "number": "DASD-750",
        "previewImages": [],
        "provider": "JavBus",
        "release": "2020-10-24 08:00:00",
        "runtime": None,
        "score": 0.0,
        "series": None,
        "studio": None,
        "summary": None,
        "tags": [],
        "thumb": "https://www.javbus.com/pics/thumb/7wub.jpg",
        "title": "隣人に俺の彼女が寝取られて。「騒音クレーマーに洗脳された美人すぎる彼女」 木下ひまり",
        "url": "https://www.javbus.com/ja/DASD-750",
    },
    {
        "source": "ThePornDB",
        "actors": ["Himari Kinoshita"],
        "cover": "https://thumb.theporndb.net/rT-iPQaunhUr9K5K-Rxc4GaqHWQ=/800x1200/smart/filters:sharpen():upscale()/scene%2Fe5%2F50%2Ff9%2F3aa204b91719372be81f21c0d98a9cf%2Fbackground%2Fbg-das-my-neighbor-fucked-my-girlfriend-an-excessively-beautiful-girlfriend-who-was-deceived-by-a-dasd-750.webp",
        "director": None,
        "genres": [],
        "id": "ea8e2545-fc46-4e37-9a91-03a7639aab3c",
        "label": None,
        "mosaic": None,
        "number": "dasd-750",
        "previewImages": [],
        "provider": "jav",
        "release": "2020-10-24 08:00:00",
        "runtime": 7860,
        "score": 0.0,
        "series": None,
        "studio": "Das",
        "summary": "My Neighbor Fucked My Girlfriend. Himari Kinoshita",
        "tags": ["Asian", "Beautiful", "Cheating", "Creampie"],
        "thumb": "https://cdn.theporndb.net/scene/e5/50/f9/3aa204b91719372be81f21c0d98a9cf/background/bg-das-my-neighbor-fucked-my-girlfriend-an-excessively-beautiful-girlfriend-who-was-deceived-by-a-dasd-750.webp",
        "title": "My Neighbor Fucked My Girlfriend. - Dasd-750",
        "url": "https://r18.com/videos/vod/movies/detail/-/id=dasd00750",
    },
    {
        "source": "ThePornDB",
        "actors": ["Himari Kinoshita"],
        "cover": "https://another-cover.example.com/dasd750.jpg",
        "director": None,
        "genres": ["JAV"],
        "id": "another-id",
        "label": None,
        "mosaic": None,
        "number": "dasd-750",
        "previewImages": ["https://preview.example.com/dasd750_1.jpg"],
        "provider": "jav",
        "release": "2020-10-24 08:00:00",
        "runtime": 7860,
        "score": 0.0,
        "series": None,
        "studio": "Das",
        "summary": "",
        "tags": [],
        "thumb": "https://another-thumb.example.com/dasd750.jpg",
        "title": "Dasd-750",
        "url": "https://example.com/dasd750",
    },
    {
        "source": "StashBox",
        "actors": ["木下ひまり"],
        "cover": "https://javstash.org/images/c9c707db-34e2-415a-b4bd-9a477bbd5f55",
        "director": "三島六三郎",
        "genres": ["美女", "単体作品", "調教", "寝取り・寝取られ・ＮＴＲ", "中出し"],
        "id": "6f3a8915-0ae5-4a16-bd5a-690bacffa81e",
        "label": None,
        "mosaic": None,
        "number": "DASD-750",
        "previewImages": [],
        "provider": "3378815515802865664",
        "release": "2020-10-25 08:00:00",
        "runtime": 130,
        "score": None,
        "series": None,
        "studio": "ダスッ！",
        "summary": "「お前ら！うるせえんだよ！」念願の同棲生活をスタートさせたその日、音に神経質すぎる隣人が扉を叩き怒鳴り散らす。彼女を見ると意味深な笑顔でその場を立ち去る隣人。",
        "tags": [],
        "thumb": None,
        "title": "隣人に俺の彼女が寝取られて。「騒音クレーマーに洗脳された美人すぎる彼女」　木下ひまり",
        "url": "https://dasdas.jp/works/detail/DASD750",
    },
]


def test_check_response():
    """测试 _check_response 响应校验"""
    # 正常响应
    ok, _ = _check_response({"code": 200, "message": "ok", "data": {}}, "test")
    assert ok, "code=200 + data={} should be OK"

    # data 为 None
    ok, err = _check_response({"code": 200, "message": "ok", "data": None}, "test")
    assert not ok, "data=None should fail"
    assert "data 为空" in err

    # data 为空数组
    ok, err = _check_response({"code": 200, "message": "ok", "data": []}, "test")
    assert not ok, "data=[] should fail"
    assert "空数组" in err

    # code != 200
    ok, err = _check_response({"code": 404, "message": "not found", "data": None}, "test")
    assert not ok, "code=404 should fail"
    assert "404" in err

    # 响应为 None
    ok, err = _check_response(None, "test")
    assert not ok, "None response should fail"
    assert "响应为空" in err

    # 非 JSON
    ok, err = _check_response("not json", "test")
    assert not ok, "non-dict should fail"
    assert "非 JSON" in err

    print("  ✓ _check_response: 所有校验通过")


def test_empty_result():
    """测试空结果"""
    r = _empty_result("ABC-123")
    assert r["number"] == "ABC-123"
    assert r["title"] == ""
    assert r["source"] == "ammds"
    assert r["mosaic"] == "有码"
    assert r["extrafanart"] == []
    assert r["actor_photo"] == {}
    print("  ✓ _empty_result: 通过")


def test_get_year():
    """测试年份提取"""
    assert get_year("2020-10-24") == "2020"
    assert get_year("2020-10-24 08:00:00") == "2020"
    assert get_year("") == ""
    assert get_year("no date") == ""
    print("  ✓ get_year: 通过")


def test_get_actor_photo():
    """测试演员照片映射"""
    r = get_actor_photo("Alice,Bob,Charlie")
    assert r == {"Alice": "", "Bob": "", "Charlie": ""}
    r = get_actor_photo("")
    assert r == {}
    print("  ✓ get_actor_photo: 通过")


def test_search_merge_dasd750():
    """核心测试：DASD-750 搜索结果合并"""
    result = _build_result_from_search(DASD750_SEARCH_DATA, "DASD-750")

    # --- 标题验证：日文优先 ---
    assert result["title"].startswith("隣人に俺の彼女が寝取られて"), (
        f"标题应为日文，实际: {result['title']}"
    )

    # --- 简介验证：日文优先 ---
    assert "お前ら" in result["outline"] or "うるせえ" in result["outline"], (
        f"简介应为日文优先，实际: {result['outline']}"
    )

    # --- 演员验证：合并去重 ---
    actors = result["actor"]
    assert "Himari Kinoshita" in actors, f"演员应包含 Himari Kinoshita，实际: {actors}"
    assert "木下ひまり" in actors, f"演员应包含 木下ひまり，实际: {actors}"

    # --- 标签验证：合并 genres + tags ---
    tags = result["tag"]
    assert "美女" in tags, f"标签应包含 美女，实际: {tags}"
    assert "中出し" in tags, f"标签应包含 中出し，实际: {tags}"
    assert "Asian" in tags, f"标签应包含 Asian，实际: {tags}"
    assert "Creampie" in tags, f"标签应包含 Creampie，实际: {tags}"

    # --- 导演验证：日文优先 ---
    assert result["director"] == "三島六三郎", (
        f"导演应为 三島六三郎，实际: {result['director']}"
    )

    # --- 制作商验证：日文优先 ---
    assert result["studio"] == "ダスッ！", (
        f"制作商应为 ダスッ！，实际: {result['studio']}"
    )

    # --- 图片验证：非 javbus 优先 ---
    assert "javbus.com" not in result["poster"], (
        f"poster 不应使用 javbus.com 图片，实际: {result['poster']}"
    )
    assert result["poster"] != "", "poster 不应为空"

    # thumb 也应优先非 javbus
    if result["thumb"]:
        assert "javbus.com" not in result["thumb"], (
            f"thumb 不应使用 javbus.com 图片，实际: {result['thumb']}"
        )

    # extrafanart 应包含图片
    assert len(result["extrafanart"]) > 0, "extrafanart 不应为空"

    # --- 发行日期 ---
    assert "2020" in result["release"], (
        f"发行日期应包含 2020，实际: {result['release']}"
    )
    assert result["year"] == "2020", f"年份应为 2020，实际: {result['year']}"

    # --- 时长 ---
    assert result["runtime"] == "7860" or result["runtime"] == "130", (
        f"runtime 应从搜索结果获取，实际: {result['runtime']}"
    )

    # --- 网站 ---
    assert result["website"] != "", "website 不应为空"

    # --- source ---
    assert result["source"] == "ammds"

    # --- 马赛克 ---
    assert result["mosaic"] == "有码"

    # --- 所有字段存在 ---
    required_fields = [
        "number", "title", "originaltitle", "actor", "all_actor",
        "outline", "originalplot", "tag", "release", "year",
        "runtime", "score", "series", "director", "studio",
        "publisher", "source", "actor_photo", "all_actor_photo",
        "thumb", "poster", "extrafanart", "trailer",
        "image_download", "image_cut", "mosaic", "website", "wanted",
    ]
    for field in required_fields:
        assert field in result, f"缺少字段: {field}"

    print("  ✓ DASD-750 搜索合并: 通过")


def test_search_no_exact_match():
    """测试无精确匹配的兜底逻辑"""
    data = [
        {"number": "SSNI-999", "title": "Test Title", "actors": ["Actor A"], "cover": "", "thumb": ""},
    ]
    result = _build_result_from_search(data, "DASD-750")
    # 应使用第一个结果兜底
    assert result["title"] == "Test Title"
    assert result["actor"] == "Actor A"
    print("  ✓ 无精确匹配兜底: 通过")


def test_search_empty():
    """测试空搜索结果"""
    result = _build_result_from_search([], "ABC-123")
    assert result["number"] == "ABC-123"
    assert result["title"] == ""
    assert result["source"] == "ammds"
    print("  ✓ 空搜索结果: 通过")


def test_build_result():
    """测试 _build_result 从 Detail API 数据构建"""
    detail = {
        "uniqueid": "DASD-750",
        "originalTitle": "隣人に俺の彼女が寝取られて",
        "titleCn": "中文标题",
        "plot": "剧情简介",
        "plotCn": "中文剧情",
        "premiered": "2020-10-24",
        "runtime": 130,
        "rating": 4.5,
        "poster": "https://example.com/poster.jpg",
        "thumb": "https://example.com/thumb.jpg",
        "fanart": "https://example.com/fanart.jpg",
        "genre": ["美少女", "調教"],
        "tag": ["単体作品"],
        "studio": ["ダスッ！"],
        "issueStudio": ["发行商"],
        "sets": {"name": "系列名"},
        "director": ["三島六三郎"],
        "actors": {"木下ひまり": "主演"},
        "mpaa": "有码",
    }
    result = _build_result(detail, "https://example.com/DASD-750", "DASD-750")

    assert result["title"] == "隣人に俺の彼女が寝取られて"
    assert result["originaltitle"] == "隣人に俺の彼女が寝取られて"
    assert result["outline"] == "中文剧情"  # plotCn 优先
    assert result["originalplot"] == "剧情简介"
    assert result["actor"] == "木下ひまり"
    assert result["director"] == "三島六三郎"
    assert result["studio"] == "ダスッ！"
    assert result["publisher"] == "发行商"
    assert result["series"] == "系列名"
    assert result["release"] == "2020-10-24"
    assert result["year"] == "2020"
    assert result["runtime"] == "130"
    assert result["score"] == "4.5"
    assert result["mosaic"] == "有码"
    assert result["poster"] == "https://example.com/poster.jpg"
    assert result["thumb"] == "https://example.com/thumb.jpg"
    assert result["tag"] == "美少女,調教,単体作品"
    assert len(result["extrafanart"]) == 1
    assert result["extrafanart"][0] == "https://example.com/fanart.jpg"
    assert result["source"] == "ammds"
    assert result["website"] == "https://example.com/DASD-750"

    print("  ✓ _build_result: 通过")


def test_build_result_empty_detail():
    """测试空详情"""
    result = _build_result({}, "", "TEST-001")
    assert result["title"] == ""
    assert result["number"] == "TEST-001"
    assert result["source"] == "ammds"
    print("  ✓ _build_result 空数据: 通过")


def test_image_priority():
    """测试图片优先级：非 javbus 优先"""
    data = [
        {
            "number": "TEST-001",
            "title": "Test",
            "cover": "https://www.javbus.com/pics/cover/bad.jpg",
            "thumb": "https://www.javbus.com/pics/thumb/bad_t.jpg",
            "previewImages": [],
            "actors": [],
            "genres": [],
            "tags": [],
        },
        {
            "number": "TEST-001",
            "title": "Test 2",
            "cover": "https://good-cdn.example.com/good.jpg",
            "thumb": "https://good-cdn.example.com/good_t.jpg",
            "previewImages": [],
            "actors": [],
            "genres": [],
            "tags": [],
        },
    ]
    result = _build_result_from_search(data, "TEST-001")
    assert result["poster"] == "https://good-cdn.example.com/good.jpg", (
        f"poster 应优先非 javbus，实际: {result['poster']}"
    )
    assert result["thumb"] == "https://good-cdn.example.com/good_t.jpg", (
        f"thumb 应优先非 javbus，实际: {result['thumb']}"
    )
    print("  ✓ 图片优先级: 通过")


def test_image_fallback_all_javbus():
    """测试所有图片都是 javbus 时的降级"""
    data = [
        {
            "number": "TEST-001",
            "title": "Test",
            "cover": "https://www.javbus.com/pics/cover/only.jpg",
            "thumb": "https://www.javbus.com/pics/thumb/only_t.jpg",
            "previewImages": [],
            "actors": [],
            "genres": [],
            "tags": [],
        },
    ]
    result = _build_result_from_search(data, "TEST-001")
    # 应该降级使用 javbus 图片
    assert "javbus.com" in result["poster"], "没有其他来源时应使用 javbus"
    assert result["poster"] != "", "poster 不应为空"
    print("  ✓ 全 javbus 降级: 通过")


if __name__ == "__main__":
    print("=== AMMDS 单元测试 ===")
    print()

    tests = [
        ("_check_response 校验", test_check_response),
        ("_empty_result 空结果", test_empty_result),
        ("get_year 年份提取", test_get_year),
        ("get_actor_photo 演员照片", test_get_actor_photo),
        ("_build_result 详情构建", test_build_result),
        ("_build_result 空数据", test_build_result_empty_detail),
        ("DASD-750 搜索合并", test_search_merge_dasd750),
        ("无精确匹配兜底", test_search_no_exact_match),
        ("空搜索结果", test_search_empty),
        ("图片优先级", test_image_priority),
        ("全 javbus 降级", test_image_fallback_all_javbus),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ {name}: {e}")

    print()
    print(f"结果: {passed}/{passed+failed} 通过, {failed} 失败")
    if failed > 0:
        sys.exit(1)
