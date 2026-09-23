from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from curbshade_data.osm import convert_place, first, number


def test_first_normalizes_scalar_and_list_values():
    assert first("asphalt") == "asphalt"
    assert first(["asphalt", "gravel"]) == "asphalt"
    assert first([]) is None


def test_number_rejects_non_finite_and_parses_percentages():
    assert number(None) is None
    assert number("12%") == 12.0
    assert number(["1.5"]) == 1.5
    assert number("nan") is None
    assert number("inf") is None
    assert number("not-a-number") is None


def test_convert_place_rejects_blank_query():
    with pytest.raises(ValueError, match="must not be empty"):
        convert_place("   ")


def test_convert_place_reports_missing_osmnx(monkeypatch):
    monkeypatch.setitem(sys.modules, "osmnx", None)
    with pytest.raises(RuntimeError, match="curbshade-data\[osm\]"):
        convert_place("Madrid")


def test_convert_place_normalizes_osm_graph(monkeypatch):
    class FakeGraph:
        nodes = [1, 2, 3]

        def edges(self, *, keys, data):
            assert keys is True
            assert data is True
            return [
                (
                    1,
                    2,
                    0,
                    {
                        "length": "12.5",
                        "surface": ["asphalt"],
                        "width": "1.8",
                        "incline": "4%",
                        "kerb:height": "0.08",
                        "highway": "crossing",
                    },
                ),
                (
                    2,
                    3,
                    0,
                    {
                        "length": 7,
                        "surface": "unknown_surface",
                        "width": -1,
                        "kerb:height": 4,
                        "highway": "footway",
                    },
                ),
                (3, 1, 0, {"length": "nan"}),
                (3, 2, 0, {"length": 0}),
            ]

    fake = SimpleNamespace(
        __version__="2.1.1",
        graph_from_place=lambda place, network_type, simplify: FakeGraph(),
    )
    monkeypatch.setitem(sys.modules, "osmnx", fake)

    result = convert_place("Madrid, Spain")

    assert result["schema_version"] == "curbshade-network/1"
    assert result["source"]["query"] == "Madrid, Spain"
    assert result["source"]["osmnx_version"] == "2.1.1"
    assert result["quality"]["skipped_edges_invalid_length"] == 2
    assert result["nodes"] == [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    assert len(result["edges"]) == 2

    crossing = result["edges"][0]
    assert crossing["length_m"] == 12.5
    assert crossing["slope_pct"] == 4.0
    assert crossing["curb_cm"] == 8.0
    assert crossing["width_m"] == 1.8
    assert crossing["surface_score"] == 0.95
    assert crossing["crossing_risk"] == 0.4

    footway = result["edges"][1]
    assert footway["curb_cm"] == 4.0
    assert footway["width_m"] is None
    assert footway["surface_score"] is None
    assert footway["crossing_risk"] is None
