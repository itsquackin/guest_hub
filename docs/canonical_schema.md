# Canonical Schema

## Canonical outputs

The v1 scaffold targets three guest/activity canonical tables:

- `rooms_canonical`: one row per guest attached to a reservation/stay.
- `spa_canonical`: one row per spa appointment.
- `dining_canonical`: one row per dining reservation/visit.

## Stay-truth separation

To prevent double-counting from room guest expansion, keep reservation/stay metrics in
`fact_room_stay` and relate guests via `bridge_guest_room_stay`.

## Matching-ready shared fields

Canonical source tables should expose:

- `full_name_clean`, `match_name_key`
- `phone_clean`, `match_phone_key` (where available)
- `activity_date`, `activity_time`
- QA columns: `is_valid_record`, `qa_issue`, `qa_notes`

## Status

This document is a starter reference. Detailed column-level contracts are TODO for Phase 1.
