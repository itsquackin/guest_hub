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
from src.matching.fuzzy_match import are_fuzzy_scores_ambiguous, match_fuzzy_name_date
from src.matching.guest_resolver import resolve_room_guests, update_guest_activity_counts
from src.matching.keys import make_activity_source_key
from src.matching.scorer import make_exact_result, make_fuzzy_result
from src.models.hub_schema import BridgeGuestActivity, BridgeGuestRoomStay, DimPhone, FactRoomStay
from src.parsers.dining_parser import parse_dining_csv_file
from src.parsers.room_parser import parse_room_xml_file
from src.parsers.spa_parser import parse_spa_pdf_file
from src.pipeline.run_context import RunContext
from src.qa.possible_matches import collect_ambiguous_fuzzy
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


# ── Stage 6+7+8: standardize, expand, enrich ─────────────────────────────────

def stage_standardize_and_expand_rooms(ctx: RunContext) -> None:
    """Stages 6, 7, 8 combined: standardize → expand guests → enrich lookups."""
    with _timed(ctx, "standardize_expand_enrich_rooms"):
        ts = make_load_timestamp()
        lookups = RoomLookupBundle(
            room_type_map=ctx.room_type_map,
            special_request_map=ctx.special_request_map,
        )
        expanded: list = []
        for raw in getattr(ctx, "_rooms_raw", []):
            try:
                # Standardize (reservation-level)
                std_row = standardize_room_record(
                    raw,
                    load_timestamp=ts,
                    date_tolerance_days=ctx.date_tolerance_days,
                )
                # Enrich room type / specials lookups
                enrich_result = enrich_room_lookups(
                    std_row.room_type_code,
                    std_row.assigned_room_type_code,
                    std_row.specials_list,
                    lookups,
                )
                std_row.room_type_description = enrich_result.room_type_description
                std_row.assigned_room_type_description = enrich_result.assigned_room_type_description
                std_row.specials_descriptions = enrich_result.specials_descriptions
                # Collect lookup QA issues
                for issue_str in enrich_result.qa_lookup_issues:
                    from src.models.qa_schema import QaLookupIssue
                    ctx.qa_lookup_issues.append(
                        QaLookupIssue(
                            source_system=std_row.source_system,
                            source_row_id=std_row.source_row_id,
                            confirmation_number=std_row.confirmation_number,
                            lookup_type=issue_str.split(":")[0],
                            lookup_code=issue_str.split(":")[-1],
                            issue_code=issue_str.split(":")[0],
                        )
                    )
                # Expand guests (reservation → guest-grain)
                guest_rows = expand_rooms_canonical_row(std_row)
                expanded.extend(guest_rows)
            except Exception as exc:
                msg = f"rooms_expand_error:{raw.source_row_id}:{exc}"
                logger.error(msg)
                ctx.errors.append(msg)

        ctx.rooms_canonical = expanded
        logger.info(
            "Rooms canonical: %d guest rows from %d raw records",
            len(expanded), len(getattr(ctx, "_rooms_raw", [])),
        )


def stage_standardize_spa(ctx: RunContext) -> None:
    with _timed(ctx, "standardize_spa"):
        ts = make_load_timestamp()
        ctx.spa_canonical = standardize_spa_file(
            getattr(ctx, "_spa_raw", []), load_timestamp=ts
        )
        logger.info("Spa canonical: %d rows", len(ctx.spa_canonical))


def stage_standardize_dining(ctx: RunContext) -> None:
    with _timed(ctx, "standardize_dining"):
        ts = make_load_timestamp()
        ctx.dining_canonical = standardize_dining_file(
            getattr(ctx, "_dining_raw", []), load_timestamp=ts
        )
        logger.info("Dining canonical: %d rows", len(ctx.dining_canonical))


# ── Stage 10: QA validation ───────────────────────────────────────────────────

def stage_run_qa_validations(ctx: RunContext) -> None:
    with _timed(ctx, "run_qa_validations"):
        report = validate_canonical_outputs(
            ctx.rooms_canonical,
            ctx.spa_canonical,
            ctx.dining_canonical,
            lookup_issues=ctx.qa_lookup_issues,
        )
        ctx.qa_name_issues.extend(report.name_issues)
        ctx.qa_phone_issues.extend(report.phone_issues)
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


# ── Stages 12–15: matching and hub tables ─────────────────────────────────────

def stage_run_matching(ctx: RunContext) -> None:
    """Run exact + fuzzy matching for spa and dining against room guests."""
    with _timed(ctx, "run_matching"):
        # Build room stay contexts from canonical
        stays: list[RoomStayContext] = []
        guest_by_key: dict[str, str] = {}  # match_name_key -> guest_id
        for name_key, guest in ctx.dim_guests.items():
            # Find a row for this guest to get arrival/departure
            for row in ctx.rooms_canonical:
                if row.match_name_key == name_key and row.arrival_date and row.departure_date:
                    stays.append(
                        RoomStayContext(
                            guest_id=guest.guest_id,
                            match_name_key=name_key,
                            arrival_date=row.arrival_date,
                            departure_date=row.departure_date,
                        )
                    )
                    guest_by_key[name_key] = guest.guest_id
                    break  # one stay context per guest

        results = []
        matched_spa_keys: set[str] = set()
        matched_dining_keys: set[str] = set()

        # Match spa rows
        for spa_row in ctx.spa_canonical:
            if not spa_row.match_name_key or not spa_row.activity_date:
                continue
            candidate = ExactMatchCandidate(
                guest_id="",
                match_name_key=spa_row.match_name_key,
                activity_date=spa_row.activity_date,
            )
            act_key = make_activity_source_key(spa_row.source_system, spa_row.source_row_id)

            # Try exact match first
            exact = match_exact_name_date(candidate, stays, ctx.date_tolerance_days)
            if exact:
                results.append(make_exact_result(
                    exact.stay.guest_id, spa_row.source_system, act_key,
                    spa_row.activity_date, spa_row.activity_time,
                ))
                matched_spa_keys.add(spa_row.source_row_id)
                continue

            # Try fuzzy
            ambiguous = are_fuzzy_scores_ambiguous(
                candidate, stays,
                score_cutoff=ctx.fuzzy_score_cutoff,
                tolerance_days=ctx.date_tolerance_days,
            )
            if len(ambiguous) == 1:
                results.append(make_fuzzy_result(
                    ambiguous[0].stay.guest_id, spa_row.source_system, act_key,
                    spa_row.activity_date, ambiguous[0].score, spa_row.activity_time,
                ))
                matched_spa_keys.add(spa_row.source_row_id)
            elif len(ambiguous) > 1:
                ctx.qa_possible_matches.extend(
                    collect_ambiguous_fuzzy(
                        spa_row.source_system, act_key, ambiguous,
                        spa_row.activity_date, spa_row.match_name_key,
                    )
                )

        # Match dining rows
        for din_row in ctx.dining_canonical:
            if not din_row.match_name_key or not din_row.activity_date:
                continue
            candidate = ExactMatchCandidate(
                guest_id="",
                match_name_key=din_row.match_name_key,
                activity_date=din_row.activity_date,
            )
            act_key = make_activity_source_key(din_row.source_system, din_row.source_row_id)

            exact = match_exact_name_date(candidate, stays, ctx.date_tolerance_days)
            if exact:
                results.append(make_exact_result(
                    exact.stay.guest_id, din_row.source_system, act_key,
                    din_row.activity_date, din_row.activity_time,
                ))
                matched_dining_keys.add(din_row.source_row_id)
                continue

            ambiguous = are_fuzzy_scores_ambiguous(
                candidate, stays,
                score_cutoff=ctx.fuzzy_score_cutoff,
                tolerance_days=ctx.date_tolerance_days,
            )
            if len(ambiguous) == 1:
                results.append(make_fuzzy_result(
                    ambiguous[0].stay.guest_id, din_row.source_system, act_key,
                    din_row.activity_date, ambiguous[0].score, din_row.activity_time,
                ))
                matched_dining_keys.add(din_row.source_row_id)
            elif len(ambiguous) > 1:
                ctx.qa_possible_matches.extend(
                    collect_ambiguous_fuzzy(
                        din_row.source_system, act_key, ambiguous,
                        din_row.activity_date, din_row.match_name_key,
                    )
                )

        # Update dim_guest activity counts
        update_guest_activity_counts(ctx.dim_guests, results)

        # Convert match results to BridgeGuestActivity
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
                qa_review_required=r.qa_review_required,
            )
            for r in results
        ]

        # Collect unmatched
        ctx.qa_unmatched_spa = collect_unmatched_spa(ctx.spa_canonical, matched_spa_keys)
        ctx.qa_unmatched_dining = collect_unmatched_dining(ctx.dining_canonical, matched_dining_keys)

        logger.info(
            "Matching complete: %d links (spa:%d dining:%d), unmatched spa:%d dining:%d",
            len(results),
            len(matched_spa_keys),
            len(matched_dining_keys),
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
