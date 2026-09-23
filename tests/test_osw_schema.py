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


def test_osw_validation_rejects_invalid_limits_and_digest(tmp_path):
    schema = tmp_path / "schema.json"
    dataset = tmp_path / "dataset.zip"
    _write_schema(schema)
    _write_zip(dataset, "nodes.geojson", {"type": "FeatureCollection", "features": []})

    with pytest.raises(ValueError, match="max_errors must be positive"):
        validate_dataset(dataset, schema_path=schema, max_errors=0)

    with pytest.raises(ValueError, match="64-character hexadecimal"):
        validate_dataset(
            dataset,
            schema_path=schema,
            expected_schema_sha256="not-a-digest",
        )


def test_osw_validation_rejects_bad_schema_files(tmp_path, monkeypatch):
    import curbshade_data.osw as module

    missing = tmp_path / "missing.json"
    dataset = tmp_path / "dataset.zip"
    _write_zip(dataset, "nodes.geojson", {"type": "FeatureCollection", "features": []})
    with pytest.raises(ValueError, match="cannot stat OSW schema"):
        validate_dataset(dataset, schema_path=missing)

    too_big = tmp_path / "too-big.json"
    too_big.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(module, "MAX_SCHEMA_BYTES", 1)
    with pytest.raises(ValueError, match="OSW schema exceeds"):
        validate_dataset(dataset, schema_path=too_big)

    monkeypatch.setattr(module, "MAX_SCHEMA_BYTES", 5 * 1024 * 1024)
    non_utf8 = tmp_path / "non-utf8.json"
    non_utf8.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="must be UTF-8"):
        validate_dataset(dataset, schema_path=non_utf8)

    broken = tmp_path / "broken.json"
    broken.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid OSW schema JSON"):
        validate_dataset(dataset, schema_path=broken)

    not_object = tmp_path / "list.json"
    not_object.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="root must be an object"):
        validate_dataset(dataset, schema_path=not_object)

    wrong_draft = dict(SCHEMA)
    wrong_draft["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    wrong_path = tmp_path / "wrong-draft.json"
    wrong_path.write_text(json.dumps(wrong_draft), encoding="utf-8")
    with pytest.raises(ValueError, match="OSW schema must declare"):
        validate_dataset(dataset, schema_path=wrong_path)


def test_osw_validation_rejects_bad_zip_content(tmp_path, monkeypatch):
    import curbshade_data.osw as module

    schema = tmp_path / "schema.json"
    _write_schema(schema)

    no_geojson = tmp_path / "none.zip"
    with zipfile.ZipFile(no_geojson, "w") as archive:
        archive.writestr("README.txt", "hello")
    result = validate_dataset(no_geojson, schema_path=schema)
    assert result["valid"] is False
    assert any("contains no .geojson" in error for error in result["errors"])

    invalid_json = tmp_path / "invalid-json.zip"
    with zipfile.ZipFile(invalid_json, "w") as archive:
        archive.writestr("nodes.geojson", "{")
    result = validate_dataset(invalid_json, schema_path=schema)
    assert any("invalid JSON" in error for error in result["errors"])

    invalid_utf8 = tmp_path / "invalid-utf8.zip"
    with zipfile.ZipFile(invalid_utf8, "w") as archive:
        archive.writestr("nodes.geojson", b"\xff")
    result = validate_dataset(invalid_utf8, schema_path=schema)
    assert any("must be UTF-8" in error for error in result["errors"])

    oversized = tmp_path / "oversized.zip"
    _write_zip(oversized, "nodes.geojson", {"type": "FeatureCollection", "features": []})
    monkeypatch.setattr(module, "MAX_MEMBER_BYTES", 1)
    result = validate_dataset(oversized, schema_path=schema)
    assert any("uncompressed bytes" in error for error in result["errors"])

    monkeypatch.setattr(module, "MAX_MEMBER_BYTES", 25 * 1024 * 1024)
    monkeypatch.setattr(module, "MAX_TOTAL_UNCOMPRESSED_BYTES", 1)
    result = validate_dataset(oversized, schema_path=schema)
    assert any("dataset exceeds" in error for error in result["errors"])


def test_osw_validation_rejects_backslash_paths_and_excess_file_count(tmp_path, monkeypatch):
    import curbshade_data.osw as module

    schema = tmp_path / "schema.json"
    _write_schema(schema)

    unsafe = tmp_path / "unsafe.zip"
    _write_zip(unsafe, "folder\\nodes.geojson", {"type": "FeatureCollection", "features": []})
    result = validate_dataset(unsafe, schema_path=schema)
    assert any("unsafe ZIP member path" in error for error in result["errors"])

    many = tmp_path / "many.zip"
    with zipfile.ZipFile(many, "w") as archive:
        for index in range(3):
            archive.writestr(f"{index}.txt", "x")
    monkeypatch.setattr(module, "MAX_ZIP_FILES", 2)
    result = validate_dataset(many, schema_path=schema)
    assert any("more than 2 files" in error for error in result["errors"])
