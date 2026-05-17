"""Stage 1: Script Generator — trend topic → structured storyboard.

Refactored from the original story_prompt.py into a pipeline stage.
"""
from __future__ import annotations

import json
import logging
import os

from core_engine.src.pipeline.base import BaseStage, PipelineContext

log = logging.getLogger("aiedio")
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

# Save every prompt for debugging
_PROMPT_LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "prompts")
os.makedirs(_PROMPT_LOG, exist_ok=True)
import time as _time

def _save_prompt(topic: str, prompt: str, response: str = ""):
    slug = "".join(c for c in topic[:30] if c.isalnum() or c in " _-").strip().replace(" ", "_") or "untitled"
    fname = os.path.join(_PROMPT_LOG, f"prompt_{slug}_{int(_time.time())}.txt")
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write("TOPIC: " + topic + "\n")
            f.write("=" * 60 + "\n\n")
            f.write("PROMPT:\n" + prompt + "\n\n")
            f.write("=" * 60 + "\n\n")
            f.write("RESPONSE:\n" + response)
    except Exception:
        pass


def _build_wan_prompt(trend: dict, lang: str = "en", knowledge: list | None = None, analyses: list | None = None, scene_count: int = 0) -> str:
    """Build a prompt that requests Wan 2.6 compatible storyboard JSON.

    Args:
        trend: Dict with platform/title/hot_value.
        lang: Output language.
        knowledge: Optional list of knowledge source dicts from crawler.
        analyses: Optional list of video analysis dicts [{title, url, content}].
    """
    lang_inst = "Write all content in Chinese." if lang == "zh" else "Write all content in English."

    # Inject knowledge context if available
    knowledge_section = ""
    if knowledge:
        items = []
        for src in knowledge:
            platform_src = src.get("platform", "unknown")
            title = src.get("title", "")
            summary = src.get("summary", "")
            items.append(f"  - [{platform_src}] {title}")
            if summary:
                items.append(f"    Summary: {summary[:200]}")
        if items:
            knowledge_section = "Background knowledge for this topic:\n" + "\n".join(items[:8])

    # Inject video analysis (4 cards worth) — this is the SAME content shown on the frontend
    analysis_section = ""
    if analyses:
        items = []
        for i, a in enumerate(analyses[:4], 1):
            title = a.get("title", "")
            conflict = a.get("conflict", "")
            content = a.get("content", "")
            drama = a.get("drama", "")
            items.append(f"\n  Source {i}: {title[:80]}")
            if conflict:
                items.append(f"  Conflict: {conflict[:200]}")
            if drama:
                items.append(f"  Why it works: {drama[:300]}")
            if content:
                items.append(f"  Details: {content[:500]}")
        if items:
            analysis_section = "\nSource videos (use these as inspiration for tone, humor, and pacing):" + "\n".join(items)

    # Scene-specific instruction
    if scene_count == 1:
        scene_inst = "ONE-SCENE story: Generate exactly 1 self-contained scene that tells a COMPLETE story with setup, reveal, and reaction all in one continuous moment."
    elif scene_count == 2:
        scene_inst = "Generate exactly 2 scenes: Scene 1 sets up, Scene 2 delivers the payoff."
    elif scene_count >= 3:
        scene_inst = f"Generate exactly {scene_count} scenes with a clear narrative arc."
    else:
        scene_inst = ""

    return f"""You are a viral short-video creator. Turn this trending topic into an engaging short video.

{scene_inst}

Trending topic:
- Platform: {trend.get('platform', 'unknown')}
- Title: {trend.get('title', 'Untitled')}
- Popularity: {trend.get('hot_value', 'N/A')}

{knowledge_section}
{analysis_section}

Decide what format best suits this content. Options include:
- A narrative story with scenes
- A fast-paced montage/compliation showing highlights
- A single continuous moment
- A before/after comparison
- Whatever fits the content best

CRITICAL — Scene continuity:
- Each scene must flow naturally into the next (same characters, same location, or clear cause → effect)
- Scene 2 continues from where Scene 1 ends, Scene 3 continues from Scene 2, and so on
- Do NOT jump to unrelated characters or locations unless intentional
- Every scene must feel like it belongs to the same video

CRITICAL — Use the analysis:
- The "Why it's engaging" sections describe what makes similar content work
- Your storyboard should capture the SAME type of humor/drama that made the source videos engaging
- If the analysis says humor comes from exaggerated reactions, your scenes should use that too

Don't force a full story arc where none fits. Keep scenes focused on one core idea.

Note: this content comes from the {trend.get('platform', 'trending')} {trend.get('category', '')} section — interpret the tone accordingly.
Make the viewer want to watch until the end.

Wan 2.6 can generate native audio with lip-sync, so embed dialogue directly into the visual_prompt where appropriate.

For each visual_prompt, describe what the viewer sees in clear detail.

The narration field stores text shown as subtitles (empty for purely visual content).

{lang_inst}

--- EXAMPLE of a good output (copy this level of detail) ---
Topic: "He Hallucinated LeBron in His Room"
{{
  "story_background": "A deadpan guy tries the viral ping-pong ball sensory deprivation hack expecting trippy visuals, but instead hallucinates LeBron James in his bedroom. Humor comes from treating absurdity with complete seriousness.",
  "scenes": [
    {{
      "scene_id": 1, "duration": 10,
      "visual_prompt": "Medium shot, messy bedroom at night. A guy in his 20s sits on his bed, holding two halved ping-pong balls. His expression is dead serious, like he's performing surgery. He carefully tapes a ball half over each eye, hands slightly shaky.",
      "narration": "Okay. Sensory deprivation. Fifteen minutes. Let's do this.",
      "fun_point": "Ridiculous DIY setup + deadly serious expression = immediate hook",
      "camera_motion": "static", "style": "cinematic", "transition": "cut"
    }},
    {{
      "scene_id": 2, "duration": 10,
      "visual_prompt": "Wide shot. He lies back, ping-pong balls taped on, headphones on. Dead silence. Slow zoom on his face. He counts silently with his lips. Complete stillness for 10 seconds building tension for the reveal.",
      "narration": "",
      "fun_point": "Extended silence builds anticipation: audience expects profundity, gets absurdity",
      "camera_motion": "slow_zoom", "style": "cinematic", "transition": "fade"
    }},
    {{
      "scene_id": 3, "duration": 12,
      "visual_prompt": "POV through ping-pong ball gaps. Dark shapes form into LeBron James standing in the corner, wearing a tracksuit, checking his phone, looking mildly annoyed. The guy's hands frantically tear off the tape.",
      "narration": "Bro. Is that... LeBron?",
      "fun_point": "Climax: expecting cosmic truth, getting a basketball star on his phone",
      "camera_motion": "static", "style": "cinematic", "transition": "cut"
    }},
    {{
      "scene_id": 4, "duration": 8,
      "visual_prompt": "The guy sits up, staring at the empty corner. His face transitions from confusion to slow acceptance to a small smirk. He shrugs and lies back down, putting headphones on again.",
      "narration": "You know what? Fair enough.",
      "fun_point": "Complete acceptance of absurdity as the final punchline",
      "camera_motion": "static", "style": "cinematic", "transition": "fade"
    }}
  ]
}}
--- END EXAMPLE ---

IMPORTANT: Match the EXAMPLE's level of specific detail. Include facial expressions, emotional shifts, and comedic timing. Do NOT just describe actions.

Return ONLY a JSON object (no markdown) with:
- story_background: Brief summary of the creative direction
- scenes: Array of scene/moment objects ({f"{scene_count} scene" if scene_count == 1 else f"{scene_count} scenes" if scene_count > 1 else "1-4 items"}, whatever fits the content)

For each scene, include a "fun_point" field explaining why this moment is interesting, funny, or engaging — what makes the viewer want to watch.

{{
  "story_background": "Creative direction summary...",
  "scenes": [
    {{
      "scene_id": 1,
      "duration": 15,
      "visual_prompt": "Description of what the viewer sees...",
      "narration": "Subtitle text (can be empty)",
      "fun_point": "The humor comes from the contrast between his calm voice and the chaotic fridge contents",
      "style": "cinematic",
      "camera_motion": "zoom_in",
      "transition": "fade"
    }},
    ...
  ]
}}"""


class ScriptGenerator(BaseStage):
    """Stage 1: Generate a structured storyboard from a topic/trend."""

    name = "script_generator"

    def __init__(self, topic: str | None = None, trend: dict | None = None, lang: str = "en", scene_count: int = 0):
        self.topic = topic
        self.trend = trend
        self.lang = lang
        self.scene_count = scene_count

    def execute(self, ctx: PipelineContext) -> None:
        trend = self.trend
        if not trend and self.topic:
            trend = {"platform": "user", "title": self.topic, "hot_value": "N/A"}
        if not trend:
            trend = self._fetch_trending()

        # Read knowledge and analyses from context metadata (passed from backend via run_pipeline)
        knowledge = ctx.metadata.get("knowledge") or None
        analyses = ctx.metadata.get("analyses") or None

        log.info("  Topic: %s (%d video analyses)", trend.get('title', 'Unknown'), len(analyses or []))
        prompt = _build_wan_prompt(trend, self.lang, knowledge=knowledge, analyses=analyses, scene_count=self.scene_count)
        raw = call_llm(prompt, lang=self.lang, json_mode=True)
        _save_prompt(trend.get('title', 'untitled'), prompt, raw)

        story_background, scenes = self._parse_response(raw)

        # Trim to requested scene count (LLM often ignores scene_count in prompt)
        if self.scene_count > 0 and len(scenes) > self.scene_count:
            # Keep the best scenes: prioritize first and last, then middle
            kept = [scenes[0]]  # first scene always
            if self.scene_count > 1:
                kept.append(scenes[-1])  # last scene
            mid = scenes[1:-1]
            while len(kept) < self.scene_count and mid:
                kept.insert(1, mid.pop(0))
            scenes = kept
            # Re-number scene IDs
            for i, s in enumerate(scenes):
                s.scene_id = i + 1

        ctx.storyboard = StoryboardSchema(
            title=trend.get("title", "Untitled"),
            story_background=story_background,
            description=f"Auto-generated from {trend.get('platform', 'unknown')} trending",
            target_duration=sum(s.duration for s in scenes),
            lang=self.lang,
            scenes=scenes,
        )
        log.info("  Generated %d scenes, total %ds", len(scenes), ctx.storyboard.total_duration)

    def _parse_response(self, raw: str) -> tuple[str, list[SceneSchema]]:
        """Parse LLM response into (story_background, scenes).

        Raises ValueError with the offending raw text when parsing fails — never
        silently falls back to placeholder scenes (that hides real bugs).
        """
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            start = text.find("[") if text.find("{") == -1 else text.find("{")
            end = text.rfind("]") + 1 if text.find("{") == -1 or text.find("{") > text.find("[") else text.rfind("}") + 1
            if start < 0 or end <= start:
                raise ValueError(
                    f"LLM response contains no JSON object/array. "
                    f"JSON error: {e.msg} at line {e.lineno} col {e.colno}. "
                    f"Raw (first 600 chars): {text[:600]!r}"
                ) from e
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError as e2:
                raise ValueError(
                    f"LLM response had JSON braces but inner content invalid. "
                    f"JSON error: {e2.msg} at line {e2.lineno} col {e2.colno}. "
                    f"Extracted (first 600 chars): {text[start:end][:600]!r}"
                ) from e2

        # Handle dict format: {"story_background": "...", "scenes": [...]}
        if isinstance(data, dict):
            story_bg = data.get("story_background", "")
            scenes_data = data.get("scenes", [])
        else:
            # Legacy array format
            story_bg = ""
            scenes_data = data

        return story_bg, self._parse_scenes(scenes_data)

    def _fetch_trending(self) -> dict:
        """Try to import crawler and fetch first trend."""
        try:
            from crawler.src.github_spider import fetch_github_hot
            trends = fetch_github_hot()
            if trends:
                return trends[0]
        except Exception as e:
            log.warning("  Could not fetch trends: %s", e)
        return {"platform": "demo", "title": "AI Video Generation Technology", "hot_value": "demo"}

    def _parse_scenes(self, items: list[dict]) -> list[SceneSchema]:
        """Convert parsed scene dicts into SceneSchema list."""
        if isinstance(items, dict):
            items = items.get("scenes", [items])

        scenes = []
        for item in items:
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

            dur = item.get("duration", 5)
            if not isinstance(dur, int) or dur < 3 or dur > 15:
                dur = 5

            scenes.append(SceneSchema(
                scene_id=item.get("scene_id", len(scenes) + 1),
                duration=dur,
                visual_prompt=item.get("visual_prompt", item.get("visual", "")),
                narration=item.get("narration", ""),
                text_overlay=item.get("text_overlay", ""),
                fun_point=item.get("fun_point", ""),
                style=style,
                camera_motion=camera,
                transition=transition,
                audio_mode=AudioMode.NATIVE,
            ))

        if not scenes:
            raise ValueError(
                f"LLM returned valid JSON but no scenes were parsed. "
                f"Items received (first 600 chars): {str(items)[:600]!r}"
            )
        return scenes


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
