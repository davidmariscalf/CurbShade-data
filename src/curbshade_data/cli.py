from __future__ import annotations

import argparse
import json
import sys
from importlib.resources import files as resource_files
from pathlib import Path

from .coverage import profile_coverage
from .osm import convert_place
from .osw import validate_dataset
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


def schema_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print or write the CurbShade network JSON Schema")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    content = resource_files("curbshade_data").joinpath("network.schema.json").read_text(encoding="utf-8")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        print(f"curbshade schema: wrote={args.out}")
    else:
        print(content)
    return 0


def fetch_osm_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and normalize an OpenStreetMap walking graph")
    parser.add_argument("place")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        data = convert_place(args.place)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"OSM acquisition failed: {exc}", file=sys.stderr)
        return 2
    print(args.out)
    return 0


def validate_osw_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate OSW GeoJSON in a ZIP against an explicit OpenSidewalks Draft 7 schema."
    )
    parser.add_argument("dataset_zip", type=Path)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--max-errors", type=int, default=20)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        payload = validate_dataset(
            args.dataset_zip,
            schema_path=args.schema,
            max_errors=args.max_errors,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"OpenSidewalks validation failed: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(payload, indent=2, default=str))
    elif payload["valid"]:
        print("OK: OSW GeoJSON passes schema validation and ZIP safety checks")
    else:
        for error in payload["errors"]:
            print(error, file=sys.stderr)
    return 0 if payload["valid"] else 1
