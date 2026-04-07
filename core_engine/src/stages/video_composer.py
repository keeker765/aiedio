"""Stage 3: Video Composer — uses Wan 2.6/2.7 (via provider) to generate video clips per scene.

Two composition modes:
  - T2V: Send visual_prompt directly to Wan text-to-video (fal.ai)
  - I2V: Use a pre-generated image as first frame + motion prompt (DashScope)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from core_engine.src.pipeline.base import BaseStage, PipelineContext
from core_engine.src.providers.base import VideoProvider
from core_engine.src.providers.video.dashscope_wan import DashScopeWanProvider
from core_engine.src.schemas.models import AudioMode


class VideoComposer(BaseStage):
    """Stage 3: Generate video clips using Wan 2.6/2.7."""

    name = "video_composer"

    def __init__(self, video_provider: VideoProvider | None = None):
        self.video_provider = video_provider

    def execute(self, ctx: PipelineContext) -> None:
        if ctx.storyboard is None:
            raise RuntimeError("No storyboard in context")
        if self.video_provider is None:
            raise RuntimeError("No video provider configured")

        sb = ctx.storyboard
        wan = sb.wan_config
        project_dir = Path(ctx.project_dir)
        videos_dir = project_dir / "videos" / ctx.project_id
        videos_dir.mkdir(parents=True, exist_ok=True)

        is_dashscope = isinstance(self.video_provider, DashScopeWanProvider)
        clip_paths: list[Path] = []

        for scene in sb.scenes:
            print(f"  [Scene {scene.scene_id}] Generating video ({scene.duration}s)...")

            # Check if we have an image for this scene (for I2V mode)
            image_url: Optional[str] = None
            if ctx.assets:
                scene_asset = ctx.assets.get_scene(scene.scene_id)
                if scene_asset:
                    # Prefer public URL for DashScope (needs HTTP-accessible image)
                    if scene_asset.image_url:
                        image_url = scene_asset.image_url
                    elif scene_asset.image_path and str(scene_asset.image_path).startswith("http"):
                        image_url = str(scene_asset.image_path)

            try:
                if is_dashscope and image_url:
                    # DashScope I2V mode: use image as first frame
                    clip_path = self.video_provider.image_to_video(
                        prompt=scene.visual_prompt,
                        image_url=image_url,
                        duration=str(scene.duration),
                        resolution=wan.resolution.value,
                    )
                else:
                    # T2V mode (fal.ai or placeholder)
                    clip_path = self.video_provider.text_to_video(
                        prompt=scene.visual_prompt,
                        duration=str(scene.duration),
                        resolution=wan.resolution.value,
                        aspect_ratio=wan.aspect_ratio.value,
                        seed=wan.seed,
                    )

                clip_paths.append(clip_path)

                # Update asset manifest
                if ctx.assets:
                    scene_asset = ctx.assets.get_scene(scene.scene_id)
                    if scene_asset:
                        scene_asset.video_path = clip_path

                print(f"  [Scene {scene.scene_id}] ✅ Video saved: {clip_path.name}")

            except Exception as e:
                print(f"  [Scene {scene.scene_id}] ❌ Video generation failed: {e}")

        if clip_paths:
            ctx.video_path = clip_paths[0] if len(clip_paths) == 1 else clip_paths[0]
            ctx.metadata["clip_paths"] = [str(p) for p in clip_paths]
            print(f"  Total clips generated: {len(clip_paths)}")
        else:
            print("  ⚠️ No video clips were generated")
