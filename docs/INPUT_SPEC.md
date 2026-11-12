# Input specification (schema 1.0)

Only JSON input is supported in v0.1.0. All examples must be fictional. Normalize and pseudonymize at the source. **Do not pass raw reservations or hotel exports into this program.**

```json
{
  "property_id": "DEMO_INN_01",
  "rooms": [{"id":"101", "category":"standard", "beds":"twin", "active":true,
             "maintenance":[{"start":"2026-11-13", "end":"2026-11-15"}]}],
  "reservations": [{"ref":"R001", "source":"CHANNEL_A", "status":"confirmed",
                    "checkin":"2026-11-13", "checkout":"2026-11-15",
                    "category":"standard", "room_id":null, "twin_requested":true,
                    "nightly_base":"65.00", "total_base":"130.00", "currency":"EUR"}]
}
```

- Allowed statuses: `confirmed`, `pending`, `cancelled`.
- Allowed bed layouts: `double`, `twin`, `flex`.
- Currency (only with `nightly_base` and `total_base`): `TRY`, `EUR`, `GBP`, `USD`.
- Monetary values: **decimal strings** with at most two decimal places, non-negative, up to 12 integer digits; exponent notation is rejected. No FX conversion.
- Reservation `ref`, `source`, `property_id`, room IDs and categories use 1-40 alphanumeric, underscore or hyphen characters. **This formatting restriction does not make a real booking ID anonymous**; generate pseudonyms before input.
- `checkout` is exclusive: stays 12→13 and 13→14 do not conflict.
- Room maintenance `end` is exclusive.
- Unknown properties (including name, email, passport, phone, national ID and any unrecognized fields) are rejected rather than silently carried forward.
- `total_base` refers to the base accommodation amount *excluding* fees, taxes, discounts or complex pricing rules. Mismatches are review flags only.
- Future unassigned **confirmed** reservations may get a room proposal; no action is executed.
- Already assigned **pending** reservations are treated conservatively as inventory holds, subject to property policy.

Output JSON contains `summary`, `issues`, `room_proposals`, and `tomorrow_arrivals`. It is intended for review only. There is no guest communication, update or write-back API.
