# CurbShade-data

Data ingestion and normalization for **CurbShade**.

The goal is not to pretend that OpenStreetMap has complete accessibility data. The pipeline preserves missing values so the routing engine can penalize uncertainty instead of interpreting absence as accessibility.

## Sources

- OpenStreetMap / OSMnx for baseline pedestrian topology
- OpenSidewalks-compatible GeoJSON for explicit sidewalk/curb semantics
- optional local shade observations as normalized `shade_fraction`

## Quick demo

```bash
python scripts/build_demo.py > demo_network.json
python scripts/validate.py demo_network.json
```

The generated file can be routed by the main repository.

## Audit data completeness

Accessibility routing is only as credible as the attributes behind it. Use the built-in coverage profiler to see how much of a graph actually contains curb, width, slope, surface, shade and crossing-risk data:

```bash
python scripts/profile_coverage.py demo_network.json
```

For machine-readable output:

```bash
python scripts/profile_coverage.py demo_network.json --json
```

The report includes both edge-count coverage and length-weighted coverage. This makes missing data visible instead of letting a route score look more certain than its source data justifies.

## Production integrations

### OpenStreetMap / OSMnx

OSM acquisition uses OSMnx 2.1.1 and requires Python 3.11+:

```bash
pip install -e ".[osm]"
curbshade-fetch-osm "Arganda del Rey, Spain" --out arganda.json
curbshade-validate arganda.json
```

The normalized artifact records source query, generation time, OSMnx version and OpenStreetMap attribution. OSM data is useful for topology but often lacks curb, width, slope and surface fields. Those remain `null`; they are **not** filled with optimistic defaults.

### OpenSidewalks

CurbShade validates OSW GeoJSON against an explicit, unmodified OpenSidewalks Draft 7 schema. Keep the schema outside this repository and pass its path explicitly:

```bash
pip install -e ".[osw]"
curbshade-validate-osw dataset.zip --schema /path/to/opensidewalks.schema.json \
  --schema-sha256 <pinned-digest>
```

The supported contract is [OpenSidewalks/OpenSidewalks-Schema](https://github.com/OpenSidewalks/OpenSidewalks-Schema), currently schema 0.3. For production, pin the exact schema bytes with `--schema-sha256`. The validator also rejects unsafe ZIP member paths, encrypted entries, excessive uncompressed sizes and extreme compression ratios.

This is **schema validation plus ZIP-safety checking**. It does not claim parity with auxiliary validators that add cross-file topology or geometry-mapping checks.

## Licensing

Code in this repo is MIT. OpenStreetMap-derived databases are subject to ODbL. This repository does not copy the OpenSidewalks schema; it only documents and accepts a small compatible subset of common pedestrian attributes.


## Installed commands

The wheel exposes the production-facing commands directly:

```bash
curbshade-validate graph.json
curbshade-profile graph.json --json
curbshade-schema --out network.schema.json
curbshade-fetch-osm "Madrid, Spain" --out madrid.json      # install [osm]
curbshade-validate-osw dataset.zip --schema osw.schema.json # install [osw]
```

The legacy files under `scripts/` remain thin wrappers for source-checkout compatibility.

## Maintenance and releases

- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Release checklist](docs/RELEASE.md)
- [Production data pipeline](docs/PRODUCTION.md)
- [Security policy](SECURITY.md)

Release builds verify the versioned network schema, build and check the distributions, install the wheel in an isolated environment and produce SHA-256 checksums.
