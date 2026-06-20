from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_session_volatility_candidate_design_board import (
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_PROFILER,
    build_xauusd_session_volatility_candidate_design_board_v0_55,
    save_xauusd_session_volatility_candidate_design_board,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_55 XAUUSD session/volatility fixed-rule design board.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-profiler", type=Path, default=ROOT / DEFAULT_SOURCE_PROFILER)
    args = parser.parse_args()

    report = build_xauusd_session_volatility_candidate_design_board_v0_55(
        source_profiler_path=args.source_profiler,
    )
    save_xauusd_session_volatility_candidate_design_board(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_session_volatility_design_status={report['design_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
