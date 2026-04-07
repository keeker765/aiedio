"""ZhipuAI CogView image generation provider.

Uses the existing ZHIPU_API_KEY to generate images via CogView-3 model.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

from core_engine.src.providers.base import ImageProvider

_API_KEY = os.getenv("ZHIPU_API_KEY", "")


class ZhipuImageProvider(ImageProvider):
    """Image generation via ZhipuAI CogView-3 API."""

    def __init__(self, output_dir: str | Path = "core_engine/output/assets", api_key: str = ""):
        self.api_key = api_key or _API_KEY
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        prompt: str,
        style: str = "cinematic",
        size: tuple[int, int] = (1920, 1080),
    ) -> Path:
        if not self.api_key:
            return self._placeholder(prompt, style)

        try:
            import zhipuai
            client = zhipuai.ZhipuAI(api_key=self.api_key)
            response = client.images.generations(
                model="cogview-3",
                prompt=f"{prompt}. Style: {style}",
            )
            image_url = response.data[0].url
            self._last_image_url = image_url

            ts = int(time.time())
            out_path = self.output_dir / f"cogview_{ts}.png"
            r = requests.get(image_url, timeout=60)
            r.raise_for_status()
            out_path.write_bytes(r.content)
            print(f"  [CogView] Saved: {out_path.name}")
            return out_path

        except Exception as e:
            print(f"  [CogView] Error: {e}")
            return self._placeholder(prompt, style)

    def _placeholder(self, prompt: str, style: str) -> Path:
        ts = int(time.time())
        path = self.output_dir / f"img_placeholder_{ts}.txt"
        path.write_text(
            f"[Placeholder Image]\nStyle: {style}\nPrompt: {prompt[:300]}\n"
            f"\nSet ZHIPU_API_KEY to enable real image generation.\n",
            encoding="utf-8",
        )
        print(f"  [CogView] Wrote placeholder: {path.name}")
        return path
