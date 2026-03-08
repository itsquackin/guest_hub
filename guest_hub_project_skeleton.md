# Guest Hub Project Skeleton

## 1. Project goal

Build a Python-based **guest intelligence hub** that:

- ingests **Rooms XML**, **Spa PDF**, and **Dining CSV**
- converts each source into a clean canonical structure
- treats every person as an **individual guest from the start**
- expands accompanying room guests into full guest rows
- preserves reservation/stay truth separately to avoid double-counting
- links cross-department activity using:
  - **Exact Name + Date Window**
  - **Fuzzy Name + Date Window**
  - supporting signals like phone, outside-stay activity, and repeated cross-source patterns
- produces QA outputs for anything uncertain
- keeps the current spa converter script inside the project so the repo is all-in-one

---

## 2. Locked business rules

### Rooms

- `C9` = Booked By
- `C15` = Booked On
- `C18` = Confirmation Number
- `C21` = Last Name
- `C24` = First Name
- `C27` = Accompanying Guest(s)
- `C30` = Arrival
- `C33` = Departure
- `C36` = Nights
- `C39` = Rate Code
- `C45` = Room Type
- `C48` = Nightly Rate
- `C51` = Company
- `C54` = Status
- `C66` = Specials
- `C81` = Last Stay Date
- `C84` = Last Room
- `C93` = Phone Number
- `C129` = VIP Status
- `C135` = Assigned Room Type

### Guest grain

- Rooms must be **guest-grain from the start**
- every accompanying guest becomes a full guest row
- incomplete names still become rows
- messy formatting is preserved and flagged for QA
- accompanying guests inherit the reservation phone when needed
- inherited phone must be flagged as **shared/inherited**

### Financial treatment

- Rooms has the usable financial signal for v1: **Nightly Rate**
- Spa and Dining are **not financial systems** for this project
- dining revenue-style columns are removed from the canonical dining model

### Matching

- primary link methods:
  - `ExactNameDate`
  - `FuzzyNameDate`
- fuzzy matches must be visibly flagged
- keep room for these supporting conditions:
  - same last name, slightly different first name
  - same phone, different last name
  - same name outside stay window
  - no room match, but repeated spa/dining activity across time
- date tolerance = **±1 day**

---

## 3. Architecture principles

- keep **source parsing** separate from **matching**
- preserve **raw values** before cleaning
- make every match **explainable**
- write QA outputs instead of forcing uncertain joins
- use **guest-grain canonical tables**
- keep a separate **reservation/stay fact table** so room nights and rates are not multiplied by guest expansion
- make lookups and thresholds **configurable**
- preserve the current spa script as a first-class project asset

---

## 4. Recommended root folder structure

```text
guest_hub/
│
├── README.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── run_pipeline.py
├── run_spa_legacy.py
│
├── config/
│   ├── settings.yaml
│   ├── source_rules.yaml
│   ├── column_maps.yaml
│   ├── matching_rules.yaml
│   ├── qa_rules.yaml
│   └── logging.yaml
│
├── data/
│   ├── raw/
│   │   ├── rooms/
│   │   ├── spa/
│   │   └── dining/
│   ├── reference/
│   │   ├── room_types.tsv
│   │   └── special_requests.tsv
│   ├── interim/
│   │   ├── rooms/
│   │   ├── spa/
│   │   └── dining/
│   ├── processed/
│   │   ├── canonical/
│   │   ├── hub/
│   │   └── qa/
│   └── archive/
│       ├── runs/
│       └── source_snapshots/
│
├── docs/
│   ├── project_overview.md
│   ├── source_dictionary.md
│   ├── canonical_schema.md
│   ├── matching_logic.md
│   ├── business_rules.md
│   ├── qa_checklist.md
│   ├── runbook.md
│   └── changelog.md
│
├── logs/
│   └── .gitkeep
│
├── src/
│   ├── __init__.py
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── stages.py
│   │   ├── run_context.py
│   │   └── manifest_builder.py
│   │
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── room_loader.py
│   │   ├── spa_loader.py
│   │   ├── dining_loader.py
│   │   └── reference_loader.py
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── room_parser.py
│   │   ├── spa_parser.py
│   │   ├── dining_parser.py
│   │   ├── room_types_parser.py
│   │   └── specials_parser.py
│   │
│   ├── cleaners/
│   │   ├── __init__.py
│   │   ├── names.py
│   │   ├── phones.py
│   │   ├── dates.py
│   │   ├── text.py
│   │   ├── codes.py
│   │   └── nulls.py
│   │
│   ├── transforms/
│   │   ├── __init__.py
│   │   ├── rooms_standardize.py
│   │   ├── rooms_expand_guests.py
│   │   ├── rooms_enrich.py
│   │   ├── spa_standardize.py
│   │   ├── dining_standardize.py
│   │   └── shared_fields.py
│   │
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── keys.py
│   │   ├── exact_match.py
│   │   ├── fuzzy_match.py
│   │   ├── phone_support.py
│   │   ├── stay_window.py
│   │   ├── repeated_pattern.py
│   │   ├── scorer.py
│   │   └── guest_resolver.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── canonical_schema.py
│   │   ├── hub_schema.py
│   │   ├── qa_schema.py
│   │   └── enums.py
│   │
│   ├── qa/
│   │   ├── __init__.py
│   │   ├── validation.py
│   │   ├── name_issues.py
│   │   ├── phone_issues.py
│   │   ├── duplicate_checks.py
│   │   ├── unmatched.py
│   │   ├── possible_matches.py
│   │   └── audit_flags.py
│   │
│   ├── outputs/
│   │   ├── __init__.py
│   │   ├── export_csv.py
│   │   ├── export_excel.py
│   │   ├── export_json.py
│   │   └── package_run.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging_utils.py
│   │   ├── file_utils.py
│   │   ├── id_utils.py
│   │   ├── hashing.py
│   │   ├── constants.py
│   │   └── decorators.py
│   │
│   └── legacy/
│       ├── __init__.py
│       └── spa_calendar_converter.py
│
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   ├── sample_room.xml
    │   ├── sample_spa.pdf
    │   ├── sample_dining.csv
    │   ├── room_types.tsv
    │   └── special_requests.tsv
    ├── test_room_parser.py
    ├── test_room_expansion.py
    ├── test_room_enrichment.py
    ├── test_spa_parser.py
    ├── test_dining_parser.py
    ├── test_name_cleaning.py
    ├── test_phone_cleaning.py
    ├── test_exact_match.py
    ├── test_fuzzy_match.py
    ├── test_stay_window.py
    └── test_possible_matches.py
```

---

## 5. What each top-level area does

### `config/`

Stores settings that should not be hard-coded:

- folder paths
- file naming assumptions
- matching thresholds
- fuzzy score cutoffs
- date-window tolerance
- QA flag rules
- log settings

### `data/raw/`

Drop zone for original source files:

- room XML
- spa PDF
- dining CSV

### `data/reference/`

Lookup tables that enrich the room source:

- room type descriptions
- special request descriptions

### `data/interim/`

Holds pre-canonical source outputs, such as:

- parsed room rows before guest expansion
- raw spa appointment rows from PDF extraction
- parsed dining rows before field pruning

### `data/processed/canonical/`

Stores canonical source tables:

- `rooms_canonical`
- `spa_canonical`
- `dining_canonical`

### `data/processed/hub/`

Stores hub-level output tables:

- `dim_guest`
- `dim_phone`
- `fact_room_stay`
- `bridge_guest_room_stay`
- `bridge_guest_activity`

### `data/processed/qa/`

Stores QA and exception outputs:

- incomplete names
- inherited/shared phone flags
- possible matches
- unmatched records
- ambiguous fuzzy matches
- bad or unknown lookup codes

### `src/legacy/`

Preserves the current spa converter so the project remains all-in-one and you never lose the working PDF-to-Excel utility.

---

## 6. Source-by-source design

## Rooms

### Room source grain

The original room XML is reservation-grain, but the canonical room table will be **guest-grain**.

That means one source reservation can become:

- one primary guest row
- zero or more accompanying guest rows

### Room canonical grain

`rooms_canonical` = **one row per individual guest attached to a reservation/stay**

### Room canonical columns

Recommended v1 columns:

- `source_system`
- `source_file_name`
- `source_row_id`
- `load_timestamp`
- `booked_by_raw`
- `booked_on_date`
- `confirmation_number`
- `guest_name_raw`
- `first_name`
- `last_name`
- `full_name_clean`
- `match_name_key`
- `primary_guest_name_raw`
- `accompanying_guest_raw`
- `guest_role`
- `guest_sequence_in_reservation`
- `is_primary_reservation_guest`
- `is_expanded_from_accompanying_text`
- `relationship_to_primary_guest`
- `arrival_date`
- `departure_date`
- `nights`
- `stay_window_start`
- `stay_window_end`
- `rate_code`
- `nightly_rate`
- `room_type_code`
- `room_type_description`
- `assigned_room_type_code`
- `assigned_room_type_description`
- `company_raw`
- `reservation_status_raw`
- `specials_raw`
- `specials_list`
- `specials_descriptions`
- `last_stay_date`
- `last_room_raw`
- `vip_status_raw`
- `phone_raw`
- `phone_clean`
- `match_phone_key`
- `phone_is_inherited`
- `phone_is_shared`
- `reservation_guest_key`
- `stay_span_key`
- `is_valid_record`
- `qa_issue`
- `qa_notes`

### Room financial truth table

Because guest expansion would otherwise duplicate room nights and rate values, create a separate reservation/stay fact:

`fact_room_stay` = **one row per reservation/stay**

Recommended columns:

- `confirmation_number`
- `arrival_date`
- `departure_date`
- `nights`
- `rate_code`
- `nightly_rate`
- `room_type_code`
- `room_type_description`
- `assigned_room_type_code`
- `assigned_room_type_description`
- `company_raw`
- `reservation_status_raw`
- `specials_raw`
- `vip_status_raw`
- `last_stay_date`
- `last_room_raw`

### Room guest bridge

`bridge_guest_room_stay` = links resolved guests to room stays

Recommended columns:

- `guest_id`
- `confirmation_number`
- `reservation_guest_key`
- `guest_role`
- `is_primary_reservation_guest`
- `phone_is_inherited`
- `link_source`

---

## Spa

### Spa canonical grain

`spa_canonical` = **one row per spa appointment**

### Spa canonical columns

Recommended v1 columns:

- `source_system`
- `source_file_name`
- `source_row_id`
- `load_timestamp`
- `guest_name_raw`
- `first_name`
- `last_name`
- `full_name_clean`
- `match_name_key`
- `service_date`
- `service_time`
- `activity_date`
- `activity_time`
- `service_type_raw`
- `service_name`
- `duration_mins`
- `service_category`
- `is_couples_service`
- `guest_total_spa_appts`
- `guest_total_spa_time_mins`
- `guest_has_same_day_multi`
- `guest_is_multi_day`
- `guest_has_any_couples`
- `appointment_group_key`
- `is_valid_record`
- `qa_issue`
- `qa_notes`

### Spa note

Preserve the legacy script, but also create a `spa_parser.py` that extracts the same core appointment rows for the new hub pipeline.

---

## Dining

### Dining canonical grain

`dining_canonical` = **one row per dining reservation or visit**

### Dining canonical columns to keep

- `source_system`
- `source_file_name`
- `source_row_id`
- `load_timestamp`
- `visit_date`
- `visit_time`
- `activity_date`
- `activity_time`
- `guest_name_raw`
- `first_name`
- `last_name`
- `full_name_clean`
- `match_name_key`
- `phone_raw`
- `phone_clean`
- `match_phone_key`
- `party_size`
- `dining_status`
- `table_raw`
- `dining_area`
- `booking_source`
- `server_name`
- `guest_requests_raw`
- `visit_notes_raw`
- `reservation_tags_raw`
- `guest_tags_raw`
- `completed_visits`
- `is_valid_record`
- `qa_issue`
- `qa_notes`

### Dining columns explicitly removed

- Experience Title
- Experience Price Type
- Experience Price
- Additional Payments
- Additional Payments Subtotal
- Experience Gratuity
- POS Subtotal
- POS Tax
- POS Service Charges
- POS Gratuity
- POS Paid
- POS Due
- Prepayment Method
- Prepayment Status
- Prepaid Experience Total Paid
- Total Gratuity
- Total Tax
- Experience Total Sales
- Experience Total Sales with Gratuity
- Total Revenue
- Total Revenue with Gratuity

---

## 7. Shared hub tables

### `dim_guest`

One row per resolved person identity.

Recommended columns:

- `guest_id`
- `best_first_name`
- `best_last_name`
- `best_full_name`
- `canonical_name_key`
- `first_seen_date`
- `last_seen_date`
- `has_room_activity`
- `has_spa_activity`
- `has_dining_activity`
- `room_activity_count`
- `spa_activity_count`
- `dining_activity_count`
- `linked_phone_count`
- `name_confidence`
- `identity_status`

### `dim_phone`

One row per normalized phone.

Recommended columns:

- `phone_id`
- `phone_clean`
- `phone_raw_example`
- `linked_guest_count`
- `is_shared_phone`
- `is_international_like`
- `is_incomplete_like`
- `is_valid_like`

### `bridge_guest_activity`

One row per guest-to-activity link across all source systems.

Recommended columns:

- `guest_id`
- `source_system`
- `source_activity_key`
- `activity_date`
- `activity_time`
- `match_method`
- `match_score`
- `match_flag_fuzzy`
- `matched_within_stay_window`
- `matched_by_phone_support`
- `outside_stay_window_flag`
- `repeated_pattern_flag`
- `qa_review_required`

---

## 8. Matching framework

This should not be one giant function. Break it into layers.

### Match keys

Create:

- `match_name_key`
- `match_phone_key`
- `stay_window_key`
- activity-specific source keys

### Primary match methods

- `ExactNameDate`
- `FuzzyNameDate`

### Supporting signals

- `PhoneSupport`
- `OutsideStayWindow`
- `RepeatedCrossSourcePattern`
- `SameLastNameNearStay`
- `DifferentLastNameSharedPhone`

### Scoring approach

Recommended pattern:

- exact name + within date window = strongest
- fuzzy name + within date window = allowed, but flagged
- phone-only = support signal, not sole truth in v1
- same name outside stay window = possible pattern, not automatic core match
- repeated spa/dining over time with consistent identity hints = candidate for later guest unification

### Date window rule

- room stay link tolerance = **arrival through departure, plus ±1 day**

---

## 9. QA framework

The project should intentionally surface ambiguity.

Recommended QA outputs:

### `qa_room_guest_name_issues`

- incomplete accompanying names
- odd delimiters
- unparseable guest text
- multi-name first-name fields

### `qa_phone_issues`

- blank phones
- inherited/shared phones
- suspicious formatting
- international-like values
- same phone linked to many guests

### `qa_lookup_issues`

- unknown room type code
- unknown special request code

### `qa_unmatched_spa`

Spa guests not confidently linked to room stay or existing guest identity.

### `qa_unmatched_dining`

Dining guests not confidently linked to room stay or existing guest identity.

### `qa_possible_matches`

Near matches that need review:

- fuzzy-only hits
- same phone/different last name
- same name outside stay
- same last name/similar first name

### `qa_run_summary`

Counts by stage:

- rows loaded
- rows rejected
- rows expanded
- matches by method
- unmatched counts
- lookup misses

---

## 10. Pipeline order

1. load raw source files
2. load reference files
3. parse raw room XML
4. parse raw spa PDF
5. parse raw dining CSV
6. standardize shared fields
7. expand room accompanying guests into guest-grain rows
8. enrich room type descriptions
9. enrich special request descriptions
10. write canonical source tables
11. run QA validations on canonical outputs
12. build guest and phone dimensions
13. run exact matching
14. run fuzzy matching
15. add support signals like phone and outside-stay patterns
16. build bridges and hub tables
17. export CSV/Excel/JSON deliverables
18. write run manifest and QA summary

---

## 11. Phase plan

### Phase 1

Build the canonical foundation.

Deliverables:

- `rooms_canonical`
- `spa_canonical`
- `dining_canonical`
- room type enrichment
- specials enrichment
- QA flags for names and phone inheritance
- preserved `legacy/spa_calendar_converter.py`

### Phase 2

Build identity and linking.

Deliverables:

- `dim_guest`
- `dim_phone`
- `bridge_guest_activity`
- exact/fuzzy matching
- QA possible matches
- unmatched spa/dining outputs

### Phase 3

Build reporting-grade room truth and packaging.

Deliverables:

- `fact_room_stay`
- `bridge_guest_room_stay`
- run manifest
- export package for Excel / Power BI

---

## 12. Minimal file purposes

### `room_loader.py`

Find and load XML files.

### `room_parser.py`

Read each room block and convert coded XML fields into raw room rows.

### `rooms_expand_guests.py`

Turn primary + accompanying guest text into individual guest rows.

### `rooms_enrich.py`

Map room type codes and specials into readable descriptions.

### `spa_parser.py`

Create appointment rows from PDF itinerary content for the new pipeline.

### `dining_parser.py`

Read the dining CSV and keep only the fields still relevant to the hub.

### `names.py`

Shared guest-name cleaning and normalization functions.

### `phones.py`

Normalize phones and assign flags like inherited/shared, international-like, incomplete-like.

### `exact_match.py`

Link activity using exact normalized name plus date logic.

### `fuzzy_match.py`

Link near-name activity with visible fuzzy indicators.

### `stay_window.py`

Apply arrival/departure plus ±1 day rules.

### `possible_matches.py`

Create review tables for ambiguous links.

### `package_run.py`

Bundle outputs from one run into a neat delivery set.

---

## 13. Files that should exist from day one, even if empty

These are worth creating immediately:

- `README.md`
- `run_pipeline.py`
- `run_spa_legacy.py`
- `config/settings.yaml`
- `config/matching_rules.yaml`
- `docs/project_overview.md`
- `docs/canonical_schema.md`
- `docs/matching_logic.md`
- `src/pipeline/orchestrator.py`
- `src/parsers/room_parser.py`
- `src/parsers/spa_parser.py`
- `src/parsers/dining_parser.py`
- `src/transforms/rooms_expand_guests.py`
- `src/transforms/rooms_enrich.py`
- `src/matching/exact_match.py`
- `src/matching/fuzzy_match.py`
- `src/qa/possible_matches.py`
- `src/legacy/spa_calendar_converter.py`
- `tests/test_room_expansion.py`
- `tests/test_exact_match.py`

---

## 14. Final recommended shape of the project

At a high level, this project should think in **two parallel truths**:

### Guest truth

Who is this person, what did they do, and how can we connect them across departments?

Tables:

- `rooms_canonical`
- `spa_canonical`
- `dining_canonical`
- `dim_guest`
- `dim_phone`
- `bridge_guest_activity`

### Stay truth

What is the reservation/stay-level room record that should remain financially and operationally accurate?

Tables:

- `fact_room_stay`
- `bridge_guest_room_stay`

That split is what keeps the project both **guest-intelligent** and **reporting-safe**.

