from __future__ import annotations

import json
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

MAX_SCHEMA_BYTES = 5 * 1024 * 1024
MAX_ZIP_FILES = 64
MAX_MEMBER_BYTES = 25 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200.0


def _load_json(path: Path, *, max_bytes: int, label: str) -> Any:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ValueError(f"cannot stat {label}: {exc}") from exc
    if size > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} bytes")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid {label} JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts


def validate_dataset(
    dataset_zip: str | Path,
    *,
    schema_path: str | Path,
    max_errors: int = 20,
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

    schema = _load_json(Path(schema_path), max_bytes=MAX_SCHEMA_BYTES, label="OSW schema")
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

            for info in members:
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
                except RuntimeError as exc:
                    add_error(f"cannot read {info.filename}: {exc}", info.filename)
                    continue

                for err in validator.iter_errors(data):
                    message = getattr(err, "message", None) or str(err)
                    add_error(f"{info.filename}: {message}", info.filename)
                    if len(errors) >= max_errors:
                        break
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"cannot read OSW dataset ZIP: {exc}") from exc

    if geojson_count == 0:
        add_error("dataset ZIP contains no .geojson files")

    return {
        "valid": not errors,
        "validation_level": "schema",
        "schema": str(schema_path),
        "geojson_files": geojson_count,
        "errors": errors,
        "issues": issues,
        "truncated": len(errors) >= max_errors,
    }
