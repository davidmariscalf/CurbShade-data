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

## Optional OSM acquisition

Install:

```bash
pip install ".[osm]"
python scripts/fetch_osm.py "Arganda del Rey, Spain" --out arganda.json
```

OSM data is useful for topology but often lacks curb, width, slope and surface fields. Those remain `null`; they are **not** filled with optimistic defaults.

## Licensing

Code in this repo is MIT. OpenStreetMap-derived databases are subject to ODbL. This repository does not copy the OpenSidewalks schema; it only documents and accepts a small compatible subset of common pedestrian attributes.
