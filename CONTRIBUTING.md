# Contributing to CurbShade-data

Contributions should preserve missing accessibility values as uncertainty. Do not fill unknown curb, slope, width, surface, shade or crossing attributes with optimistic defaults.

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
pytest -q
```

OSMnx and the official OpenSidewalks validator currently require separate environments; see `docs/PRODUCTION.md`.

Data-model changes require tests, provenance considerations and compatibility with the versioned network schema. Breaking changes require a new schema version. When adding a source adapter, document licensing/attribution requirements and keep raw-source assumptions explicit.
