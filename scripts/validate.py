from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

FIELDS_01 = ("shade_fraction", "surface_score", "crossing_risk")
POSITIVE_FIELDS = ("length_m", "width_m")
NONNEGATIVE_FIELDS = ("curb_cm",)


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["graph root must be an object"]

    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list):
        errors.append("nodes must be an array")
        nodes = []
    if not isinstance(edges, list):
        errors.append("edges must be an array")
        edges = []

    node_ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"node {index}: must be an object")
            continue
        raw_id = node.get("id")
        if not isinstance(raw_id, str) or not raw_id.strip():
            errors.append(f"node {index}: id must be a non-empty string")
            continue
        node_id = raw_id.strip()
        if node_id in node_ids:
            errors.append(f"node {index}: duplicate id {node_id!r}")
        node_ids.add(node_id)

    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edge {i}: must be an object")
            continue

        for endpoint in ("u", "v"):
            value = edge.get(endpoint)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"edge {i}: {endpoint} must be a non-empty string")
            elif value.strip() not in node_ids:
                errors.append(f"edge {i}: unknown endpoint {endpoint}={value!r}")

        length = _finite_number(edge.get("length_m"))
        if length is None or length <= 0:
            errors.append(f"edge {i}: length_m must be finite and > 0")

        for field in FIELDS_01:
            value = edge.get(field)
            if value is None:
                continue
            number = _finite_number(value)
            if number is None or not 0 <= number <= 1:
                errors.append(f"edge {i}: {field} must be finite and in [0,1] or null")

        for field in NONNEGATIVE_FIELDS:
            value = edge.get(field)
            if value is None:
                continue
            number = _finite_number(value)
            if number is None or number < 0:
                errors.append(f"edge {i}: {field} must be finite and >= 0 or null")

        width = edge.get("width_m")
        if width is not None:
            number = _finite_number(width)
            if number is None or number <= 0:
                errors.append(f"edge {i}: width_m must be finite and > 0 or null")

        slope = edge.get("slope_pct")
        if slope is not None and _finite_number(slope) is None:
            errors.append(f"edge {i}: slope_pct must be finite or null")

    return errors


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

    errors = validate(data)
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
