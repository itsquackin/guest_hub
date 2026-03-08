"""Pipeline run context — carries all state for one pipeline execution."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _new_run_id() -> str:
    return f"run-{datetime.now(tz=timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"


@dataclass
class RunContext:
    """Holds configuration and mutable state for one pipeline run.

    Passed to stage handlers so they share a single source of truth.
    """
    # Identity
    run_id: str = field(default_factory=_new_run_id)
    run_timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    # Configured input paths
    raw_rooms_dir: Path = Path("data/raw/rooms")
    raw_spa_dir: Path = Path("data/raw/spa")
    raw_dining_dir: Path = Path("data/raw/dining")
    reference_dir: Path = Path("data/reference")

    # Configured output paths
    canonical_dir: Path = Path("data/processed/canonical")
    hub_dir: Path = Path("data/processed/hub")
    qa_dir: Path = Path("data/processed/qa")
    archive_dir: Path = Path("data/archive/runs")

    # Matching settings
    date_tolerance_days: int = 1
    fuzzy_score_cutoff: float = 0.88

    # Mutable canonical outputs (populated during pipeline run)
    rooms_canonical: list = field(default_factory=list)
    spa_canonical: list = field(default_factory=list)
    dining_canonical: list = field(default_factory=list)

    # Hub outputs
    dim_guests: dict = field(default_factory=dict)
    dim_phones: dict = field(default_factory=dict)
    fact_room_stays: list = field(default_factory=list)
    bridge_guest_activity: list = field(default_factory=list)
    bridge_guest_room_stay: list = field(default_factory=list)

    # Reference lookups
    room_type_map: dict[str, str] = field(default_factory=dict)
    special_request_map: dict[str, str] = field(default_factory=dict)

    # QA outputs
    qa_name_issues: list = field(default_factory=list)
    qa_phone_issues: list = field(default_factory=list)
    qa_lookup_issues: list = field(default_factory=list)
    qa_possible_matches: list = field(default_factory=list)
    qa_unmatched_spa: list = field(default_factory=list)
    qa_unmatched_dining: list = field(default_factory=list)

    # Run telemetry
    stage_times: dict[str, float] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @classmethod
    def from_config(cls, config: dict) -> "RunContext":
        """Construct a RunContext from a parsed settings.yaml dict."""
        paths = config.get("paths", {})
        matching = config.get("matching", {})
        return cls(
            raw_rooms_dir=Path(paths.get("raw_rooms", "data/raw/rooms")),
            raw_spa_dir=Path(paths.get("raw_spa", "data/raw/spa")),
            raw_dining_dir=Path(paths.get("raw_dining", "data/raw/dining")),
            reference_dir=Path(paths.get("reference", "data/reference")),
            canonical_dir=Path(paths.get("canonical", "data/processed/canonical")),
            hub_dir=Path(paths.get("hub", "data/processed/hub")),
            qa_dir=Path(paths.get("qa", "data/processed/qa")),
            archive_dir=Path(paths.get("archive_runs", "data/archive/runs")),
            date_tolerance_days=config.get("date_window_tolerance_days", 1),
            fuzzy_score_cutoff=matching.get("score_cutoff", 0.88),
        )
