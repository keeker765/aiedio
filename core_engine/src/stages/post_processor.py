"""Stage 4: Post Processor — concatenate clips, burn subtitles, add intro/outro.

Uses MoviePy (already in requirements) for video editing operations.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from core_engine.src.pipeline.base import BaseStage, PipelineContext


class PostProcessor(BaseStage):
    """Stage 4: Concatenate video clips, add subtitles, export final video."""

    name = "post_processor"

    def execute(self, ctx: PipelineContext) -> None:
        clip_paths_raw = ctx.metadata.get("clip_paths", [])
        clip_paths = [Path(p) for p in clip_paths_raw if Path(p).exists() and Path(p).suffix == ".mp4"]

        if not clip_paths:
            print("  No video clips to process")
            self._save_metadata(ctx)
            return

        project_dir = Path(ctx.project_dir)
        output_dir = project_dir / "videos" / ctx.project_id
        output_dir.mkdir(parents=True, exist_ok=True)

        if len(clip_paths) == 1:
            # Single clip — just apply post-processing
            ctx.final_path = clip_paths[0]
            print(f"  Single clip — output: {clip_paths[0].name}")
        else:
            # Multiple clips — concatenate with MoviePy
            final_path = self._concatenate_clips(clip_paths, output_dir, ctx)
            if final_path:
                ctx.final_path = final_path

        # Generate SRT subtitle file from storyboard narrations
        if ctx.storyboard:
            srt_path = self._generate_srt(ctx, output_dir)
            if srt_path:
                ctx.metadata["srt_path"] = str(srt_path)
                print(f"  Subtitles saved: {srt_path.name}")

        self._save_metadata(ctx)

    def _concatenate_clips(
        self, clips: list[Path], output_dir: Path, ctx: PipelineContext
    ) -> Optional[Path]:
        """Concatenate multiple MP4 clips into one video."""
        try:
            # moviepy 2.x changed import path
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
                    print(f"  [WARN] Could not load clip {p.name}: {e}")

            if not video_clips:
                return None

            final = concatenate_videoclips(video_clips, method="compose")
            final_path = output_dir / f"{ctx.project_id}_final.mp4"
            final.write_videofile(
                str(final_path),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )

            for vc in video_clips:
                vc.close()

            print(f"  Concatenated {len(video_clips)} clips → {final_path.name}")
            return final_path

        except ImportError:
            print("  [WARN] MoviePy not available — skipping concatenation")
            return clips[0] if clips else None
        except Exception as e:
            print(f"  [ERROR] Concatenation failed: {e}")
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
        }
        meta_path = output_dir / "metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Metadata saved: {meta_path.name}")
