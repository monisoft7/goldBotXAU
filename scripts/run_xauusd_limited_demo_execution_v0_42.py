from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.execution.xauusd_limited_demo_executor import (
    DEFAULT_OUTPUT,
    REQUIRED_APPROVAL_TOKEN,
    build_xauusd_limited_demo_execution_v0_42,
    save_xauusd_limited_demo_execution,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the v0_42 XAUUSD limited demo execution scaffold.")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--lot", type=float, default=0.01)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--no-dry-run", action="store_false", dest="dry_run")
    parser.add_argument("--allow-demo-order-send", action="store_true")
    parser.add_argument("--approval-token")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_limited_demo_execution_v0_42(
        symbol=args.symbol,
        lot=args.lot,
        dry_run=args.dry_run,
        allow_demo_order_send=args.allow_demo_order_send,
        approval_token=args.approval_token,
    )
    save_xauusd_limited_demo_execution(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_limited_demo_executor_status={report['executor_status']}")

    if args.allow_demo_order_send and args.approval_token == REQUIRED_APPROVAL_TOKEN and not args.dry_run:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
