# Maintainer plan & evidence log (for actual open-source adoption)

The objective is useful public infrastructure, **not artificial star counts, staged PRs, or invented traction**. As of 2026-11-12, this repository is a new prototype prepared for publication; no adoption is claimed.

## What would count as genuine progress?

| Evidence | How to produce and verify |
|---|---|
| Real user value | Opt-in feedback from small hospitality businesses; redact all guest/property data |
| Active maintenance | Issues labelled, real bugs fixed with regression tests, public releases with changelogs |
| Community engagement | External contributors with meaningful PRs, questions, translations and documentation fixes |
| Adoption | Independently verifiable downloads/clones, third-party integrations or public mentions (with permission) |
| Safety | Reviewed code changes, secret scanning, safe issue templates, security response policy |
| Platform independence | Vendor-neutral schema and documented adapters, no terms-of-service circumvention |

## First 12 weeks (suggested, **not a program requirement**)

- Weeks 1–2: publish v0.1, build install/demo instructions, run CI on supported Python versions, add test cases from synthetic scenarios.
- Weeks 3–4: collect anonymized feedback from 2–3 willing hotel operators; publish known issues and operator priorities.
- Weeks 5–8: implement local-only read-only dashboard, add property policy configuration, label and triage issues; release v0.2 only when features work.
- Weeks 9–12: write transparent pilot report, improve translations/accessibility, document supported vendor APIs, accept and review outside contributions where available.

Do not set arbitrary GitHub stars or issue volume targets. Record *actual* feedback and releases only.

## Codex for Open Source application (when truthful evidence exists)

The official form asks for a public repository, maintainer role, why the repo qualifies (max 500 chars), OpenAI organization ID, and how API credits would support core maintenance (max 500 chars). See https://openai.com/tr-TR/form/codex-for-oss/ . Acceptance and Pro access are not guaranteed. Apply with the links and actual metrics available at the time.

## Responsible AI workflow

Codex or another code assistant may suggest test cases, review diffs, document issues and prepare releases. The human maintainer remains responsible for ensuring correctness, legality and non-disclosure before any merge or release.
