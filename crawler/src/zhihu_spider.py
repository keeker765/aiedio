from __future__ import annotations

import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "hot_trends.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def _fallback_items() -> list[dict]:
    return [
        {"platform": "zhihu", "title": f"知乎热点 {i}", "hot_value": "N/A"}
        for i in range(1, 6)
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