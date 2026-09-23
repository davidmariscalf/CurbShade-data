from __future__ import annotations

import json
from pathlib import Path

from curbshade_data import cli


def graph() -> dict:
    return {
        "schema_version": "curbshade-network/1",
        "nodes": [{"id": "A"}, {"id": "B"}],
        "edges": [
            {
                "u": "A",
                "v": "B",
                "length_m": 10,
                "slope_pct": 1.0,
                "curb_cm": 0.0,
                "width_m": 1.5,
                "surface_score": 0.8,
                "shade_fraction": 0.4,
                "crossing_risk": 0.1,
            }
        ],
    }


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_validate_main_success_and_json_output(tmp_path, capsys):
    path = tmp_path / "graph.json"
    write_json(path, graph())

    assert cli.validate_main([str(path)]) == 0
    assert "OK: 2 nodes, 1 edges" in capsys.readouterr().out

    assert cli.validate_main([str(path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["errors"] == []


def test_validate_main_reports_invalid_graph_and_limits_output(tmp_path, capsys):
    data = graph()
    data["edges"][0]["v"] = "missing"
    data["edges"][0]["width_m"] = 0
    path = tmp_path / "bad.json"
    write_json(path, data)

    assert cli.validate_main([str(path), "--max-errors", "1"]) == 1
    err = capsys.readouterr().err
    assert "more errors" in err

    assert cli.validate_main([str(path), "--json", "--max-errors", "1"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert payload["truncated"] is True
    assert len(payload["errors"]) == 1


def test_validate_main_handles_bad_arguments_and_bad_json(tmp_path, capsys):
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")

    assert cli.validate_main([str(path)]) == 2
    assert "cannot read graph" in capsys.readouterr().err

    assert cli.validate_main([str(path), "--max-errors", "0"]) == 2
    assert "max-errors must be positive" in capsys.readouterr().err


def test_profile_main_text_and_json(tmp_path, capsys):
    path = tmp_path / "graph.json"
    write_json(path, graph())

    assert cli.profile_main([str(path)]) == 0
    out = capsys.readouterr().out
    assert "CurbShade coverage: 2 nodes, 1 edges, 10.00 m" in out
    assert "shade_fraction" in out

    assert cli.profile_main([str(path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["edges"] == 1
    assert payload["fields"]["shade_fraction"]["edge_coverage_pct"] == 100.0


def test_profile_main_rejects_non_object_and_missing_file(tmp_path, capsys):
    path = tmp_path / "list.json"
    write_json(path, [])

    assert cli.profile_main([str(path)]) == 2
    assert "graph root must be an object" in capsys.readouterr().err

    assert cli.profile_main([str(tmp_path / "missing.json")]) == 2
    assert "cannot read graph" in capsys.readouterr().err


def test_schema_main_writes_packaged_schema(tmp_path, capsys):
    out = tmp_path / "nested" / "network.schema.json"
    assert cli.schema_main(["--out", str(out)]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["$schema"]
    assert "wrote=" in capsys.readouterr().out


def test_fetch_osm_main_success_and_failure(tmp_path, monkeypatch, capsys):
    out = tmp_path / "osm.json"
    monkeypatch.setattr(cli, "convert_place", lambda place: {"place": place, "nodes": [], "edges": []})

    assert cli.fetch_osm_main(["Madrid, Spain", "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["place"] == "Madrid, Spain"
    assert str(out) in capsys.readouterr().out

    def fail(_place):
        raise RuntimeError("offline")

    monkeypatch.setattr(cli, "convert_place", fail)
    assert cli.fetch_osm_main(["Madrid, Spain", "--out", str(out)]) == 2
    assert "OSM acquisition failed: offline" in capsys.readouterr().err


def test_validate_osw_main_valid_invalid_and_error(tmp_path, monkeypatch, capsys):
    dataset = tmp_path / "dataset.zip"
    schema = tmp_path / "schema.json"

    monkeypatch.setattr(
        cli,
        "validate_dataset",
        lambda *args, **kwargs: {"valid": True, "errors": [], "issues": []},
    )
    assert cli.validate_osw_main([str(dataset), "--schema", str(schema)]) == 0
    assert "passes schema validation" in capsys.readouterr().out

    monkeypatch.setattr(
        cli,
        "validate_dataset",
        lambda *args, **kwargs: {"valid": False, "errors": ["bad feature"], "issues": []},
    )
    assert cli.validate_osw_main([str(dataset), "--schema", str(schema)]) == 1
    assert "bad feature" in capsys.readouterr().err

    def fail(*args, **kwargs):
        raise ValueError("bad schema")

    monkeypatch.setattr(cli, "validate_dataset", fail)
    assert cli.validate_osw_main([str(dataset), "--schema", str(schema)]) == 2
    assert "OpenSidewalks validation failed: bad schema" in capsys.readouterr().err
