"""Acquire a baseline walking graph from OpenStreetMap using OSMnx.

This deliberately preserves unknown accessibility values as None.
"""
from __future__ import annotations
import argparse, json
import osmnx as ox

SURFACE_SCORE = {
    "asphalt": 0.95,
    "concrete": 0.9,
    "paving_stones": 0.75,
    "compacted": 0.6,
    "gravel": 0.35,
    "ground": 0.25,
    "sand": 0.1,
}


def first(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def number(value):
    value = first(value)
    if value is None:
        return None
    text = str(value).strip().lower().replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None


def convert(place: str):
    g = ox.graph_from_place(place, network_type="walk", simplify=True)
    nodes = [{"id": str(n)} for n in g.nodes]
    edges = []
    for u, v, k, d in g.edges(keys=True, data=True):
        surface = first(d.get("surface"))
        width = number(d.get("width"))
        incline = number(d.get("incline"))
        kerb = number(d.get("kerb:height"))
        edges.append({
            "u": str(u),
            "v": str(v),
            "length_m": float(d.get("length", 0.0)),
            "slope_pct": incline,
            "curb_cm": None if kerb is None else kerb * 100.0 if kerb < 1 else kerb,
            "width_m": width,
            "surface_score": SURFACE_SCORE.get(str(surface).lower()) if surface is not None else None,
            "shade_fraction": None,
            "crossing_risk": 0.4 if first(d.get("highway")) == "crossing" else None,
            "source": "OpenStreetMap",
        })
    return {"nodes": nodes, "edges": edges, "attribution": "© OpenStreetMap contributors"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("place")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    data = convert(args.place)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(args.out)


if __name__ == "__main__":
    main()
