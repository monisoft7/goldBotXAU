from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_spike_family_decision import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_PROFILE_REPORT,
    decide_spike_family_v0_23,
    save_spike_family_decision_reports,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the v0_23 XAUUSD spike-family decision gate.")
    parser.add_argument("--profile-report", default=str(DEFAULT_PROFILE_REPORT))
    parser.add_argument("--output", default="reports/xauusd_spike_family_decision_v0_23.json")
    parser.add_argument("--candidate-output", default=str(DEFAULT_CANDIDATE_REPORT))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    result = decide_spike_family_v0_23(args.profile_report)
    save_spike_family_decision_reports(result, args.output, args.candidate_output)
    text = json.dumps(result.decision_report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"decision_version={result.decision_report['decision_version']} decision={result.decision_report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
