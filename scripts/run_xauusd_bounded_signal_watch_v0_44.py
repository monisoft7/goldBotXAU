from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.execution.xauusd_bounded_signal_watch_runner import (
    DEFAULT_OUTPUT,
    run_xauusd_bounded_signal_watch_v0_44,
    save_xauusd_bounded_signal_watch,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_44 bounded dry-run XAUUSD signal watch.")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--lot", type=float, default=0.01)
    parser.add_argument("--max-cycles", type=int, default=6)
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--sleep-between-cycles",
        action="store_true",
        help="Actually sleep between bounded foreground dry-run cycles.",
    )
    args = parser.parse_args()

    report = run_xauusd_bounded_signal_watch_v0_44(
        symbol=args.symbol,
        lot=args.lot,
        max_cycles=args.max_cycles,
        interval_seconds=args.interval_seconds,
        dry_run=args.dry_run,
        sleep_between_cycles=args.sleep_between_cycles,
    )
    save_xauusd_bounded_signal_watch(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_bounded_signal_watch_status={report['watch_status']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
