from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_historical_data_expansion_feasibility_audit import (
    DEFAULT_OUTPUT,
    build_xauusd_historical_data_expansion_feasibility_audit_v0_50,
    save_xauusd_historical_data_expansion_feasibility_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_50 XAUUSD historical data expansion feasibility audit.")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--to-date", required=True)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_historical_data_expansion_feasibility_audit_v0_50(
        symbol=args.symbol,
        from_date=args.from_date,
        to_date=args.to_date,
    )
    save_xauusd_historical_data_expansion_feasibility_audit(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_historical_data_expansion_feasibility_status={report['audit_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
