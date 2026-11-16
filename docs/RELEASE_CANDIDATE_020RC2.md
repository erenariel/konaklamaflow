# v0.2.0rc2 Python distribution candidate — release gates

This document is for the **Python package**, not the separate browser demo
(v0.5.x-era). No publication is performed by adding this document or CI.

## Existing published facts (16 November 2026)

- GitHub Releases v0.1.1 and v0.2.0rc1 exist; neither has individually
  attached wheel, sdist or offline product ZIP assets.
- The GitHub Pages **fictional offline demo ZIP** is already distributed
  independently of a Python package release.
- v0.2.0rc2 is a **new candidate** in pyproject.toml; do not describe it
  as published to PyPI/TestPyPI until its registry page is verified.
- CI now builds both wheel and sdist, checks metadata, records SHA-256 and
  installs the wheel into a clean Python virtual environment to run
  the bundled demo and fictional CSV review.

## Packaging gate (required before tagging)

1. Commit to a reviewed branch and confirm the full Python 3.11, 3.12,
   3.13, Chromium **and clean-wheel package** jobs pass on the exact commit.
2. Download the CI distribution artifact. Verify wheel/sdist names, metadata,
   README, bundled fictional data, checksum and no private files.
3. Confirm a fresh environment can install the wheel and execute:
   - konaklamaflow demo
   - konaklamaflow review-csv with the fictional examples/csv files
   - the legacy JSON command and help
4. Audit filenames and releases for personal identifiers, real hotel
   data, secrets, large/generated files and accidental credentials.
5. Confirm the new package version is unique for the target index.
   Reusing a published version is unsafe; bump version for any rebuilt upload.
6. Record the exact main commit and SHA-256 before issuing a permanent tag.

## TestPyPI first

A separate **manually triggered** OIDC workflow may publish only after:

- The project owner creates/confirms the TestPyPI project or Pending Trusted
  Publisher for owner erenariel, repository konaklamaflow, workflow
  publish-testpypi.yml, and GitHub environment testpypi.
- The repository has the protected GitHub environment, with required
  reviewers when appropriate.
- The maintainer explicitly approves that exact candidate, enters the
  expected confirmation string and manually starts the workflow from main.
- After upload, a fresh virtual environment installs from TestPyPI, with
  dependencies from PyPI only if separately reviewed, and reruns demo/CSV.
- The TestPyPI page and its exact file checksums are confirmed. No download
  totals, independent user installation or uptake may be inferred from CI.

**Publishing to public PyPI is a separate irreversible decision** after
the TestPyPI smoke test and review of long-term namespace ownership.
Never enable automatic publishing on push/PR. Do not confuse a green
GitHub Actions run with a published distribution.

## GitHub Release with real assets

Once release approval exists, create a *new immutable Python package tag*,
attach the verified wheel/sdist and SHA256SUMS, and provide exact supported
features, limitations, clean install command and the commit SHA. Do not use
the old Python release tags or imply the browser demo and Python package
have the same version. The browser demo ZIP has its own separately verified
publication track.

## Personal-data boundary

The new local CSV command deliberately discards named private columns,
uses per-run pseudonymous IDs and leaves CSV inputs on the owner's disk.
It is **not a guarantee of irreversible anonymization, legal clearance, or
safe use with real exports**. Independent privacy review is required before
real hotel data tests. No CSV exports or user reports should be uploaded to
GitHub Actions, public issues, PyPI or Pages.
