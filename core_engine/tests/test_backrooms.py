"""The Backrooms — Opening Scene Pipeline Test.

Story: A lone wanderer noclips into the Backrooms, Level 0.
Yellow wallpaper, humming fluorescent lights, the smell of moist carpet.
This is the opening scene — 15 seconds of pure dread.

Pipeline:
  Stage 1: Fixed storyboard (no LLM, pre-written for quality)
  Stage 2: DashScope wanx-v1 → first frame image (T2I)
  Stage 3: DashScope wan2.7-i2v → 15s video (I2V, max duration)
"""
import os
import time

os.environ.setdefault("DASHSCOPE_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))

print("=" * 65)
print("  THE BACKROOMS — Opening Scene")
print("  后室 · 第零层 · 入侵者")
print("=" * 65)

# ── STAGE 1: Manually craft the storyboard ────────────────────────
print("\n[STAGE 1] Storyboard — 后室 Level 0 开场")

from core_engine.src.schemas.models import (
    AudioMode, CameraMotion, Resolution, SceneSchema,
    StoryboardSchema, TransitionType, VideoStyle, WanConfig,
)
from core_engine.src.pipeline.base import PipelineContext

# The first frame image prompt — describe exactly what wanx-v1 should draw
FIRST_FRAME_PROMPT = (
    "The Backrooms Level 0. An endless corridor of yellowed wallpaper with "
    "a repeating geometric pattern, worn beige carpet, long rows of flickering "
    "fluorescent tube lights on the ceiling casting a pale sickly glow. "
    "A lone figure in a hoodie stands at the far end of the corridor, "
    "their back to the camera, looking into the infinite darkness ahead. "
    "The walls stretch endlessly in both directions. No windows, no doors. "
    "Liminal horror atmosphere, photorealistic, cinematic 16:9 composition, "
    "found-footage aesthetic, ultra-detailed."
)

# The 15-second I2V video prompt — Wan 2.7 multi-shot format
VIDEO_PROMPT = (
    "The Backrooms Level 0. An infinite corridor of yellowed wallpaper and "
    "flickering fluorescent lights. "
    "Shot 1 [0-5s]: Camera slowly drifts forward down the endless corridor, "
    "fluorescent light above flickers and buzzes, shadows shift unnaturally. "
    "A distant humming grows louder. The lone figure does not move. "
    "Shot 2 [5-10s]: The camera pans left to reveal a side passage — "
    "another identical infinite corridor. Something moves at the very edge of the darkness, "
    "too quick to identify. The figure tenses. "
    "Shot 3 [10-15s]: The camera drifts back slowly, the figure turns around "
    "to face the camera — their face is pale, eyes wide with realization. "
    "They whisper: 'There's no way out.' Fluorescent lights suddenly all flicker at once. "
    "Cut to black. Distant sound of wet footsteps echo."
)

scene = SceneSchema(
    scene_id=1,
    duration=15,
    visual_prompt=VIDEO_PROMPT,
    narration="第零层。无尽的回廊。黄色墙纸，荧光灯嗡嗡作响。没有出口。",
    style=VideoStyle.CINEMATIC,
    camera_motion=CameraMotion.ZOOM_IN,
    transition=TransitionType.FADE,
    audio_mode=AudioMode.NATIVE,
)

storyboard = StoryboardSchema(
    title="The Backrooms — 后室 Level 0",
    description="A wanderer noclips into the Backrooms. No way back.",
    target_duration=15,
    lang="en",
    scenes=[scene],
    wan_config=WanConfig(resolution=Resolution.HD),
)

ctx = PipelineContext(project_dir="core_engine/output", project_id="backrooms_opening")
ctx.storyboard = storyboard

print(f"  Title: {storyboard.title}")
print(f"  Scene 1: {scene.duration}s (MAX duration)")
print(f"  Visual: {scene.visual_prompt[:120]}...")

# ── STAGE 2: Generate first frame via DashScope wanx-v1 ───────────
print("\n[STAGE 2] 生成首帧图片 — DashScope wanx-v1 (T2I)")

from core_engine.src.providers.image.dashscope_wanx import DashScopeWanxImageProvider
from core_engine.src.schemas.models import AssetManifest, SceneAssets

img_provider = DashScopeWanxImageProvider(output_dir="core_engine/output/assets")
img_path = img_provider.generate(
    prompt=FIRST_FRAME_PROMPT,
    style="cinematic",
    size=(1280, 720),
)
print(f"  First frame: {img_path}")
print(f"  Image URL: {img_provider._last_image_url[:80]}...")

# Build asset manifest with the image URL
manifest = AssetManifest(project_id="backrooms_opening", base_dir=None)
scene_asset = SceneAssets(
    scene_id=1,
    image_path=img_path,
    image_url=img_provider._last_image_url,
)
manifest.scenes.append(scene_asset)
ctx.assets = manifest

# ── STAGE 3: Generate video via DashScope wan2.7-i2v ──────────────
print("\n[STAGE 3] 生成视频 — DashScope wan2.7-i2v (I2V, 15s max)")
print("  Prompt preview:")
print(f"    {scene.visual_prompt[:200]}...")

from core_engine.src.stages.video_composer import VideoComposer
from core_engine.src.providers.video.dashscope_wan import DashScopeWanProvider

vid_provider = DashScopeWanProvider(output_dir="core_engine/output/videos")
composer = VideoComposer(video_provider=vid_provider)
composer.execute(ctx)

# ── Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  PIPELINE COMPLETE")
print("=" * 65)
clip_paths = ctx.metadata.get("clip_paths", [])
if clip_paths:
    import pathlib
    p = pathlib.Path(clip_paths[0])
    if p.exists():
        size_mb = p.stat().st_size / (1024 * 1024)
        print(f"  📹 Video : {p}")
        print(f"  💾 Size  : {size_mb:.1f} MB")
        print(f"  ⏱️  Duration: 15s (1080P)")
    else:
        print(f"  Output path: {clip_paths[0]}")
print(f"  🖼️  Frame : {img_path}")
