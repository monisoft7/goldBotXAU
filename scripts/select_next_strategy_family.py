from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.strategy_family_selection_board import build_strategy_family_selection_board


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_13 train-only strategy family selection board.")
    parser.add_argument("--profile", default="reports/xauusd_market_profile_v0_10.json")
    parser.add_argument("--diagnostic", default="reports/xauusd_candidate_stability_v0_12.json")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_strategy_family_selection_board(
        profile_path=args.profile,
        diagnostic_path=args.diagnostic,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"board_version={report['board_version']} "
            f"status={report['status']} "
            f"recommended_next_family={report['recommended_next_family']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
