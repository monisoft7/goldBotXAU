from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_demo_broker_safety_preflight import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_DEMO_PREFLIGHT_REVIEW,
    DEFAULT_OOS_REPAIR_REPORT,
    DEFAULT_OUTPUT,
    DEMO_PREFLIGHT_SAFETY_DESIGN_READY,
    build_xauusd_demo_broker_safety_preflight_v0_38,
    save_xauusd_demo_broker_safety_preflight,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_38 XAUUSD demo/broker safety preflight design.")
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--oos-repair-report", type=Path, default=DEFAULT_OOS_REPAIR_REPORT)
    parser.add_argument("--demo-preflight-review", type=Path, default=DEFAULT_DEMO_PREFLIGHT_REVIEW)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_demo_broker_safety_preflight_v0_38(
        candidate_report_path=args.candidate_report,
        oos_repair_report_path=args.oos_repair_report,
        demo_preflight_review_path=args.demo_preflight_review,
    )
    save_xauusd_demo_broker_safety_preflight(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"demo_broker_safety_preflight_decision={report['decision']}")
    return 0 if report["decision"] == DEMO_PREFLIGHT_SAFETY_DESIGN_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
