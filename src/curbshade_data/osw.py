from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

MAX_SCHEMA_BYTES = 5 * 1024 * 1024
MAX_ZIP_FILES = 64
MAX_MEMBER_BYTES = 25 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200.0
OSW_03_SCHEMA_ID = "https://sidewalks.washington.edu/opensidewalks/0.3/schema.json"
DRAFT7_SCHEMA_URI = "http://json-schema.org/draft-07/schema#"
OSW_DATASET_TYPES = {"edges", "lines", "nodes", "points", "polygons", "zones"}


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and "\\" not in name
        and not path.is_absolute()
        and ".." not in path.parts
    )


def _supported_geojson_name(name: str) -> bool:
    base = PurePosixPath(name).name
    parts = base.split(".")
    if len(parts) < 2 or parts[-1] != "geojson":
        return False
    if parts[-2] in OSW_DATASET_TYPES:
        return True
    return len(parts) >= 3 and parts[-2] == "OSW" and parts[-3] in OSW_DATASET_TYPES


def validate_dataset(
    dataset_zip: str | Path,
    *,
    schema_path: str | Path,
    max_errors: int = 20,
    expected_schema_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate OSW GeoJSON files against an explicit Draft 7 schema.

    This intentionally performs schema validation and ZIP hygiene only. It does
    not claim parity with auxiliary validators that add cross-file geometry or
    topology checks.
    """
    if max_errors < 1:
        raise ValueError("max_errors must be positive")

    try:
        import jsonschema_rs
    except ImportError as exc:
        raise RuntimeError(
            'OpenSidewalks schema validation requires: pip install "curbshade-data[osw]"'
        ) from exc

    schema_file = Path(schema_path)
    try:
        schema_size = schema_file.stat().st_size
    except OSError as exc:
        raise ValueError(f"cannot stat OSW schema: {exc}") from exc
    if schema_size > MAX_SCHEMA_BYTES:
        raise ValueError(f"OSW schema exceeds {MAX_SCHEMA_BYTES} bytes")
    try:
        schema_bytes = schema_file.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read OSW schema: {exc}") from exc
    schema_sha256 = hashlib.sha256(schema_bytes).hexdigest()
    if expected_schema_sha256 is not None:
        expected = expected_schema_sha256.lower().strip()
        if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
            raise ValueError("expected_schema_sha256 must be a 64-character hexadecimal digest")
        if schema_sha256 != expected:
            raise ValueError(
                f"OSW schema SHA-256 mismatch: expected {expected}, got {schema_sha256}"
            )
    try:
        schema = json.loads(schema_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("OSW schema must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid OSW schema JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(schema, dict):
        raise ValueError("OSW schema root must be an object")
    if schema.get("$schema") != DRAFT7_SCHEMA_URI:
        raise ValueError(f"OSW schema must declare {DRAFT7_SCHEMA_URI!r}")
    if schema.get("$id") != OSW_03_SCHEMA_ID:
        raise ValueError(f"OSW schema must declare $id {OSW_03_SCHEMA_ID!r}")

    try:
        validator = jsonschema_rs.Draft7Validator(schema)
    except Exception as exc:
        raise ValueError(f"invalid Draft 7 OSW schema: {exc}") from exc

    errors: list[str] = []
    issues: list[dict[str, Any]] = []
    geojson_count = 0
    total_uncompressed = 0

    def add_error(message: str, filename: str | None = None) -> None:
        if len(errors) >= max_errors:
            return
        errors.append(message)
        issue: dict[str, Any] = {"error_message": [message]}
        if filename is not None:
            issue["filename"] = filename
        issues.append(issue)

    try:
        with zipfile.ZipFile(dataset_zip) as archive:
            members = [info for info in archive.infolist() if not info.is_dir()]
            if len(members) > MAX_ZIP_FILES:
                add_error(f"dataset contains more than {MAX_ZIP_FILES} files")

            for info in members[:MAX_ZIP_FILES]:
                if len(errors) >= max_errors:
                    break
                if not _safe_member_name(info.filename):
                    add_error(f"unsafe ZIP member path: {info.filename!r}", info.filename)
                    continue
                if info.flag_bits & 0x1:
                    add_error(f"encrypted ZIP member is not supported: {info.filename}", info.filename)
                    continue
                if info.file_size > MAX_MEMBER_BYTES:
                    add_error(
                        f"{info.filename} exceeds {MAX_MEMBER_BYTES} uncompressed bytes",
                        info.filename,
                    )
                    continue

                total_uncompressed += info.file_size
                if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                    add_error(
                        f"dataset exceeds {MAX_TOTAL_UNCOMPRESSED_BYTES} uncompressed bytes"
                    )
                    break

                if info.file_size > 0:
                    ratio = info.file_size / max(info.compress_size, 1)
                    if ratio > MAX_COMPRESSION_RATIO:
                        add_error(
                            f"{info.filename} exceeds the maximum compression ratio "
                            f"of {MAX_COMPRESSION_RATIO:g}",
                            info.filename,
                        )
                        continue

                if not info.filename.lower().endswith(".geojson"):
                    continue
                if not _supported_geojson_name(info.filename):
                    add_error(
                        f"unsupported OSW GeoJSON filename: {info.filename}",
                        info.filename,
                    )
                    continue
                geojson_count += 1
                try:
                    raw = archive.read(info)
                    data = json.loads(raw.decode("utf-8"))
                except UnicodeDecodeError:
                    add_error(f"{info.filename} must be UTF-8", info.filename)
                    continue
                except json.JSONDecodeError as exc:
                    add_error(
                        f"invalid JSON in {info.filename} at line {exc.lineno}, "
                        f"column {exc.colno}: {exc.msg}",
                        info.filename,
                    )
                    continue
                except RecursionError:
                    add_error(f"JSON nesting is too deep in {info.filename}", info.filename)
                    continue
                except RuntimeError as exc:
                    add_error(f"cannot read {info.filename}: {exc}", info.filename)
                    continue

                try:
                    for err in validator.iter_errors(data):
                        message = getattr(err, "message", None) or str(err)
                        add_error(f"{info.filename}: {message}", info.filename)
                        if len(errors) >= max_errors:
                            break
                except Exception as exc:
                    add_error(
                        f"{info.filename}: schema validation failed safely: {exc}",
                        info.filename,
                    )
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"cannot read OSW dataset ZIP: {exc}") from exc

    if geojson_count == 0:
        add_error("dataset ZIP contains no .geojson files")

    return {
        "valid": not errors,
        "validation_level": "schema",
        "schema": str(schema_path),
        "schema_sha256": schema_sha256,
        "geojson_files": geojson_count,
        "errors": errors,
        "issues": issues,
        "truncated": len(errors) >= max_errors,
    }
