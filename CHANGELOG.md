# Changelog

All notable changes are recorded here.

## Unreleased

No unreleased changes yet.

## 0.2.0 - 2026-09-22

- Moved reusable validation and coverage logic into the installable `curbshade_data` package.
- Added installed CLIs for validation, coverage profiling, schema export, OSM acquisition and OpenSidewalks validation.
- Added the versioned `curbshade-network/1` JSON Schema contract.
- Added stricter graph integrity, finite-value and empty-network validation.
- Added OSM acquisition provenance and explicit skipped-edge quality metadata.
- Added OSMnx 2.1.1 integration and the official OpenSidewalks validator in isolated dependency environments.
- Added edge-count and length-weighted accessibility-data coverage reporting.
- Expanded CI across Python 3.10 through 3.14 and external integration jobs.
