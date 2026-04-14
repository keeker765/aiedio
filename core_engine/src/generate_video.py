"""Aiedio Core Engine — CLI entry point for the video generation pipeline.

Usage (from project root):
  python -m core_engine.src.generate_video                        # default: fetch trending topic
  python -m core_engine.src.generate_video --topic "AI in 2026"   # custom topic
  python -m core_engine.src.generate_video --lang zh              # Chinese output
"""
from __future__ import annotations

import argparse
import os
import time
import uuid

from core_engine.src.pipeline.base import PipelineContext
from core_engine.src.pipeline.runner import PipelineRunner

# Stages
from core_engine.src.stages.script_generator import ScriptGenerator
from core_engine.src.stages.asset_generator import AssetGenerator
from core_engine.src.stages.video_composer import VideoComposer
from core_engine.src.stages.post_processor import PostProcessor

# Providers
from core_engine.src.providers.video.fal_wan import FalWanProvider
from core_engine.src.providers.video.dashscope_wan import DashScopeWanProvider
from core_engine.src.providers.video.kling_v3_video import KlingVideoProvider
from core_engine.src.providers.video.placeholder import PlaceholderVideoProvider
from core_engine.src.providers.tts.edge_tts_provider import EdgeTTSProvider
from core_engine.src.providers.image.zhipu_cogview import ZhipuImageProvider
from core_engine.src.providers.music.local_library import LocalMusicProvider


_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _select_video_provider(output_dir: str) -> KlingVideoProvider | FalWanProvider | DashScopeWanProvider | PlaceholderVideoProvider:
    """Auto-select video provider based on available API keys.

    Priority: Kling V3 > wan2.7 (DashScope) > Wan2.6 (fal.ai) > Placeholder
    Both Kling V3 and wan2.7 use the same DASHSCOPE_API_KEY.
    """
    if os.getenv("DASHSCOPE_API_KEY"):
        print("  Video provider: Kling V3 via DashScope (kling/kling-v3-video-generation) ✅")
        return KlingVideoProvider(output_dir=output_dir)
    if os.getenv("FAL_KEY"):
        print("  Video provider: Wan 2.6 via fal.ai ✅")
        return FalWanProvider(output_dir=output_dir)
    print("  Video provider: Placeholder (set DASHSCOPE_API_KEY or FAL_KEY)")
    return PlaceholderVideoProvider(output_dir=output_dir)


def run_pipeline(
    topic: str,
    knowledge: list | None = None,
    *,
    project_id: str | None = None,
    lang: str = "zh",
    storyboard_only: bool = False,
    on_scene_done: callable | None = None,
) -> dict:
    """Public API for backend to call the pipeline.

    Args:
        topic: Video topic string.
        knowledge: Optional list of knowledge dicts from crawler.
        project_id: Optional project ID (auto-generated if None).
        lang: Output language ("en" or "zh").
        storyboard_only: If True, only run ScriptGenerator (for B3).
        on_scene_done: Optional callback(scene_idx, total, clip_path) for progress.

    Returns:
        dict with keys: success, project_id, storyboard, final_path, error
    """
    if not project_id:
        project_id = f"vid_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    project_dir = os.path.join(_ROOT, "core_engine", "output")

    runner = PipelineRunner()

    # Stage 1: Script — inject knowledge into metadata
    runner.add_stage(ScriptGenerator(topic=topic, lang=lang))

    if not storyboard_only:
        # Stage 2: Assets
        assets_dir = os.path.join(project_dir, "assets", project_id)
        runner.add_stage(AssetGenerator(
            image_provider=ZhipuImageProvider(output_dir=assets_dir),
            tts_provider=EdgeTTSProvider(output_dir=assets_dir),
            music_provider=LocalMusicProvider(),
        ))

        # Stage 3: Video
        video_dir = os.path.join(project_dir, "videos", project_id)
        video_provider = _select_video_provider(video_dir)
        runner.add_stage(VideoComposer(video_provider=video_provider))

        # Stage 4: Post-processing
        runner.add_stage(PostProcessor())

    ctx = PipelineContext(project_id=project_id, project_dir=project_dir)
    if knowledge:
        ctx.metadata["knowledge"] = knowledge

    result = runner.run(ctx)

    # Convert to plain dict for JSON serialization
    storyboard_dict = None
    if result.storyboard:
        storyboard_dict = result.storyboard.model_dump()

    return {
        "success": result.success,
        "project_id": result.project_id,
        "storyboard": storyboard_dict,
        "final_path": str(result.final_path) if result.final_path else None,
        "error": result.error,
    }


def main():
    parser = argparse.ArgumentParser(description="Aiedio Video Generation Pipeline")
    parser.add_argument("--topic", type=str, default=None, help="Custom topic (skips trending fetch)")
    parser.add_argument("--lang", default="en", choices=["en", "zh"], help="Output language")
    parser.add_argument("--no-assets", action="store_true", help="Skip asset generation (images/TTS)")
    parser.add_argument("--no-video", action="store_true", help="Script-only mode (no video generation)")
    args = parser.parse_args()

    project_id = f"vid_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    project_dir = os.path.join(_ROOT, "core_engine", "output")

    print(f"\n🎬 Aiedio Video Pipeline")
    print(f"  Project ID: {project_id}")

    # Build pipeline
    runner = PipelineRunner()

    # Stage 1: Script
    runner.add_stage(ScriptGenerator(topic=args.topic, lang=args.lang))

    if not args.no_video:
        # Stage 2: Assets
        if not args.no_assets:
            assets_dir = os.path.join(project_dir, "assets", project_id)
            runner.add_stage(AssetGenerator(
                image_provider=ZhipuImageProvider(output_dir=assets_dir),
                tts_provider=EdgeTTSProvider(output_dir=assets_dir),
                music_provider=LocalMusicProvider(),
            ))

        # Stage 3: Video
        video_dir = os.path.join(project_dir, "videos", project_id)
        video_provider = _select_video_provider(video_dir)
        runner.add_stage(VideoComposer(video_provider=video_provider))

        # Stage 4: Post-processing
        runner.add_stage(PostProcessor())

    # Create context and run
    ctx = PipelineContext(project_id=project_id, project_dir=project_dir)
    result = runner.run(ctx)

    # Print summary
    print(f"\n📋 Result Summary:")
    print(f"  Success: {result.success}")
    if result.storyboard:
        print(f"  Title: {result.storyboard.title}")
        print(f"  Scenes: {len(result.storyboard.scenes)}")
        print(f"  Duration: {result.storyboard.total_duration}s")
    if result.final_path:
        print(f"  Output: {result.final_path}")
    if result.error:
        print(f"  Error: {result.error}")

    return result


if __name__ == "__main__":
    main()
