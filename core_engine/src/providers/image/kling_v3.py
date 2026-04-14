"""Kling V3 image generation provider via Alibaba Cloud DashScope (百炼).

Model: kling/kling-v3-image-generation
  - Text-to-image
  - Image-to-image (single reference image)
  - Resolution: 1K / 2K
  - Aspect ratio: 16:9 / 9:16 / 1:1

Model: kling/kling-v3-omni-image-generation
  - Text-to-image / multi-image reference
  - result_type=series: generates narrative-consistent storyboard frames
  - Resolution: 1K / 2K / 4K

Endpoint: POST https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation
Poll:      GET  https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}
Output:    output.choices[0].message.content[].image  (URL valid 30 days)

Reference: https://help.aliyun.com/zh/model-studio/kling-image-generation-api-reference
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

import requests

from core_engine.src.providers.base import ImageProvider

_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
_SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks"

# Models
MODEL_I2I = "kling/kling-v3-image-generation"        # single reference image
MODEL_OMNI = "kling/kling-v3-omni-image-generation"  # multi-image + series mode


def _log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"  [Kling {ts}] {msg}")


def _make_headers(api_key: str, oss_resolve: bool = False) -> dict:
    h = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    if oss_resolve:
        # Required when using oss:// URLs as image references
        h["X-DashScope-OssResourceResolve"] = "enable"
    return h


class KlingImageProvider(ImageProvider):
    """Kling V3 image generation via DashScope.

    Supports:
      - generate(prompt)                     → T2I (text-to-image)
      - image_to_image(prompt, image_url)    → I2I (last frame reference)
      - series(prompts, [ref_image_url])     → Omni series mode (storyboard continuity)
    """

    def __init__(
        self,
        output_dir: str | Path = "core_engine/output/assets",
        api_key: str = "",
        resolution: str = "1k",
        aspect_ratio: str = "16:9",
    ):
        self.api_key = api_key or _API_KEY
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio
        self._last_image_url: str = ""

    # ── Public API ────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        style: str = "cinematic",
        size: tuple[int, int] = (1280, 720),
    ) -> Path:
        """T2I: Text-to-image via kling-v3."""
        return self._t2i(prompt)

    def image_to_image(
        self,
        prompt: str,
        image_url: str,
        resolution: Optional[str] = None,
    ) -> Path:
        """I2I: Generate image using a reference image (e.g. last frame of previous scene).

        Accepts:
          - https:// URL  → sent as-is
          - oss:// URL    → sent with OssResourceResolve header
          - local path    → compressed to JPEG, sent as base64 data URI
        """
        if not self.api_key:
            return self._placeholder(prompt)

        # Handle local file path → base64 JPEG
        local_path = Path(image_url) if not image_url.startswith(("http", "oss://", "data:")) else None
        if local_path and local_path.exists():
            image_url = self._to_base64_jpeg(local_path)

        is_oss = image_url.startswith("oss://")
        is_b64 = image_url.startswith("data:")

        payload = {
            "model": MODEL_I2I,
            "input": {
                "messages": [{
                    "role": "user",
                    "content": [
                        {"text": prompt[:2500]},
                        {"image": image_url},
                    ],
                }]
            },
            "parameters": {
                "n": 1,
                "aspect_ratio": self.aspect_ratio,
                "resolution": resolution or self.resolution,
                "watermark": False,
            },
        }

        mode = "oss" if is_oss else ("b64" if is_b64 else "url")
        _log(f"I2I submit — ref={mode} model={MODEL_I2I}")
        return self._submit_and_poll(payload, oss_resolve=is_oss)

    def generate_series(
        self,
        scene_prompts: list[str],
        ref_image_url: Optional[str] = None,
        series_amount: Optional[int] = None,
    ) -> list[Path]:
        """Omni series mode: generate N visually-consistent storyboard frames.

        Uses kling-v3-omni with result_type=series to ensure narrative continuity
        across all scene transitions.

        Args:
            scene_prompts: List of per-scene opening descriptions
            ref_image_url: Optional reference image (e.g. style/character reference)
            series_amount: How many images to generate (default: len(scene_prompts))
        """
        if not self.api_key:
            return [self._placeholder(p) for p in scene_prompts]

        n = series_amount or len(scene_prompts)
        combined_prompt = self._build_series_prompt(scene_prompts)

        content = [{"text": combined_prompt}]
        if ref_image_url:
            content.append({"image": ref_image_url})

        is_oss = bool(ref_image_url and ref_image_url.startswith("oss://"))

        payload = {
            "model": MODEL_OMNI,
            "input": {
                "messages": [{"role": "user", "content": content}]
            },
            "parameters": {
                "result_type": "series",
                "series_amount": n,
                "aspect_ratio": self.aspect_ratio,
                "resolution": self.resolution,
                "watermark": False,
            },
        }

        _log(f"Series submit — {n} frames model={MODEL_OMNI}")
        result_paths = self._submit_and_poll_series(payload, oss_resolve=is_oss)
        return result_paths

    # ── Internal helpers ─────────────────────────────────────────

    def _t2i(self, prompt: str) -> Path:
        payload = {
            "model": MODEL_I2I,
            "input": {
                "messages": [{"role": "user", "content": [{"text": prompt[:2500]}]}]
            },
            "parameters": {
                "n": 1,
                "aspect_ratio": self.aspect_ratio,
                "resolution": self.resolution,
                "watermark": False,
            },
        }
        _log(f"T2I submit — model={MODEL_I2I}")
        return self._submit_and_poll(payload)

    def _to_base64_jpeg(self, path: Path, max_size: int = 800, quality: int = 75) -> str:
        """Compress a local image to JPEG and return as base64 data URI."""
        import base64
        import io
        from PIL import Image

        img = Image.open(path).convert("RGB")
        # Resize so longest side ≤ max_size
        w, h = img.size
        if max(w, h) > max_size:
            scale = max_size / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        b64 = base64.b64encode(buf.getvalue()).decode()
        _log(f"Compressed to JPEG {img.size}: {len(b64) // 1024}KB base64")
        return f"data:image/jpeg;base64,{b64}"

    def _submit_and_poll(self, payload: dict, oss_resolve: bool = False) -> Path:
        """Submit task, poll, download FIRST result image."""
        headers = _make_headers(self.api_key, oss_resolve)
        resp = requests.post(_SUBMIT_URL, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        task_id = data.get("output", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"No task_id: {data}")
        _log(f"task_id={task_id}")

        urls = self._poll_task(task_id)
        if not urls:
            raise RuntimeError("No image URLs in response")

        self._last_image_url = urls[0]
        return self._download(urls[0])

    def _submit_and_poll_series(self, payload: dict, oss_resolve: bool = False) -> list[Path]:
        """Submit task, poll, download ALL result images."""
        headers = _make_headers(self.api_key, oss_resolve)
        resp = requests.post(_SUBMIT_URL, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        task_id = data.get("output", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"No task_id: {data}")
        _log(f"Series task_id={task_id}")

        urls = self._poll_task(task_id)
        paths = []
        for url in urls:
            self._last_image_url = url
            paths.append(self._download(url))
        _log(f"Series done: {len(paths)} images")
        return paths

    def _poll_task(self, task_id: str, max_attempts: int = 30) -> list[str]:
        """Poll task until SUCCEEDED, return list of image URLs."""
        poll_headers = {"Authorization": f"Bearer {self.api_key}"}
        for attempt in range(max_attempts):
            time.sleep(10)
            resp = requests.get(f"{_TASK_URL}/{task_id}", headers=poll_headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("output", {}).get("task_status", "UNKNOWN")

            if status == "SUCCEEDED":
                choices = data.get("output", {}).get("choices", [])
                urls = []
                for choice in choices:
                    for item in choice.get("message", {}).get("content", []):
                        if item.get("type") == "image" and item.get("image"):
                            urls.append(item["image"])
                _log(f"SUCCEEDED — {len(urls)} image(s)")
                return urls

            elif status in ("FAILED", "CANCELED"):
                raise RuntimeError(f"Kling task {status}: {data}")

            elapsed = (attempt + 1) * 10
            if attempt % 3 == 0:
                _log(f"Status: {status} ({elapsed}s)")

        raise TimeoutError("Kling image task timed out after 300s")

    def _download(self, url: str) -> Path:
        ts = int(time.time())
        out_path = self.output_dir / f"kling_v3_{ts}.png"
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
        p = self.output_dir / f"kling_placeholder_{int(time.time())}.txt"
        p.write_text(f"[Placeholder Kling]\n{prompt[:200]}\n", encoding="utf-8")
        return p

    @staticmethod
    def _build_series_prompt(prompts: list[str]) -> str:
        """Build a combined prompt for series mode."""
        parts = ["Generate a visually consistent storyboard series. Each frame should flow naturally into the next."]
        for i, p in enumerate(prompts, 1):
            parts.append(f"Frame {i}: {p}")
        return " | ".join(parts)
