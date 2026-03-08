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

## Column-level contracts

### rooms_canonical (guest-grain, one row per person per reservation)

Key fields: `guest_id` (after resolution), `confirmation_number`, `first_name`, `last_name`, `full_name_clean`, `match_name_key`, `arrival_date`, `departure_date`, `nights`, `stay_window_start`, `stay_window_end`, `nightly_rate`, `room_type_code`, `room_type_description`, `assigned_room_type_code`, `phone_raw`, `phone_clean`, `match_phone_key`, `phone_is_inherited`, `phone_is_shared`, `guest_role`, `is_primary_reservation_guest`, `is_expanded_from_accompanying_text`, `specials_list`, `specials_descriptions`, `is_valid_record`, `qa_issue`, `qa_notes`.

### spa_canonical (one row per appointment)

Key fields: `source_row_id`, `guest_name_raw`, `first_name`, `last_name`, `match_name_key`, `service_date`, `service_time`, `service_name`, `duration_minutes`, `therapist_name`, `match_phone_key`, `is_valid_record`, `qa_issue`.

### dining_canonical (one row per visit)

Key fields: `source_row_id`, `guest_name_raw`, `first_name`, `last_name`, `match_name_key`, `visit_date`, `visit_time`, `party_size`, `dining_status`, `dining_area`, `server_name`, `table_raw`, `phone_raw`, `match_phone_key`, `is_valid_record`, `qa_issue`. Revenue columns are stripped at parse time.

### fact_room_stay (reservation-grain, not multiplied by guest expansion)

Key fields: `confirmation_number`, `arrival_date`, `departure_date`, `nights`, `rate_code`, `nightly_rate`, `room_type_code`, `reservation_status_raw`, `vip_status_raw`.

### dim_guest

Key fields: `guest_id`, `best_first_name`, `best_last_name`, `best_full_name`, `canonical_name_key`, `first_seen_date`, `last_seen_date`, `has_room_activity`, `has_spa_activity`, `has_dining_activity`, activity counts, `identity_status`.

### bridge_guest_activity

Key fields: `guest_id`, `source_system`, `source_activity_key`, `activity_date`, `match_method`, `match_score`, `match_flag_fuzzy`, `matched_within_stay_window`, `matched_by_phone_support`, `qa_review_required`.
