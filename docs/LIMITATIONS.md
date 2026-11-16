# Limitations & non-goals

This project is **not yet a production hotel automation platform**.

- No OTA/channel manager integration, PMS API connector, login robot, messaging, payment processing, KBS or government record submissions.
- No staff payroll, room revenue management or regulatory tax rules.
- The default CLI's room suggestions are deterministic and greedy. **Only if greedy planning misses a reservation**, a bounded recovery search may find a full alternative plan for up to **8 eligible stays / 18 rooms / 20,000 candidate placements**. This is not a global optimizer; large or unsolved cases retain partial advisory suggestions and critical warnings. Every proposal still requires human review.
- Reservations are treated as snapshot input. There is no event history, concurrency lock, immutable audit log, persisted calendar or booking hold TTL.
- No timezone/time-of-day distinction; dates only. Same-day occupancy policies vary by property.
- Partial transfers, room moves, occupancy by number of persons, different bed lengths and special requests are not modelled yet.
- CLI may process input in memory. There is a prototype size guard, not a security guarantee.
- No real users, download figures, stars, pilots, certifications or regulator approvals are claimed.
