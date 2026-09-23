from __future__ import annotations

from curbshade_data.coverage import profile_coverage


def test_profile_coverage_counts_edges_and_length_weighting():
    data = {
        "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
        "edges": [
            {
                "length_m": 10,
                "slope_pct": 1,
                "curb_cm": 0,
                "width_m": 1.5,
                "surface_score": 0.8,
                "shade_fraction": 0.5,
                "crossing_risk": 0.1,
            },
            {
                "length_m": 30,
                "slope_pct": None,
                "curb_cm": 5,
                "width_m": None,
                "surface_score": 0.7,
                "shade_fraction": None,
                "crossing_risk": 0.2,
            },
            "ignored",
        ],
    }

    result = profile_coverage(data)

    assert result["nodes"] == 3
    assert result["edges"] == 2
    assert result["total_length_m"] == 40.0
    assert result["fields"]["slope_pct"] == {
        "known_edges": 1,
        "edge_coverage_pct": 50.0,
        "known_length_m": 10.0,
        "length_coverage_pct": 25.0,
    }
    assert result["fields"]["curb_cm"]["edge_coverage_pct"] == 100.0
    assert result["fields"]["curb_cm"]["length_coverage_pct"] == 100.0


def test_profile_coverage_treats_invalid_values_as_unknown_and_bad_lengths_as_zero():
    data = {
        "nodes": [],
        "edges": [
            {
                "length_m": "not-a-number",
                "slope_pct": True,
                "curb_cm": float("nan"),
                "width_m": "wide",
                "surface_score": float("inf"),
                "shade_fraction": None,
                "crossing_risk": {},
            },
            {"length_m": -5, "slope_pct": 2},
        ],
    }

    result = profile_coverage(data)

    assert result["edges"] == 2
    assert result["total_length_m"] == 0.0
    assert result["fields"]["slope_pct"]["known_edges"] == 1
    assert result["fields"]["slope_pct"]["edge_coverage_pct"] == 50.0
    assert result["fields"]["slope_pct"]["length_coverage_pct"] == 0.0
    for field in ("curb_cm", "width_m", "surface_score", "shade_fraction", "crossing_risk"):
        assert result["fields"][field]["known_edges"] == 0
        assert result["fields"][field]["length_coverage_pct"] == 0.0


def test_profile_coverage_handles_empty_graph():
    result = profile_coverage({"nodes": [], "edges": []})

    assert result["edges"] == 0
    assert result["total_length_m"] == 0.0
    for stats in result["fields"].values():
        assert stats["edge_coverage_pct"] == 0.0
        assert stats["length_coverage_pct"] == 0.0
