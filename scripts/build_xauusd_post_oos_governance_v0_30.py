from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_post_oos_governance import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_MARKER,
    DEFAULT_OUTPUT,
    DEFAULT_REPAIR_REPORT,
    build_xauusd_post_oos_governance_v0_30,
    save_xauusd_post_oos_governance_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_30 post-OOS governance and paper-shadow design report.")
    parser.add_argument("--marker", type=Path, default=DEFAULT_MARKER)
    parser.add_argument("--repair-report", type=Path, default=DEFAULT_REPAIR_REPORT)
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_post_oos_governance_v0_30(
        marker_path=args.marker,
        repair_report_path=args.repair_report,
        candidate_report_path=args.candidate_report,
    )
    save_xauusd_post_oos_governance_report(report, args.output)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"governance_version={report['governance_version']} status={report['governance_status']}")
    return 0 if not report["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
