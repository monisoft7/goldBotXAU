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
    DEFAULT_RUNNER_PROTOCOL,
    DEFAULT_V0_34_OUTPUT,
    build_xauusd_forward_observation_journal_v0_34,
    save_xauusd_forward_observation_journal,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_34 read-only forward observation journal pass.")
    parser.add_argument("--runner-protocol", type=Path, default=DEFAULT_RUNNER_PROTOCOL)
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--forward-csv", type=Path, action="append", dest="forward_csv_paths")
    parser.add_argument("--fixture-csv", type=Path)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_V0_34_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_forward_observation_journal_v0_34(
        runner_protocol_path=args.runner_protocol,
        candidate_report_path=args.candidate_report,
        data_dir=args.data_dir,
        forward_csv_paths=args.forward_csv_paths,
        fixture_csv_path=args.fixture_csv,
    )
    save_xauusd_forward_observation_journal(report, args.output)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(
            "observation_version="
            f"{report['observation_version']} observation_status={report['observation_status']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
