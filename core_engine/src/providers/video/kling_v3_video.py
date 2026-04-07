"""DashScope Kling V3 Video Generation Provider.

Supports:
  - text_to_video(): single prompt T2V
  - multi_shot_video(): multi-shot with individual shot prompts
  - image_to_video(): first-frame I2V

API: POST https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis
Region: Beijing ONLY (same DASHSCOPE_API_KEY)
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Literal, Optional

import requests

_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks"


def _log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"  [KlingVideo {ts}] {msg}", flush=True)


class KlingVideoProvider:
    """Kling V3 video generation via DashScope API."""

    def __init__(
        self,
        output_dir: Path | str = "core_engine/output/videos/kling_v3",
        model: str = "kling/kling-v3-video-generation",
        mode: Literal["std", "pro"] = "pro",
        aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9",
        audio: bool = True,
        watermark: bool = False,
    ) -> None:
        api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY not set")
        self.model = model
        self.mode = mode
        self.aspect_ratio = aspect_ratio
        self.audio = audio
        self.watermark = watermark
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        self._poll_headers = {"Authorization": f"Bearer {api_key}"}

    # ── Public API ─────────────────────────────────────────────────

    def text_to_video(
        self,
        prompt: str,
        duration: Literal[5, 10] = 10,
    ) -> Path:
        """Single prompt → video."""
        payload = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {
                "mode": self.mode,
                "aspect_ratio": self.aspect_ratio,
                "duration": duration,
                "audio": self.audio,
                "watermark": self.watermark,
            },
        }
        _log(f"T2V submit — {duration}s {self.mode} model={self.model}")
        return self._submit_and_poll(payload)

    def multi_shot_video(
        self,
        shots: list[dict],
        duration: Literal[5, 10] = 10,
        shot_type: Literal["intelligence", "customize"] = "customize",
    ) -> Path:
        """Multi-shot video generation.

        Args:
            shots: list of {"index": int, "prompt": str, "duration": int}
                   duration per shot should sum to total duration
            duration: total video duration (5 or 10)
            shot_type: "customize" for manually specified shots, "intelligence" for auto
        """
        payload = {
            "model": self.model,
            "input": {
                "prompt": "",
                "multi_shot": True,
                "shot_type": shot_type,
                "multi_prompt": shots,
                "media": [],
                "element_list": [],
            },
            "parameters": {
                "mode": self.mode,
                "aspect_ratio": self.aspect_ratio,
                "duration": duration,
                "audio": self.audio,
                "watermark": self.watermark,
            },
        }
        _log(f"Multi-shot submit — {len(shots)} shots, {duration}s {self.mode}")
        for s in shots:
            _log(f"  Shot {s['index']}: {s['prompt'][:60]}...")
        return self._submit_and_poll(payload)

    def image_to_video(
        self,
        prompt: str,
        image_url: str,
        duration: Literal[5, 10] = 10,
    ) -> Path:
        """First-frame I2V."""
        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt,
                "media": [{"type": "first_frame", "url": image_url}],
            },
            "parameters": {
                "mode": self.mode,
                "aspect_ratio": self.aspect_ratio,
                "duration": duration,
                "audio": self.audio,
                "watermark": self.watermark,
            },
        }
        _log(f"I2V submit — {duration}s {self.mode} first_frame={image_url[:60]}...")
        return self._submit_and_poll(payload)

    # ── Internal ───────────────────────────────────────────────────

    def _submit_and_poll(self, payload: dict) -> Path:
        # Submit
        resp = requests.post(_API_URL, headers=self._headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        task_id = data.get("output", {}).get("task_id")
        status = data.get("output", {}).get("task_status", "UNKNOWN")
        if not task_id:
            raise RuntimeError(f"No task_id in response: {data}")
        _log(f"Task submitted — task_id={task_id} status={status}")

        # Poll (max 30 min)
        for attempt in range(120):
            time.sleep(15)
            try:
                poll_resp = requests.get(
                    f"{_TASK_URL}/{task_id}",
                    headers=self._poll_headers,
                    timeout=20,
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
                _log("Generation complete — downloading...")
                return self._download_video(video_url)

            elif status == "FAILED":
                code = poll_data.get("output", {}).get("code", "")
                msg = poll_data.get("output", {}).get("message", "")
                raise RuntimeError(f"Kling video task failed: {code} - {msg}")

            elif status in ("CANCELED", "UNKNOWN"):
                raise RuntimeError(f"Kling video task {status}: {poll_data}")

            else:
                elapsed = (attempt + 1) * 15
                if attempt % 4 == 0:
                    _log(f"Status: {status} ({elapsed}s elapsed)")

        raise TimeoutError("Kling video task timed out after 1800s")

    def _download_video(self, url: str) -> Path:
        ts = int(time.time())
        out_path = self.output_dir / f"kling_v3_video_{ts}.mp4"
        _log(f"Downloading → {out_path.name}")
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
        size_mb = out_path.stat().st_size / (1024 * 1024)
        _log(f"Saved: {out_path} ({size_mb:.1f} MB)")
        return out_path
