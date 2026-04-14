"""Unified LLM client for the Aiedio core engine.

Consolidates all LLM calling logic (OpenRouter, ZhipuAI) into one place.
Every module that needs LLM should import from here instead of rolling its own.
"""
from __future__ import annotations

import os

import requests as req

_OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
_ZHIPU_KEY = os.getenv("ZHIPU_API_KEY", "")
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


def call_llm(
    prompt: str,
    *,
    lang: str = "en",
    system_msg: str | None = None,
    json_mode: bool = False,
    timeout: int = 90,
) -> str:
    """Call LLM via OpenRouter (primary) or ZhipuAI (fallback).

    Args:
        prompt: User prompt text.
        lang: "en" or "zh" — affects default system message.
        system_msg: Custom system message. If None, uses a default.
        json_mode: If True, instructs LLM to return only valid JSON.
        timeout: Request timeout in seconds.

    Returns:
        LLM response text. Returns a placeholder string if no API key is set.
    """
    if system_msg is None:
        lang_part = "Chinese" if lang == "zh" else "English"
        json_part = " Return ONLY valid JSON, no markdown fences." if json_mode else ""
        system_msg = f"You are an AI video creative director. Respond in {lang_part}.{json_part}"

    # Priority 1: OpenRouter (free tier)
    if _OPENROUTER_KEY:
        return _call_openrouter(prompt, system_msg, timeout)

    # Priority 2: ZhipuAI GLM
    if _ZHIPU_KEY:
        return _call_zhipu(prompt, system_msg)

    # No keys configured
    return f"[Placeholder] No LLM API key configured. Received: '{prompt[:80]}...'"


def _call_openrouter(prompt: str, system_msg: str, timeout: int) -> str:
    resp = req.post(
        _OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {_OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": _OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_zhipu(prompt: str, system_msg: str) -> str:
    import zhipuai
    client = zhipuai.ZhipuAI(api_key=_ZHIPU_KEY)
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
