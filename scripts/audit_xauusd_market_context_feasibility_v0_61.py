from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_market_context_feasibility_audit import (
    DEFAULT_OUTPUT,
    DEFAULT_V0_60_REPORT,
    build_xauusd_market_context_feasibility_audit_v0_61,
    save_xauusd_market_context_feasibility_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_61 XAUUSD market-context feasibility audit.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--previous-board", type=Path, default=ROOT / DEFAULT_V0_60_REPORT)
    parser.add_argument("--skip-mt5-symbol-discovery", action="store_true")
    args = parser.parse_args()

    report = build_xauusd_market_context_feasibility_audit_v0_61(
        previous_board_path=args.previous_board,
        policy_root=ROOT,
        attempt_mt5_symbol_discovery=not args.skip_mt5_symbol_discovery,
    )
    save_xauusd_market_context_feasibility_audit(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_market_context_feasibility_status={report['audit_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
