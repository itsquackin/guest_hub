"""Concrete pipeline stage handler functions.

Each function receives the shared RunContext, performs one stage of the
18-step pipeline, and mutates ctx in place with its outputs.
"""
from __future__ import annotations

import logging
import time

from src.loaders.reference_loader import load_all_reference_maps
from src.loaders.room_loader import load_room_files
from src.loaders.spa_loader import load_spa_files
from src.loaders.dining_loader import load_dining_files
from src.matching.exact_match import ExactMatchCandidate, RoomStayContext, match_exact_name_date
from src.matching.fuzzy_match import are_fuzzy_scores_ambiguous
from src.matching.guest_resolver import resolve_room_guests, update_guest_activity_counts
from src.matching.keys import make_activity_source_key
from src.matching.phone_support import GuestPhoneContext, PhoneMatchCandidate, find_phone_support_candidates
from src.matching.repeated_pattern import ActivityRecord, find_repeated_patterns
from src.matching.scorer import add_phone_support, make_exact_result, make_fuzzy_result
from src.models.hub_schema import BridgeGuestActivity, BridgeGuestRoomStay, DimPhone, FactRoomStay
from src.parsers.dining_parser import parse_dining_csv_file
from src.parsers.room_parser import parse_room_xml_file
from src.parsers.spa_parser import parse_spa_pdf_file
from src.pipeline.run_context import RunContext
from src.qa.possible_matches import (
    build_possible_match_issue,
    collect_ambiguous_fuzzy,
    collect_outside_stay_window,
    collect_shared_phone_different_name,
)
from src.qa.unmatched import collect_unmatched_dining, collect_unmatched_spa
from src.qa.validation import validate_canonical_outputs
from src.transforms.rooms_enrich import RoomLookupBundle, enrich_room_lookups
from src.transforms.rooms_expand_guests import expand_rooms_canonical_row
from src.transforms.rooms_standardize import standardize_room_record
from src.transforms.spa_standardize import standardize_spa_file
from src.transforms.dining_standardize import standardize_dining_file
from src.transforms.shared_fields import make_load_timestamp
from src.utils.id_utils import make_stay_span_key, new_phone_id
from src.cleaners.phones import normalize_phone, build_match_phone_key, is_international_like, is_incomplete_like, is_valid_like

logger = logging.getLogger(__name__)


def _timed(ctx: RunContext, name: str):
    """Context manager that records elapsed seconds for a stage."""
    import contextlib

    @contextlib.contextmanager
    def _cm():
        start = time.monotonic()
        try:
            yield
        finally:
            ctx.stage_times[name] = round(time.monotonic() - start, 3)

    return _cm()


# ── Stage 1: load raw sources ─────────────────────────────────────────────────

def stage_load_raw_sources(ctx: RunContext) -> None:
    """Discover and validate raw source files (does not parse yet)."""
    with _timed(ctx, "load_raw_sources"):
        ctx._room_files = load_room_files(ctx.raw_rooms_dir)
        ctx._spa_files = load_spa_files(ctx.raw_spa_dir)
        ctx._dining_files = load_dining_files(ctx.raw_dining_dir)
        logger.info(
            "Source files queued — rooms:%d spa:%d dining:%d",
            len(ctx._room_files), len(ctx._spa_files), len(ctx._dining_files),
        )


# ── Stage 2: load reference tables ───────────────────────────────────────────

def stage_load_reference_tables(ctx: RunContext) -> None:
    with _timed(ctx, "load_reference_tables"):
        ctx.room_type_map, ctx.special_request_map = load_all_reference_maps(ctx.reference_dir)


# ── Stage 3: parse rooms XML ──────────────────────────────────────────────────

def stage_parse_rooms_xml(ctx: RunContext) -> None:
    with _timed(ctx, "parse_rooms_xml"):
        raw_records = []
        for path in getattr(ctx, "_room_files", []):
            try:
                raw_records.extend(parse_room_xml_file(path))
            except Exception as exc:
                msg = f"room_parse_error:{path.name}:{exc}"
                logger.error(msg)
                ctx.errors.append(msg)
        ctx._rooms_raw = raw_records
        logger.info("Parsed %d raw room records", len(raw_records))


# ── Stage 4: parse spa PDF ────────────────────────────────────────────────────

def stage_parse_spa_pdf(ctx: RunContext) -> None:
    with _timed(ctx, "parse_spa_pdf"):
        raw_records = []
        for path in getattr(ctx, "_spa_files", []):
            try:
                raw_records.extend(parse_spa_pdf_file(path))
            except Exception as exc:
                msg = f"spa_parse_error:{path.name}:{exc}"
                logger.error(msg)
                ctx.errors.append(msg)
        ctx._spa_raw = raw_records
        logger.info("Parsed %d raw spa records", len(raw_records))


# ── Stage 5: parse dining CSV ─────────────────────────────────────────────────

def stage_parse_dining_csv(ctx: RunContext) -> None:
    with _timed(ctx, "parse_dining_csv"):
        raw_records = []
        for path in getattr(ctx, "_dining_files", []):
            try:
                raw_records.extend(parse_dining_csv_file(path))
            except Exception as exc:
                msg = f"dining_parse_error:{path.name}:{exc}"
                logger.error(msg)
                ctx.errors.append(msg)
        ctx._dining_raw = raw_records
        logger.info("Parsed %d raw dining records", len(raw_records))


# ── Stages 6-8: standardize shared fields, expand rooms, enrich lookups ──────

def stage_standardize_shared_fields(ctx: RunContext) -> None:
    """Stage 6: standardize source rows into canonical-ready records.

    - rooms are standardized to reservation-level rows (guest expansion deferred)
    - spa and dining are standardized directly to canonical rows
    """
    with _timed(ctx, "standardize_shared_fields"):
        ts = make_load_timestamp()
        standardized_rooms: list = []
        for raw in getattr(ctx, "_rooms_raw", []):
            try:
                standardized_rooms.append(
                    standardize_room_record(
                        raw,
                        load_timestamp=ts,
                        date_tolerance_days=ctx.date_tolerance_days,
                    )
                )
            except Exception as exc:
                msg = f"rooms_standardize_error:{raw.source_row_id}:{exc}"
                logger.error(msg)
                ctx.errors.append(msg)

        ctx._rooms_standardized = standardized_rooms
        ctx.spa_canonical = standardize_spa_file(getattr(ctx, "_spa_raw", []), load_timestamp=ts)
        ctx.dining_canonical = standardize_dining_file(getattr(ctx, "_dining_raw", []), load_timestamp=ts)
        logger.info(
            "Standardized rows — rooms:%d spa:%d dining:%d",
            len(standardized_rooms), len(ctx.spa_canonical), len(ctx.dining_canonical),
        )


def stage_expand_room_guests(ctx: RunContext) -> None:
    """Stage 7: expand standardized room reservations to guest-grain rows."""
    with _timed(ctx, "expand_room_guests"):
        expanded: list = []
        for row in getattr(ctx, "_rooms_standardized", []):
            try:
                expanded.extend(expand_rooms_canonical_row(row))
            except Exception as exc:
                msg = f"rooms_expand_error:{row.source_row_id}:{exc}"
                logger.error(msg)
                ctx.errors.append(msg)
        ctx.rooms_canonical = expanded
        logger.info(
            "Expanded room guests: %d guest rows from %d reservation rows",
            len(expanded), len(getattr(ctx, "_rooms_standardized", [])),
        )


def stage_enrich_room_lookups(ctx: RunContext) -> None:
    """Stage 8: enrich room type/special-request lookups and emit lookup QA."""
    with _timed(ctx, "enrich_room_lookups"):
        from src.models.qa_schema import QaLookupIssue

        lookups = RoomLookupBundle(
            room_type_map=ctx.room_type_map,
            special_request_map=ctx.special_request_map,
        )
        for row in ctx.rooms_canonical:
            enrich_result = enrich_room_lookups(
                row.room_type_code,
                row.assigned_room_type_code,
                row.specials_list,
                lookups,
            )
            row.room_type_description = enrich_result.room_type_description
            row.assigned_room_type_description = enrich_result.assigned_room_type_description
            row.specials_descriptions = enrich_result.specials_descriptions

            for issue_str in enrich_result.qa_lookup_issues:
                issue_parts = issue_str.split(":")
                lookup_code = issue_parts[-1] if issue_parts else ""
                issue_code = issue_parts[0] if issue_parts else "lookup_issue"
                ctx.qa_lookup_issues.append(
                    QaLookupIssue(
                        source_system=row.source_system,
                        source_row_id=row.source_row_id,
                        confirmation_number=row.confirmation_number,
                        lookup_type=issue_code,
                        lookup_code=lookup_code,
                        issue_code=issue_code,
                    )
                )

        logger.info(
            "Room lookup enrichment complete: rows:%d lookup_issues:%d",
            len(ctx.rooms_canonical), len(ctx.qa_lookup_issues),
        )


# ── Stage 10: QA validation ───────────────────────────────────────────────────

def stage_run_qa_validations(ctx: RunContext) -> None:
    with _timed(ctx, "run_qa_validations"):
        report = validate_canonical_outputs(
            ctx.rooms_canonical,
            ctx.spa_canonical,
            ctx.dining_canonical,
            lookup_issues=ctx.qa_lookup_issues,
            shared_phone_threshold=ctx.shared_phone_threshold,
        )
        ctx.qa_name_issues.extend(report.name_issues)
        ctx.qa_phone_issues.extend(report.phone_issues)
        ctx.qa_duplicate_issues.extend(report.duplicate_issues)
        logger.info("QA validation complete: %d total issues", report.total_issues)


# ── Stage 11: build guest and phone dimensions ────────────────────────────────

def stage_build_guest_phone_dimensions(ctx: RunContext) -> None:
    with _timed(ctx, "build_guest_phone_dimensions"):
        ctx.dim_guests = resolve_room_guests(ctx.rooms_canonical)

        # Build phone dimension
        seen_phones: dict[str, DimPhone] = {}
        from collections import Counter
        phone_guest_counts: Counter = Counter()

        for row in ctx.rooms_canonical:
            if row.match_phone_key:
                phone_guest_counts[row.match_phone_key] += 1

        for key, count in phone_guest_counts.items():
            raw_example = None
            for row in ctx.rooms_canonical:
                if row.match_phone_key == key:
                    raw_example = row.phone_raw
                    break
            seen_phones[key] = DimPhone(
                phone_id=new_phone_id(),
                phone_clean=normalize_phone(raw_example),
                phone_raw_example=raw_example,
                linked_guest_count=count,
                is_shared_phone=count > 1,
                is_international_like=is_international_like(normalize_phone(raw_example), raw_example),
                is_incomplete_like=is_incomplete_like(normalize_phone(raw_example)),
                is_valid_like=is_valid_like(normalize_phone(raw_example)),
            )

        ctx.dim_phones = seen_phones
        logger.info(
            "Built %d guest identities, %d phone records",
            len(ctx.dim_guests), len(ctx.dim_phones),
        )


def _build_stays(ctx: RunContext) -> list[RoomStayContext]:
    """Build stay contexts at room-row grain for robust exact/fuzzy matching."""
    name_to_guest_id = {
        name_key: guest.guest_id
        for name_key, guest in ctx.dim_guests.items()
    }
    stays: list[RoomStayContext] = []
    for row in ctx.rooms_canonical:
        if not row.match_name_key or not row.arrival_date or not row.departure_date:
            continue
        guest_id = name_to_guest_id.get(row.match_name_key)
        if not guest_id:
            continue
        stays.append(
            RoomStayContext(
                guest_id=guest_id,
                match_name_key=row.match_name_key,
                arrival_date=row.arrival_date,
                departure_date=row.departure_date,
            )
        )
    return stays


def stage_run_exact_matching(ctx: RunContext) -> None:
    """Run ExactNameDate matching against room stay contexts."""
    with _timed(ctx, "run_exact_matching"):
        stays = _build_stays(ctx)
        results = list(getattr(ctx, "_match_results", []))
        matched_spa = set(getattr(ctx, "_matched_spa_row_ids", set()))
        matched_dining = set(getattr(ctx, "_matched_dining_row_ids", set()))

        for source_rows in (ctx.spa_canonical, ctx.dining_canonical):
            for row in source_rows:
                if not row.match_name_key or not row.activity_date:
                    continue
                candidate = ExactMatchCandidate(
                    guest_id="",
                    match_name_key=row.match_name_key,
                    activity_date=row.activity_date,
                )
                act_key = make_activity_source_key(row.source_system, row.source_row_id)
                exact = match_exact_name_date(candidate, stays, ctx.date_tolerance_days)
                if exact:
                    results.append(
                        make_exact_result(
                            exact.stay.guest_id,
                            row.source_system,
                            act_key,
                            row.activity_date,
                            row.activity_time,
                        )
                    )
                    if row.source_system == "spa":
                        matched_spa.add(row.source_row_id)
                    else:
                        matched_dining.add(row.source_row_id)
                    continue

                same_name_outside = [
                    s for s in stays if s.match_name_key == row.match_name_key
                ]
                if same_name_outside:
                    ctx.qa_possible_matches.append(
                        collect_outside_stay_window(
                            source_system=row.source_system,
                            source_activity_key=act_key,
                            guest_id=same_name_outside[0].guest_id,
                            score=1.0,
                            activity_date=row.activity_date,
                            left_name_key=row.match_name_key,
                            right_name_key=same_name_outside[0].match_name_key,
                        )
                    )

        ctx._match_results = results
        ctx._matched_spa_row_ids = matched_spa
        ctx._matched_dining_row_ids = matched_dining
        logger.info("Exact matching complete: %d links", len(results))


def stage_run_fuzzy_matching(ctx: RunContext) -> None:
    """Run FuzzyNameDate matching for still-unmatched activity rows."""
    with _timed(ctx, "run_fuzzy_matching"):
        stays = _build_stays(ctx)
        results = list(getattr(ctx, "_match_results", []))
        matched_spa = set(getattr(ctx, "_matched_spa_row_ids", set()))
        matched_dining = set(getattr(ctx, "_matched_dining_row_ids", set()))

        for source_rows in (ctx.spa_canonical, ctx.dining_canonical):
            for row in source_rows:
                if not row.match_name_key or not row.activity_date:
                    continue
                if row.source_system == "spa" and row.source_row_id in matched_spa:
                    continue
                if row.source_system == "dining" and row.source_row_id in matched_dining:
                    continue

                candidate = ExactMatchCandidate(
                    guest_id="",
                    match_name_key=row.match_name_key,
                    activity_date=row.activity_date,
                )
                act_key = make_activity_source_key(row.source_system, row.source_row_id)
                ambiguous = are_fuzzy_scores_ambiguous(
                    candidate,
                    stays,
                    score_cutoff=ctx.fuzzy_score_cutoff,
                    tolerance_days=ctx.date_tolerance_days,
                    ambiguity_margin=ctx.fuzzy_ambiguity_margin,
                )

                if len(ambiguous) == 1:
                    results.append(
                        make_fuzzy_result(
                            ambiguous[0].stay.guest_id,
                            row.source_system,
                            act_key,
                            row.activity_date,
                            ambiguous[0].score,
                            row.activity_time,
                        )
                    )
                    if row.source_system == "spa":
                        matched_spa.add(row.source_row_id)
                    else:
                        matched_dining.add(row.source_row_id)
                elif len(ambiguous) > 1:
                    ctx.qa_possible_matches.extend(
                        collect_ambiguous_fuzzy(
                            row.source_system,
                            act_key,
                            ambiguous,
                            row.activity_date,
                            row.match_name_key,
                        )
                    )

        ctx._match_results = results
        ctx._matched_spa_row_ids = matched_spa
        ctx._matched_dining_row_ids = matched_dining
        logger.info("Fuzzy matching complete: %d cumulative links", len(results))


def stage_apply_support_signals(ctx: RunContext) -> None:
    """Apply phone and repeated-pattern support signals; finalize match outputs."""
    with _timed(ctx, "apply_support_signals"):
        results = list(getattr(ctx, "_match_results", []))
        matched_spa = set(getattr(ctx, "_matched_spa_row_ids", set()))
        matched_dining = set(getattr(ctx, "_matched_dining_row_ids", set()))

        rooms_by_name = {
            row.match_name_key: row
            for row in ctx.rooms_canonical
            if row.match_name_key
        }
        guest_contexts = [
            GuestPhoneContext(
                guest_id=guest.guest_id,
                match_name_key=name_key,
                match_phone_key=rooms_by_name.get(name_key).match_phone_key if rooms_by_name.get(name_key) else None,
            )
            for name_key, guest in ctx.dim_guests.items()
        ]
        result_by_activity = {r.source_activity_key: r for r in results}

        for source_rows in (ctx.spa_canonical, ctx.dining_canonical):
            for row in source_rows:
                act_key = make_activity_source_key(row.source_system, row.source_row_id)
                candidate = PhoneMatchCandidate(
                    source_system=row.source_system,
                    source_activity_key=act_key,
                    match_name_key=row.match_name_key,
                    match_phone_key=getattr(row, "match_phone_key", None),
                    activity_date=row.activity_date,
                )
                phone_candidates = find_phone_support_candidates(candidate, guest_contexts)
                if act_key in result_by_activity and phone_candidates:
                    result_by_activity[act_key] = add_phone_support(result_by_activity[act_key])
                elif phone_candidates:
                    best_guest, reason = phone_candidates[0]
                    if reason == "DifferentLastNameSharedPhone":
                        ctx.qa_possible_matches.append(
                            collect_shared_phone_different_name(
                                source_system=row.source_system,
                                source_activity_key=act_key,
                                guest_id=best_guest.guest_id,
                                activity_date=row.activity_date,
                                left_name_key=row.match_name_key,
                                right_name_key=best_guest.match_name_key,
                                phone_key=row.match_phone_key,
                            )
                        )

        # Repeated cross-source unmatched activity pattern detection
        unmatched_spa_rows = [r for r in ctx.spa_canonical if r.source_row_id not in matched_spa]
        unmatched_dining_rows = [r for r in ctx.dining_canonical if r.source_row_id not in matched_dining]
        unmatched_records = [
            ActivityRecord(
                source_system=r.source_system,
                source_activity_key=make_activity_source_key(r.source_system, r.source_row_id),
                match_name_key=r.match_name_key,
                match_phone_key=getattr(r, "match_phone_key", None),
                activity_date=r.activity_date,
            )
            for r in [*unmatched_spa_rows, *unmatched_dining_rows]
            if r.match_name_key
        ]
        for pattern in find_repeated_patterns(unmatched_records, min_occurrences=2):
            ctx.qa_possible_matches.append(
                build_possible_match_issue(
                    source_system="multi_source",
                    source_activity_key=pattern.activity_keys[0],
                    candidate_guest_id="",
                    reason="repeated_cross_source_pattern",
                    score=None,
                    match_method="RepeatedCrossSourcePattern",
                    left_name_key=pattern.match_name_key,
                    right_name_key=pattern.match_name_key,
                )
            )

        results = list(result_by_activity.values())
        update_guest_activity_counts(ctx.dim_guests, results)
        ctx.bridge_guest_activity = [
            BridgeGuestActivity(
                guest_id=r.guest_id,
                source_system=r.source_system,
                source_activity_key=r.source_activity_key,
                activity_date=r.activity_date,
                activity_time=r.activity_time,
                match_method=r.match_method,
                match_score=r.match_score,
                match_flag_fuzzy=r.match_flag_fuzzy,
                matched_within_stay_window=r.matched_within_stay_window,
                matched_by_phone_support=r.matched_by_phone_support,
                outside_stay_window_flag=r.outside_stay_window_flag,
                repeated_pattern_flag=r.repeated_pattern_flag,
                qa_review_required=r.qa_review_required,
            )
            for r in results
        ]

        ctx.qa_unmatched_spa = collect_unmatched_spa(ctx.spa_canonical, matched_spa)
        ctx.qa_unmatched_dining = collect_unmatched_dining(ctx.dining_canonical, matched_dining)
        logger.info(
            "Support signals complete: %d links, unmatched spa:%d dining:%d",
            len(results),
            len(ctx.qa_unmatched_spa),
            len(ctx.qa_unmatched_dining),
        )


# ── Stage: build fact_room_stay ───────────────────────────────────────────────

def stage_build_fact_room_stay(ctx: RunContext) -> None:
    """Build FactRoomStay rows — one per unique confirmation_number."""
    with _timed(ctx, "build_fact_room_stay"):
        seen: set[str] = set()
        stays: list[FactRoomStay] = []
        for row in ctx.rooms_canonical:
            if row.confirmation_number in seen:
                continue
            seen.add(row.confirmation_number)
            stays.append(
                FactRoomStay(
                    confirmation_number=row.confirmation_number,
                    arrival_date=row.arrival_date,
                    departure_date=row.departure_date,
                    nights=row.nights,
                    rate_code=row.rate_code,
                    nightly_rate=row.nightly_rate,
                    room_type_code=row.room_type_code,
                    room_type_description=row.room_type_description,
                    assigned_room_type_code=row.assigned_room_type_code,
                    assigned_room_type_description=row.assigned_room_type_description,
                    company_raw=row.company_raw,
                    reservation_status_raw=row.reservation_status_raw,
                    specials_raw=row.specials_raw,
                    vip_status_raw=row.vip_status_raw,
                    last_stay_date=row.last_stay_date,
                    last_room_raw=row.last_room_raw,
                )
            )

        # Build bridge_guest_room_stay
        bridges: list[BridgeGuestRoomStay] = []
        name_to_guest: dict[str, str] = {
            g.canonical_name_key: g.guest_id
            for g in ctx.dim_guests.values()
            if g.canonical_name_key
        }
        for row in ctx.rooms_canonical:
            gid = name_to_guest.get(row.match_name_key or "")
            if gid:
                bridges.append(
                    BridgeGuestRoomStay(
                        guest_id=gid,
                        confirmation_number=row.confirmation_number,
                        reservation_guest_key=row.reservation_guest_key,
                        guest_role=row.guest_role,
                        is_primary_reservation_guest=row.is_primary_reservation_guest,
                        phone_is_inherited=row.phone_is_inherited,
                    )
                )

        ctx.fact_room_stays = stays
        ctx.bridge_guest_room_stay = bridges
        logger.info(
            "Built %d fact_room_stay rows and %d bridge_guest_room_stay rows",
            len(stays), len(bridges),
        )
