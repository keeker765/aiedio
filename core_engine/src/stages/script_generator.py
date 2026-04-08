"""Stage 1: Script Generator — trend topic → structured storyboard.

Refactored from the original story_prompt.py into a pipeline stage.
"""
from __future__ import annotations

import json
import os

from core_engine.src.pipeline.base import BaseStage, PipelineContext
from core_engine.src.schemas.models import (
    AudioMode,
    CameraMotion,
    SceneSchema,
    StoryboardSchema,
    TransitionType,
    VideoStyle,
)
from core_engine.src.utils.llm_client import call_llm

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _build_wan_prompt(trend: dict, lang: str = "en") -> str:
    """Build a prompt that requests Wan 2.6 compatible storyboard JSON."""
    lang_inst = "Write all content in Chinese." if lang == "zh" else "Write all content in English."
    return f"""You are a short-video creative director designing for the Wan 2.6 AI video model.
Wan 2.6 can generate native audio with lip-sync, so embed dialogue directly into the visual_prompt.

Trending topic:
- Platform: {trend.get('platform', 'unknown')}
- Title: {trend.get('title', 'Untitled')}
- Popularity: {trend.get('hot_value', 'N/A')}

Generate a 3-scene video storyboard. Each scene will be generated as a separate 15-second Wan 2.6 video clip.

For each scene's visual_prompt, use the Wan 2.6 multi-shot format WITH dialogue:
"Overall description. Shot 1 [0-5s] visual details. Character says: 'dialogue'. Shot 2 [5-10s] ... Shot 3 [10-15s] ..."

The narration field stores the script text for subtitle generation (not for TTS — Wan handles audio natively).

{lang_inst}

Return ONLY a JSON array (no markdown):
[
  {{
    "scene_id": 1,
    "duration": 15,
    "visual_prompt": "Overall scene description with dialogue embedded. Shot 1 [0-5s] ... character says: '...' Shot 2 [5-10s] ... Shot 3 [10-15s] ...",
    "narration": "Subtitle text for this scene",
    "style": "cinematic",
    "camera_motion": "zoom_in",
    "transition": "fade"
  }},
  ...
]"""


class ScriptGenerator(BaseStage):
    """Stage 1: Generate a structured storyboard from a topic/trend."""

    name = "script_generator"

    def __init__(self, topic: str | None = None, trend: dict | None = None, lang: str = "en"):
        self.topic = topic
        self.trend = trend
        self.lang = lang

    def execute(self, ctx: PipelineContext) -> None:
        trend = self.trend
        if not trend and self.topic:
            trend = {"platform": "user", "title": self.topic, "hot_value": "N/A"}
        if not trend:
            trend = self._fetch_trending()

        print(f"  Topic: {trend.get('title', 'Unknown')}")
        prompt = _build_wan_prompt(trend, self.lang)
        raw = call_llm(prompt, lang=self.lang, json_mode=True)

        scenes = self._parse_scenes(raw)

        ctx.storyboard = StoryboardSchema(
            title=trend.get("title", "Untitled"),
            description=f"Auto-generated from {trend.get('platform', 'unknown')} trending",
            target_duration=sum(s.duration for s in scenes),
            lang=self.lang,
            scenes=scenes,
        )
        print(f"  Generated {len(scenes)} scenes, total {ctx.storyboard.total_duration}s")

    def _fetch_trending(self) -> dict:
        """Try to import crawler and fetch first trend."""
        try:
            from crawler.src.github_spider import fetch_github_hot
            trends = fetch_github_hot()
            if trends:
                return trends[0]
        except Exception as e:
            print(f"  [WARN] Could not fetch trends: {e}")
        return {"platform": "demo", "title": "AI Video Generation Technology", "hot_value": "demo"}

    def _parse_scenes(self, raw: str) -> list[SceneSchema]:
        """Parse LLM output into SceneSchema list."""
        # Strip markdown fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # try to extract JSON array from response
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(text[start:end])
                except json.JSONDecodeError:
                    print("  [WARN] Could not parse LLM JSON, using fallback scene")
                    data = [{"scene_id": 1, "duration": 15, "visual_prompt": text[:800], "narration": "", "style": "cinematic"}]
            else:
                data = [{"scene_id": 1, "duration": 15, "visual_prompt": text[:800], "narration": "", "style": "cinematic"}]

        if isinstance(data, dict):
            data = data.get("scenes", [data])

        scenes = []
        for item in data:
            style_str = item.get("style", "cinematic").lower()
            try:
                style = VideoStyle(style_str)
            except ValueError:
                style = VideoStyle.CINEMATIC

            camera_str = item.get("camera_motion", "static").lower()
            try:
                camera = CameraMotion(camera_str)
            except ValueError:
                camera = CameraMotion.STATIC

            transition_str = item.get("transition", "fade").lower()
            try:
                transition = TransitionType(transition_str)
            except ValueError:
                transition = TransitionType.FADE

            dur = item.get("duration", 15)
            if dur not in (5, 10, 15):
                dur = 15

            scenes.append(SceneSchema(
                scene_id=item.get("scene_id", len(scenes) + 1),
                duration=dur,
                visual_prompt=item.get("visual_prompt", item.get("visual", "")),
                narration=item.get("narration", ""),
                text_overlay=item.get("text_overlay", ""),
                style=style,
                camera_motion=camera,
                transition=transition,
                audio_mode=AudioMode.NATIVE,
            ))

        return scenes or [SceneSchema(
            scene_id=1,
            duration=15,
            visual_prompt="A dynamic technology overview scene",
            narration="Welcome to today's trending topic.",
        )]


if __name__ == "__main__":
    """Standalone storyboard test: python -m core_engine.src.stages.script_generator [--topic X]"""
    import argparse, json, pathlib
    from core_engine.src.pipeline.base import PipelineContext

    parser = argparse.ArgumentParser(description="Generate storyboard only")
    parser.add_argument("--topic", type=str, default=None)
    parser.add_argument("--lang", default="zh", choices=["en", "zh"])
    args = parser.parse_args()

    ctx = PipelineContext(project_id="storyboard_test", project_dir="core_engine/output")
    stage = ScriptGenerator(topic=args.topic, lang=args.lang)
    stage.execute(ctx)

    sb = ctx.storyboard
    print(f"\n📋 Storyboard: {sb.title} ({sb.total_duration}s, {len(sb.scenes)} scenes)")
    for s in sb.scenes:
        print(f"\n  Scene {s.scene_id} [{s.duration}s] {s.style.value}")
        print(f"  Prompt: {s.visual_prompt[:120]}...")
        print(f"  Narration: {s.narration[:80]}")

    out = pathlib.Path("core_engine/output/storyboards")
    out.mkdir(parents=True, exist_ok=True)
    import time
    fname = out / f"storyboard_{int(time.time())}.json"
    fname.write_text(sb.model_dump_json(indent=2), encoding="utf-8")
    print(f"\n💾 Saved: {fname}")
