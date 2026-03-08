from __future__ import annotations

from pathlib import Path
from shutil import copy2

from src.pipeline.orchestrator import build_default_pipeline
from src.pipeline.run_context import RunContext
from src.utils.constants import MATCH_EXACT_NAME_DATE, MATCH_FUZZY_NAME_DATE


def _copy_fixture(src_name: str, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    copy2(Path("tests/fixtures") / src_name, dst_dir / src_name)


def test_pipeline_end_to_end_preserves_core_business_rules(tmp_path: Path) -> None:
    raw_rooms = tmp_path / "data/raw/rooms"
    raw_spa = tmp_path / "data/raw/spa"
    raw_dining = tmp_path / "data/raw/dining"
    reference = tmp_path / "data/reference"

    _copy_fixture("sample_room.xml", raw_rooms)
    _copy_fixture("sample_spa.pdf", raw_spa)
    _copy_fixture("sample_dining.csv", raw_dining)
    _copy_fixture("room_types.tsv", reference)
    _copy_fixture("special_requests.tsv", reference)

    config = {
        "paths": {
            "raw_rooms": str(raw_rooms),
            "raw_spa": str(raw_spa),
            "raw_dining": str(raw_dining),
            "reference": str(reference),
            "canonical": str(tmp_path / "data/processed/canonical"),
            "hub": str(tmp_path / "data/processed/hub"),
            "qa": str(tmp_path / "data/processed/qa"),
            "archive_runs": str(tmp_path / "data/archive/runs"),
            "interim_rooms": str(tmp_path / "data/interim/rooms"),
        },
        "matching": {
            "date_window": {"tolerance_days": 1},
            "fuzzy": {"score_cutoff": 0.88},
        },
        "qa": {
            "phone_issues": {"shared_phone_guest_threshold": 3},
            "possible_matches": {"ambiguity_margin": 0.03},
        },
        "pipeline": {
            "stages": [
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
            ]
        },
    }

    ctx = RunContext.from_config(config)
    pipeline = build_default_pipeline(ctx)
    pipeline.run(ctx)

    assert not ctx.errors
    assert len(ctx.rooms_canonical) > 3  # accompanying guests expanded
    assert any(row.phone_is_inherited for row in ctx.rooms_canonical)

    confirmation_numbers = {row.confirmation_number for row in ctx.rooms_canonical}
    assert len(ctx.fact_room_stays) == len(confirmation_numbers)

    assert len(ctx.bridge_guest_room_stay) == len(ctx.rooms_canonical)

    for link in ctx.bridge_guest_activity:
        assert link.match_method in {MATCH_EXACT_NAME_DATE, MATCH_FUZZY_NAME_DATE}
        if link.match_method == MATCH_FUZZY_NAME_DATE:
            assert link.match_flag_fuzzy is True
        if link.match_method == MATCH_EXACT_NAME_DATE:
            assert link.match_flag_fuzzy is False

    assert all(not hasattr(row, "total_revenue") for row in ctx.dining_canonical)
