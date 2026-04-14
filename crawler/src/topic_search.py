"""Topic knowledge search — search Zhihu/GitHub for background knowledge on a topic.

Stub implementation: returns mock data so backend can start.
TODO(@HuYuxuan): Replace with real Zhihu search + GitHub API search.
"""
from __future__ import annotations

import os
import json

_OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topic_knowledge.json")


def search_topic_knowledge(topic: str, max_results: int = 5) -> dict:
    """Search for topic-related knowledge from Zhihu and GitHub.

    Args:
        topic: The topic to search for.
        max_results: Maximum number of results per platform.

    Returns:
        dict with keys: topic, sources (list of {platform, title, summary, url})
    """
    sources = []

    # Try real search, fall back to stub
    try:
        sources = _search_zhihu(topic, max_results) + _search_github(topic, max_results)
    except Exception as e:
        print(f"  [WARN] Topic search failed, using stub: {e}")

    if not sources:
        sources = [
            {
                "platform": "stub",
                "title": f"关于「{topic}」的背景知识",
                "summary": f"这是一个关于「{topic}」的占位摘要。真实数据将由爬虫模块提供。",
                "url": "",
            }
        ]

    result = {"topic": topic, "sources": sources}

    # Write to file for other modules
    try:
        with open(_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return result


def _search_zhihu(topic: str, max_results: int = 3) -> list[dict]:
    """Search Zhihu for topic-related content.

    TODO(@HuYuxuan): Implement real Zhihu search using requests/Playwright.
    """
    return []


def _search_github(topic: str, max_results: int = 3) -> list[dict]:
    """Search GitHub for topic-related repositories.

    TODO(@HuYuxuan): Implement using GitHub search API.
    """
    return []
