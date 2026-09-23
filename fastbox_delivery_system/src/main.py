"""Command-line entry point for the FastBox delivery simulator."""

from __future__ import annotations

import argparse
from pathlib import Path

from delivery_system import build_report, export_top_performer_csv, load_json, save_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate the FastBox delivery system.")
    parser.add_argument("input", help="Path to the input JSON file")
    parser.add_argument(
        "-o",
        "--output",
        default="report.json",
        help="Path for the generated report (default: report.json)",
    )
    parser.add_argument(
        "--top-performer-csv",
        help="Optional CSV path for the top performer bonus output",
    )
    args = parser.parse_args()

    data = load_json(args.input)
    report = build_report(data)
    save_report(report, args.output)
    if args.top_performer_csv:
        export_top_performer_csv(report, args.top_performer_csv)
        print(f"Top performer CSV written to {Path(args.top_performer_csv).resolve()}")
    print(f"Report written to {Path(args.output).resolve()}")
    print(f"Best agent: {report['best_agent']}")


if __name__ == "__main__":
    main()
