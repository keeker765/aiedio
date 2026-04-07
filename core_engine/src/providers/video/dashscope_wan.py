"""Alibaba Cloud DashScope (百炼) Wan video generation provider.

Official API from Alibaba Cloud for Wan 2.7 video generation.
Supports:
  - wan2.7-t2v: Text-to-Video (prompt only, up to 5000 chars, 720P/1080P, 2-15s)
  - wan2.7-i2v: Image-to-Video (first_frame image + prompt)

Endpoints:
  Submit: POST https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis
  Poll:   GET  https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}

Reference: https://help.aliyun.com/zh/model-studio/text-to-video-api-reference
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Literal, Optional

import requests

from core_engine.src.providers.base import VideoProvider

_DASHSCOPE_KEY = os.getenv("DASHSCOPE_API_KEY", "")

_SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks"


def _log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"  [DashScope {ts}] {msg}")


class DashScopeWanProvider(VideoProvider):
    """Wan video generation via Alibaba Cloud DashScope API."""

    def __init__(
        self,
        output_dir: str | Path = "core_engine/output/videos",
        api_key: str = "",
        model: str = "wan2.7-t2v",
    ):
        self.api_key = api_key or _DASHSCOPE_KEY
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = model

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

    @property
    def _poll_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    # ---- public API ----

    def text_to_video(
        self,
        prompt: str,
        duration: Literal["5", "10", "15"] = "15",
        resolution: Literal["720p", "1080p"] = "720p",
        aspect_ratio: str = "16:9",
        audio_url: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Path:
        """T2V: Generate video from text prompt via wan2.7-t2v."""
        if not self.api_key:
            return self._placeholder("t2v", prompt)

        res_map = {"480p": "480P", "720p": "720P", "1080p": "1080P"}
        res_str = res_map.get(resolution, "720P")

        payload = {
            "model": "wan2.7-t2v",
            "input": {"prompt": prompt[:5000]},
            "parameters": {
                "resolution": res_str,
                "duration": int(duration),
                "prompt_extend": True,
                "watermark": False,
            },
        }

        _log(f"T2V submit — {duration}s {res_str} model=wan2.7-t2v")
        return self._submit_and_poll(payload)

    def image_to_video(
        self,
        prompt: str,
        image_url: str,
        duration: Literal["5", "10", "15"] = "5",
        resolution: Literal["480p", "720p", "1080p"] = "1080p",
        audio_url: Optional[str] = None,
    ) -> Path:
        """I2V: Generate video from first_frame image + prompt."""
        if not self.api_key:
            return self._placeholder("i2v", prompt)

        res_map = {"480p": "480P", "720p": "720P", "1080p": "1080P"}
        res_str = res_map.get(resolution, "1080P")

        # Build media array
        media = [{"type": "first_frame", "url": image_url}]
        if audio_url:
            media.append({"type": "driving_audio", "url": audio_url})

        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt[:5000],
                "media": media,
            },
            "parameters": {
                "resolution": res_str,
                "duration": int(duration),
                "prompt_extend": True,
                "watermark": False,
            },
        }
        if audio_url is None:
            # Let model auto-generate audio
            pass

        _log(f"I2V submit — {duration}s {res_str} model={self.model}")
        return self._submit_and_poll(payload)

    # ---- internal helpers ----

    def _submit_and_poll(self, payload: dict) -> Path:
        """Submit async task, poll for completion, download result."""
        # Step 1: Submit task
        resp = requests.post(
            _SUBMIT_URL,
            json=payload,
            headers=self._headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        task_id = data.get("output", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"No task_id in response: {data}")

        task_status = data.get("output", {}).get("task_status", "UNKNOWN")
        _log(f"Task submitted — task_id={task_id} status={task_status}")

        # Step 2: Poll for completion (max ~30 min)
        for attempt in range(120):
            time.sleep(15)
            try:
                poll_resp = requests.get(
                    f"{_TASK_URL}/{task_id}",
                    headers=self._poll_headers,
                    timeout=15,
                )
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()
            except Exception as e:
                _log(f"Poll error: {e}")
                continue

            status = poll_data.get("output", {}).get("task_status", "UNKNOWN")

            if status == "SUCCEEDED":
                video_url = poll_data["output"].get("video_url")
                if not video_url:
                    raise RuntimeError(f"SUCCEEDED but no video_url: {poll_data}")
                _log(f"Generation complete — downloading...")
                return self._download_video(video_url)

            elif status == "FAILED":
                error_code = poll_data.get("output", {}).get("code", "")
                error_msg = poll_data.get("output", {}).get("message", "")
                raise RuntimeError(f"DashScope task failed: {error_code} - {error_msg}")

            elif status in ("CANCELED", "UNKNOWN"):
                raise RuntimeError(f"DashScope task {status}: {poll_data}")

            else:
                # PENDING or RUNNING
                elapsed = (attempt + 1) * 15
                if attempt % 4 == 0:
                    _log(f"Status: {status} ({elapsed}s elapsed)")

        raise TimeoutError("DashScope task timed out after 1800s")

    def _download_video(self, video_url: str) -> Path:
        """Download generated video from DashScope URL (valid 24h)."""
        ts = int(time.time())
        out_path = self.output_dir / f"dashscope_i2v_{ts}.mp4"
        _log(f"Downloading → {out_path.name}")

        r = requests.get(video_url, stream=True, timeout=120)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        size_mb = out_path.stat().st_size / (1024 * 1024)
        _log(f"Saved: {out_path} ({size_mb:.1f} MB)")
        return out_path

    def _placeholder(self, mode: str, prompt: str) -> Path:
        _log(f"[Placeholder] DASHSCOPE_API_KEY not set — skipping {mode}")
        out_path = self.output_dir / f"placeholder_{mode}.txt"
        out_path.write_text(
            f"[Placeholder] DashScope Wan {mode} video\n"
            f"Model: {self.model}\n"
            f"Prompt: {prompt[:300]}\n"
            f"Set DASHSCOPE_API_KEY to enable real generation.\n",
            encoding="utf-8",
        )
        return out_path
