from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "topic_knowledge.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def _truncate(text: str, limit: int = 200) -> str:
    text = " ".join((text or "").split())
    return text[:limit]


def _search_zhihu(topic: str, max_results: int = 5) -> list[dict]:
    url = f"https://www.zhihu.com/search?q={quote(topic)}&type=content"
    results: list[dict] = []
    seen: set[str] = set()

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text(" ", strip=True)

            if not title:
                continue

            if "zhihu.com/question" not in href and "zhihu.com/p/" not in href:
                continue

            if href.startswith("/"):
                href = "https://www.zhihu.com" + href

            if href in seen:
                continue
            seen.add(href)

            summary = ""
            if a.parent:
                summary = _truncate(a.parent.get_text(" ", strip=True).replace(title, ""))

            results.append({
                "platform": "zhihu",
                "title": _truncate(title, 100),
                "summary": summary,
                "url": href,
            })

            if len(results) >= max_results:
                break

    except Exception as e:
        print(f"Zhihu topic search failed: {e}")

    return results


def _search_github(topic: str, max_results: int = 3) -> list[dict]:
    url = "https://api.github.com/search/repositories"
    headers = dict(HEADERS)

    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results: list[dict] = []

    try:
        response = requests.get(
            url,
            headers=headers,
            params={
                "q": topic,
                "sort": "stars",
                "order": "desc",
                "per_page": max_results,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", [])[:max_results]:
            results.append({
                "platform": "github",
                "title": item.get("full_name", ""),
                "summary": _truncate(item.get("description") or ""),
                "url": item.get("html_url", ""),
            })

    except Exception as e:
        print(f"GitHub topic search failed: {e}")

    return results


def search_topic_knowledge(topic: str, max_results: int = 5) -> dict:
    zhihu_sources = _search_zhihu(topic, max_results=max_results)
    github_sources = _search_github(topic, max_results=3)

    result = {
        "topic": topic,
        "sources": zhihu_sources + github_sources
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result