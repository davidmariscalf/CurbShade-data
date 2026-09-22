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

## External integrations

OSM acquisition and OSW schema validation are optional extras so the core package remains lightweight.

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

Use an unchanged OpenSidewalks 0.3 Draft 7 schema supplied by the caller:

```bash
python -m venv .venv-osw
# activate it
pip install -e ".[osw]"
curbshade-validate-osw dataset.zip --schema /path/to/opensidewalks.schema.json \
  --schema-sha256 <pinned-digest>
```

CurbShade intentionally does not bundle or modify the OpenSidewalks schema. Production jobs should pin the expected schema digest with `--schema-sha256` so validation cannot silently move to different schema bytes. Validation covers the supplied JSON Schema plus ZIP hygiene and resource limits. It does not replace specialized cross-file geometry/topology validation.

The previous auxiliary validator dependency was removed after dependency auditing showed that it forced a vulnerable GeoPandas version. The OSW extra now uses `jsonschema-rs` directly and is audited independently in CI.

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
