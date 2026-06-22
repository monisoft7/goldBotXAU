"""Validate inline external yield sample records for v0_75."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_external_yield_dataset_validator import validate_external_yield_sample_records

REPORT_PATH = ROOT / "reports" / "xauusd_external_yield_sample_validator_v0_75.json"


def sample_records() -> list[dict[str, object]]:
    return [
        {
            "series_id": "DGS10",
            "observation_date": "2026-06-18",
            "value": "4.12",
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00+00:00",
            "vintage_date": "2026-06-19",
            "value_unit": "percent",
            "source_reference": "inline sample fixture only; no API call",
            "quality_flag": "sample_valid",
        },
        {
            "series_id": "DFII10",
            "observation_date": "2026-06-18",
            "value": ".",
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00+00:00",
            "vintage_date": "2026-06-19",
            "value_unit": "percent",
            "source_reference": "explicit missing marker policy sample",
            "quality_flag": "source_missing_marker",
        },
        {
            "series_id": "DGS10",
            "observation_date": "2026-06-18",
            "value": "4.13",
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00+00:00",
            "vintage_date": "2026-06-19",
            "value_unit": "percent",
            "source_reference": "intentional duplicate fixture rejection",
            "quality_flag": "sample_duplicate_expected_rejection",
        },
        {
            "series_id": "BADYIELD",
            "observation_date": "2026/06/18",
            "value": "not_numeric",
            "source_name": "",
            "release_timestamp": "2026-06-19T20:15:00",
            "vintage_date": "2026-06-17",
            "value_unit": "percent",
            "source_reference": "intentional invalid fixture rejection",
            "quality_flag": "sample_invalid_expected_rejection",
        },
    ]


def build_report() -> dict[str, object]:
    return validate_external_yield_sample_records(sample_records())


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v0_75 inline external yield sample records.")
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
        print(f"v0_75 external yield sample validator: {report['validator_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
