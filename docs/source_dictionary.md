# Source Dictionary

## Rooms source

- **Format**: XML
- **Grain**: One `<room>` element per reservation
- **Canonical grain**: One row per guest (primary + accompanying)
- **Key fields**: confirmation_number (C18), arrival (C30), departure (C33)
- **Lookup tables**: room_types.tsv, special_requests.tsv
- **Financial field**: nightly_rate (C48) — only rooms carries financial signal in v1

## Spa source

- **Format**: PDF (itinerary / calendar format)
- **Grain**: One appointment per row in the extracted table
- **Canonical grain**: One row per spa appointment
- **Key fields**: guest_name_raw, service_date, service_time
- **Not financial**: No cost/revenue fields in canonical

## Dining source

- **Format**: CSV
- **Grain**: One row per reservation or cover
- **Canonical grain**: One row per dining visit
- **Key fields**: guest_name_raw, visit_date, phone_raw
- **Not financial**: 20+ revenue columns stripped before canonicalization

## Reference tables

### room_types.tsv

| Column                  | Description                    |
|-------------------------|--------------------------------|
| room_type_code          | Short code from C45 / C135     |
| room_type_description   | Human-readable room type name  |

### special_requests.tsv

| Column                       | Description                        |
|------------------------------|------------------------------------|
| special_request_code         | Short code from C66                |
| special_request_description  | Human-readable request description |
