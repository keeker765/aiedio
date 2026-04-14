from __future__ import annotations

import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "hot_trends.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.zhihu.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def _fallback_items() -> list[dict]:
    return [
        {"platform": "zhihu", "title": "知乎热点 1", "hot_value": "N/A"},
        {"platform": "zhihu", "title": "知乎热点 2", "hot_value": "N/A"},
        {"platform": "zhihu", "title": "知乎热点 3", "hot_value": "N/A"},
        {"platform": "zhihu", "title": "知乎热点 4", "hot_value": "N/A"},
        {"platform": "zhihu", "title": "知乎热点 5", "hot_value": "N/A"},
    ]

def fetch_zhihu_hot() -> list[dict]:
    print("Zhihu spider running")

    url = "https://www.zhihu.com/hot"
    result: list[dict] = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select(".HotItem")

        for item in items:
            title = item.select_one(".HotItem-title")
            if title is None:
                continue

            hot = item.select_one(".HotItem-metrics")
            result.append({
                "platform": "zhihu",
                "title": title.text.strip(),
                "hot_value": hot.text.strip() if hot else "N/A"
            })

            if len(result) >= 5:
                break

    except Exception as e:
        print(f"Zhihu spider failed: {e}")

    if len(result) < 5:
        result = _fallback_items()

    return result[:5]