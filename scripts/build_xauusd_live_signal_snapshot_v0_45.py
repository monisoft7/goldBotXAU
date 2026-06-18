from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.execution.xauusd_live_signal_snapshot_provider import (
    DEFAULT_OUTPUT,
    build_xauusd_live_signal_snapshot_v0_45,
    save_xauusd_live_signal_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_45 read-only XAUUSD live signal snapshot.")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_live_signal_snapshot_v0_45(
        symbol=args.symbol,
        dry_run=args.dry_run,
    )
    save_xauusd_live_signal_snapshot(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_live_signal_snapshot_status={report['snapshot_status']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
