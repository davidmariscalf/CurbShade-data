from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile

import pytest

from curbshade_data.osw import validate_dataset

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("jsonschema_rs") is None,
    reason="OSW extra is not installed",
)


SCHEMA = {
    "$id": "https://sidewalks.washington.edu/opensidewalks/0.3/schema.json",
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


def test_osw_schema_digest_can_be_pinned(tmp_path):
    schema = tmp_path / "schema.json"
    dataset = tmp_path / "dataset.zip"
    _write_schema(schema)
    _write_zip(dataset, "nodes.geojson", {"type": "FeatureCollection", "features": []})
    digest = hashlib.sha256(schema.read_bytes()).hexdigest()

    result = validate_dataset(
        dataset,
        schema_path=schema,
        expected_schema_sha256=digest,
    )
    assert result["valid"] is True
    assert result["schema_sha256"] == digest

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        validate_dataset(
            dataset,
            schema_path=schema,
            expected_schema_sha256="0" * 64,
        )


def test_osw_validation_rejects_wrong_schema_identity(tmp_path):
    schema = tmp_path / "schema.json"
    dataset = tmp_path / "dataset.zip"
    wrong = dict(SCHEMA)
    wrong["$id"] = "https://example.invalid/not-osw.json"
    schema.write_text(json.dumps(wrong), encoding="utf-8")
    _write_zip(dataset, "nodes.geojson", {"type": "FeatureCollection", "features": []})

    with pytest.raises(ValueError, match="must declare \\$id"):
        validate_dataset(dataset, schema_path=schema)


def test_osw_validation_rejects_nonstandard_dataset_filename(tmp_path):
    schema = tmp_path / "schema.json"
    dataset = tmp_path / "dataset.zip"
    _write_schema(schema)
    _write_zip(dataset, "random.geojson", {"type": "FeatureCollection", "features": []})

    result = validate_dataset(dataset, schema_path=schema)

    assert result["valid"] is False
    assert any("unsupported OSW GeoJSON filename" in error for error in result["errors"])
