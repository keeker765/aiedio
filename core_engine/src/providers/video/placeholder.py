"""Placeholder video provider — used when no API key is available."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Literal, Optional

from core_engine.src.providers.base import VideoProvider


class PlaceholderVideoProvider(VideoProvider):
    """Returns text stubs instead of real videos for local testing."""

    def __init__(self, output_dir: str | Path = "core_engine/output/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def text_to_video(
        self,
        prompt: str,
        duration: Literal["5", "10", "15"] = "5",
        resolution: Literal["720p", "1080p"] = "1080p",
        aspect_ratio: str = "16:9",
        audio_url: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Path:
        return self._write_stub("t2v", prompt, duration, resolution)

    def image_to_video(
        self,
        prompt: str,
        image_url: str,
        duration: Literal["5", "10", "15"] = "5",
        resolution: Literal["480p", "720p", "1080p"] = "1080p",
        audio_url: Optional[str] = None,
    ) -> Path:
        return self._write_stub("i2v", prompt, duration, resolution)

    def _write_stub(self, mode: str, prompt: str, duration: str, resolution: str) -> Path:
        ts = int(time.time())
        path = self.output_dir / f"placeholder_{mode}_{ts}.txt"
        path.write_text(
            f"[Placeholder Video — {mode.upper()}]\n"
            f"Duration: {duration}s | Resolution: {resolution}\n"
            f"Prompt: {prompt[:300]}\n"
            f"\nTo generate real videos, set FAL_KEY environment variable.\n",
            encoding="utf-8",
        )
        print(f"  [Placeholder] Wrote stub: {path.name}")
        return path
