from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_oos_review import (
    BLOCKED_ALREADY_EVALUATED_DECISION,
    run_xauusd_oos_review_v0_29,
    save_xauusd_oos_review_result,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the v0_29 one-time XAUUSD OOS review.")
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--approval-token", required=True)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_xauusd_oos_review_v0_29(
        protocol_path=args.protocol,
        approval_token=args.approval_token,
        output_path=args.output,
    )
    if not (report.get("decision") == BLOCKED_ALREADY_EVALUATED_DECISION and Path(args.output).exists()):
        save_xauusd_oos_review_result(report, args.output)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"review_version={report['review_version']} decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
