"""Pipeline runner — orchestrates stage execution."""
from __future__ import annotations

import logging
import time
from typing import Optional

from core_engine.src.pipeline.base import BaseStage, PipelineContext
from core_engine.src.schemas.models import PipelineResult

log = logging.getLogger("aiedio")


class PipelineRunner:
    """Execute a sequence of stages, supporting checkpoint-based resumption."""

    def __init__(self, stages: list[BaseStage] | None = None):
        self.stages: list[BaseStage] = stages or []

    def add_stage(self, stage: BaseStage) -> "PipelineRunner":
        self.stages.append(stage)
        return self

    def run(self, ctx: PipelineContext, *, resume: bool = False) -> PipelineResult:
        """Run all stages sequentially.

        Args:
            ctx: shared context object.
            resume: if True, skip stages that already have a checkpoint.
        """
        total = len(self.stages)
        print(f"\n{'='*60}")
        print(f"  AIEDIO Pipeline — {total} stages")
        print(f"  Project: {ctx.project_id}")
        print(f"{'='*60}\n")

        for idx, stage in enumerate(self.stages, 1):
            if resume and ctx.load_checkpoint(stage.name) is not None:
                print(f"[{idx}/{total}] ⏭  Skipping '{stage.name}' (checkpoint found)")
                continue

            print(f"[{idx}/{total}] ▶  Running '{stage.name}' ...")
            t0 = time.time()
            try:
                stage.execute(ctx)
                elapsed = time.time() - t0
                ctx.save_checkpoint(stage.name, {"status": "done", "elapsed": elapsed})
                print(f"[{idx}/{total}] ✅ '{stage.name}' done ({elapsed:.1f}s)\n")
            except Exception as exc:
                elapsed = time.time() - t0
                ctx.save_checkpoint(stage.name, {"status": "error", "error": str(exc)})
                # Use log.exception so the full traceback lands in server.log,
                # not just stdout (where uvicorn's reload-watcher may swallow it).
                log.exception("Stage '%s' failed (%.1fs)", stage.name, elapsed)
                print(f"[{idx}/{total}] ❌ '{stage.name}' failed ({elapsed:.1f}s): {exc}\n")
                return PipelineResult(
                    project_id=ctx.project_id,
                    success=False,
                    storyboard=ctx.storyboard,
                    assets=ctx.assets,
                    error=f"Stage '{stage.name}' failed: {type(exc).__name__}: {exc}",
                )

        print(f"{'='*60}")
        print(f"  Pipeline complete!")
        print(f"{'='*60}\n")
        return ctx.to_result()
