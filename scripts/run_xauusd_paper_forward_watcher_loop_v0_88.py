from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_forward_observation_runner import DEFAULT_CANDIDATE_REPORT
from src.research.xauusd_paper_forward_journal import (
    DEFAULT_JOURNAL_PATH,
    DEFAULT_LOOP_REPORT_PATH,
    run_paper_forward_watcher_loop_v0_88,
    save_paper_forward_watcher_loop_report,
)
from src.research.xauusd_paper_forward_watcher import (
    DEFAULT_REAL_MARKET_FROM_DATE,
    DEFAULT_REAL_MARKET_TIMEFRAMES,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_88 paper forward watcher loop and append JSONL journal records.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--interval-seconds", type=float, default=1)
    parser.add_argument("--max-records-per-cycle", type=int, default=10)
    parser.add_argument("--journal-path", type=Path, default=DEFAULT_JOURNAL_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_LOOP_REPORT_PATH)
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--market-csv-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--from-date", default=DEFAULT_REAL_MARKET_FROM_DATE)
    parser.add_argument("--to-date")
    parser.add_argument("--timeframes", default=",".join(DEFAULT_REAL_MARKET_TIMEFRAMES))
    args = parser.parse_args()

    timeframes = [part.strip() for part in args.timeframes.split(",") if part.strip()]
    report = run_paper_forward_watcher_loop_v0_88(
        cycles=args.cycles,
        interval_seconds=args.interval_seconds,
        max_records_per_cycle=args.max_records_per_cycle,
        journal_path=args.journal_path,
        candidate_report_path=args.candidate_report,
        market_csv_dir=args.market_csv_dir,
        from_date=args.from_date,
        to_date=args.to_date,
        timeframes=timeframes,
    )
    save_paper_forward_watcher_loop_report(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"loop_version={report['loop_version']} loop_status={report['loop_status']}")
    return 0 if report["loop_status"] in {"loop_completed", "loop_completed_no_observations"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
