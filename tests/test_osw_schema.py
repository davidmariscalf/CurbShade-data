from __future__ import annotations

import json
import zipfile

import pytest

pytest.importorskip("jsonschema_rs")

from curbshade_data.osw import validate_dataset


SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["type", "features"],
    "properties": {
        "type": {"const": "FeatureCollection"},
        "features": {"type": "array"},
    },
    "additionalProperties": True,
}


def _write_schema(path):
    path.write_text(json.dumps(SCHEMA), encoding="utf-8")


def _write_zip(path, filename: str, payload: dict):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(filename, json.dumps(payload))


def test_osw_schema_validation_accepts_valid_geojson(tmp_path):
    schema = tmp_path / "schema.json"
    dataset = tmp_path / "dataset.zip"
    _write_schema(schema)
    _write_zip(dataset, "nodes.geojson", {"type": "FeatureCollection", "features": []})

    result = validate_dataset(dataset, schema_path=schema)

    assert result["valid"] is True
    assert result["validation_level"] == "schema"
    assert result["geojson_files"] == 1


def test_osw_schema_validation_rejects_invalid_geojson(tmp_path):
    schema = tmp_path / "schema.json"
    dataset = tmp_path / "dataset.zip"
    _write_schema(schema)
    _write_zip(dataset, "nodes.geojson", {"type": "FeatureCollection"})

    result = validate_dataset(dataset, schema_path=schema)

    assert result["valid"] is False
    assert any("nodes.geojson" in error for error in result["errors"])


def test_osw_validation_rejects_unsafe_zip_paths(tmp_path):
    schema = tmp_path / "schema.json"
    dataset = tmp_path / "dataset.zip"
    _write_schema(schema)
    _write_zip(dataset, "../nodes.geojson", {"type": "FeatureCollection", "features": []})

    result = validate_dataset(dataset, schema_path=schema)

    assert result["valid"] is False
    assert any("unsafe ZIP member path" in error for error in result["errors"])
