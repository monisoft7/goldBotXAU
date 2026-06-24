from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_paper_forward_watcher import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_OUTPUT_V0_87,
    DEFAULT_REAL_MARKET_FROM_DATE,
    DEFAULT_REAL_MARKET_TIMEFRAMES,
    build_xauusd_paper_forward_watcher_v0_87,
    save_xauusd_paper_forward_watcher_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_87 local read-only market CSV paper watcher report.")
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--market-csv-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_V0_87)
    parser.add_argument("--max-records", type=int, default=30)
    parser.add_argument("--from-date", default=DEFAULT_REAL_MARKET_FROM_DATE)
    parser.add_argument("--to-date")
    parser.add_argument("--timeframes", default=",".join(DEFAULT_REAL_MARKET_TIMEFRAMES))
    args = parser.parse_args()

    timeframes = [part.strip() for part in args.timeframes.split(",") if part.strip()]
    report = build_xauusd_paper_forward_watcher_v0_87(
        candidate_report_path=args.candidate_report,
        market_csv_dir=args.market_csv_dir,
        max_records=args.max_records,
        from_date=args.from_date,
        to_date=args.to_date,
        timeframes=timeframes,
    )
    save_xauusd_paper_forward_watcher_report(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"watch_version={report['watch_version']} watch_status={report['watch_status']}")
    return 0 if report["watch_status"] in {"watch_completed", "watch_completed_no_records"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
