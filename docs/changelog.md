# Changelog

## v0.2.0 — 2026-03-08

### Added
- Full implementation of all cleaners (names, phones, dates, codes, text, nulls)
- Complete utils layer (constants, hashing, id_utils, file_utils, logging_utils, decorators)
- Canonical schema dataclasses (RoomsCanonicalRow, SpaCanonicalRow, DiningCanonicalRow)
- Hub schema dataclasses (DimGuest, DimPhone, FactRoomStay, BridgeGuestRoomStay, BridgeGuestActivity)
- QA schema dataclasses (QaNameIssue, QaPhoneIssue, QaLookupIssue, QaPossibleMatch, QaUnmatchedRecord, QaRunSummary)
- Room XML parser with element and attribute field strategy auto-detection
- Spa PDF parser with pdfplumber support and built-in fallback
- Dining CSV parser with automatic revenue column stripping
- rooms_standardize transform (reservation-level → typed fields)
- rooms_expand_guests transform (accompanying guest splitting, phone inheritance flags)
- spa_standardize transform (service classification, guest aggregates)
- dining_standardize transform (column alias resolution, name parsing)
- Complete matching layer (keys, stay_window, exact_match, fuzzy_match, scorer, phone_support, repeated_pattern, guest_resolver)
- All QA modules (validation, name_issues, phone_issues, duplicate_checks, possible_matches, unmatched, audit_flags)
- Full pipeline orchestration (run_context, stages, manifest_builder, orchestrator)
- CSV, Excel, JSON, and package_run output modules
- run_pipeline.py CLI entry point (18-stage pipeline)
- run_spa_legacy.py CLI entry point (legacy PDF→Excel converter)
- Reference data rows for room_types.tsv and special_requests.tsv
- Realistic test fixtures (sample_room.xml, sample_dining.csv)
- All config files populated (column_maps.yaml, source_rules.yaml, qa_rules.yaml, logging.yaml)
- Comprehensive docs (business_rules, source_dictionary, qa_checklist, runbook)

## v0.1.0 — initial scaffold

- Repository structure created by ChatGPT Codex scaffold
- Repository structure and initial module stubs
