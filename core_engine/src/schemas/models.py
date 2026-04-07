"""Pydantic data models for the Aiedio video generation pipeline."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


# --------------- Enums ---------------

class AspectRatio(str, Enum):
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    SQUARE = "1:1"
    CLASSIC = "4:3"
    CLASSIC_PORTRAIT = "3:4"


class Resolution(str, Enum):
    SD = "480p"
    HD = "720p"
    FHD = "1080p"


class Duration(str, Enum):
    SHORT = "5"
    MEDIUM = "10"
    LONG = "15"


class VideoStyle(str, Enum):
    CINEMATIC = "cinematic"
    ANIME = "anime"
    MINIMALIST = "minimalist"
    DOCUMENTARY = "documentary"
    TECH = "tech"


class TransitionType(str, Enum):
    FADE = "fade"
    CUT = "cut"
    DISSOLVE = "dissolve"
    SLIDE = "slide"


class CameraMotion(str, Enum):
    STATIC = "static"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"


class AudioMode(str, Enum):
    """How audio is handled for each scene.

    Wan 2.6 generates native audio with lip-sync by default.
    Use TTS_OVERLAY only when you need precise narration text control.
    """
    NATIVE = "native"                 # Let Wan 2.6 generate native audio (default, recommended)
    TTS_OVERLAY = "tts_overlay"       # External TTS narration passed as audio_url
    SILENT = "silent"                 # No audio for this scene
    MUSIC_ONLY = "music_only"         # Background music only


# --------------- Scene & Storyboard ---------------

class SceneSchema(BaseModel):
    """A single scene within the storyboard."""
    scene_id: int = Field(..., ge=1)
    duration: int = Field(default=5, ge=5, le=15, description="Scene duration in seconds (5/10/15)")
    visual_prompt: str = Field(..., max_length=5000, description="Visual description for video generation (wan2.7-t2v supports up to 5000 chars)")
    narration: str = Field(default="", description="Narration text for TTS")
    text_overlay: str = Field(default="", description="On-screen text overlay")
    style: VideoStyle = Field(default=VideoStyle.CINEMATIC)
    transition: TransitionType = Field(default=TransitionType.FADE)
    camera_motion: CameraMotion = Field(default=CameraMotion.STATIC)
    audio_mode: AudioMode = Field(default=AudioMode.NATIVE)

    @property
    def wan_duration(self) -> Duration:
        """Map scene duration to Wan 2.6 duration enum."""
        if self.duration <= 5:
            return Duration.SHORT
        elif self.duration <= 10:
            return Duration.MEDIUM
        return Duration.LONG


class GlobalStyle(BaseModel):
    """Global visual style configuration."""
    aspect_ratio: AspectRatio = Field(default=AspectRatio.LANDSCAPE)
    resolution: Resolution = Field(default=Resolution.FHD)
    color_palette: list[str] = Field(default_factory=lambda: ["#1a1a2e", "#16213e", "#0f3460"])
    font: str = Field(default="Noto Sans SC")
    mood: str = Field(default="futuristic")
    negative_prompt: str = Field(
        default="low resolution, error, worst quality, low quality, defects, blurry text",
        max_length=500,
    )


class WanConfig(BaseModel):
    """Wan 2.6 specific generation configuration."""
    resolution: Resolution = Field(default=Resolution.FHD)
    aspect_ratio: AspectRatio = Field(default=AspectRatio.LANDSCAPE)
    enable_prompt_expansion: bool = Field(default=True)
    multi_shots: bool = Field(default=True)
    enable_safety_checker: bool = Field(default=True)
    seed: Optional[int] = Field(default=None)


class StoryboardSchema(BaseModel):
    """Complete storyboard for video generation."""
    title: str
    description: str = ""
    target_duration: int = Field(default=45, description="Target total duration in seconds")
    lang: str = Field(default="en", description="Output language (en/zh)")
    scenes: list[SceneSchema] = Field(default_factory=list)
    global_style: GlobalStyle = Field(default_factory=GlobalStyle)
    wan_config: WanConfig = Field(default_factory=WanConfig)

    @property
    def total_duration(self) -> int:
        return sum(s.duration for s in self.scenes)


# --------------- Asset Manifest ---------------

class SceneAssets(BaseModel):
    """Generated assets for a single scene."""
    scene_id: int
    image_path: Optional[Path] = None
    image_url: Optional[str] = None
    audio_path: Optional[Path] = None
    video_path: Optional[Path] = None
    video_url: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class AssetManifest(BaseModel):
    """Manifest of all generated assets."""
    project_id: str
    scenes: list[SceneAssets] = Field(default_factory=list)
    bgm_path: Optional[Path] = None
    base_dir: Optional[Path] = None

    class Config:
        arbitrary_types_allowed = True

    def get_scene(self, scene_id: int) -> Optional[SceneAssets]:
        for s in self.scenes:
            if s.scene_id == scene_id:
                return s
        return None


# --------------- Pipeline Result ---------------

class PipelineResult(BaseModel):
    """Final result of the pipeline run."""
    project_id: str
    success: bool = False
    storyboard: Optional[StoryboardSchema] = None
    assets: Optional[AssetManifest] = None
    video_path: Optional[Path] = None
    final_path: Optional[Path] = None
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
