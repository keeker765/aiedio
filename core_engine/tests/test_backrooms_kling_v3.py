"""《困于后室》Kling V3 视频生成 — ACT I + ACT II 预览.

生成两幕（20s），查看效果。
"""
import os
import pathlib

os.environ.setdefault("DASHSCOPE_API_KEY", "sk-a502b56390664a90aa0daa32df5c068a")

from core_engine.src.providers.video.kling_v3_video import KlingVideoProvider

OUT_DIR = pathlib.Path("core_engine/output/videos/backrooms_kling")
OUT_DIR.mkdir(parents=True, exist_ok=True)

kling = KlingVideoProvider(output_dir=OUT_DIR, mode="pro", audio=True)

print("=" * 65)
print("  《困于后室》— Kling V3 Video — ACT I + ACT II")
print("=" * 65)

# ── ACT I  「穿越」 ────────────────────────────────────────────────
print("\n" + "=" * 50)
print("  ACT I — 「穿越」The Slip (10s, 2 shots)")
print("=" * 50)

act1_shots = [
    {
        "index": 1,
        "duration": 5,
        "prompt": (
            "POV found-footage. Abandoned shopping mall, afternoon light through skylights. "
            "Man raises camera to photograph graffiti shutter. He steps forward — "
            "the floor silently yields like cold pudding, his legs sink, whole body swallowed. "
            "Camera falls spinning — tile ceiling flash, then black. "
            "16mm grain, handheld micro-shake, cinematic horror realism."
        ),
    },
    {
        "index": 2,
        "duration": 5,
        "prompt": (
            "Extreme wide dolly-out. A young man in grey hoodie lies on worn damp beige carpet. "
            "Infinite corridor stretches all directions to vanishing points, "
            "yellowed arrow-pattern wallpaper on every wall. Fluorescent tubes flicker. "
            "Camera pulls back: man shrinks to a speck in an ocean of yellow. "
            "Desaturated yellow-green grade, deep shadows, fluorescent hum audio. Cinematic horror."
        ),
    },
]

print("\n[生成中] ACT I multi_shot → kling-v3-video-generation...")
act1_path = kling.multi_shot_video(shots=act1_shots, duration=10)
act1_mb = act1_path.stat().st_size / (1024 * 1024)
print(f"\n✅ ACT I 完成: {act1_path.name} ({act1_mb:.1f}MB)")

# ── ACT II  「漂移」 ───────────────────────────────────────────────
print("\n" + "=" * 50)
print("  ACT II — 「漂移」The Drift (10s, 2 shots)")
print("=" * 50)

act2_shots = [
    {
        "index": 1,
        "duration": 5,
        "prompt": (
            "Tracking shot, persistent Dutch angle 8 degrees. "
            "Man in grey hoodie walks down infinite corridor, fingertips grazing yellowed wallpaper. "
            "An arrow he scratched in the carpet reappears in front of him — he's walked in a loop. "
            "He crouches, traces the arrow silently. Stands. Turns 180 degrees. Walks again. "
            "One-sided fluorescent key light, deep shadow opposite side. Desaturated horror grade."
        ),
    },
    {
        "index": 2,
        "duration": 5,
        "prompt": (
            "Rack focus between man's face and wall text. "
            "Wall has layers of handwriting from multiple people: "
            "newest in black marker reads: DO NOT TRUST RIGHT TURNS. THE LIGHTS LIE. DON'T SLEEP. "
            "He photographs the wall. Checks camera screen — blank yellow wallpaper, no text. "
            "Looks back: text still there. ECU trembling fingers touch the pen indentations. "
            "Motivated flashlight lighting. Desaturated horror grade."
        ),
    },
]

print("\n[生成中] ACT II multi_shot → kling-v3-video-generation...")
act2_path = kling.multi_shot_video(shots=act2_shots, duration=10)
act2_mb = act2_path.stat().st_size / (1024 * 1024)
print(f"\n✅ ACT II 完成: {act2_path.name} ({act2_mb:.1f}MB)")

# ── Quick concat preview ───────────────────────────────────────────
print("\n" + "=" * 50)
print("  拼接预览（无字幕）")
print("=" * 50)

try:
    from moviepy import VideoFileClip, concatenate_videoclips
except ImportError:
    from moviepy.editor import VideoFileClip, concatenate_videoclips

clips = [VideoFileClip(str(act1_path)), VideoFileClip(str(act2_path))]
for c, p in zip(clips, [act1_path, act2_path]):
    print(f"  {p.name}: {c.duration:.1f}s")

preview_out = OUT_DIR / "backrooms_act1_act2_preview.mp4"
concat = concatenate_videoclips(clips, method="compose")
concat.write_videofile(str(preview_out), fps=24, codec="libx264", audio_codec="aac", logger=None)
for c in clips:
    c.close()
print(f"\n✅ 预览视频: {preview_out.name} ({preview_out.stat().st_size//(1024*1024)}MB / {concat.duration:.0f}s)")

print("\n" + "=" * 65)
print("  两幕生成完毕！请查看效果")
print(f"  {OUT_DIR}")
print("=" * 65)
