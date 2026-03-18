"""
故事提示词生成器 — 从 GitHub 热点生成 AI 视频故事板提示词
调用方式: python core_engine/src/story_prompt.py
"""
import sys
import os
import requests as req

# 将 crawler/src 加入搜索路径，以便导入 github_spider
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "crawler", "src"))

from github_spider import fetch_github_hot

_OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm(prompt: str) -> str:
    """通过 OpenRouter 调用免费 LLM"""
    if not _OPENROUTER_KEY:
        return f"[占位回复] API Key 未配置。收到指令: '{prompt[:80]}...'"

    resp = req.post(
        _API_URL,
        headers={
            "Authorization": f"Bearer {_OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": _MODEL,
            "messages": [
                {"role": "system", "content": "你是一个帮助生成视频脚本和内容创意的 AI 助手。"},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_story_prompt(trend: dict) -> str:
    """根据单条热点数据，构造故事板生成提示词"""
    return (
        f"你是一个短视频创意策划师。\n"
        f"以下是一个当前热门话题：\n"
        f"- 平台: {trend['platform']}\n"
        f"- 标题: {trend['title']}\n"
        f"- 热度: {trend['hot_value']}\n\n"
        f"请基于这个话题，生成一个4场景的短视频故事板，包含：\n"
        f"1. 每个场景的画面描述\n"
        f"2. 对应的旁白/台词\n"
        f"3. 推荐的视觉风格\n"
        f"请用JSON格式返回，格式如下：\n"
        f'{{"scenes": [{{"scene_id": 1, "visual": "...", "narration": "...", "style": "..."}}]}}'
    )


def generate_stories():
    """抓取 GitHub 热点 → 生成故事提示词 → 调用 AI 引擎"""
    print("=== 抓取 GitHub 热点 ===")
    trends = fetch_github_hot()

    if not trends:
        print("未获取到热点数据")
        return []

    print(f"获取到 {len(trends)} 条热点\n")

    results = []
    for i, trend in enumerate(trends, 1):
        print(f"--- [{i}/{len(trends)}] {trend['title']} ({trend['hot_value']}) ---")
        prompt = build_story_prompt(trend)
        print(f"提示词已构造，调用 AI 引擎...\n")

        story = call_llm(prompt)
        print(story)
        print()

        results.append({
            "trend": trend,
            "prompt": prompt,
            "story": story
        })

    return results


if __name__ == "__main__":
    generate_stories()
