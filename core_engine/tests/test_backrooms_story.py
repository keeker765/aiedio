"""The Backrooms — Full Story (4 Scenes, ~60s total) using wan2.7-t2v.

Story arc:
  Scene 1 (15s): The noclip — A person falls through reality into Level 0
  Scene 2 (15s): The wandering — Endless corridors, something follows
  Scene 3 (15s): The encounter — A silhouette appears at the end of the hall
  Scene 4 (15s): The descent — The floor gives way, falling into Level 1

All scenes use wan2.7-t2v (pure text-to-video, no image needed).
PostProcessor concatenates all 4 clips into one ~60s final video.
"""
import os
import time

os.environ.setdefault("DASHSCOPE_API_KEY", "sk-a502b56390664a90aa0daa32df5c068a")

print("=" * 65)
print("  THE BACKROOMS — Complete Story (4 Scenes / ~60s)")
print("  后室 · 完整短片")
print("=" * 65)

# ── STAGE 1: Storyboard ───────────────────────────────────────────
print("\n[STAGE 1] Storyboard — 4 scenes, 15s each")

from core_engine.src.schemas.models import (
    AudioMode, CameraMotion, Resolution, SceneSchema,
    StoryboardSchema, TransitionType, VideoStyle, WanConfig,
)
from core_engine.src.pipeline.base import PipelineContext

scenes = [
    SceneSchema(
        scene_id=1,
        duration=15,
        visual_prompt=(
            "Cinematic horror short film. A young man in a grey hoodie and jeans is walking "
            "through a normal shopping mall corridor with white tiles and bright lights. "
            "Shot 1 [0-4s]: He glances down at his phone, takes one wrong step — the floor "
            "suddenly ripples like water under his foot. His face shows confusion. "
            "Shot 2 [4-9s]: The floor gives way in slow motion, white tiles dissolving into "
            "darkness. He falls downward, reaching upward desperately — the shopping mall "
            "ceiling shrinks to a pinhole of light above him. "
            "Shot 3 [9-15s]: He crashes onto soft, yellowed carpet. He looks up — an infinite "
            "corridor stretches in every direction, covered in yellowed geometric-pattern wallpaper. "
            "Flickering fluorescent lights hum overhead. He whispers in disbelief: 'Where am I?' "
            "Photorealistic, found-footage aesthetic, cinematic 16:9, 24fps."
        ),
        narration="你走错了一步。购物中心消失了。黄色的墙纸，荧光灯的嗡鸣。欢迎来到后室。",
        style=VideoStyle.CINEMATIC,
        camera_motion=CameraMotion.ZOOM_IN,
        transition=TransitionType.FADE,
        audio_mode=AudioMode.NATIVE,
    ),
    SceneSchema(
        scene_id=2,
        duration=15,
        visual_prompt=(
            "Cinematic psychological horror. The same young man in grey hoodie walks cautiously "
            "down an infinite corridor of yellowed wallpaper and flickering fluorescent tubes. "
            "Shot 1 [0-5s]: He walks forward — the corridor ahead is identical to the one behind, "
            "stretching infinitely. His footsteps echo wetly on the beige carpet. "
            "He keeps glancing over his shoulder — nothing there. "
            "Shot 2 [5-10s]: Camera slowly rotates to reveal his shadow on the wall — "
            "the shadow has a slightly different shape, taller, with elongated arms. "
            "He hasn't noticed yet. The fluorescent light nearest to him flickers and dies. "
            "Shot 3 [10-15s]: He freezes. He has noticed his shadow. He turns around slowly — "
            "the corridor behind him is now slightly darker. Something is wrong with the geometry. "
            "The walls seem slightly closer than before. He runs. "
            "Handheld camera shake, pale sickly fluorescent light, ultra-detailed, photorealistic."
        ),
        narration="走廊没有尽头。荧光灯一盏一盏熄灭。你的影子不是你的影子。",
        style=VideoStyle.CINEMATIC,
        camera_motion=CameraMotion.PAN_RIGHT,
        transition=TransitionType.CUT,
        audio_mode=AudioMode.NATIVE,
    ),
    SceneSchema(
        scene_id=3,
        duration=15,
        visual_prompt=(
            "Cinematic horror. The young man in grey hoodie runs down a long corridor, "
            "panting heavily, fluorescent lights strobing around him. "
            "Shot 1 [0-5s]: He skids to a stop — at the very far end of the corridor, "
            "500 meters away, stands a tall dark humanoid silhouette. Completely still. "
            "No facial features. Just watching. The lights between them begin to go out one by one, "
            "starting from the silhouette and moving toward him. "
            "Shot 2 [5-10s]: He backs away slowly. The silhouette has not moved — but it is closer. "
            "Much closer. It is now only 50 meters away. It did not walk. It simply is closer. "
            "The remaining lights flicker. The humming intensifies to a painful frequency. "
            "Shot 3 [10-15s]: Close-up of his face — pure terror. He turns and sprints. "
            "Behind him we hear a sound: a long, slow exhale. "
            "The silhouette is now standing exactly where he was standing. "
            "Strobe lighting, handheld camera, found footage style, extreme close-up detail."
        ),
        narration="走廊尽头有什么东西。它没有移动。但它更近了。",
        style=VideoStyle.CINEMATIC,
        camera_motion=CameraMotion.ZOOM_OUT,
        transition=TransitionType.CUT,
        audio_mode=AudioMode.NATIVE,
    ),
    SceneSchema(
        scene_id=4,
        duration=15,
        visual_prompt=(
            "Cinematic horror ending sequence. The young man in grey hoodie is crawling on all fours "
            "across the yellowed carpet, gasping, completely exhausted. "
            "Shot 1 [0-5s]: He stops crawling — the carpet in front of him is wet. "
            "The ceiling is dripping dark water. The wallpaper is peeling. "
            "The geometry is wrong — the corridor curves in a direction that shouldn't exist. "
            "Shot 2 [5-10s]: The floor beneath him begins to crack like a frozen lake. "
            "Through the cracks: darkness, and far below, the sound of rushing water. "
            "He scrambles backward but the cracks chase him. "
            "Shot 3 [10-15s]: The floor collapses completely. He falls — "
            "but this time into a vast dark cavern with a distant pale blue light below. "
            "As he falls he sees other corridors, other levels, an infinite vertical maze "
            "of rooms and hallways. He screams. Cut to black. "
            "A single title card appears on black screen: LEVEL 1 — THE POOLROOMS. "
            "Cinematic, photorealistic, found footage, terrifying."
        ),
        narration="地板裂开了。他落入第一层。游泳池室。水声。无穷无尽。",
        style=VideoStyle.CINEMATIC,
        camera_motion=CameraMotion.TILT_DOWN,
        transition=TransitionType.FADE,
        audio_mode=AudioMode.NATIVE,
    ),
]

storyboard = StoryboardSchema(
    title="The Backrooms — 后室",
    description="4-scene horror short: noclip, wandering, encounter, descent",
    target_duration=60,
    lang="en",
    scenes=scenes,
    wan_config=WanConfig(resolution=Resolution.HD),
)

ctx = PipelineContext(project_dir="core_engine/output", project_id="backrooms_story")
ctx.storyboard = storyboard

for s in scenes:
    print(f"  Scene {s.scene_id}: {s.duration}s | {s.visual_prompt[:70]}...")

# ── STAGE 3: VideoComposer (T2V, 4 scenes) ───────────────────────
print("\n[STAGE 3] VideoComposer — wan2.7-t2v (4 × 15s)")

from core_engine.src.stages.video_composer import VideoComposer
from core_engine.src.providers.video.dashscope_wan import DashScopeWanProvider

provider = DashScopeWanProvider(output_dir="core_engine/output/videos/backrooms_story")
composer = VideoComposer(video_provider=provider)
composer.execute(ctx)

clip_paths = ctx.metadata.get("clip_paths", [])
print(f"\n  Generated {len(clip_paths)} clips:")
for p in clip_paths:
    import pathlib
    pp = pathlib.Path(p)
    if pp.exists():
        print(f"    {pp.name}  ({pp.stat().st_size // (1024*1024)}MB)")

# ── STAGE 4: PostProcessor — concatenate + SRT ───────────────────
print("\n[STAGE 4] PostProcessor — concatenate clips + generate SRT")

from core_engine.src.stages.post_processor import PostProcessor
post = PostProcessor()
post.execute(ctx)

# ── Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  BACKROOMS STORY — COMPLETE")
print("=" * 65)

import pathlib
if ctx.final_path:
    fp = pathlib.Path(ctx.final_path)
    if fp.exists() and fp.suffix == ".mp4":
        size_mb = fp.stat().st_size / (1024 * 1024)
        print(f"  📹 Final video : {fp}")
        print(f"  💾 Size        : {size_mb:.1f} MB")
        print(f"  ⏱️  Duration    : ~60s (4 × 15s)")
    else:
        print(f"  Final: {ctx.final_path}")

srt = ctx.metadata.get("srt_path")
if srt:
    print(f"  📝 Subtitles   : {srt}")

print(f"\n  Clips: {len(clip_paths)}/4 generated")
