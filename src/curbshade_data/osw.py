from __future__ import annotations

from pathlib import Path
from typing import Any


def validate_dataset(dataset_zip: str | Path, max_errors: int = 20) -> dict[str, Any]:
    if max_errors < 1:
        raise ValueError("max_errors must be positive")

    try:
        from python_osw_validation import OSWValidation
    except ImportError as exc:
        raise RuntimeError(
            'OpenSidewalks validation requires: pip install "curbshade-data[osw]"'
        ) from exc

    result = OSWValidation(zipfile_path=str(dataset_zip)).validate(max_errors=max_errors)
    return {
        "valid": bool(result.is_valid),
        "errors": list(result.errors),
        "issues": list(result.issues),
    }
