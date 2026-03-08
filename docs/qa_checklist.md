# QA Checklist

## Name issues (`qa_name_issues`)

- [ ] Both first and last name blank → `incomplete_name`
- [ ] Only last name present → `incomplete_name` (quality: last_only)
- [ ] Only first name present → `incomplete_name` (quality: first_only)
- [ ] First-name field appears to contain multiple people → `multi_name_field`
- [ ] Accompanying guest segment contains odd delimiter → `odd_delimiter`

## Phone issues (`qa_phone_issues`)

- [ ] Phone field blank or null → `blank_phone`
- [ ] Fewer than 7 digits → `incomplete_phone`
- [ ] More than 11 digits or starts with + → `international_phone`
- [ ] Accompanying guest phone inherited from reservation → `inherited_phone`
- [ ] Phone shared by more than 3 guests → `shared_phone`

## Lookup issues (`qa_lookup_issues`)

- [ ] Room type code not found in room_types.tsv → `unknown_room_type`
- [ ] Assigned room type code not found → `unknown_assigned_room_type`
- [ ] Special request code not found in special_requests.tsv → `unknown_special_request`

## Matching issues (`qa_possible_matches`)

- [ ] Fuzzy match with score in ambiguous range (two scores within 0.03) → `fuzzy_only`
- [ ] Same phone, different last name → `same_phone_different_last_name`
- [ ] Same name match but activity outside stay window → `same_name_outside_stay_window`
- [ ] Same last name, similar first name → `same_last_similar_first`

## Unmatched records

- [ ] Spa appointment not linked to any room guest → `qa_unmatched_spa`
- [ ] Dining visit not linked to any room guest → `qa_unmatched_dining`

## Run summary

- [ ] `qa_run_manifest.json` produced per run with row counts for all stages
