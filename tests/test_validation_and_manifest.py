from __future__ import annotations

from src.models.canonical_schema import RoomsCanonicalRow
from src.pipeline.manifest_builder import build_run_summary
from src.pipeline.run_context import RunContext
from src.qa.validation import validate_canonical_outputs


def _room_row(source_row_id: str, phone_raw: str) -> RoomsCanonicalRow:
    row = RoomsCanonicalRow(
        source_system="rooms",
        source_row_id=source_row_id,
        confirmation_number="CONF-1",
        phone_raw=phone_raw,
        phone_clean=phone_raw,
        match_phone_key=phone_raw,
    )
    return row


def test_validate_canonical_outputs_respects_shared_phone_threshold() -> None:
    rows = [_room_row("r1", "5551234567"), _room_row("r2", "5551234567")]

    strict = validate_canonical_outputs(rows, [], [], shared_phone_threshold=1)
    relaxed = validate_canonical_outputs(rows, [], [], shared_phone_threshold=3)

    strict_shared = [i for i in strict.phone_issues if i.issue_code == "shared_phone"]
    relaxed_shared = [i for i in relaxed.phone_issues if i.issue_code == "shared_phone"]

    assert len(strict_shared) == 2
    assert len(relaxed_shared) == 0


def test_build_run_summary_populates_file_and_raw_counts() -> None:
    ctx = RunContext()
    ctx._room_files = ["a.xml", "b.xml"]
    ctx._spa_files = ["a.pdf"]
    ctx._dining_files = ["a.csv", "b.csv", "c.csv"]
    ctx._rooms_raw = [1, 2, 3]
    ctx._spa_raw = [1]
    ctx._dining_raw = [1, 2]

    summary = build_run_summary(ctx)

    assert summary.rooms_files_loaded == 2
    assert summary.spa_files_loaded == 1
    assert summary.dining_files_loaded == 3
    assert summary.rooms_raw_records == 3
    assert summary.spa_raw_records == 1
    assert summary.dining_raw_records == 2


def test_run_context_uses_matching_date_window_tolerance() -> None:
    ctx = RunContext.from_config(
        {
            "matching": {"date_window": {"tolerance_days": 2}},
            "date_window_tolerance_days": 1,
        }
    )
    assert ctx.date_tolerance_days == 2


def test_orchestrator_respects_configured_stage_order() -> None:
    from src.pipeline.orchestrator import build_default_pipeline

    ctx = RunContext(pipeline_stages=["load_raw_sources", "write_run_manifest"])
    pipeline = build_default_pipeline(ctx)

    assert [s.name for s in pipeline.stages] == ["load_raw_sources", "write_run_manifest"]


def test_orchestrator_raises_on_unknown_stage_name() -> None:
    from src.pipeline.orchestrator import build_default_pipeline

    ctx = RunContext(pipeline_stages=["load_raw_sources", "not_a_real_stage"])
    try:
        build_default_pipeline(ctx)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Unknown configured pipeline stage" in str(exc)
