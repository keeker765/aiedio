from __future__ import annotations

import json
from pathlib import Path

from zhihu_spider import fetch_zhihu_hot
from github_spider import fetch_github_hot

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "hot_trends.json"

print("crawler started")


def run():
    trends = []

    zhihu_data = fetch_zhihu_hot()
    github_data = fetch_github_hot()

    if zhihu_data:
        trends.extend(zhihu_data)

    if github_data:
        trends.extend(github_data)

    # 只保留前 10 条，避免太长
    trends = trends[:10]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(trends, f, ensure_ascii=False, indent=4)

    print("抓取完成!")
    print(trends)
    return trends


if __name__ == "__main__":
    run()