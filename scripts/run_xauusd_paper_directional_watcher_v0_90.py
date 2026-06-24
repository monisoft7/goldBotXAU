from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_paper_direction_annotator import (
    DEFAULT_FROM_DATE,
    DEFAULT_JOURNAL_PATH,
    DEFAULT_LOOKBACK_BARS,
    DEFAULT_MARKET_CSV_DIR,
    DEFAULT_MAX_RECORDS,
    DEFAULT_REPORT_PATH,
    DEFAULT_TIMEFRAMES,
    build_xauusd_paper_directional_watcher_v0_90,
    save_xauusd_paper_directional_watcher_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_90 paper-only directional observation watcher.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS)
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE)
    parser.add_argument("--to-date")
    parser.add_argument("--timeframes", default=",".join(DEFAULT_TIMEFRAMES))
    parser.add_argument("--lookback-bars", type=int, default=DEFAULT_LOOKBACK_BARS)
    parser.add_argument("--journal-path", type=Path, default=DEFAULT_JOURNAL_PATH)
    parser.add_argument("--market-csv-dir", type=Path, default=DEFAULT_MARKET_CSV_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()

    timeframes = [part.strip() for part in args.timeframes.split(",") if part.strip()]
    report = build_xauusd_paper_directional_watcher_v0_90(
        market_csv_dir=args.market_csv_dir,
        max_records=args.max_records,
        from_date=args.from_date,
        to_date=args.to_date,
        timeframes=timeframes,
        lookback_bars=args.lookback_bars,
        journal_path=args.journal_path,
    )
    save_xauusd_paper_directional_watcher_report(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"watch_version={report['watch_version']} watch_status={report['watch_status']}")
    return 0 if report["watch_status"] != "directional_watch_blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
