from __future__ import annotations

import argparse
import json
from pathlib import Path

from curbshade_data.coverage import profile_coverage


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report how complete accessibility and shade attributes are in a CurbShade graph."
    )
    parser.add_argument("graph", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    with args.graph.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

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


if __name__ == "__main__":
    raise SystemExit(main())
