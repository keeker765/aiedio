"""Scene continuity: extract last frame from video, generate next scene's first frame via Kling V3.

Flow:
  Scene N video
      ↓ ffmpeg extract last frame
  last_frame.png (local)
      ↓ DashScope upload → oss:// URL
  oss://dashscope-instant/.../last_frame.png
      ↓ kling/kling-v3-image-generation I2I
  scene_{N+1}_first_frame.png (kling-generated, visually continuing from Scene N)
      ↓ wan2.7-i2v first_frame input
  Scene N+1 video (starts exactly where Scene N left off)
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Optional

import imageio_ffmpeg

from core_engine.src.providers.image.kling_v3 import KlingImageProvider
from core_engine.src.providers.utils.dashscope_upload import upload_file

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def extract_last_frame(video_path: str | Path, output_dir: Optional[Path] = None) -> Path:
    """Extract the very last frame from a video as PNG using ffmpeg.

    Uses `-sseof -0.1` to seek 0.1s before the end and capture 1 frame.
    """
    video_path = Path(video_path)
    out_dir = output_dir or video_path.parent
    ts = int(time.time())
    out_path = out_dir / f"lastframe_{video_path.stem}_{ts}.png"

    cmd = [
        FFMPEG, "-y",
        "-sseof", "-0.1",          # seek 0.1s before end
        "-i", str(video_path),
        "-vframes", "1",           # capture exactly 1 frame
        "-q:v", "1",               # highest quality
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not out_path.exists():
        # Fallback: use ffmpeg to count frames and extract last
        cmd2 = [
            FFMPEG, "-y",
            "-i", str(video_path),
            "-vf", "select='eq(n\\,last_frame_number)'",
            "-vframes", "1",
            "-q:v", "1",
            str(out_path),
        ]
        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        if result2.returncode != 0 or not out_path.exists():
            raise RuntimeError(
                f"Cannot extract last frame from {video_path.name}:\n{result.stderr[-200:]}"
            )

    size_kb = out_path.stat().st_size // 1024
    print(f"  [LastFrame] Extracted: {out_path.name} ({size_kb}KB)")
    return out_path


def generate_transition_frame(
    last_frame_path: Path,
    next_scene_prompt: str,
    kling: KlingImageProvider,
    api_key: str = "",
) -> Path:
    """Use kling I2I with the last frame as reference to generate Scene N+1's opening frame.

    Accepts a local PNG path — it will be compressed and sent as base64 JPEG.
    """
    transition_prompt = (
        f"Continue this scene naturally into the next shot. "
        f"Maintain the same visual style, lighting, and atmosphere. "
        f"{next_scene_prompt}"
    )
    print(f"  [Kling I2I] Generating transition frame (ref={last_frame_path.name})...")
    return kling.image_to_image(
        prompt=transition_prompt,
        image_url=str(last_frame_path),  # local path → auto base64 compressed
    )


def build_continuity_frames(
    clip_paths: list[Path],
    scene_prompts: list[str],
    output_dir: Path,
    api_key: str = "",
) -> list[Optional[Path]]:
    """Extract last frames and generate continuity first frames for scenes 2..N.

    For N scenes:
      - Scene 1: no previous frame, returns None (use T2V directly)
      - Scene 2: last frame of Scene 1 → kling I2I → first frame of Scene 2
      - Scene 3: last frame of Scene 2 → kling I2I → first frame of Scene 3
      - ...

    Returns a list of Optional[Path] — None means "no first frame, use T2V".
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    kling = KlingImageProvider(output_dir=output_dir, api_key=api_key)

    first_frames: list[Optional[Path]] = [None]  # Scene 1 has no previous

    for i in range(len(clip_paths) - 1):
        clip = clip_paths[i]
        next_prompt = scene_prompts[i + 1] if i + 1 < len(scene_prompts) else ""

        print(f"\n  [Continuity] Scene {i+1} → Scene {i+2}")
        try:
            last_frame = extract_last_frame(clip, output_dir)
            transition = generate_transition_frame(
                last_frame, next_prompt, kling, api_key
            )
            first_frames.append(transition)
            print(f"  [Continuity] Scene {i+2} first frame: {transition.name}")
        except Exception as e:
            print(f"  [Continuity] ⚠️ Failed for Scene {i+2}: {e}")
            first_frames.append(None)

    return first_frames
