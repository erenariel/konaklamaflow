# Privacy-first AI workflow ideas (not integrations)

This project's design is informed by hospitality automation challenges and experience coordinating multiple AI assistants. It does **not** include any private Grokbot/Smart/Sweet instructions, email identities, internal property codes or credentials.

## Suggested separation of responsibilities

- **Deterministic engine:** validates inventory, identifies conflicts, and creates an explainable JSON report. No model inference is needed for these decisions.
- **Optional language assistant (future):** converts report codes to staff-facing explanations in Turkish/English/Russian/Italian *without sending guest data*.
- **Human approver:** reviews suggestions, checks the property policy and decides whether to update the authorized PMS.
- **Auditor (future):** records approvals and outcomes with minimum necessary metadata; never stores customer IDs in public logs.

## Example

An incoming *fictional* double-room booking requests twin beds. The deterministic rules locate only a double room. They output `NO_SAFE_ROOM_PROPOSAL`; a future assistant might draft a message saying bed configuration is unconfirmed, but **must not promise twin beds or send the message without approval**.
