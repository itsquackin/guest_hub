# Business Rules

All rules in this document are **locked** — they must not be changed without
explicit revision to this document and the project skeleton spec.

## Rooms source

### XML field codes

The rooms XML uses numeric C-codes for every field.  The locked mapping is:

| Code  | Canonical field         | Notes                                |
|-------|-------------------------|--------------------------------------|
| C9    | booked_by_raw           | Name of person who made the booking  |
| C15   | booked_on_raw           | Date the reservation was created     |
| C18   | confirmation_number     | Primary reservation identifier       |
| C21   | last_name_raw           | Primary guest last name              |
| C24   | first_name_raw          | Primary guest first name             |
| C27   | accompanying_guest_raw  | Free-text accompanying guest field   |
| C30   | arrival_raw             | Check-in date                        |
| C33   | departure_raw           | Check-out date                       |
| C36   | nights_raw              | Number of nights                     |
| C39   | rate_code               | Rate plan code                       |
| C45   | room_type_code          | Room type code                       |
| C48   | nightly_rate_raw        | Per-night rate                       |
| C51   | company_raw             | Company name                         |
| C54   | reservation_status_raw  | Status (Confirmed, Cancelled, etc.)  |
| C66   | specials_raw            | Special request codes (delimited)    |
| C81   | last_stay_date_raw      | Most recent prior stay date          |
| C84   | last_room_raw           | Most recent prior room               |
| C93   | phone_raw               | Contact phone number                 |
| C129  | vip_status_raw          | VIP tier / flag                      |
| C135  | assigned_room_type_code | Actually assigned room type          |

## Guest grain rule

- Rooms canonical output is **guest-grain**, not reservation-grain.
- Every person attached to a reservation becomes a separate row.
- This includes the primary guest and every name in the accompanying guest field.
- Incomplete or unparseable names still become rows and receive QA flags.
- They must never be silently dropped.

## Phone inheritance

- When an accompanying guest has no phone of their own, the reservation phone
  is propagated to their row.
- Inherited phones must be flagged: `phone_is_inherited = True`.
- When more than one guest shares a phone, it must also be flagged:
  `phone_is_shared = True`.

## Financial truth

- The `fact_room_stay` table holds one row per reservation.
- Rate and night counts must not be duplicated by guest expansion.
- Spa and Dining are **not financial systems** for v1.
- All revenue-style columns from Dining CSV are stripped before canonicalization.

## Matching rules

- Primary match methods: **ExactNameDate** and **FuzzyNameDate**.
- Fuzzy matches must be visibly flagged in all output tables (`match_flag_fuzzy = True`).
- Date tolerance is **±1 day** around the stay window (arrival through departure).
- Phone is a supporting signal only — never the sole basis for a confident match in v1.
- Uncertain joins must become `qa_possible_matches` rows, not forced links.

## Dining revenue columns removed

The following CSV columns are stripped and never enter the canonical model:

Experience Title, Experience Price Type, Experience Price, Additional Payments,
Additional Payments Subtotal, Experience Gratuity, POS Subtotal, POS Tax,
POS Service Charges, POS Gratuity, POS Paid, POS Due, Prepayment Method,
Prepayment Status, Prepaid Experience Total Paid, Total Gratuity, Total Tax,
Experience Total Sales, Experience Total Sales with Gratuity, Total Revenue,
Total Revenue with Gratuity.
