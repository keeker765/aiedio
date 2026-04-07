"""Stage 2: Asset Generator — storyboard → images, TTS audio, background music.

Generates all media assets needed for video composition.
"""
from __future__ import annotations

import os
from pathlib import Path

from core_engine.src.pipeline.base import BaseStage, PipelineContext
from core_engine.src.providers.base import ImageProvider, MusicProvider, TTSProvider
from core_engine.src.schemas.models import AssetManifest, AudioMode, SceneAssets


class AssetGenerator(BaseStage):
    """Stage 2: Generate visual and audio assets for each scene."""

    name = "asset_generator"

    def __init__(
        self,
        image_provider: ImageProvider | None = None,
        tts_provider: TTSProvider | None = None,
        music_provider: MusicProvider | None = None,
    ):
        self.image_provider = image_provider
        self.tts_provider = tts_provider
        self.music_provider = music_provider

    def execute(self, ctx: PipelineContext) -> None:
        if ctx.storyboard is None:
            raise RuntimeError("No storyboard in context — run ScriptGenerator first")

        sb = ctx.storyboard
        project_dir = Path(ctx.project_dir)
        assets_dir = project_dir / "assets" / ctx.project_id
        assets_dir.mkdir(parents=True, exist_ok=True)

        manifest = AssetManifest(project_id=ctx.project_id, base_dir=assets_dir)

        for scene in sb.scenes:
            scene_assets = SceneAssets(scene_id=scene.scene_id)

            # Generate image (for I2V mode or as thumbnail)
            if self.image_provider:
                print(f"  [Scene {scene.scene_id}] Generating image...")
                try:
                    img_path = self.image_provider.generate(
                        prompt=scene.visual_prompt,
                        style=scene.style.value,
                    )
                    scene_assets.image_path = img_path
                    # Capture public URL if provider stores it (for DashScope I2V)
                    url = getattr(self.image_provider, "_last_image_url", None)
                    if url:
                        scene_assets.image_url = url
                except Exception as e:
                    print(f"  [Scene {scene.scene_id}] Image generation failed: {e}")

            # Generate TTS narration (only in TTS_OVERLAY mode — native mode uses Wan's built-in audio)
            if (
                self.tts_provider
                and scene.narration
                and scene.audio_mode == AudioMode.TTS_OVERLAY
            ):
                print(f"  [Scene {scene.scene_id}] Generating TTS...")
                try:
                    audio_path = self.tts_provider.synthesize(
                        text=scene.narration,
                        lang=sb.lang,
                    )
                    scene_assets.audio_path = audio_path
                except Exception as e:
                    print(f"  [Scene {scene.scene_id}] TTS failed: {e}")

            manifest.scenes.append(scene_assets)

        # Generate background music
        if self.music_provider:
            print(f"  Selecting background music (mood={sb.global_style.mood})...")
            try:
                bgm_path = self.music_provider.get_track(
                    mood=sb.global_style.mood,
                    duration=float(sb.total_duration),
                )
                manifest.bgm_path = bgm_path
            except Exception as e:
                print(f"  BGM selection failed: {e}")

        ctx.assets = manifest
        print(f"  Assets generated: {len(manifest.scenes)} scenes")
