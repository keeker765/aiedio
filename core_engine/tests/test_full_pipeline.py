"""Full pipeline integration test with real APIs.

Stage 1: ScriptGenerator (OpenRouter LLM)
Stage 2: AssetGenerator (skipped — using sample image)
Stage 3: VideoComposer (DashScope Wan 2.7 I2V)
"""
import os
import json
import time

os.environ.setdefault("OPENROUTER_API_KEY", "")
os.environ.setdefault("DASHSCOPE_API_KEY", "")

print("=" * 60)
print("AIEDIO FULL PIPELINE TEST")
print("=" * 60)

# === STAGE 1: Script Generation ===
print("\n[STAGE 1] ScriptGenerator — LLM storyboard generation")
from core_engine.src.stages.script_generator import ScriptGenerator
from core_engine.src.pipeline.base import PipelineContext

ctx = PipelineContext(project_dir="core_engine/output", project_id="fulltest")
gen = ScriptGenerator(topic="A tiger walking through a bamboo forest at golden hour", lang="en")
gen.execute(ctx)

sb = ctx.storyboard
print(f"  Title: {sb.title}")
print(f"  Scenes: {len(sb.scenes)}")
for s in sb.scenes:
    prompt_preview = s.visual_prompt[:100]
    narr_preview = s.narration[:80] if s.narration else "(none)"
    print(f"  Scene {s.scene_id}: {s.duration}s — {prompt_preview}...")
    print(f"    Narration: {narr_preview}")

# Save storyboard
sb_path = "core_engine/output/storyboards/fulltest.json"
os.makedirs("core_engine/output/storyboards", exist_ok=True)
with open(sb_path, "w", encoding="utf-8") as f:
    f.write(sb.model_dump_json(indent=2))
print(f"  Saved: {sb_path}")

# === Reduce to 1 scene for DashScope timing ===
print("\n  Trimming to 1 scene for test (each DashScope call ~14 min)...")
scene = sb.scenes[0]
scene.duration = 5
sb.scenes = [scene]

# === STAGE 2: Asset Generation (placeholder — no ZHIPU key) ===
print("\n[STAGE 2] AssetGenerator — using public sample image")
from core_engine.src.schemas.models import AssetManifest, SceneAssets

sample_url = "https://dashscope.oss-cn-beijing.aliyuncs.com/images/tiger.png"
manifest = AssetManifest(project_id="fulltest", base_dir=None)
scene_asset = SceneAssets(scene_id=1, image_url=sample_url)
manifest.scenes.append(scene_asset)
ctx.assets = manifest
print(f"  First frame URL: {sample_url}")

# === STAGE 3: VideoComposer (DashScope I2V) ===
print("\n[STAGE 3] VideoComposer — DashScope Wan 2.7 I2V")
from core_engine.src.stages.video_composer import VideoComposer
from core_engine.src.providers.video.dashscope_wan import DashScopeWanProvider

provider = DashScopeWanProvider(output_dir="core_engine/output/videos")
composer = VideoComposer(video_provider=provider)
composer.execute(ctx)

clip_paths = ctx.metadata.get("clip_paths", [])
print(f"\n  Video path: {ctx.video_path}")
print(f"  Clip paths: {clip_paths}")

# === Summary ===
print("\n" + "=" * 60)
print("FULL PIPELINE TEST COMPLETE")
print("=" * 60)
if ctx.video_path:
    vp = ctx.video_path
    if hasattr(vp, "stat"):
        size_mb = vp.stat().st_size / (1024 * 1024)
        print(f"  Output: {vp} ({size_mb:.1f} MB)")
    else:
        print(f"  Output: {vp}")
