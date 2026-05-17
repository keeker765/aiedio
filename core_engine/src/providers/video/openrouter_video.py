"""OpenRouter video generation provider — uses OpenRouter's /api/v1/videos endpoint.

Currently configured for kwaivgi/kling-video-o1.
Supports text-to-video and image-to-video (via first_frame_url).
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

import requests

from core_engine.src.providers.base import VideoProvider

_OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
_VIDEOS_URL = "https://openrouter.ai/api/v1/videos"
_DEFAULT_MODEL = "kwaivgi/kling-video-o1"


class OpenRouterVideoProvider(VideoProvider):
    """Video generation via OpenRouter (kwaivgi/kling-video-o1 by default;
    pass model="happyhorse-1.0-t2v" to use Happyhorse)."""

    def __init__(self, output_dir: str | Path = "core_engine/output/videos", model: str = ""):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = model or _DEFAULT_MODEL

    def text_to_video(
        self,
        prompt: str,
        duration: str = "5",
        resolution: str = "1080p",
        aspect_ratio: str = "16:9",
        audio_url: str | None = None,
        seed: int | None = None,
    ) -> Path:
        return self._generate(prompt=prompt, duration=duration, aspect_ratio=aspect_ratio)

    def image_to_video(
        self,
        prompt: str,
        image_url: str,
        duration: str = "5",
        resolution: str = "480p",
        audio_url: str | None = None,
    ) -> Path:
        return self._generate(prompt=prompt, image_url=image_url, duration=duration)

    def _generate(
        self,
        prompt: str,
        image_url: str | None = None,
        duration: str = "5",
        aspect_ratio: str = "16:9",
    ) -> Path:
        if not _OPENROUTER_KEY:
            return self._placeholder(prompt)

        # Validate duration (Kling supports 5 or 10)
        duration_sec = 10 if duration in ("10", "15") else 5

        payload = {
            "model": self.model,
            "prompt": prompt[:1000],
            "duration": duration_sec,
            "aspect_ratio": aspect_ratio,
            "resolution": "1080p",
        }
        if image_url:
            payload["first_frame_url"] = image_url

        # Step 1: Submit
        try:
            resp = requests.post(
                _VIDEOS_URL,
                headers={
                    "Authorization": f"Bearer {_OPENROUTER_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            print(f"  [WARN] OpenRouter video submit failed: {e}")
            return self._placeholder(prompt)

        job_id = result.get("id")
        if not job_id:
            print(f"  [WARN] No job id in submit response: {result}")
            return self._placeholder(prompt)

        # OpenRouter sometimes returns a polling_url that points at the binary
        # /content endpoint (which returns 401 until the video is ready), so we
        # always construct the status endpoint explicitly from the job id.
        poll_url = f"{_VIDEOS_URL}/{job_id}"

        print(f"  Video job submitted: {job_id}")
        auth_headers = {"Authorization": f"Bearer {_OPENROUTER_KEY}"}

        # Step 2: Poll for completion
        max_polls = 120  # 10 min max (5s each)
        for attempt in range(max_polls):
            try:
                poll_resp = requests.get(poll_url, headers=auth_headers, timeout=30)
                poll_resp.raise_for_status()
                status_data = poll_resp.json()
                status = status_data.get("status", "")

                if attempt % 6 == 0:  # log every ~30s
                    print(f"  Video status: {status} ({attempt * 5}s)")

                if status == "completed":
                    urls = (
                        status_data.get("unsigned_urls")
                        or status_data.get("output", {}).get("video_url")
                        or []
                    )
                    if isinstance(urls, str):
                        urls = [urls]
                    if urls:
                        return self._download(urls[0], auth_headers)
                    print(f"  [WARN] Completed but no video URLs. Response: {status_data}")
                    return self._placeholder(prompt)

                elif status == "failed":
                    err = status_data.get("error", "Unknown")
                    print(f"  [WARN] Video generation failed: {err}")
                    return self._placeholder(prompt)

                time.sleep(5)

            except Exception as e:
                print(f"  [WARN] Poll error: {e}")
                time.sleep(5)

        print(f"  [WARN] Video generation timed out (job_id={job_id})")
        return self._placeholder(prompt)

    def _download(self, url: str, auth_headers: dict | None = None) -> Path:
        """Download the generated video file.

        OpenRouter's content endpoint (/videos/{id}/content) requires the same
        Bearer auth as the rest of the API — passing headers explicitly avoids
        401s when the unsigned_url returned by the API is actually a protected
        endpoint rather than a pre-signed CDN URL.
        """
        fname = f"openrouter_vid_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp4"
        dest = self.output_dir / fname
        r = requests.get(url, headers=auth_headers or {}, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  [Video] Saved: {dest.name} ({(len(r.content) / 1024 / 1024):.1f} MB)")
        return dest

    def _placeholder(self, prompt: str) -> Path:
        """Fallback placeholder when API is unavailable."""
        fname = f"openrouter_placeholder_{int(time.time())}.txt"
        dest = self.output_dir / fname
        dest.write_text(f"[Placeholder] OpenRouter video not available. Prompt: {prompt[:200]}", encoding="utf-8")
        return dest
