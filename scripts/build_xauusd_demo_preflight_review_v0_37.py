from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_demo_preflight_review import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_LEDGER_REPORT,
    DEFAULT_OOS_REPAIR_REPORT,
    DEFAULT_OUTPUT,
    READY_FOR_DEMO_PREFLIGHT_DESIGN,
    build_xauusd_demo_preflight_review_v0_37,
    save_xauusd_demo_preflight_review,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_37 XAUUSD demo preflight review.")
    parser.add_argument("--ledger-report", type=Path, default=DEFAULT_LEDGER_REPORT)
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--oos-repair-report", type=Path, default=DEFAULT_OOS_REPAIR_REPORT)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_demo_preflight_review_v0_37(
        ledger_report_path=args.ledger_report,
        candidate_report_path=args.candidate_report,
        oos_repair_report_path=args.oos_repair_report,
    )
    save_xauusd_demo_preflight_review(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"demo_preflight_review_decision={report['decision']}")
    return 0 if report["decision"] == READY_FOR_DEMO_PREFLIGHT_DESIGN else 1


if __name__ == "__main__":
    raise SystemExit(main())
