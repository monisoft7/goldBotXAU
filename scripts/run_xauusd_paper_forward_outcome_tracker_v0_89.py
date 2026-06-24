from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_paper_forward_outcome_tracker import (
    DEFAULT_HORIZON_BARS,
    DEFAULT_JOURNAL_PATH,
    DEFAULT_MARKET_CSV_DIR,
    DEFAULT_MAX_RECORDS,
    DEFAULT_REPORT_PATH,
    build_xauusd_paper_forward_outcome_tracker_v0_89,
    save_xauusd_paper_forward_outcome_tracker_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_89 paper forward outcome tracker.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--journal-path", type=Path, default=DEFAULT_JOURNAL_PATH)
    parser.add_argument("--horizon-bars", type=int, default=DEFAULT_HORIZON_BARS)
    parser.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS)
    parser.add_argument("--market-csv-dir", type=Path, default=DEFAULT_MARKET_CSV_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()

    report = build_xauusd_paper_forward_outcome_tracker_v0_89(
        journal_path=args.journal_path,
        market_csv_dir=args.market_csv_dir,
        horizon_bars=args.horizon_bars,
        max_records=args.max_records,
    )
    save_xauusd_paper_forward_outcome_tracker_report(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"tracker_version={report['tracker_version']} tracker_status={report['tracker_status']}")
    return 0 if report["tracker_status"] != "outcome_tracker_blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
