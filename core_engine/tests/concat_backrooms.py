"""Concatenate all 4 Backrooms clips into final video."""
import os, pathlib

os.environ.setdefault("DASHSCOPE_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))

clips_dir = pathlib.Path("core_engine/output/videos/backrooms_story")
clip_order = [
    clips_dir / "dashscope_i2v_1775254603.mp4",
    clips_dir / "scene2_recovered.mp4",
    clips_dir / "dashscope_i2v_1775255945.mp4",
    clips_dir / "dashscope_i2v_1775256632.mp4",
]

print("Clips:")
for p in clip_order:
    status = "OK" if p.exists() else "MISSING"
    size = p.stat().st_size // (1024 * 1024) if p.exists() else 0
    print(f"  {p.name}: {status} ({size}MB)")

try:
    from moviepy import VideoFileClip, concatenate_videoclips
except ImportError:
    from moviepy.editor import VideoFileClip, concatenate_videoclips

print("\nLoading clips...")
video_clips = []
for p in clip_order:
    if p.exists():
        vc = VideoFileClip(str(p))
        print(f"  {p.name}: {vc.duration:.1f}s")
        video_clips.append(vc)

final = concatenate_videoclips(video_clips, method="compose")
out_path = clips_dir / "backrooms_final.mp4"
print(f"\nWriting {final.duration:.1f}s final video...")
final.write_videofile(str(out_path), fps=24, codec="libx264", audio_codec="aac", logger=None)
for vc in video_clips:
    vc.close()

size_mb = out_path.stat().st_size / (1024 * 1024)
print(f"\nDone: {out_path.name} ({size_mb:.1f} MB, {final.duration:.0f}s)")

# Also generate SRT subtitles
srt_lines = [
    "1\n00:00:00,000 --> 00:00:15,000\n你走错了一步。购物中心消失了。黄色的墙纸，荧光灯的嗡鸣。欢迎来到后室。\n",
    "2\n00:00:15,000 --> 00:00:30,000\n走廊没有尽头。荧光灯一盏一盏熄灭。你的影子不是你的影子。\n",
    "3\n00:00:30,000 --> 00:00:45,000\n走廊尽头有什么东西。它没有移动。但它更近了。\n",
    "4\n00:00:45,000 --> 00:01:00,000\n地板裂开了。他落入第一层。游泳池室。水声。无穷无尽。\n",
]
srt_path = clips_dir / "backrooms_final.srt"
srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
print(f"Subtitles: {srt_path.name}")
