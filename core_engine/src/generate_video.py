"""Aiedio Core Engine — CLI entry point for the video generation pipeline.

Usage (from project root):
  python -m core_engine.src.generate_video                        # default: fetch trending topic
  python -m core_engine.src.generate_video --topic "AI in 2026"   # custom topic
  python -m core_engine.src.generate_video --lang zh              # Chinese output
"""
from __future__ import annotations

import argparse
import logging
import os
import time
import uuid

from core_engine.src.pipeline.base import PipelineContext

log = logging.getLogger("aiedio")
from core_engine.src.pipeline.runner import PipelineRunner

# Stages
from core_engine.src.stages.script_generator import ScriptGenerator
from core_engine.src.stages.asset_generator import AssetGenerator
from core_engine.src.stages.video_composer import VideoComposer
from core_engine.src.stages.post_processor import PostProcessor

# Providers
from core_engine.src.providers.video.fal_wan import FalWanProvider
from core_engine.src.providers.video.dashscope_video import DashScopeWanProvider, DashScopeHappyhorseProvider
from core_engine.src.providers.video.kling_v3_video import KlingVideoProvider
from core_engine.src.providers.video.placeholder import PlaceholderVideoProvider
from core_engine.src.providers.video.openrouter_video import OpenRouterVideoProvider
from core_engine.src.providers.tts.edge_tts_provider import EdgeTTSProvider
from core_engine.src.providers.image.zhipu_cogview import ZhipuImageProvider
from core_engine.src.providers.image.openrouter_image import OpenRouterImageProvider
from core_engine.src.providers.music.local_library import LocalMusicProvider
from core_engine.src.schemas.models import StoryboardSchema


_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _select_image_provider(output_dir: str) -> OpenRouterImageProvider | ZhipuImageProvider:
    """Auto-select image provider. Priority: OpenRouter > ZhipuAI."""
    if os.getenv("OPENROUTER_API_KEY"):
        log.info("  Image provider: GPT-5.4 Image 2 via OpenRouter")
        return OpenRouterImageProvider(output_dir=output_dir)
    log.info("  Image provider: Zhipu CogView (set OPENROUTER_API_KEY for GPT-5.4 Image)")
    return ZhipuImageProvider(output_dir=output_dir)


def run_pipeline(
    topic: str,
    knowledge: list | None = None,
    storyboard_dict: dict | None = None,
    *,
    project_id: str | None = None,
    lang: str = "en",
    storyboard_only: bool = False,
    on_scene_done: callable | None = None,
    video_provider: str = "openrouter",
    image_provider: str = "openrouter",
    analyses: list | None = None,
    video_model: str = "",
    scene_count: int = 0,
) -> dict:
    """Public API for backend to call the pipeline.

    Args:
        topic: Video topic string.
        knowledge: Optional list of knowledge dicts from crawler.
        storyboard_dict: Optional pre-generated storyboard dict (skip ScriptGenerator).
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

    ctx = PipelineContext(project_id=project_id, project_dir=project_dir)
    if knowledge:
        ctx.metadata["knowledge"] = knowledge
    if analyses:
        ctx.metadata["analyses"] = analyses
    if on_scene_done:
        ctx.metadata["on_scene_done"] = on_scene_done

    # If a pre-built storyboard is provided, hydrate it and skip ScriptGenerator
    if storyboard_dict:
        ctx.storyboard = StoryboardSchema(**storyboard_dict)
        log.info("  Using pre-generated storyboard: %s (%d scenes)", ctx.storyboard.title, len(ctx.storyboard.scenes))

    runner = PipelineRunner()

    # Stage 1: Script — skip if storyboard already provided
    if not storyboard_dict:
        runner.add_stage(ScriptGenerator(topic=topic, lang=lang, scene_count=scene_count))

    if not storyboard_only:
        # Stage 2: Assets
        assets_dir = os.path.join(project_dir, "assets", project_id)
        img_prov = {
            "openrouter": OpenRouterImageProvider,
            "zhipu": ZhipuImageProvider,
        }.get(image_provider, OpenRouterImageProvider)
        runner.add_stage(AssetGenerator(
            image_provider=img_prov(output_dir=assets_dir) if img_prov else ZhipuImageProvider(output_dir=assets_dir),
            tts_provider=EdgeTTSProvider(output_dir=assets_dir),
            music_provider=LocalMusicProvider(),
        ))

        # Stage 3: Video
        video_dir = os.path.join(project_dir, "videos", project_id)
        vid_prov_cls = {
            "kling_v3": KlingVideoProvider,
            "openrouter": OpenRouterVideoProvider,
            "dashscope": DashScopeWanProvider,
            "happyhorse": DashScopeHappyhorseProvider,
            "fal": FalWanProvider,
            "placeholder": PlaceholderVideoProvider,
        }.get(video_provider, KlingVideoProvider)  # default: Kling V3 (highest quality)
        log.info("  Video provider: %s (%s) model=%s", vid_prov_cls.__name__, video_provider, video_model or 'default')
        vid_kwargs = {"output_dir": video_dir}
        if video_model:
            vid_kwargs["model"] = video_model
        runner.add_stage(VideoComposer(video_provider=vid_prov_cls(**vid_kwargs)))

        # Stage 4: Post-processing
        runner.add_stage(PostProcessor())

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

    log.info("Aiedio Video Pipeline — Project ID: %s", project_id)

    # Build pipeline
    runner = PipelineRunner()

    # Stage 1: Script
    runner.add_stage(ScriptGenerator(topic=args.topic, lang=args.lang))

    if not args.no_video:
        # Stage 2: Assets
        if not args.no_assets:
            assets_dir = os.path.join(project_dir, "assets", project_id)
            runner.add_stage(AssetGenerator(
                image_provider=OpenRouterImageProvider(output_dir=assets_dir),
                tts_provider=EdgeTTSProvider(output_dir=assets_dir),
                music_provider=LocalMusicProvider(),
            ))

        # Stage 3: Video (hardcoded to OpenRouter Kling Video O1)
        video_dir = os.path.join(project_dir, "videos", project_id)
        runner.add_stage(VideoComposer(video_provider=OpenRouterVideoProvider(output_dir=video_dir)))

        # Stage 4: Post-processing
        runner.add_stage(PostProcessor())

    # Create context and run
    ctx = PipelineContext(project_id=project_id, project_dir=project_dir)
    result = runner.run(ctx)

    # Print summary
    log.info("Result: success=%s", result.success)
    if result.storyboard:
        log.info("  Title: %s", result.storyboard.title)
        log.info("  Scenes: %d", len(result.storyboard.scenes))
        log.info("  Duration: %ds", result.storyboard.total_duration)
    if result.final_path:
        log.info("  Output: %s", result.final_path)
    if result.error:
        log.error("  Error: %s", result.error)

    return result


if __name__ == "__main__":
    main()
