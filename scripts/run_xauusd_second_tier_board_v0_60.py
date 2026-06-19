from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_second_tier_fixed_rule_board import (
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT,
    DEFAULT_V0_59_REPORT,
    build_xauusd_second_tier_fixed_rule_board_v0_60,
    save_xauusd_second_tier_fixed_rule_board,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_60 XAUUSD second-tier train/validation board.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--manifest", type=Path, default=ROOT / DEFAULT_MANIFEST)
    parser.add_argument("--source-standardization", type=Path, default=ROOT / DEFAULT_V0_59_REPORT)
    parser.add_argument("--m15-pattern", default="xauusd_m15_*.csv")
    parser.add_argument("--m5-pattern", default="xauusd_m5_xauusd_2023-01-01_2025-12-31.csv")
    args = parser.parse_args()

    report = build_xauusd_second_tier_fixed_rule_board_v0_60(
        data_dir=args.data_dir,
        m15_pattern=args.m15_pattern,
        m5_pattern=args.m5_pattern,
        manifest_path=args.manifest,
        source_standardization_path=args.source_standardization,
        policy_root=ROOT,
    )
    save_xauusd_second_tier_fixed_rule_board(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_second_tier_board_status={report['board_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
