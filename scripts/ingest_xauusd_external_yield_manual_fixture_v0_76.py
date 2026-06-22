"""Ingest a controlled inline external yield manual fixture for v0_76."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_external_yield_manual_fixture_ingestion import ingest_external_yield_manual_fixture_csv

REPORT_PATH = ROOT / "reports" / "xauusd_external_yield_manual_fixture_ingestion_v0_76.json"


def inline_fixture_text() -> str:
    return """series_id,observation_date,value,source_name,release_timestamp,vintage_date,value_unit,source_reference,quality_flag
DGS10,2026-06-18,4.12,FRED / Federal Reserve Economic Data,2026-06-19T20:15:00+00:00,2026-06-19,percent,inline manual fixture only,sample_valid
DFII10,2026-06-18,.,FRED / Federal Reserve Economic Data,2026-06-19T20:15:00+00:00,2026-06-19,percent,explicit missing marker policy sample,source_missing_marker
DGS2,2026-06-17,4.70,FRED / Federal Reserve Economic Data,2026-06-18T20:15:00+00:00,2026-06-18,percent,inline manual fixture only,sample_valid
DGS10,2026-06-18,4.13,FRED / Federal Reserve Economic Data,2026-06-19T20:15:00+00:00,2026-06-19,percent,intentional duplicate fixture rejection,sample_duplicate_expected_rejection
BADYIELD,2026/06/18,not_numeric,,2026-06-19T20:15:00,2026-06-17,percent,intentional invalid fixture rejection,sample_invalid_expected_rejection
"""


def build_report() -> dict[str, object]:
    return ingest_external_yield_manual_fixture_csv(inline_fixture_text())


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest v0_76 controlled external yield manual fixture.")
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
        print(f"v0_76 external yield manual fixture ingestion: {report['ingestion_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
