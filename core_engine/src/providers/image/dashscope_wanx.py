"""Alibaba Cloud DashScope Wanx text-to-image provider.

Uses wanx-v1 model (万相) for image generation.
Same API key as video generation (DASHSCOPE_API_KEY).

Submit: POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis
Poll:   GET  https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}
Output: output.results[0].url
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

from core_engine.src.providers.base import ImageProvider

_DASHSCOPE_KEY = os.getenv("DASHSCOPE_API_KEY", "")
_SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks"


def _log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"  [Wanx T2I {ts}] {msg}")


class DashScopeWanxImageProvider(ImageProvider):
    """Text-to-image via Alibaba Cloud DashScope wanx-v1."""

    def __init__(
        self,
        output_dir: str | Path = "core_engine/output/assets",
        api_key: str = "",
        model: str = "wanx-v1",
    ):
        self.api_key = api_key or _DASHSCOPE_KEY
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = model
        self._last_image_url: str = ""

    def generate(
        self,
        prompt: str,
        style: str = "cinematic",
        size: tuple[int, int] = (1280, 720),
    ) -> Path:
        if not self.api_key:
            return self._placeholder(prompt)

        # wanx-v1 size format: "WxH"
        w, h = size
        size_str = f"{w}*{h}"

        # Map style to wanx style tags
        style_map = {
            "cinematic": "<photography>",
            "anime": "<anime>",
            "minimalist": "<flat illustration>",
            "documentary": "<photography>",
            "tech": "<3d cartoon>",
        }
        wanx_style = style_map.get(style.lower(), "<auto>")

        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt[:800],
                "negative_prompt": "low quality, blurry, watermark, text, signature, logo",
            },
            "parameters": {
                "style": wanx_style,
                "size": size_str,
                "n": 1,
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        _log(f"Submitting T2I — size={size_str} style={wanx_style}")
        resp = requests.post(_SUBMIT_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        task_id = data.get("output", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"No task_id in response: {data}")
        _log(f"Task submitted — task_id={task_id}")

        # Poll for completion (image gen is fast, usually <60s)
        poll_headers = {"Authorization": f"Bearer {self.api_key}"}
        for attempt in range(30):
            time.sleep(10)
            poll_resp = requests.get(
                f"{_TASK_URL}/{task_id}",
                headers=poll_headers,
                timeout=15,
            )
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()
            status = poll_data.get("output", {}).get("task_status", "UNKNOWN")

            if status == "SUCCEEDED":
                results = poll_data.get("output", {}).get("results", [])
                if not results:
                    raise RuntimeError(f"SUCCEEDED but no results: {poll_data}")
                image_url = results[0].get("url", "")
                _log(f"Image ready: {image_url[:80]}...")
                self._last_image_url = image_url
                return self._download(image_url)

            elif status in ("FAILED", "CANCELED"):
                raise RuntimeError(f"T2I task {status}: {poll_data}")

            elapsed = (attempt + 1) * 10
            if attempt % 3 == 0:
                _log(f"Status: {status} ({elapsed}s)")

        raise TimeoutError("Wanx T2I task timed out after 300s")

    def _download(self, url: str) -> Path:
        ts = int(time.time())
        out_path = self.output_dir / f"wanx_t2i_{ts}.png"
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        size_kb = out_path.stat().st_size // 1024
        _log(f"Saved: {out_path.name} ({size_kb}KB)")
        return out_path

    def _placeholder(self, prompt: str) -> Path:
        _log("[Placeholder] DASHSCOPE_API_KEY not set")
        out_path = self.output_dir / f"img_placeholder_{int(time.time())}.txt"
        out_path.write_text(f"[Placeholder]\n{prompt[:300]}\n", encoding="utf-8")
        return out_path
