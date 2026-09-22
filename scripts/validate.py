from __future__ import annotations

import argparse
import json
import sys

from curbshade_data.validation import validate_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a normalized CurbShade graph")
    parser.add_argument("graph")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--max-errors", type=int, default=100)
    args = parser.parse_args()
    if args.max_errors < 1:
        print("max-errors must be positive", file=sys.stderr)
        return 2

    try:
        with open(args.graph, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"cannot read graph: {exc}", file=sys.stderr)
        return 2

    errors = validate_graph(data)
    shown = errors[: args.max_errors]
    if args.as_json:
        print(json.dumps({
            "valid": not errors,
            "error_count": len(errors),
            "errors": shown,
            "truncated": len(errors) > len(shown),
        }, indent=2))
    elif errors:
        print("\n".join(shown), file=sys.stderr)
        if len(errors) > len(shown):
            print(f"... {len(errors) - len(shown)} more errors", file=sys.stderr)
    else:
        print(f"OK: {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
