"""Wan 2.6 video generation provider via fal.ai API.

Endpoints used:
  - wan/v2.6/text-to-video  (T2V)
  - wan/v2.6/image-to-video (I2V)

Reference: https://fal.ai/models/wan/v2.6/text-to-video/api
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Literal, Optional

import requests

from core_engine.src.providers.base import VideoProvider

_FAL_KEY = os.getenv("FAL_KEY", "")


def _log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"  [Wan2.6 {ts}] {msg}")


class FalWanProvider(VideoProvider):
    """Wan 2.6 via fal.ai REST API (no fal_client dependency required)."""

    T2V_ENDPOINT = "https://queue.fal.run/wan/v2.6/text-to-video"
    I2V_ENDPOINT = "https://queue.fal.run/wan/v2.6/image-to-video"
    STATUS_BASE = "https://queue.fal.run/wan/v2.6"

    def __init__(self, output_dir: str | Path = "core_engine/output/videos", api_key: str = ""):
        self.api_key = api_key or _FAL_KEY
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }

    # ---- public API ----

    def text_to_video(
        self,
        prompt: str,
        duration: Literal["5", "10", "15"] = "5",
        resolution: Literal["720p", "1080p"] = "1080p",
        aspect_ratio: str = "16:9",
        audio_url: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Path:
        if not self.api_key:
            return self._placeholder("t2v", prompt)

        payload: dict = {
            "prompt": prompt[:800],
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "enable_prompt_expansion": True,
            "multi_shots": True,
            "enable_safety_checker": True,
            "negative_prompt": "low resolution, error, worst quality, low quality, defects",
        }
        if audio_url:
            payload["audio_url"] = audio_url
        if seed is not None:
            payload["seed"] = seed

        _log(f"T2V submit — {duration}s {resolution} {aspect_ratio}")
        return self._submit_and_poll(self.T2V_ENDPOINT, "text-to-video", payload)

    def image_to_video(
        self,
        prompt: str,
        image_url: str,
        duration: Literal["5", "10", "15"] = "5",
        resolution: Literal["480p", "720p", "1080p"] = "1080p",
        audio_url: Optional[str] = None,
    ) -> Path:
        if not self.api_key:
            return self._placeholder("i2v", prompt)

        payload: dict = {
            "prompt": prompt[:800],
            "image_url": image_url,
            "duration": duration,
            "resolution": resolution,
            "enable_safety_checker": True,
        }
        if audio_url:
            payload["audio_url"] = audio_url

        _log(f"I2V submit — {duration}s {resolution}")
        return self._submit_and_poll(self.I2V_ENDPOINT, "image-to-video", payload)

    # ---- internal helpers ----

    def _submit_and_poll(self, endpoint: str, mode: str, payload: dict) -> Path:
        """Submit a job to fal queue, poll until complete, download result."""
        resp = requests.post(endpoint, json=payload, headers=self._headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        request_id = data.get("request_id")

        if not request_id:
            # synchronous response (unlikely for video)
            return self._download_video(data, mode)

        _log(f"Queued — request_id={request_id}")

        # poll for completion
        status_url = f"{self.STATUS_BASE}/{mode}/requests/{request_id}/status"
        result_url = f"{self.STATUS_BASE}/{mode}/requests/{request_id}"

        for attempt in range(120):  # max ~10 min
            time.sleep(5)
            try:
                sr = requests.get(status_url, headers=self._headers, timeout=15)
                sr.raise_for_status()
                status = sr.json().get("status", "")
            except Exception:
                continue

            if status == "COMPLETED":
                _log("Generation complete — downloading...")
                rr = requests.get(result_url, headers=self._headers, timeout=30)
                rr.raise_for_status()
                return self._download_video(rr.json(), mode)
            elif status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"Wan 2.6 {mode} failed: {sr.json()}")
            else:
                if attempt % 6 == 0:
                    _log(f"Still processing... ({attempt * 5}s)")

        raise TimeoutError(f"Wan 2.6 {mode} timed out after 600s")

    def _download_video(self, result: dict, mode: str) -> Path:
        video_url = result.get("video", {}).get("url")
        if not video_url:
            raise ValueError(f"No video URL in response: {result}")

        ts = int(time.time())
        out_path = self.output_dir / f"wan26_{mode}_{ts}.mp4"
        _log(f"Downloading → {out_path.name}")

        r = requests.get(video_url, stream=True, timeout=120)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        _log(f"Saved: {out_path}")
        return out_path

    def _placeholder(self, mode: str, prompt: str) -> Path:
        """Return a placeholder file when no API key is configured."""
        _log(f"[Placeholder] FAL_KEY not set — skipping {mode}")
        out_path = self.output_dir / f"placeholder_{mode}.txt"
        out_path.write_text(
            f"[Placeholder] Wan 2.6 {mode} video\n"
            f"Prompt: {prompt[:200]}\n"
            f"Configure FAL_KEY to enable real generation.\n",
            encoding="utf-8",
        )
        return out_path
