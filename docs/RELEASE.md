# Release checklist

Current package version: **0.2.0**.

A release is acceptable only when Python 3.10–3.14 core jobs, installed CLI/schema checks, OSMnx integration and OpenSidewalks validation jobs are green.

## Build

```bash
python -m pip install "build>=1.2,<2" "twine>=5,<7"
python -m build
python -m twine check dist/*
```

For a tag-based build, the tag must exactly match the package version, for example `v0.2.0`. The Release build workflow enforces this, installs the built wheel into a clean virtual environment, validates the packaged schema and demo graph through installed CLIs, verifies the changelog contains the released version, verifies SHA-256 checksums, and only then uploads the distributions.

Changes to the release workflow, package metadata or changelog also execute the release build on pull requests so release breakage is detected before tagging.

Before release, verify that `curbshade-fetch-osm --help` and `curbshade-validate-osw --help` are present in the built wheel, that the `core`, `osm`, and `osw` dependency-audit jobs are green, that OSW tests validate against an explicit Draft 7 schema, and that production deployments pin the expected schema SHA-256. A schema-breaking network change requires a new `schema_version`, not a silent edit to `curbshade-network/1`.

CI also enforces branch coverage at or above 84% (measured baseline: 87%). A release must not lower this gate to make CI pass; add tests or justify a deliberate contract change instead.
