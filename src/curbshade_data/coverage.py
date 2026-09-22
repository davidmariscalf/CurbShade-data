from __future__ import annotations

import math
from typing import Any

FIELDS = (
    "slope_pct",
    "curb_cm",
    "width_m",
    "surface_score",
    "shade_fraction",
    "crossing_risk",
)


def _length(edge: dict[str, Any]) -> float:
    try:
        value = float(edge.get("length_m", 0.0))
    except (TypeError, ValueError):
        return 0.0
    return value if math.isfinite(value) and value > 0 else 0.0


def _known(edge: dict[str, Any], field: str) -> bool:
    value = edge.get(field)
    if value is None or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def profile_coverage(data: dict[str, Any]) -> dict[str, Any]:
    edges = [edge for edge in data.get("edges", []) if isinstance(edge, dict)]
    total_edges = len(edges)
    total_length = sum(_length(edge) for edge in edges)

    fields: dict[str, Any] = {}
    for field in FIELDS:
        known_edges = sum(_known(edge, field) for edge in edges)
        known_length = sum(_length(edge) for edge in edges if _known(edge, field))
        fields[field] = {
            "known_edges": known_edges,
            "edge_coverage_pct": round((known_edges / total_edges * 100.0) if total_edges else 0.0, 2),
            "known_length_m": round(known_length, 2),
            "length_coverage_pct": round((known_length / total_length * 100.0) if total_length else 0.0, 2),
        }

    return {
        "nodes": len(data.get("nodes", [])),
        "edges": total_edges,
        "total_length_m": round(total_length, 2),
        "fields": fields,
    }
