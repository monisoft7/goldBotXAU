"""Build the v0_77 external yield backward as-of alignment design report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_external_yield_asof_alignment_design import design_external_yield_asof_alignment

REPORT_PATH = ROOT / "reports" / "xauusd_external_yield_asof_alignment_design_v0_77.json"


def inline_records() -> list[dict[str, object]]:
    return [
        {
            "series_id": "DGS10",
            "observation_date": "2026-06-17",
            "value": 4.10,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-18T20:15:00+00:00",
            "value_unit": "percent",
            "input_index": 0,
        },
        {
            "series_id": "DGS10",
            "observation_date": "2026-06-18",
            "value": 4.12,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00+00:00",
            "value_unit": "percent",
            "input_index": 1,
        },
        {
            "series_id": "DGS2",
            "observation_date": "2026-06-17",
            "value": 4.70,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-18T20:15:00+00:00",
            "value_unit": "percent",
            "input_index": 2,
        },
        {
            "series_id": "DFII10",
            "observation_date": "2026-06-18",
            "value": None,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00+00:00",
            "value_unit": "percent",
            "quality_flag": "source_missing_marker",
            "input_index": 3,
        },
        {
            "series_id": "DFF",
            "observation_date": "2026-06-18",
            "value": 4.33,
            "source_name": "FRED / Federal Reserve Economic Data",
            "value_unit": "percent",
            "input_index": 4,
        },
        {
            "series_id": "T10YIE",
            "observation_date": "2026-06-18",
            "value": 2.32,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00",
            "value_unit": "percent",
            "input_index": 5,
        },
        {
            "series_id": "DGS10",
            "observation_date": "2026-06-18",
            "value": 4.13,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00+00:00",
            "value_unit": "percent",
            "input_index": 6,
        },
    ]


def synthetic_target_timestamps() -> list[str]:
    return [
        "2026-06-18T19:00:00+00:00",
        "2026-06-18T21:00:00+00:00",
        "2026-06-19T19:00:00+00:00",
        "2026-06-19T21:00:00+00:00",
    ]


def build_report() -> dict[str, object]:
    return design_external_yield_asof_alignment(inline_records(), synthetic_target_timestamps())


def main() -> int:
    parser = argparse.ArgumentParser(description="Design v0_77 external yield backward as-of alignment policy.")
    parser.add_argument("--json", action="store_true", help="Print the report JSON.")
    parser.add_argument("--output", type=Path, default=REPORT_PATH, help="Report path to write.")
    args = parser.parse_args()

    report = build_report()
    report_text = json.dumps(report, indent=2, sort_keys=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report_text + "\n", encoding="utf-8")

    if args.json:
        print(report_text)
    else:
        print(f"v0_77 external yield as-of alignment design: {report['alignment_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
