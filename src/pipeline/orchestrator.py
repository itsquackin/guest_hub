"""Pipeline orchestration for the Guest Hub project."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable

from src.pipeline.run_context import RunContext
from src.models.enums import IdentityStatus

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
        stage_standardize_shared_fields,
        stage_expand_room_guests,
        stage_enrich_room_lookups,
        stage_run_qa_validations,
        stage_build_guest_phone_dimensions,
        stage_run_exact_matching,
        stage_run_fuzzy_matching,
        stage_apply_support_signals,
        stage_build_fact_room_stay,
    )
    from src.outputs.export_csv import export_all_csv
    from src.pipeline.manifest_builder import build_run_summary, write_run_manifest

    def _write_canonical_outputs(ctx: RunContext) -> None:
        """Stage 9: write interim canonical CSVs for debugging and auditability."""
        from src.outputs.export_csv import write_csv
        from src.utils.file_utils import ensure_dir
        interim = ensure_dir(ctx.interim_dir)
        write_csv(ctx.rooms_canonical,  interim / "rooms_canonical_interim.csv")
        write_csv(ctx.spa_canonical,    interim / "spa_canonical_interim.csv")
        write_csv(ctx.dining_canonical, interim / "dining_canonical_interim.csv")
        logger.info(
            "Interim canonical outputs written: rooms:%d spa:%d dining:%d",
            len(ctx.rooms_canonical), len(ctx.spa_canonical), len(ctx.dining_canonical),
        )

    def _build_hub_tables(ctx: RunContext) -> None:
        """Stage 15: finalize identity_status on dim_guest after matching is complete."""
        confirmed = IdentityStatus.CONFIRMED
        probable = IdentityStatus.PROBABLE
        unresolved = IdentityStatus.UNRESOLVED
        for guest in ctx.dim_guests.values():
            # Upgrade to Confirmed when guest has activity in ≥2 source systems
            source_count = sum([
                guest.has_room_activity,
                guest.has_spa_activity,
                guest.has_dining_activity,
            ])
            if guest.has_room_activity:
                # Room is the authoritative source — always Confirmed
                guest.identity_status = confirmed
            elif source_count >= 2:
                # Multi-source spa/dining link without room stay
                guest.identity_status = probable
            else:
                guest.identity_status = unresolved
        logger.info(
            "Hub tables finalised: %d guests, %d phones, %d activity bridges",
            len(ctx.dim_guests), len(ctx.dim_phones), len(ctx.bridge_guest_activity),
        )

    def _export(ctx: RunContext) -> None:
        export_all_csv(ctx)

    def _manifest(ctx: RunContext) -> None:
        summary = build_run_summary(ctx)
        write_run_manifest(ctx, summary)

    stage_map: dict[str, Callable[[RunContext], None]] = {
        "load_raw_sources": stage_load_raw_sources,
        "load_reference_tables": stage_load_reference_tables,
        "parse_rooms_xml": stage_parse_rooms_xml,
        "parse_spa_pdf": stage_parse_spa_pdf,
        "parse_dining_csv": stage_parse_dining_csv,
        "standardize_shared_fields": stage_standardize_shared_fields,
        "expand_room_guests": stage_expand_room_guests,
        "enrich_room_lookups": stage_enrich_room_lookups,
        "write_canonical_outputs": _write_canonical_outputs,
        "run_qa_validations": stage_run_qa_validations,
        "build_guest_phone_dimensions": stage_build_guest_phone_dimensions,
        "run_exact_matching": stage_run_exact_matching,
        "run_fuzzy_matching": stage_run_fuzzy_matching,
        "apply_support_signals": stage_apply_support_signals,
        "build_hub_tables": _build_hub_tables,
        "build_fact_room_stay": stage_build_fact_room_stay,
        "export_deliverables": _export,
        "write_run_manifest": _manifest,
    }

    stage_order = ctx.pipeline_stages or list(build_default_stages())
    orchestrator = PipelineOrchestrator()
    for name in stage_order:
        handler = stage_map.get(name)
        if handler is None:
            raise ValueError(f"Unknown configured pipeline stage: {name}")
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
