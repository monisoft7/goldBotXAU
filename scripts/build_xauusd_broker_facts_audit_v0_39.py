from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_broker_facts_audit import (
    DEFAULT_OUTPUT,
    build_xauusd_broker_facts_audit_v0_39,
    save_xauusd_broker_facts_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_39 XAUUSD read-only broker facts audit.")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_broker_facts_audit_v0_39(symbol=args.symbol)
    save_xauusd_broker_facts_audit(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"broker_facts_audit_decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
