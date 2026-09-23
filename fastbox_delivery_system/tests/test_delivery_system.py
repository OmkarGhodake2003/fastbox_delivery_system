from __future__ import annotations

import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from delivery_system import (  # noqa: E402
    assign_packages,
    build_report,
    euclidean_distance,
    export_top_performer_csv,
    normalize_input,
)

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_euclidean_distance() -> None:
    assert euclidean_distance((0, 0), (3, 4)) == 5.0


def test_base_case_assignment() -> None:
    data = read_json(ROOT / "data" / "base_case.json")
    warehouses, agents, packages = normalize_input(data)
    assigned = assign_packages(packages, warehouses, agents)

    assert [p["id"] for p in assigned["A1"]] == ["P1", "P4"]
    assert [p["id"] for p in assigned["A2"]] == ["P2", "P5"]
    assert [p["id"] for p in assigned["A3"]] == ["P3"]


def test_base_case_report() -> None:
    data = read_json(ROOT / "data" / "base_case.json")
    report = build_report(data)

    assert report["A1"] == {
        "packages_delivered": 2,
        "total_distance": 121.21,
        "efficiency": 60.61,
    }
    assert report["A2"] == {
        "packages_delivered": 2,
        "total_distance": 79.21,
        "efficiency": 39.6,
    }
    assert report["A3"] == {
        "packages_delivered": 1,
        "total_distance": 14.14,
        "efficiency": 14.14,
    }
    assert report["best_agent"] == "A3"


def test_all_supplied_test_cases_process_successfully() -> None:
    files = sorted((ROOT / "data" / "test_cases").glob("test_case_*.json"))
    assert len(files) == 10

    for path in files:
        data = read_json(path)
        report = build_report(data)
        total_packages = len(data["packages"])
        delivered = sum(
            int(values["packages_delivered"])
            for key, values in report.items()
            if key != "best_agent"
        )
        assert delivered == total_packages, path.name
        assert report["best_agent"] is not None, path.name


def test_dictionary_and_list_input_formats_are_both_supported() -> None:
    list_data = read_json(ROOT / "data" / "base_case.json")
    dict_data = {
        "warehouses": {item["id"]: item["location"] for item in list_data["warehouses"]},
        "agents": {item["id"]: item["location"] for item in list_data["agents"]},
        "packages": [
            {
                "id": p["id"],
                "warehouse": p["warehouse_id"],
                "destination": p["destination"],
            }
            for p in list_data["packages"]
        ],
    }

    assert build_report(list_data) == build_report(dict_data)


def test_tie_breaking_is_deterministic() -> None:
    data = {
        "warehouses": {"W1": [0, 0]},
        "agents": {"A2": [1, 0], "A1": [-1, 0]},
        "packages": [{"id": "P1", "warehouse": "W1", "destination": [2, 0]}],
    }
    report = build_report(data)
    assert report["A1"]["packages_delivered"] == 1
    assert report["A2"]["packages_delivered"] == 0


def test_top_performer_csv_bonus(tmp_path: Path) -> None:
    data = read_json(ROOT / "data" / "base_case.json")
    report = build_report(data)
    output = tmp_path / "top_performer.csv"
    export_top_performer_csv(report, output)
    content = output.read_text(encoding="utf-8")
    assert "agent_id,packages_delivered,total_distance,efficiency" in content
    assert "A3,1,14.14,14.14" in content
