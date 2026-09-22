# Production data pipeline

CurbShade-data treats missing accessibility information as uncertainty, not as evidence that a route is accessible.

## Pipeline stages

A production pipeline should keep these stages explicit:

1. Acquire baseline pedestrian topology.
2. Validate source-specific data.
3. Normalize into the CurbShade graph contract.
4. Run `scripts/validate.py`.
5. Run `scripts/profile_coverage.py`.
6. Reject or quarantine outputs that fail validation.
7. Preserve source/provenance metadata with the artifact consumed by routing.

## Isolated external integrations

Two mature external stacks are supported, but they currently have incompatible GeoPandas requirements and therefore must run in separate environments.

### OpenStreetMap acquisition

OSMnx 2.1.1 is used for walking-network acquisition:

```bash
python -m venv .venv-osm
# activate it
pip install -e ".[osm]"
python scripts/fetch_osm.py "Madrid, Spain" --out madrid.json
```

OSM acquisition requires Python 3.11+.

### OpenSidewalks validation

OpenSidewalks interchange data should be validated with the official Taskar Center validator before conversion or use:

```bash
python -m venv .venv-osw
# activate it
pip install -e ".[osw]"
python scripts/validate_osw.py dataset.zip
```

Do not install the `osm` and `osw` extras into the same environment while their GeoPandas constraints conflict. CI deliberately tests them in separate jobs.

## Normalized graph gate

Every normalized graph must pass:

```bash
python scripts/validate.py graph.json
python scripts/profile_coverage.py graph.json --json > coverage.json
```

Validation rejects duplicate node IDs, missing endpoints, non-finite lengths/attributes, non-positive widths/lengths, and out-of-range normalized scores.

Coverage is reported by both edge count and network length. A high route score must never hide low source-data coverage.

## Provenance

OSM acquisitions record:

- source name
- original place query
- OSMnx version
- generation timestamp
- OpenStreetMap attribution
- number of edges skipped because length was invalid

Preserve this metadata with derived routing artifacts.

## Licensing

CurbShade-data code is MIT. OpenStreetMap-derived databases remain subject to ODbL attribution/share-alike requirements where applicable. OpenSidewalks datasets retain their source-specific licensing and attribution.

## Production boundary

This repository provides acquisition, validation, profiling and normalization tooling. It does not by itself provide a hosted routing service, freshness scheduler, field-survey workflow, or guarantee that source data is complete enough for a particular accessibility decision.
