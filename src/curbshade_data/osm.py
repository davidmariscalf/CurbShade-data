from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

SURFACE_SCORE = {
    "asphalt": 0.95,
    "concrete": 0.9,
    "paving_stones": 0.75,
    "compacted": 0.6,
    "gravel": 0.35,
    "ground": 0.25,
    "sand": 0.1,
}


def first(value: Any) -> Any:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def number(value: Any) -> float | None:
    value = first(value)
    if value is None:
        return None
    text = str(value).strip().lower().replace("%", "")
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def convert_place(place: str) -> dict[str, Any]:
    if not place.strip():
        raise ValueError("place must not be empty")

    try:
        import osmnx as ox
    except ImportError as exc:
        raise RuntimeError(
            'OSM acquisition requires Python 3.11+ and: pip install "curbshade-data[osm]"'
        ) from exc

    graph = ox.graph_from_place(place, network_type="walk", simplify=True)
    nodes = [{"id": str(node)} for node in graph.nodes]
    edges = []
    skipped_invalid_length = 0

    for u, v, _key, data in graph.edges(keys=True, data=True):
        length = number(data.get("length"))
        if length is None or length <= 0:
            skipped_invalid_length += 1
            continue

        surface = first(data.get("surface"))
        width = number(data.get("width"))
        incline = number(data.get("incline"))
        kerb = number(data.get("kerb:height"))
        edges.append({
            "u": str(u),
            "v": str(v),
            "length_m": length,
            "slope_pct": incline,
            "curb_cm": None if kerb is None else kerb * 100.0 if kerb < 1 else kerb,
            "width_m": width if width is None or width > 0 else None,
            "surface_score": SURFACE_SCORE.get(str(surface).lower()) if surface is not None else None,
            "shade_fraction": None,
            "crossing_risk": 0.4 if first(data.get("highway")) == "crossing" else None,
            "source": "OpenStreetMap",
        })

    return {
        "schema_version": "curbshade-network/1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "name": "OpenStreetMap",
            "query": place,
            "osmnx_version": getattr(ox, "__version__", "unknown"),
            "attribution": "© OpenStreetMap contributors",
        },
        "quality": {"skipped_edges_invalid_length": skipped_invalid_length},
        "nodes": nodes,
        "edges": edges,
    }
