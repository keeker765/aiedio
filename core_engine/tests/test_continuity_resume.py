"""Resume continuity pipeline from Scene 3 (scenes 1+2 already done)."""
import os
import pathlib

os.environ.setdefault("DASHSCOPE_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))

from core_engine.src.pipeline.scene_continuity import extract_last_frame, generate_transition_frame
from core_engine.src.providers.image.kling_v3 import KlingImageProvider
from core_engine.src.providers.video.dashscope_wan import DashScopeWanProvider

OUT_DIR = pathlib.Path("core_engine/output/videos/backrooms_continuity")
ASSETS_DIR = pathlib.Path("core_engine/output/assets/backrooms_continuity")
OUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

kling = KlingImageProvider(output_dir=ASSETS_DIR, resolution="2k", aspect_ratio="16:9")
wan = DashScopeWanProvider(output_dir=OUT_DIR, model="wan2.7-i2v")

scene1_path = OUT_DIR / "dashscope_i2v_1775467158.mp4"
scene2_path = OUT_DIR / "scene2_recovered.mp4"

SCENES_REMAINING = [
    {
        "id": 3,
        "prev_clip": scene2_path,
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
    },
    {
        "id": 4,
        "prev_clip": None,  # will be set after scene 3 completes
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
    },
]

clip_paths = [scene1_path, scene2_path]

for cfg in SCENES_REMAINING:
    scene_id = cfg["id"]
    print(f"\n{'='*50}")
    print(f"  SCENE {scene_id}/4")
    print(f"{'='*50}")

    prev_clip = cfg["prev_clip"] if cfg["prev_clip"] else clip_paths[-1]

    print(f"\n[A] Extract Scene {scene_id-1} last frame → Kling I2I → Scene {scene_id} first frame")
    last_frame = extract_last_frame(prev_clip, ASSETS_DIR)
    first_frame_path = generate_transition_frame(
        last_frame_path=last_frame,
        next_scene_prompt=cfg["first_frame_kling_prompt"],
        kling=kling,
    )
    first_frame_url = kling._last_image_url
    print(f"  First frame URL: {first_frame_url[:80]}...")

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

# Concatenate all 4 scenes
print(f"\n{'='*65}")
print("  STAGE 4 — Concatenate + Subtitles")
print(f"{'='*65}")

try:
    from moviepy import VideoFileClip, concatenate_videoclips
except ImportError:
    from moviepy.editor import VideoFileClip, concatenate_videoclips

import subprocess, imageio_ffmpeg
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
final_out = OUT_DIR / "backrooms_continuity_final.mp4"
font_path = "core_engine/resources/fonts/NotoSansSC-Regular.ttf"
import pathlib as _pl
if _pl.Path(font_path).exists():
    vf = f"subtitles='{srt_esc}':force_style='FontName=Noto Sans SC,FontSize=20,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'"
else:
    vf = f"subtitles='{srt_esc}':force_style='FontSize=20,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'"

cmd = [FFMPEG, "-y", "-i", str(final_concat), "-vf", vf, "-c:v", "libx264", "-c:a", "copy", str(final_out)]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"  [WARN] subtitle burn failed: {result.stderr[-500:]}")
    import shutil
    shutil.copy(str(final_concat), str(final_out))
    print(f"  Fallback: copied concat as final")
else:
    print(f"  Final: {final_out.name} ({final_out.stat().st_size//(1024*1024)}MB)")

print("\n" + "="*65)
print("  PIPELINE COMPLETE")
for p in clip_paths:
    print(f"  {p.name}: {p.stat().st_size//(1024*1024)}MB")
print(f"  FINAL: {final_out.name}")
print("="*65)
