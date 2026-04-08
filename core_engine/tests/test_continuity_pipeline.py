"""Backrooms 后室 — Scene Continuity Pipeline (4 scenes, kling-v3 transitions).

Flow for each scene (except Scene 1):
  Previous scene's last frame (ffmpeg extract)
      ↓
  Kling V3 I2I (base64 JPEG reference → 2K image)
      ↓ first_frame URL
  DashScope wan2.7-i2v → 15s video
      ↓
  MoviePy concatenate → final 60s video
  ffmpeg subtitle burn-in
"""
import os
import pathlib
import time

os.environ.setdefault("DASHSCOPE_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))

print("=" * 65)
print("  THE BACKROOMS — Scene Continuity Pipeline")
print("  末帧→Kling V3→首帧→wan2.7-i2v × 4场景")
print("=" * 65)

from core_engine.src.pipeline.base import PipelineContext
from core_engine.src.pipeline.scene_continuity import extract_last_frame, generate_transition_frame
from core_engine.src.providers.image.kling_v3 import KlingImageProvider
from core_engine.src.providers.video.dashscope_wan import DashScopeWanProvider
from core_engine.src.schemas.models import (
    AudioMode, CameraMotion, Resolution, SceneSchema,
    StoryboardSchema, TransitionType, VideoStyle, WanConfig,
)

API_KEY = os.environ["DASHSCOPE_API_KEY"]
OUT_DIR = pathlib.Path("core_engine/output/videos/backrooms_continuity")
ASSETS_DIR = pathlib.Path("core_engine/output/assets/backrooms_continuity")
OUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

kling = KlingImageProvider(output_dir=ASSETS_DIR, resolution="2k", aspect_ratio="16:9")
wan = DashScopeWanProvider(output_dir=OUT_DIR, model="wan2.7-i2v")

# ── Scene definitions ─────────────────────────────────────────────
SCENE_CONFIGS = [
    {
        "id": 1,
        "duration": 15,
        "first_frame_prompt": (
            "The Backrooms Level 0. A young man in a grey hoodie just appeared, "
            "kneeling on yellowed geometric-pattern carpet, looking around in confusion. "
            "Infinite corridor stretching in both directions, flickering fluorescent tube lights. "
            "Photorealistic, cinematic horror, found-footage aesthetic, 16:9."
        ),
        "video_prompt": (
            "The Backrooms Level 0. An infinite corridor of yellowed wallpaper and flickering fluorescent lights. "
            "Shot 1 [0-5s]: Camera slowly drifts forward as a young man in grey hoodie picks himself up from the carpet, looks around in confusion and fear. He whispers: 'Where am I?' "
            "Shot 2 [5-10s]: He walks cautiously forward, fluorescent light above flickers violently. His footsteps make wet slapping sounds on the beige carpet. "
            "Shot 3 [10-15s]: He stops. Turns slowly. The corridor behind him looks identical to ahead. No way to tell which direction he came from. "
            "Photorealistic, found-footage, cinematic horror, 24fps."
        ),
        "narration": "你走错了一步。购物中心消失了。黄色的墙纸，荧光灯嗡嗡作响。欢迎来到后室。",
    },
    {
        "id": 2,
        "duration": 15,
        "first_frame_prompt": None,  # generated from Scene 1's last frame via kling I2I
        "first_frame_kling_prompt": (
            "Continue this corridor scene naturally. The same Backrooms Level 0 yellow wallpaper "
            "and flickering fluorescent lights. The young man in grey hoodie is walking forward, "
            "and his shadow on the wall beside him has a slightly wrong shape — taller, with longer arms. "
            "He hasn't noticed yet. Cinematic horror, photorealistic, 16:9."
        ),
        "video_prompt": (
            "Cinematic psychological horror. The Backrooms Level 0. "
            "Shot 1 [0-5s]: The young man in grey hoodie walks forward slowly, footsteps echoing. "
            "His shadow on the yellowed wallpaper is subtly wrong — slightly taller, arms too long. "
            "A fluorescent light ahead flickers off. Darkness creeps closer. "
            "Shot 2 [5-10s]: He stops and stares at his shadow. It doesn't stop moving immediately — "
            "the shadow's head slowly turns to face him even as he stands perfectly still. "
            "He backs away one step. "
            "Shot 3 [10-15s]: He runs. The camera stays fixed. The shadow on the wall does not follow. "
            "It stays where it is, facing the camera, as he disappears into the distance. "
            "Handheld camera, found footage, pale sickly light, extreme dread."
        ),
        "narration": "走廊没有尽头。荧光灯一盏一盏熄灭。你的影子……不是你的影子。",
    },
    {
        "id": 3,
        "duration": 15,
        "first_frame_prompt": None,
        "first_frame_kling_prompt": (
            "Continue this scene naturally. The Backrooms Level 0. "
            "The young man in grey hoodie has run to a halt, panting. "
            "At the far end of the infinite corridor — 500 meters away — "
            "stands a tall dark featureless humanoid silhouette. Completely still. "
            "No face. No features. Just standing there watching. "
            "The fluorescent lights between them begin to go out one by one. Cinematic horror, 16:9."
        ),
        "video_prompt": (
            "Cinematic horror. The Backrooms Level 0. "
            "Shot 1 [0-5s]: The young man stands frozen, staring at a dark humanoid silhouette "
            "at the far end of the corridor. It does not move. The lights between them go out "
            "one by one from the silhouette toward him. "
            "Shot 2 [5-10s]: He blinks. The silhouette is now 50 meters away. It did not walk. "
            "It is simply closer. The remaining lights strobe violently. "
            "The humming rises to a painful pitch. He backs away step by step. "
            "Shot 3 [10-15s]: Close-up of his face — pure white terror. "
            "Behind him, from off-camera: a single slow exhale. "
            "He doesn't look back. He runs forward toward the darkness where the lights went out. "
            "Strobe lighting, extreme close-up, found footage, body horror."
        ),
        "narration": "走廊的尽头，有什么东西站在那里。它没有移动。但是，它更近了。",
    },
    {
        "id": 4,
        "duration": 15,
        "first_frame_prompt": None,
        "first_frame_kling_prompt": (
            "Continue this scene naturally. The Backrooms Level 0 corridor. "
            "The young man in grey hoodie is crawling on all fours, completely exhausted. "
            "The yellow wallpaper is peeling. The carpet is wet. The ceiling drips dark water. "
            "The floor ahead has hairline cracks spreading across it. "
            "Dim light, atmospheric horror, photorealistic, 16:9."
        ),
        "video_prompt": (
            "Cinematic horror ending. The Backrooms Level 0. "
            "Shot 1 [0-5s]: The young man crawls on wet carpet past peeling wallpaper. "
            "The ceiling drips. He stops — the floor ahead is cracking like a frozen lake. "
            "Shot 2 [5-10s]: The cracks spread toward him. He scrambles backward but the floor "
            "beneath him cracks too. Through the gaps: infinite darkness below, and the distant "
            "sound of rushing water. He screams. "
            "Shot 3 [10-15s]: The floor collapses. He falls into a vast dark cavern. "
            "Far below: pale blue light rippling on water. Level 1 — The Poolrooms. "
            "As he falls, a title card fades in: LEVEL 1 — THE POOLROOMS. "
            "Slow-motion fall, cinematic, found footage, terrifying."
        ),
        "narration": "地板裂开了。他坠入第一层——游泳池室。水声，无穷无尽。",
    },
]

# ── Run Pipeline ──────────────────────────────────────────────────
clip_paths: list[pathlib.Path] = []
first_frame_urls: list[str] = []

for cfg in SCENE_CONFIGS:
    scene_id = cfg["id"]
    print(f"\n{'='*50}")
    print(f"  SCENE {scene_id}/4")
    print(f"{'='*50}")

    # Step A: Generate first frame
    if scene_id == 1:
        # Scene 1: T2I using kling directly
        print(f"\n[A] Kling T2I → Scene 1 first frame")
        first_frame_path = kling.generate(prompt=cfg["first_frame_prompt"])
        first_frame_url = kling._last_image_url
    else:
        # Scene N: extract last frame of Scene N-1, then kling I2I
        print(f"\n[A] Extract Scene {scene_id-1} last frame → Kling I2I → Scene {scene_id} first frame")
        prev_clip = clip_paths[-1]
        last_frame = extract_last_frame(prev_clip, ASSETS_DIR)
        first_frame_path = generate_transition_frame(
            last_frame_path=last_frame,
            next_scene_prompt=cfg["first_frame_kling_prompt"],
            kling=kling,
        )
        first_frame_url = kling._last_image_url

    first_frame_urls.append(first_frame_url)
    print(f"  First frame URL: {first_frame_url[:80]}...")

    # Step B: Generate video via wan2.7-i2v using the first frame
    print(f"\n[B] wan2.7-i2v → Scene {scene_id} video (15s)")
    clip_path = wan.image_to_video(
        prompt=cfg["video_prompt"],
        image_url=first_frame_url,
        duration="15",
        resolution="720p",
    )
    clip_paths.append(clip_path)
    size_mb = clip_path.stat().st_size / (1024 * 1024)
    print(f"  Scene {scene_id} done: {clip_path.name} ({size_mb:.1f}MB)")

# ── Concatenate ───────────────────────────────────────────────────
print(f"\n{'='*65}")
print("  STAGE 4 — Concatenate + Subtitles")
print(f"{'='*65}")

try:
    from moviepy import VideoFileClip, concatenate_videoclips
except ImportError:
    from moviepy.editor import VideoFileClip, concatenate_videoclips

import subprocess
import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

print("\n[C] MoviePy concatenate...")
vcs = [VideoFileClip(str(p)) for p in clip_paths]
for vc, p in zip(vcs, clip_paths):
    print(f"  {p.name}: {vc.duration:.1f}s")

final_concat = OUT_DIR / "concat_raw.mp4"
concat = concatenate_videoclips(vcs, method="compose")
concat.write_videofile(str(final_concat), fps=24, codec="libx264", audio_codec="aac", logger=None)
for vc in vcs:
    vc.close()
print(f"  concat_raw.mp4: {final_concat.stat().st_size//(1024*1024)}MB / {concat.duration:.0f}s")

# Subtitles
srt_content = (
    "1\n00:00:00,000 --> 00:00:15,000\n你走错了一步。购物中心消失了。\n黄色的墙纸，荧光灯嗡嗡作响。欢迎来到后室。\n\n"
    "2\n00:00:15,000 --> 00:00:30,000\n走廊没有尽头。荧光灯一盏一盏熄灭。\n你的影子……不是你的影子。\n\n"
    "3\n00:00:30,000 --> 00:00:45,000\n走廊的尽头，有什么东西站在那里。\n它没有移动。但是，它更近了。\n\n"
    "4\n00:00:45,000 --> 00:01:00,000\n地板裂开了。他坠入第一层——\n游泳池室。水声，无穷无尽。\n"
)
srt_path = OUT_DIR / "subtitles.srt"
srt_path.write_text(srt_content, encoding="utf-8")

print("\n[D] Burning subtitles...")
srt_esc = str(srt_path).replace("\\", "/").replace(":", "\\:")
style = "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,Alignment=2"
final_out = OUT_DIR / "backrooms_continuity_final.mp4"
result = subprocess.run([
    FFMPEG, "-y", "-i", str(final_concat),
    "-vf", f"subtitles={srt_esc}:force_style='{style}'",
    "-c:a", "copy", str(final_out),
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"  [WARN] subtitle burn: {result.stderr[-200:]}")
    import shutil; shutil.copy(final_concat, final_out)
else:
    print(f"  Done: {final_out.name} ({final_out.stat().st_size//(1024*1024)}MB)")

# ── Summary ───────────────────────────────────────────────────────
print(f"\n{'='*65}")
print("  COMPLETE")
print(f"{'='*65}")
if final_out.exists():
    mb = final_out.stat().st_size / (1024*1024)
    print(f"  📹 {final_out}")
    print(f"  💾 {mb:.1f} MB / 60s")
    print(f"  🎬 4场景场景连贯 (Kling V3 末帧→首帧)")
print(f"\n  Clips:")
for i, p in enumerate(clip_paths, 1):
    print(f"    Scene {i}: {p.name} ({p.stat().st_size//(1024*1024)}MB)")
