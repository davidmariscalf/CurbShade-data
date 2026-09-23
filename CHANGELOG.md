# Changelog

All notable changes are recorded here.

## Unreleased

- Raised branch coverage from 76% to 87% with deterministic OSM normalization and OSW boundary tests; CI floor raised from 73% to 84%.
- Added branch-coverage measurement (current baseline 76%) with a CI floor of 73% to prevent silent test-coverage regressions.
- Release builds now install and smoke-test the built wheel before artifact upload.
- Release PRs verify changelog/version consistency and SHA-256 checksums before tagging.
- Added weekly Dependabot updates for Python dependencies and pinned GitHub Actions.
- Added Ruff static analysis and scheduled dependency vulnerability audits.
- Replaced the auxiliary OSW validator dependency after auditing found it pinned a vulnerable GeoPandas release (PYSEC-2026-62).
- OSW ZIPs are now validated against an explicit caller-supplied Draft 7 schema with path, size, encryption and compression-ratio safety checks.
- OSW validation now requires the OpenSidewalks 0.3 schema identity and recognized OSW dataset filenames, with optional SHA-256 pinning.

## 0.2.0 - 2026-09-22

- Moved reusable validation and coverage logic into the installable `curbshade_data` package.
- Added installed CLIs for validation, coverage profiling, schema export, OSM acquisition and OpenSidewalks validation.
- Added the versioned `curbshade-network/1` JSON Schema contract.
- Added stricter graph integrity, finite-value and empty-network validation.
- Added OSM acquisition provenance and explicit skipped-edge quality metadata.
- Added OSMnx 2.1.1 integration and the official OpenSidewalks validator in isolated dependency environments.
- Added edge-count and length-weighted accessibility-data coverage reporting.
- Expanded CI across Python 3.10 through 3.14 and external integration jobs.
