#!/usr/bin/env python3
"""ammds.py 额外边缘情况测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mdcx.crawlers.ammds import _build_result_from_search


def test_mixed_casing_match():
    data = [
        {"number": "dasd-750", "title": "EN Title", "actors": ["A"], "cover": "", "thumb": "",
         "genres": [], "tags": []},
        {"number": "DASD-750", "title": "日本語タイトル", "actors": ["B"], "cover": "", "thumb": "",
         "genres": [], "tags": []},
    ]
    r = _build_result_from_search(data, "DASD-750")
    assert r["title"] == "日本語タイトル", f"Expected JP title, got: {r['title']}"
    assert "A" in r["actor"] and "B" in r["actor"], f"Expected both actors, got: {r['actor']}"
    print("  ✓ Mixed casing match: OK")


def test_zero_score():
    data = [
        {"number": "TEST-001", "title": "T", "actors": [], "cover": "", "thumb": "",
         "genres": [], "tags": [], "score": 0.0},
    ]
    r = _build_result_from_search(data, "TEST-001")
    assert r["score"] == "", f"Expected empty score, got: {r['score']}"
    print("  ✓ Zero score handling: OK")


def test_mosaic_detection():
    data = [
        {"number": "TEST-001", "title": "T", "actors": [], "cover": "", "thumb": "",
         "genres": [], "tags": [], "mosaic": "无码"},
    ]
    r = _build_result_from_search(data, "TEST-001")
    assert r["mosaic"] == "无码", f"Expected 无码, got: {r['mosaic']}"
    print("  ✓ Mosaic detection: OK")


def test_publisher_fallback():
    data = [
        {"number": "TEST-001", "title": "T", "actors": [], "cover": "", "thumb": "",
         "genres": [], "tags": [], "studio": "TestStudio"},
    ]
    r = _build_result_from_search(data, "TEST-001")
    assert r["publisher"] == "TestStudio", f"Expected TestStudio, got: {r['publisher']}"
    print("  ✓ Publisher fallback: OK")


def test_detail_resp_check():
    """_check_response 应该接受 data={} 的 detail 响应"""
    from mdcx.crawlers.ammds import _check_response
    ok, _ = _check_response({"code": 200, "message": "ok", "data": {}}, "test")
    assert ok, "code=200 + data={} should be OK"
    print("  ✓ Detail response with empty dict: OK")


if __name__ == "__main__":
    tests = [
        test_mixed_casing_match,
        test_zero_score,
        test_mosaic_detection,
        test_publisher_fallback,
        test_detail_resp_check,
    ]
    for fn in tests:
        try:
            fn()
        except Exception as e:
            print(f"  ✗ {fn.__name__}: {e}")
            sys.exit(1)
    print("All edge case tests passed!")
