from __future__ import annotations

from curbshade_data.validation import validate_graph


def graph():
    return {
        "nodes": [{"id": "A"}, {"id": "B"}],
        "edges": [{
            "u": "A",
            "v": "B",
            "length_m": 10,
            "slope_pct": None,
            "curb_cm": 0,
            "width_m": 1.5,
            "surface_score": 0.8,
            "shade_fraction": 0.4,
            "crossing_risk": 0.1,
        }],
    }


def test_valid_graph_passes():
    assert validate_graph(graph()) == []


def test_duplicate_nodes_and_unknown_endpoints_fail():
    data = graph()
    data["nodes"].append({"id": "A"})
    data["edges"][0]["v"] = "missing"
    errors = validate_graph(data)
    assert any("duplicate id" in error for error in errors)
    assert any("unknown endpoint" in error for error in errors)


def test_non_finite_and_invalid_accessibility_values_fail():
    data = graph()
    data["edges"][0]["length_m"] = float("nan")
    data["edges"][0]["shade_fraction"] = float("inf")
    data["edges"][0]["width_m"] = 0
    errors = validate_graph(data)
    assert any("length_m" in error for error in errors)
    assert any("shade_fraction" in error for error in errors)
    assert any("width_m" in error for error in errors)
