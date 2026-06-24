from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_paper_directional_outcome_audit import (
    DEFAULT_FROM_DATE,
    DEFAULT_HORIZON_BARS,
    DEFAULT_LOOKBACK_BARS,
    DEFAULT_MARKET_CSV_DIR,
    DEFAULT_MAX_DIRECTIONAL_RECORDS,
    DEFAULT_MAX_SCAN_ROWS,
    DEFAULT_REPORT_PATH,
    build_xauusd_paper_directional_outcome_audit_v0_91,
    save_xauusd_paper_directional_outcome_audit_report,
)
from src.research.xauusd_paper_direction_annotator import DEFAULT_TIMEFRAMES


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_91 paper-only directional outcome audit.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--market-csv-dir", type=Path, default=DEFAULT_MARKET_CSV_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE)
    parser.add_argument("--to-date")
    parser.add_argument("--timeframes", default=",".join(DEFAULT_TIMEFRAMES))
    parser.add_argument("--horizon-bars", type=int, default=DEFAULT_HORIZON_BARS)
    parser.add_argument("--lookback-bars", type=int, default=DEFAULT_LOOKBACK_BARS)
    parser.add_argument("--max-scan-rows", type=int, default=DEFAULT_MAX_SCAN_ROWS)
    parser.add_argument("--max-directional-records", type=int, default=DEFAULT_MAX_DIRECTIONAL_RECORDS)
    args = parser.parse_args()

    timeframes = [part.strip() for part in args.timeframes.split(",") if part.strip()]
    report = build_xauusd_paper_directional_outcome_audit_v0_91(
        market_csv_dir=args.market_csv_dir,
        from_date=args.from_date,
        to_date=args.to_date,
        timeframes=timeframes,
        horizon_bars=args.horizon_bars,
        lookback_bars=args.lookback_bars,
        max_scan_rows=args.max_scan_rows,
        max_directional_records=args.max_directional_records,
    )
    save_xauusd_paper_directional_outcome_audit_report(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"audit_version={report['audit_version']} audit_status={report['audit_status']}")
    return 0 if report["audit_status"] != "directional_outcome_audit_blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
