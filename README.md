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
python scripts/fetch_osm.py "Arganda del Rey, Spain" --out arganda.json
python scripts/validate.py arganda.json
```

The normalized artifact records source query, generation time, OSMnx version and OpenStreetMap attribution. OSM data is useful for topology but often lacks curb, width, slope and surface fields. Those remain `null`; they are **not** filled with optimistic defaults.

### OpenSidewalks

For OpenSidewalks interchange data, use the official Taskar Center validator:

```bash
pip install -e ".[osw]"
python scripts/validate_osw.py dataset.zip
```

The supported interchange contract is [OpenSidewalks/OpenSidewalks-Schema](https://github.com/OpenSidewalks/OpenSidewalks-Schema), currently schema 0.3.

**Important:** the current OSMnx and official OSW validator releases have incompatible GeoPandas constraints, so the `osm` and `osw` extras must run in separate virtual environments. CI intentionally verifies them separately. See [docs/PRODUCTION.md](docs/PRODUCTION.md).

## Licensing

Code in this repo is MIT. OpenStreetMap-derived databases are subject to ODbL. This repository does not copy the OpenSidewalks schema; it only documents and accepts a small compatible subset of common pedestrian attributes.
