from __future__ import annotations
import argparse, json, sys

FIELDS_01 = ("shade_fraction", "surface_score", "crossing_risk")


def validate(data):
    errors = []
    node_ids = {str(n.get("id")) for n in data.get("nodes", []) if "id" in n}
    for i, e in enumerate(data.get("edges", [])):
        for endpoint in ("u", "v"):
            if str(e.get(endpoint)) not in node_ids:
                errors.append(f"edge {i}: unknown endpoint {endpoint}={e.get(endpoint)!r}")
        try:
            if float(e["length_m"]) <= 0:
                errors.append(f"edge {i}: length_m must be > 0")
        except Exception:
            errors.append(f"edge {i}: invalid or missing length_m")
        for field in FIELDS_01:
            value = e.get(field)
            if value is not None:
                try:
                    x = float(value)
                    if not 0 <= x <= 1:
                        errors.append(f"edge {i}: {field} must be in [0,1]")
                except Exception:
                    errors.append(f"edge {i}: {field} must be numeric or null")
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("graph")
    args = p.parse_args()
    with open(args.graph, "r", encoding="utf-8") as f:
        data = json.load(f)
    errors = validate(data)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
