"""Pipeline base classes and abstractions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core_engine.src.schemas.models import PipelineResult


class PipelineContext:
    """Shared state passed between pipeline stages."""

    def __init__(self, project_id: str, project_dir: str, **kwargs: Any):
        self.project_id = project_id
        self.project_dir = project_dir
        self.storyboard = None          # StoryboardSchema
        self.assets = None              # AssetManifest
        self.video_path = None          # Path to raw composed video
        self.final_path = None          # Path to final post-processed video
        self.metadata: dict = kwargs    # extra runtime metadata
        self._checkpoints: dict = {}

    def save_checkpoint(self, stage_name: str, data: Any) -> None:
        self._checkpoints[stage_name] = data

    def load_checkpoint(self, stage_name: str) -> Any | None:
        return self._checkpoints.get(stage_name)

    def to_result(self) -> PipelineResult:
        return PipelineResult(
            project_id=self.project_id,
            success=self.final_path is not None or self.video_path is not None,
            storyboard=self.storyboard,
            assets=self.assets,
            video_path=self.video_path,
            final_path=self.final_path,
        )


class BaseStage(ABC):
    """Abstract base class for all pipeline stages."""

    name: str = "base"

    @abstractmethod
    def execute(self, ctx: PipelineContext) -> None:
        """Run this stage, mutating *ctx* in-place."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name}'>"
