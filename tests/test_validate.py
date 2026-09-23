from __future__ import annotations

import math

import pytest

from curbshade_data.validation import finite_number, validate_graph


def graph():
    return {
        "schema_version": "curbshade-network/1",
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


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1, 1.0),
        ("1.5", 1.5),
        (True, None),
        (None, None),
        ("not-a-number", None),
        (math.nan, None),
        (math.inf, None),
    ],
)
def test_finite_number(value, expected):
    assert finite_number(value) == expected


def test_valid_graph_passes():
    assert validate_graph(graph()) == []


def test_root_and_collection_shape_errors_are_explicit():
    assert validate_graph([]) == ["graph root must be an object"]

    data = {
        "schema_version": "wrong",
        "nodes": "not-a-list",
        "edges": {"not": "a-list"},
    }
    errors = validate_graph(data)
    assert "schema_version must be 'curbshade-network/1'" in errors
    assert "nodes must be an array" in errors
    assert "edges must be an array" in errors


def test_empty_graph_is_rejected():
    errors = validate_graph({
        "schema_version": "curbshade-network/1",
        "nodes": [],
        "edges": [],
    })
    assert "nodes must not be empty" in errors
    assert "edges must not be empty" in errors


def test_node_validation_covers_non_objects_ids_and_duplicates():
    data = graph()
    data["nodes"] = [
        "bad",
        {},
        {"id": "   "},
        {"id": "A"},
        {"id": " A "},
    ]
    errors = validate_graph(data)

    assert "node 0: must be an object" in errors
    assert "node 1: id must be a non-empty string" in errors
    assert "node 2: id must be a non-empty string" in errors
    assert "node 4: duplicate id 'A'" in errors


def test_edge_shape_endpoint_and_length_errors_are_explicit():
    data = graph()
    data["edges"] = [
        "bad",
        {"u": "", "v": "missing", "length_m": 0},
        {"u": None, "v": "B", "length_m": "not-a-number"},
    ]
    errors = validate_graph(data)

    assert "edge 0: must be an object" in errors
    assert "edge 1: u must be a non-empty string" in errors
    assert "edge 1: unknown endpoint v='missing'" in errors
    assert "edge 1: length_m must be finite and > 0" in errors
    assert "edge 2: u must be a non-empty string" in errors
    assert "edge 2: length_m must be finite and > 0" in errors


@pytest.mark.parametrize(
    ("field", "value", "needle"),
    [
        ("shade_fraction", -0.1, "shade_fraction"),
        ("shade_fraction", 1.1, "shade_fraction"),
        ("surface_score", "bad", "surface_score"),
        ("crossing_risk", math.inf, "crossing_risk"),
        ("curb_cm", -1, "curb_cm"),
        ("curb_cm", "bad", "curb_cm"),
        ("width_m", 0, "width_m"),
        ("width_m", -1, "width_m"),
        ("width_m", math.nan, "width_m"),
        ("slope_pct", math.inf, "slope_pct"),
        ("slope_pct", "bad", "slope_pct"),
    ],
)
def test_accessibility_field_validation(field, value, needle):
    data = graph()
    data["edges"][0][field] = value
    errors = validate_graph(data)
    assert any(needle in error for error in errors)


def test_optional_null_accessibility_values_are_accepted():
    data = graph()
    for field in (
        "shade_fraction",
        "surface_score",
        "crossing_risk",
        "curb_cm",
        "width_m",
        "slope_pct",
    ):
        data["edges"][0][field] = None
    assert validate_graph(data) == []


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


def test_schema_version_is_required():
    data = graph()
    del data["schema_version"]
    errors = validate_graph(data)
    assert any("schema_version" in error for error in errors)
