"""Stage 4: Post Processor — concatenate clips, burn subtitles, add intro/outro.

Uses MoviePy (already in requirements) for video editing operations.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from core_engine.src.pipeline.base import BaseStage, PipelineContext

log = logging.getLogger("aiedio")


class PostProcessor(BaseStage):
    """Stage 4: Concatenate video clips, burn subtitles, export final video."""

    name = "post_processor"

    def execute(self, ctx: PipelineContext) -> None:
        clip_paths_raw = ctx.metadata.get("clip_paths", [])
        clip_paths = [Path(p) for p in clip_paths_raw if Path(p).exists() and Path(p).suffix == ".mp4"]

        if not clip_paths:
            log.info("  No video clips to process")
            self._save_metadata(ctx)
            return

        project_dir = Path(ctx.project_dir)
        output_dir = project_dir / "videos" / ctx.project_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate SRT subtitle file from storyboard narrations
        srt_path = None
        if ctx.storyboard:
            srt_path = self._generate_srt(ctx, output_dir)
            if srt_path:
                ctx.metadata["srt_path"] = str(srt_path)
                log.info("  Subtitles saved: %s", srt_path.name)

        if len(clip_paths) == 1:
            # Single clip — burn subtitles if available
            final_path = self._burn_subtitles(clip_paths[0], output_dir, ctx, srt_path)
            ctx.final_path = final_path
        else:
            # Multiple clips — concatenate with MoviePy
            concat_path = self._concatenate_clips(clip_paths, output_dir, ctx)
            if concat_path:
                final_path = self._burn_subtitles(concat_path, output_dir, ctx, srt_path)
                ctx.final_path = final_path
            else:
                ctx.final_path = clip_paths[0]

        self._save_metadata(ctx)

    def _burn_subtitles(
        self, video_path: Path, output_dir: Path, ctx: PipelineContext, srt_path: Optional[Path]
    ) -> Path:
        """Burn SRT subtitles into video using ffmpeg. Returns final video path."""
        if not srt_path or not srt_path.exists():
            log.info("  No subtitles to burn — keeping raw video")
            return video_path

        final_path = output_dir / f"{ctx.project_id}_final.mp4"
        if final_path.exists():
            final_path.unlink()

        try:
            # Use ffmpeg to burn subtitles — escapes SRT path for Windows
            srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vf", f"subtitles='{srt_escaped}'",
                "-c:a", "copy",
                str(final_path),
            ]
            log.info("  Burning subtitles: %s → %s", video_path.name, final_path.name)
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace"
            )
            if result.returncode == 0 and final_path.exists():
                log.info("  Subtitles burned successfully: %s", final_path.name)
                return final_path
            else:
                log.warning("  ffmpeg subtitle burn failed (rc=%d): %s", result.returncode, result.stderr[:300])
        except FileNotFoundError:
            log.warning("  ffmpeg not found — skipping subtitle burn")
        except subprocess.TimeoutExpired:
            log.warning("  ffmpeg timed out — skipping subtitle burn")
        except Exception as e:
            log.warning("  Subtitle burn failed: %s", e)

        return video_path

    def _concatenate_clips(
        self, clips: list[Path], output_dir: Path, ctx: PipelineContext
    ) -> Optional[Path]:
        """Concatenate multiple MP4 clips into one video."""
        try:
            try:
                from moviepy import VideoFileClip, concatenate_videoclips
            except ImportError:
                from moviepy.editor import VideoFileClip, concatenate_videoclips

            video_clips = []
            for p in clips:
                try:
                    vc = VideoFileClip(str(p))
                    video_clips.append(vc)
                except Exception as e:
                    log.warning("  Could not load clip %s: %s", p.name, e)

            if not video_clips:
                return None

            concat_path = output_dir / f"{ctx.project_id}_concat.mp4"
            final = concatenate_videoclips(video_clips, method="compose")
            final.write_videofile(
                str(concat_path),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )

            for vc in video_clips:
                vc.close()

            log.info("  Concatenated %d clips → %s", len(video_clips), concat_path.name)
            return concat_path

        except ImportError:
            log.warning("  MoviePy not available — skipping concatenation")
            return clips[0] if clips else None
        except Exception as e:
            log.error("  Concatenation failed: %s", e)
            return clips[0] if clips else None

    def _generate_srt(self, ctx: PipelineContext, output_dir: Path) -> Optional[Path]:
        """Generate SRT subtitles from storyboard narrations."""
        if not ctx.storyboard or not ctx.storyboard.scenes:
            return None

        srt_lines = []
        current_time = 0.0
        idx = 1

        for scene in ctx.storyboard.scenes:
            if not scene.narration:
                current_time += scene.duration
                continue

            start_ts = self._format_srt_time(current_time)
            end_ts = self._format_srt_time(current_time + scene.duration)

            srt_lines.append(f"{idx}")
            srt_lines.append(f"{start_ts} --> {end_ts}")
            srt_lines.append(scene.narration)
            srt_lines.append("")

            current_time += scene.duration
            idx += 1

        if not srt_lines:
            return None

        srt_path = output_dir / f"{ctx.project_id}.srt"
        srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
        return srt_path

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _save_metadata(self, ctx: PipelineContext) -> None:
        """Save pipeline run metadata as JSON."""
        output_dir = Path(ctx.project_dir) / "videos" / ctx.project_id
        output_dir.mkdir(parents=True, exist_ok=True)

        meta = {
            "project_id": ctx.project_id,
            "title": ctx.storyboard.title if ctx.storyboard else "Unknown",
            "scenes": len(ctx.storyboard.scenes) if ctx.storyboard else 0,
            "total_duration": ctx.storyboard.total_duration if ctx.storyboard else 0,
            "video_path": str(ctx.video_path) if ctx.video_path else None,
            "final_path": str(ctx.final_path) if ctx.final_path else None,
            "srt_path": ctx.metadata.get("srt_path"),
            "clip_paths": ctx.metadata.get("clip_paths", []),
            # Embed the full storyboard so the showcase page can render scenes
            # without needing a separate file or DB lookup.
            "storyboard": ctx.storyboard.model_dump() if ctx.storyboard else None,
        }
        meta_path = output_dir / "metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("  Metadata saved: %s", meta_path.name)
