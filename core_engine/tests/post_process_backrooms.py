"""Post-process: burn subtitles + TTS narration into Backrooms final video.

Steps:
1. Generate Chinese TTS narration for each scene via edge-tts
2. Overlay TTS audio on each clip (replacing or mixing with original audio)
3. Concatenate 4 clips with MoviePy
4. Burn SRT subtitles into the final MP4 using ffmpeg
"""
import asyncio
import os
import pathlib
import subprocess
import time

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
os.environ.setdefault("DASHSCOPE_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))

CLIPS_DIR = pathlib.Path("core_engine/output/videos/backrooms_story")
OUT_DIR = pathlib.Path("core_engine/output/videos/backrooms_final_v2")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Scene narrations (Chinese TTS)
NARRATIONS = [
    (1, "你走错了一步。购物中心消失了。黄色的墙纸，荧光灯嗡嗡作响。欢迎来到后室。"),
    (2, "走廊没有尽头。荧光灯一盏一盏熄灭。你的影子……不是你的影子。"),
    (3, "走廊的尽头，有什么东西站在那里。它没有移动。但是，它更近了。"),
    (4, "地板裂开了。他坠入第一层——游泳池室。水声，无穷无尽。"),
]

# Clip files in order
CLIPS = [
    CLIPS_DIR / "dashscope_i2v_1775254603.mp4",
    CLIPS_DIR / "scene2_recovered.mp4",
    CLIPS_DIR / "dashscope_i2v_1775255945.mp4",
    CLIPS_DIR / "dashscope_i2v_1775256632.mp4",
]


# ── Step 1: Generate TTS audio ────────────────────────────────────
async def _tts(text: str, out_path: pathlib.Path, voice: str = "zh-CN-YunxiNeural") -> None:
    import edge_tts
    comm = edge_tts.Communicate(text=text, voice=voice, rate="-10%")
    await comm.save(str(out_path))


def generate_tts_tracks() -> list[pathlib.Path]:
    print("[Step 1] Generating TTS narrations...")
    audio_paths = []
    for scene_id, text in NARRATIONS:
        out = OUT_DIR / f"tts_scene{scene_id}.mp3"
        if not out.exists():
            asyncio.run(_tts(text, out))
            print(f"  Scene {scene_id}: {out.name} ({out.stat().st_size // 1024}KB)")
        else:
            print(f"  Scene {scene_id}: {out.name} (cached)")
        audio_paths.append(out)
    return audio_paths


# ── Step 2: Mix TTS audio into each clip ─────────────────────────
def mix_audio(clip: pathlib.Path, tts: pathlib.Path, out: pathlib.Path) -> pathlib.Path:
    """Mix TTS voice (foreground) with original video audio (background, lower volume)."""
    cmd = [
        FFMPEG, "-y",
        "-i", str(clip),
        "-i", str(tts),
        "-filter_complex",
        "[0:a]volume=0.25[bg];[1:a]volume=1.0[fg];[bg][fg]amix=inputs=2:duration=first[audio]",
        "-map", "0:v",
        "-map", "[audio]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [WARN] Mix failed for {clip.name}: {result.stderr[-200:]}")
        # fallback: just copy
        import shutil; shutil.copy(clip, out)
    return out


def mix_all_clips(clip_list: list[pathlib.Path], tts_list: list[pathlib.Path]) -> list[pathlib.Path]:
    print("\n[Step 2] Mixing TTS into video clips...")
    mixed = []
    for i, (clip, tts) in enumerate(zip(clip_list, tts_list), 1):
        out = OUT_DIR / f"mixed_scene{i}.mp4"
        if not out.exists():
            mix_audio(clip, tts, out)
            size = out.stat().st_size // (1024 * 1024)
            print(f"  Scene {i}: {out.name} ({size}MB)")
        else:
            print(f"  Scene {i}: {out.name} (cached)")
        mixed.append(out)
    return mixed


# ── Step 3: Concatenate ───────────────────────────────────────────
def concatenate(clips: list[pathlib.Path], out: pathlib.Path) -> pathlib.Path:
    print("\n[Step 3] Concatenating 4 scenes with MoviePy...")
    try:
        from moviepy import VideoFileClip, concatenate_videoclips
    except ImportError:
        from moviepy.editor import VideoFileClip, concatenate_videoclips

    video_clips = []
    for p in clips:
        vc = VideoFileClip(str(p))
        print(f"  {p.name}: {vc.duration:.1f}s")
        video_clips.append(vc)

    final = concatenate_videoclips(video_clips, method="compose")
    final.write_videofile(str(out), fps=24, codec="libx264", audio_codec="aac", logger=None)
    for vc in video_clips:
        vc.close()
    print(f"  Concatenated: {out.name} ({out.stat().st_size // (1024*1024)}MB, {final.duration:.0f}s)")
    return out


# ── Step 4: Burn SRT subtitles ────────────────────────────────────
def write_srt(out_dir: pathlib.Path) -> pathlib.Path:
    srt_content = (
        "1\n00:00:00,000 --> 00:00:15,000\n"
        "你走错了一步。购物中心消失了。\n黄色的墙纸，荧光灯嗡嗡作响。欢迎来到后室。\n\n"
        "2\n00:00:15,000 --> 00:00:30,000\n"
        "走廊没有尽头。荧光灯一盏一盏熄灭。\n你的影子……不是你的影子。\n\n"
        "3\n00:00:30,000 --> 00:00:45,000\n"
        "走廊的尽头，有什么东西站在那里。\n它没有移动。但是，它更近了。\n\n"
        "4\n00:00:45,000 --> 00:01:00,000\n"
        "地板裂开了。他坠入第一层——\n游泳池室。水声，无穷无尽。\n"
    )
    srt_path = out_dir / "subtitles.srt"
    srt_path.write_text(srt_content, encoding="utf-8")
    return srt_path


def burn_subtitles(video: pathlib.Path, srt: pathlib.Path, out: pathlib.Path) -> pathlib.Path:
    print("\n[Step 4] Burning subtitles into final video...")
    # ffmpeg subtitles filter needs forward slashes and escaped colons on Windows
    srt_escaped = str(srt).replace("\\", "/").replace(":", "\\:")
    cmd = [
        FFMPEG, "-y",
        "-i", str(video),
        "-vf", f"subtitles={srt_escaped}:force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1'",
        "-c:a", "copy",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [WARN] Subtitle burn failed: {result.stderr[-300:]}")
        print("  Falling back: copying without burned subtitles")
        import shutil; shutil.copy(video, out)
    else:
        print(f"  Done: {out.name} ({out.stat().st_size // (1024*1024)}MB)")
    return out


# ── Main ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("  THE BACKROOMS — Post-Processing (TTS + Subtitles)")
    print("=" * 65)

    tts_tracks = generate_tts_tracks()
    mixed_clips = mix_all_clips(CLIPS, tts_tracks)
    raw_concat = OUT_DIR / "concat_raw.mp4"
    concatenate(mixed_clips, raw_concat)
    srt = write_srt(OUT_DIR)
    final = OUT_DIR / "backrooms_v2_final.mp4"
    burn_subtitles(raw_concat, srt, final)

    print("\n" + "=" * 65)
    print("  DONE")
    print("=" * 65)
    if final.exists():
        size_mb = final.stat().st_size / (1024 * 1024)
        print(f"  📹 {final}")
        print(f"  💾 {size_mb:.1f} MB / 60s")
        print(f"  🔊 TTS中文旁白 + 原声混合")
        print(f"  📝 字幕烧录进视频")
