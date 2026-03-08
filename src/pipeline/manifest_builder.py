"""Run manifest and QA summary builder."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.models.qa_schema import QaRunSummary
from src.pipeline.run_context import RunContext
from src.utils.file_utils import ensure_dir
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def build_run_summary(ctx: RunContext) -> QaRunSummary:
    """Populate a QaRunSummary from the completed RunContext."""
    return QaRunSummary(
        run_id=ctx.run_id,
        run_timestamp=ctx.run_timestamp,
        rooms_canonical_rows=len(ctx.rooms_canonical),
        spa_canonical_rows=len(ctx.spa_canonical),
        dining_canonical_rows=len(ctx.dining_canonical),
        rooms_primary_guests=sum(
            1 for r in ctx.rooms_canonical if getattr(r, "is_primary_reservation_guest", False)
        ),
        rooms_accompanying_guests=sum(
            1 for r in ctx.rooms_canonical if not getattr(r, "is_primary_reservation_guest", True)
        ),
        name_issues=len(ctx.qa_name_issues),
        phone_issues=len(ctx.qa_phone_issues),
        lookup_issues=len(ctx.qa_lookup_issues),
        exact_matches=sum(
            1 for r in ctx.bridge_guest_activity if not getattr(r, "match_flag_fuzzy", True)
        ),
        fuzzy_matches=sum(
            1 for r in ctx.bridge_guest_activity if getattr(r, "match_flag_fuzzy", False)
        ),
        possible_matches_flagged=len(ctx.qa_possible_matches),
        unmatched_spa=len(ctx.qa_unmatched_spa),
        unmatched_dining=len(ctx.qa_unmatched_dining),
        dim_guest_rows=len(ctx.dim_guests),
        dim_phone_rows=len(ctx.dim_phones),
        fact_room_stay_rows=len(ctx.fact_room_stays),
        bridge_guest_activity_rows=len(ctx.bridge_guest_activity),
        parse_errors=list(ctx.errors),
    )


def write_run_manifest(ctx: RunContext, summary: QaRunSummary) -> Path:
    """Write the run manifest JSON to the QA output directory."""
    out_dir = ensure_dir(ctx.qa_dir)
    manifest_path = out_dir / f"{ctx.run_id}_manifest.json"
    data = {
        "run_id": summary.run_id,
        "run_timestamp": summary.run_timestamp,
        "stage_times_seconds": ctx.stage_times,
        "counts": {
            "rooms_canonical_rows": summary.rooms_canonical_rows,
            "spa_canonical_rows": summary.spa_canonical_rows,
            "dining_canonical_rows": summary.dining_canonical_rows,
            "rooms_primary_guests": summary.rooms_primary_guests,
            "rooms_accompanying_guests": summary.rooms_accompanying_guests,
            "dim_guest_rows": summary.dim_guest_rows,
            "dim_phone_rows": summary.dim_phone_rows,
            "fact_room_stay_rows": summary.fact_room_stay_rows,
            "bridge_guest_activity_rows": summary.bridge_guest_activity_rows,
            "exact_matches": summary.exact_matches,
            "fuzzy_matches": summary.fuzzy_matches,
            "possible_matches_flagged": summary.possible_matches_flagged,
            "unmatched_spa": summary.unmatched_spa,
            "unmatched_dining": summary.unmatched_dining,
        },
        "qa_issues": {
            "name_issues": summary.name_issues,
            "phone_issues": summary.phone_issues,
            "lookup_issues": summary.lookup_issues,
        },
        "errors": summary.parse_errors,
    }
    manifest_path.write_text(json.dumps(data, indent=2, default=str))
    logger.info("Run manifest written to: %s", manifest_path)
    return manifest_path
