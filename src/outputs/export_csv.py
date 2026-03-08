"""CSV export for canonical, hub, and QA tables."""
from __future__ import annotations

import csv
import dataclasses
import logging
from pathlib import Path
from typing import Any

from src.pipeline.run_context import RunContext
from src.utils.file_utils import ensure_dir

logger = logging.getLogger(__name__)


def _dataclass_to_dict(obj: Any) -> dict:
    """Convert a dataclass instance to a flat dict suitable for CSV writing."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        d = dataclasses.asdict(obj)
        # Flatten list fields to semicolon-joined strings
        for k, v in d.items():
            if isinstance(v, list):
                d[k] = "; ".join(str(x) for x in v)
        return d
    return dict(obj)


def write_csv(rows: list[Any], out_path: Path) -> None:
    """Write a list of dataclass instances to a CSV file.

    Skips silently when *rows* is empty.
    """
    if not rows:
        logger.debug("No rows to write for: %s", out_path.name)
        return
    ensure_dir(out_path.parent)
    dicts = [_dataclass_to_dict(r) for r in rows]
    fieldnames = list(dicts[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dicts)
    logger.info("Wrote %d rows to %s", len(dicts), out_path.name)


def export_all_csv(ctx: RunContext) -> None:
    """Export all canonical, hub, and QA tables to CSV files."""
    canonical_dir = ensure_dir(ctx.canonical_dir)
    hub_dir = ensure_dir(ctx.hub_dir)
    qa_dir = ensure_dir(ctx.qa_dir)

    # Canonical tables
    write_csv(ctx.rooms_canonical,  canonical_dir / "rooms_canonical.csv")
    write_csv(ctx.spa_canonical,    canonical_dir / "spa_canonical.csv")
    write_csv(ctx.dining_canonical, canonical_dir / "dining_canonical.csv")

    # Hub tables
    write_csv(list(ctx.dim_guests.values()),  hub_dir / "dim_guest.csv")
    write_csv(list(ctx.dim_phones.values()),  hub_dir / "dim_phone.csv")
    write_csv(ctx.fact_room_stays,            hub_dir / "fact_room_stay.csv")
    write_csv(ctx.bridge_guest_activity,      hub_dir / "bridge_guest_activity.csv")
    write_csv(ctx.bridge_guest_room_stay,     hub_dir / "bridge_guest_room_stay.csv")

    # QA tables
    write_csv(ctx.qa_name_issues,      qa_dir / "qa_name_issues.csv")
    write_csv(ctx.qa_phone_issues,     qa_dir / "qa_phone_issues.csv")
    write_csv(ctx.qa_lookup_issues,    qa_dir / "qa_lookup_issues.csv")
    write_csv(ctx.qa_duplicate_issues, qa_dir / "qa_duplicate_issues.csv")
    write_csv(ctx.qa_possible_matches, qa_dir / "qa_possible_matches.csv")
    write_csv(ctx.qa_unmatched_spa,    qa_dir / "qa_unmatched_spa.csv")
    write_csv(ctx.qa_unmatched_dining, qa_dir / "qa_unmatched_dining.csv")

    logger.info("CSV export complete to: %s / %s / %s", canonical_dir, hub_dir, qa_dir)
