"""Pipeline orchestration for the Guest Hub project."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable

from src.pipeline.run_context import RunContext

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineStage:
    """Describes one named stage in the ordered pipeline."""
    name: str
    handler: Callable[[RunContext], None]


@dataclass(slots=True)
class PipelineOrchestrator:
    """Coordinates high-level pipeline execution in registered stage order."""
    stages: list[PipelineStage] = field(default_factory=list)

    def register_stage(self, stage: PipelineStage) -> None:
        """Append a stage to the execution list."""
        self.stages.append(stage)

    def run(self, ctx: RunContext) -> None:
        """Run all registered stages sequentially.

        Each stage receives the shared RunContext.  Exceptions in individual
        stages are caught, logged, and recorded in ctx.errors rather than
        aborting the whole run — subsequent stages proceed with whatever
        partial state is available.
        """
        logger.info("Pipeline run started: %s", ctx.run_id)
        run_start = time.monotonic()

        for stage in self.stages:
            logger.info("→ Stage: %s", stage.name)
            stage_start = time.monotonic()
            try:
                stage.handler(ctx)
                elapsed = time.monotonic() - stage_start
                logger.info("✓ Stage %s completed (%.2fs)", stage.name, elapsed)
            except Exception as exc:
                elapsed = time.monotonic() - stage_start
                msg = f"stage_error:{stage.name}:{type(exc).__name__}:{exc}"
                logger.error("✗ Stage %s failed after %.2fs — %s", stage.name, elapsed, exc)
                ctx.errors.append(msg)

        total = time.monotonic() - run_start
        logger.info(
            "Pipeline run complete: %s (%.2fs, %d stages, %d errors)",
            ctx.run_id, total, len(self.stages), len(ctx.errors),
        )


def build_default_pipeline(ctx: RunContext) -> PipelineOrchestrator:
    """Build and return the default 18-stage pipeline orchestrator."""
    from src.pipeline.stages import (
        stage_load_raw_sources,
        stage_load_reference_tables,
        stage_parse_rooms_xml,
        stage_parse_spa_pdf,
        stage_parse_dining_csv,
        stage_standardize_and_expand_rooms,
        stage_standardize_spa,
        stage_standardize_dining,
        stage_run_qa_validations,
        stage_build_guest_phone_dimensions,
        stage_run_matching,
        stage_build_fact_room_stay,
    )
    from src.outputs.export_csv import export_all_csv
    from src.pipeline.manifest_builder import build_run_summary, write_run_manifest

    def _export(ctx: RunContext) -> None:
        export_all_csv(ctx)

    def _manifest(ctx: RunContext) -> None:
        summary = build_run_summary(ctx)
        write_run_manifest(ctx, summary)

    orchestrator = PipelineOrchestrator()
    for name, handler in [
        ("load_raw_sources",            stage_load_raw_sources),
        ("load_reference_tables",       stage_load_reference_tables),
        ("parse_rooms_xml",             stage_parse_rooms_xml),
        ("parse_spa_pdf",               stage_parse_spa_pdf),
        ("parse_dining_csv",            stage_parse_dining_csv),
        ("standardize_shared_fields",   stage_standardize_and_expand_rooms),  # covers 6+7+8
        ("standardize_spa",             stage_standardize_spa),
        ("standardize_dining",          stage_standardize_dining),
        ("write_canonical_outputs",     lambda c: None),  # handled by export step
        ("run_qa_validations",          stage_run_qa_validations),
        ("build_guest_phone_dimensions",stage_build_guest_phone_dimensions),
        ("run_exact_matching",          stage_run_matching),  # covers 12+13+14+15
        ("run_fuzzy_matching",          lambda c: None),      # included in run_matching
        ("apply_support_signals",       lambda c: None),      # included in run_matching
        ("build_hub_tables",            lambda c: None),      # included above
        ("build_fact_room_stay",        stage_build_fact_room_stay),
        ("export_deliverables",         _export),
        ("write_run_manifest",          _manifest),
    ]:
        orchestrator.register_stage(PipelineStage(name=name, handler=handler))

    return orchestrator


def build_default_stages():
    """Return default stage names (legacy compatibility helper)."""
    return (
        "load_raw_sources",
        "load_reference_tables",
        "parse_rooms_xml",
        "parse_spa_pdf",
        "parse_dining_csv",
        "standardize_shared_fields",
        "expand_room_guests",
        "enrich_room_lookups",
        "write_canonical_outputs",
        "run_qa_validations",
        "build_guest_phone_dimensions",
        "run_exact_matching",
        "run_fuzzy_matching",
        "apply_support_signals",
        "build_hub_tables",
        "build_fact_room_stay",
        "export_deliverables",
        "write_run_manifest",
    )
