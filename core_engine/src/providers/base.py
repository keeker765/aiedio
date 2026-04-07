"""Abstract base classes for all providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal, Optional


class VideoProvider(ABC):
    """Abstract interface for video generation backends (Wan 2.6, etc.)."""

    @abstractmethod
    def text_to_video(
        self,
        prompt: str,
        duration: Literal["5", "10", "15"] = "5",
        resolution: Literal["720p", "1080p"] = "1080p",
        aspect_ratio: str = "16:9",
        audio_url: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Path:
        ...

    @abstractmethod
    def image_to_video(
        self,
        prompt: str,
        image_url: str,
        duration: Literal["5", "10", "15"] = "5",
        resolution: Literal["480p", "720p", "1080p"] = "1080p",
        audio_url: Optional[str] = None,
    ) -> Path:
        ...


class ImageProvider(ABC):
    """Abstract interface for image generation backends."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        style: str = "cinematic",
        size: tuple[int, int] = (1920, 1080),
    ) -> Path:
        ...


class TTSProvider(ABC):
    """Abstract interface for text-to-speech backends."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str = "default",
        lang: str = "zh",
    ) -> Path:
        ...


class MusicProvider(ABC):
    """Abstract interface for music generation / selection."""

    @abstractmethod
    def get_track(
        self,
        mood: str = "neutral",
        duration: float = 30.0,
    ) -> Path:
        ...
