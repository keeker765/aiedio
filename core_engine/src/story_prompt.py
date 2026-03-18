"""
Story Prompt Generator — Generate AI video storyboard prompts from GitHub trends.
Usage: python core_engine/src/story_prompt.py [--lang zh]
"""
import sys
import os
import argparse
import requests as req

# Add crawler/src to search path for github_spider import
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "crawler", "src"))

from github_spider import fetch_github_hot

_OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm(prompt: str, lang: str = "en") -> str:
    """Call free LLM via OpenRouter."""
    if not _OPENROUTER_KEY:
        return f"[Placeholder] API Key not configured. Received: '{prompt[:80]}...'"

    system_msg = (
        "You are an AI assistant that helps generate video scripts and creative content. "
        f"Respond in {'Chinese' if lang == 'zh' else 'English'}."
    )

    resp = req.post(
        _API_URL,
        headers={
            "Authorization": f"Bearer {_OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": _MODEL,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_story_prompt(trend: dict, lang: str = "en") -> str:
    """Build a storyboard generation prompt from a single trend item."""
    lang_instruction = "Write all content in Chinese." if lang == "zh" else "Write all content in English."
    return (
        f"You are a short-video creative director.\n"
        f"Here is a currently trending topic:\n"
        f"- Platform: {trend['platform']}\n"
        f"- Title: {trend['title']}\n"
        f"- Popularity: {trend['hot_value']}\n\n"
        f"Based on this topic, generate a 4-scene short video storyboard containing:\n"
        f"1. Visual description for each scene\n"
        f"2. Corresponding narration/dialogue\n"
        f"3. Recommended visual style\n"
        f"{lang_instruction}\n"
        f"Return in JSON format as follows:\n"
        f'{{"scenes": [{{"scene_id": 1, "visual": "...", "narration": "...", "style": "..."}}]}}'
    )


def generate_stories(lang: str = "en"):
    """Fetch GitHub trends -> build story prompts -> call AI engine."""
    print("=== Fetching GitHub Trends ===")
    trends = fetch_github_hot()

    if not trends:
        print("No trend data retrieved.")
        return []

    print(f"Retrieved {len(trends)} trends\n")

    results = []
    for i, trend in enumerate(trends, 1):
        print(f"--- [{i}/{len(trends)}] {trend['title']} ({trend['hot_value']}) ---")
        prompt = build_story_prompt(trend, lang)
        print(f"Prompt built, calling AI engine...\n")

        story = call_llm(prompt, lang)
        print(story)
        print()

        results.append({
            "trend": trend,
            "prompt": prompt,
            "story": story
        })

    return results


if __name__ == "__main__":
    import json as _json
    parser = argparse.ArgumentParser(description="Generate storyboards from GitHub trends")
    parser.add_argument("--lang", default="en", choices=["en", "zh"], help="Output language (default: en)")
    args = parser.parse_args()
    results = generate_stories(lang=args.lang)

    # Save results to JSON file for demo
    out_path = os.path.join(_ROOT, "core_engine", "src", "generated_storyboards.json")
    output = []
    for r in results:
        try:
            scenes = _json.loads(r["story"])
        except (_json.JSONDecodeError, TypeError):
            scenes = r["story"]
        output.append({"trend": r["trend"], "storyboard": scenes})
    with open(out_path, "w", encoding="utf-8") as f:
        _json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path}")
