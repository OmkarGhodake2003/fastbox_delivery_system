"""Core logic for the FastBox delivery simulation assignment."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

Point = tuple[float, float]


def load_json(path: str | Path) -> dict[str, Any]:
    """Read and parse a JSON file using Python's standard json module."""
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_entities(raw: Any, *, id_key: str = "id", location_key: str = "location") -> dict[str, Point]:
    """Normalize either the assignment's list or dictionary entity format."""
    if isinstance(raw, dict):
        return {str(entity_id): (float(value[0]), float(value[1])) for entity_id, value in raw.items()}

    if isinstance(raw, list):
        result: dict[str, Point] = {}
        for item in raw:
            entity_id = str(item[id_key])
            location = item[location_key]
            result[entity_id] = (float(location[0]), float(location[1]))
        return result

    raise ValueError("Entities must be supplied as a dictionary or list.")


def normalize_input(data: dict[str, Any]) -> tuple[dict[str, Point], dict[str, Point], list[dict[str, Any]]]:
    """Normalize all supported input shapes into one internal representation."""
    warehouses = normalize_entities(data["warehouses"])
    agents = normalize_entities(data["agents"])

    packages: list[dict[str, Any]] = []
    for package in data["packages"]:
        warehouse_id = package.get("warehouse_id", package.get("warehouse"))
        if warehouse_id is None:
            raise ValueError(f"Package {package.get('id', '<unknown>')} has no warehouse reference.")
        destination = package["destination"]
        packages.append(
            {
                "id": str(package["id"]),
                "warehouse_id": str(warehouse_id),
                "destination": (float(destination[0]), float(destination[1])),
            }
        )
    return warehouses, agents, packages


def euclidean_distance(a: Point, b: Point) -> float:
    """Return the straight-line Euclidean distance between two points."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def assign_packages(
    packages: list[dict[str, Any]],
    warehouses: dict[str, Point],
    agents: dict[str, Point],
) -> dict[str, list[dict[str, Any]]]:
    """Assign every package to the nearest agent to its warehouse.

    Tie-breaking assumption: if two agents are exactly the same distance from a
    warehouse, the lexicographically smaller agent ID is selected. This makes
    the result deterministic across runs and input ordering.
    """
    assigned = {agent_id: [] for agent_id in agents}
    if not agents:
        if packages:
            raise ValueError("At least one agent is required when packages exist.")
        return assigned

    for package in packages:
        warehouse_id = package["warehouse_id"]
        if warehouse_id not in warehouses:
            raise ValueError(f"Unknown warehouse '{warehouse_id}' for package '{package['id']}'.")

        warehouse_location = warehouses[warehouse_id]
        agent_id = min(
            agents,
            key=lambda candidate: (euclidean_distance(agents[candidate], warehouse_location), candidate),
        )
        assigned[agent_id].append(package)
    return assigned


def simulate_delivery(
    packages: list[dict[str, Any]],
    warehouses: dict[str, Point],
    agents: dict[str, Point],
) -> dict[str, dict[str, float | int]]:
    """Assign and simulate all deliveries.

    Assumptions documented for ambiguous routing details:
    1. Assignment is based on each agent's INITIAL location, exactly as required
       by the assignment statement.
    2. Packages are delivered in the order they appear in the input JSON.
    3. After a delivery, an agent remains at that destination. The next trip is
       therefore current_position -> warehouse -> destination.
    4. Agents do not return to a warehouse or depot after the final delivery.
    5. Each package contributes the distance to its warehouse plus the distance
       from that warehouse to its destination.
    """
    assigned = assign_packages(packages, warehouses, agents)
    current_positions = dict(agents)
    totals = {agent_id: 0.0 for agent_id in agents}
    counts = {agent_id: 0 for agent_id in agents}

    for agent_id, agent_packages in assigned.items():
        for package in agent_packages:
            warehouse = warehouses[package["warehouse_id"]]
            destination = package["destination"]
            totals[agent_id] += euclidean_distance(current_positions[agent_id], warehouse)
            totals[agent_id] += euclidean_distance(warehouse, destination)
            current_positions[agent_id] = destination
            counts[agent_id] += 1

    report: dict[str, dict[str, float | int]] = {}
    for agent_id in agents:
        count = counts[agent_id]
        total = totals[agent_id]
        report[agent_id] = {
            "packages_delivered": count,
            "total_distance": round(total, 2),
            "efficiency": round(total / count, 2) if count else 0.0,
        }
    return report


def choose_best_agent(report: dict[str, dict[str, float | int]]) -> str | None:
    """Choose the agent with the lowest average distance per delivered package.

    Agents with zero deliveries are excluded. Ties are resolved by agent ID.
    """
    eligible = [
        agent_id
        for agent_id, values in report.items()
        if int(values["packages_delivered"]) > 0
    ]
    if not eligible:
        return None
    return min(eligible, key=lambda agent_id: (float(report[agent_id]["efficiency"]), agent_id))


def build_report(data: dict[str, Any]) -> dict[str, Any]:
    warehouses, agents, packages = normalize_input(data)
    report = simulate_delivery(packages, warehouses, agents)
    report["best_agent"] = choose_best_agent(report)
    return report


def save_report(report: dict[str, Any], path: str | Path) -> None:
    """Write a valid, human-readable JSON report."""
    with Path(path).open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)
        file.write("\n")


def export_top_performer_csv(report: dict[str, Any], path: str | Path) -> None:
    """Export the selected top performer as a one-row CSV bonus output."""
    best_agent = report.get("best_agent")
    if best_agent is None:
        raise ValueError("Cannot export a top performer when no agent delivered a package.")

    values = report[best_agent]
    with Path(path).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["agent_id", "packages_delivered", "total_distance", "efficiency"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "agent_id": best_agent,
                "packages_delivered": values["packages_delivered"],
                "total_distance": values["total_distance"],
                "efficiency": values["efficiency"],
            }
        )
