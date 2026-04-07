"""Post-process v3: Wan原声 + 字幕烧录（无旁白，角色自己说话）.

直接使用 Wan 2.7 T2V 生成的原始音频（包含角色台词/环境音效）。
只做：拼接 + 烧录字幕（显示角色台词，不加旁白）。
"""
import os
import pathlib
import subprocess

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

CLIPS_DIR = pathlib.Path("core_engine/output/videos/backrooms_story")
OUT_DIR = pathlib.Path("core_engine/output/videos/backrooms_v3")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 原始 Wan 生成片段（原声）
CLIPS = [
    CLIPS_DIR / "dashscope_i2v_1775254603.mp4",  # Scene 1
    CLIPS_DIR / "scene2_recovered.mp4",            # Scene 2
    CLIPS_DIR / "dashscope_i2v_1775255945.mp4",   # Scene 3
    CLIPS_DIR / "dashscope_i2v_1775256632.mp4",   # Scene 4
]

# 字幕显示角色台词（不是旁白，是对话/内心独白）
SRT_CONTENT = (
    "1\n00:00:00,000 --> 00:00:15,000\n"
    "「 Where... where am I? 」\n\n"
    "2\n00:00:15,000 --> 00:00:30,000\n"
    "「 That's... not my shadow. 」\n\n"
    "3\n00:00:30,000 --> 00:00:45,000\n"
    "「 Don't look at it. Don't. Look. At. It. 」\n\n"
    "4\n00:00:45,000 --> 00:01:00,000\n"
    "[ LEVEL 1 — THE POOLROOMS ]\n\n"
)


def concatenate(clips: list, out: pathlib.Path) -> pathlib.Path:
    print("[Step 1] Concatenating with MoviePy (original audio)...")
    try:
        from moviepy import VideoFileClip, concatenate_videoclips
    except ImportError:
        from moviepy.editor import VideoFileClip, concatenate_videoclips

    vcs = []
    for p in clips:
        vc = VideoFileClip(str(p))
        print(f"  {p.name}: {vc.duration:.1f}s")
        vcs.append(vc)

    final = concatenate_videoclips(vcs, method="compose")
    final.write_videofile(str(out), fps=24, codec="libx264", audio_codec="aac", logger=None)
    for vc in vcs:
        vc.close()
    size = out.stat().st_size // (1024 * 1024)
    print(f"  concat_raw.mp4: {size}MB / {final.duration:.0f}s")
    return out


def burn_subtitles(video: pathlib.Path, srt: pathlib.Path, out: pathlib.Path) -> pathlib.Path:
    print("\n[Step 2] Burning subtitles...")
    srt_escaped = str(srt).replace("\\", "/").replace(":", "\\:")
    style = (
        "FontName=Arial,FontSize=22,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=2,Shadow=1,"
        "Alignment=2"   # bottom center
    )
    cmd = [
        FFMPEG, "-y",
        "-i", str(video),
        "-vf", f"subtitles={srt_escaped}:force_style='{style}'",
        "-c:a", "copy",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [WARN] Subtitle burn failed:\n{result.stderr[-400:]}")
        import shutil; shutil.copy(video, out)
    else:
        size = out.stat().st_size // (1024 * 1024)
        print(f"  Done: {out.name} ({size}MB)")
    return out


if __name__ == "__main__":
    print("=" * 60)
    print("  THE BACKROOMS v3 — 原声 + 字幕台词")
    print("=" * 60)

    raw_concat = OUT_DIR / "concat_raw.mp4"
    concatenate(CLIPS, raw_concat)

    srt = OUT_DIR / "dialogue.srt"
    srt.write_text(SRT_CONTENT, encoding="utf-8")

    final = OUT_DIR / "backrooms_v3_final.mp4"
    burn_subtitles(raw_concat, srt, final)

    print("\n" + "=" * 60)
    if final.exists():
        size_mb = final.stat().st_size / (1024 * 1024)
        print(f"  📹 {final}")
        print(f"  💾 {size_mb:.1f} MB / 60s")
        print(f"  🔊 Wan 原声（无旁白，角色台词）")
        print(f"  📝 字幕台词烧录进视频")
