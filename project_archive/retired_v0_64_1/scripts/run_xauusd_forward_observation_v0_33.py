from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_forward_observation_runner import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_JOURNAL_PROTOCOL,
    DEFAULT_OUTPUT,
    DEFAULT_PLAN,
    build_xauusd_forward_observation_runner_protocol_v0_33,
    save_xauusd_forward_observation_runner_protocol,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_33 read-only forward observation runner protocol.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--journal-protocol", type=Path, default=DEFAULT_JOURNAL_PROTOCOL)
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--fixture-csv", type=Path)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_forward_observation_runner_protocol_v0_33(
        plan_path=args.plan,
        journal_protocol_path=args.journal_protocol,
        candidate_report_path=args.candidate_report,
        fixture_csv_path=args.fixture_csv,
    )
    save_xauusd_forward_observation_runner_protocol(report, args.output)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"runner_version={report['runner_version']} runner_status={report['runner_status']}")
    return 0 if not report["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
