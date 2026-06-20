from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.candidate_stability_diagnostics import (
    DEFAULT_CANDIDATE_ID,
    diagnose_candidate_stability,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run train-only rejected-candidate stability diagnostics.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--pattern", default="xauusd_m15_*.csv")
    parser.add_argument("--candidate", default=DEFAULT_CANDIDATE_ID)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--output")
    args = parser.parse_args()

    report = diagnose_candidate_stability(
        data_dir=args.data_dir,
        pattern=args.pattern,
        candidate_id=args.candidate,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"diagnostic_version={report['diagnostic_version']} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
