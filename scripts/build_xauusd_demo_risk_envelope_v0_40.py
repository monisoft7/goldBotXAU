from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_demo_risk_envelope import (
    DEFAULT_BROKER_FACTS_REPORT,
    DEFAULT_OUTPUT,
    build_xauusd_demo_risk_envelope_v0_40,
    save_xauusd_demo_risk_envelope,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_40 XAUUSD fixed demo risk envelope design.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--broker-facts-report", type=Path, default=DEFAULT_BROKER_FACTS_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_demo_risk_envelope_v0_40(broker_facts_report_path=args.broker_facts_report)
    save_xauusd_demo_risk_envelope(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"demo_risk_envelope_decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
