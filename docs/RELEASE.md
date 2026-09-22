# Release checklist

Current package version: **0.2.0**.

A release is acceptable only when Python 3.10–3.14 core jobs, installed CLI/schema checks, OSMnx integration and OpenSidewalks validation jobs are green.

## Build

```bash
python -m pip install "build>=1.2,<2" "twine>=5,<7"
python -m build
python -m twine check dist/*
```

For a tag-based build, the tag must exactly match the package version, for example `v0.2.0`. The Release build workflow enforces this and uploads verified distributions plus SHA-256 checksums.

Do not combine the `osm` and `osw` extras in one environment while their GeoPandas constraints remain incompatible. A schema-breaking network change requires a new `schema_version`, not a silent edit to `curbshade-network/1`.
