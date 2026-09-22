from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an OpenSidewalks dataset ZIP with the official TDEI library."
    )
    parser.add_argument("dataset_zip")
    parser.add_argument("--max-errors", type=int, default=20)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if args.max_errors < 1:
        print("max-errors must be positive", file=sys.stderr)
        return 2

    try:
        from python_osw_validation import OSWValidation
    except ImportError:
        print(
            'OpenSidewalks validation requires: pip install -e ".[osw]"',
            file=sys.stderr,
        )
        return 2

    try:
        result = OSWValidation(zipfile_path=args.dataset_zip).validate(
            max_errors=args.max_errors
        )
    except (OSError, ValueError) as exc:
        print(f"OSW validation failed to start: {exc}", file=sys.stderr)
        return 2

    payload = {
        "valid": bool(result.is_valid),
        "errors": list(result.errors),
        "issues": list(result.issues),
    }
    if args.as_json:
        print(json.dumps(payload, indent=2, default=str))
    elif result.is_valid:
        print("OK: OpenSidewalks dataset is valid")
    else:
        for error in result.errors:
            print(error, file=sys.stderr)
    return 0 if result.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
