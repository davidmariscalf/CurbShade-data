from __future__ import annotations

import math
from typing import Any

FIELDS_01 = ("shade_fraction", "surface_score", "crossing_risk")
NONNEGATIVE_FIELDS = ("curb_cm",)


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def validate_graph(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["graph root must be an object"]

    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list):
        errors.append("nodes must be an array")
        nodes = []
    elif not nodes:
        errors.append("nodes must not be empty")
    if not isinstance(edges, list):
        errors.append("edges must be an array")
        edges = []
    elif not edges:
        errors.append("edges must not be empty")

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

    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edge {index}: must be an object")
            continue

        for endpoint in ("u", "v"):
            value = edge.get(endpoint)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"edge {index}: {endpoint} must be a non-empty string")
            elif value.strip() not in node_ids:
                errors.append(f"edge {index}: unknown endpoint {endpoint}={value!r}")

        length = finite_number(edge.get("length_m"))
        if length is None or length <= 0:
            errors.append(f"edge {index}: length_m must be finite and > 0")

        for field in FIELDS_01:
            value = edge.get(field)
            if value is None:
                continue
            number = finite_number(value)
            if number is None or not 0 <= number <= 1:
                errors.append(f"edge {index}: {field} must be finite and in [0,1] or null")

        for field in NONNEGATIVE_FIELDS:
            value = edge.get(field)
            if value is None:
                continue
            number = finite_number(value)
            if number is None or number < 0:
                errors.append(f"edge {index}: {field} must be finite and >= 0 or null")

        width = edge.get("width_m")
        if width is not None:
            number = finite_number(width)
            if number is None or number <= 0:
                errors.append(f"edge {index}: width_m must be finite and > 0 or null")

        slope = edge.get("slope_pct")
        if slope is not None and finite_number(slope) is None:
            errors.append(f"edge {index}: slope_pct must be finite or null")

    return errors
