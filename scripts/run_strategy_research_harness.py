from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.strategy_research_runner import run_strategy_research_harness


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the locked XAUUSD strategy research harness.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--pattern", default="xauusd_m15_*.csv")
    parser.add_argument("--candidate", default="null_research_harness_test")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = run_strategy_research_harness(
        args.data_dir,
        args.pattern,
        candidate_id=args.candidate,
        compact=args.compact,
    )
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"research_harness_version={report['research_harness_version']} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
