from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .coverage import profile_coverage
from .validation import validate_graph


def validate_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a normalized CurbShade graph")
    parser.add_argument("graph")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--max-errors", type=int, default=100)
    args = parser.parse_args(argv)
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


def profile_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report accessibility and shade attribute coverage."
    )
    parser.add_argument("graph", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    try:
        with args.graph.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"cannot read graph: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("graph root must be an object", file=sys.stderr)
        return 2

    result = profile_coverage(data)
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print(
        f"CurbShade coverage: {result['nodes']} nodes, {result['edges']} edges, "
        f"{result['total_length_m']:.2f} m"
    )
    print(f"{'field':18} {'edges known':>12} {'edge %':>9} {'length %':>10}")
    for field, stats in result["fields"].items():
        print(
            f"{field:18} "
            f"{stats['known_edges']:>12} "
            f"{stats['edge_coverage_pct']:>8.2f}% "
            f"{stats['length_coverage_pct']:>9.2f}%"
        )
    return 0
