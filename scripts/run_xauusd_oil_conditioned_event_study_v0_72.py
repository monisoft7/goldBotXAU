from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_oil_conditioned_event_study import (
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_MACRO_BOARD,
    DEFAULT_SOURCE_QUALITY_DESIGN,
    build_xauusd_oil_conditioned_event_study_v0_72,
    save_xauusd_oil_conditioned_event_study,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_72 XAUUSD oil-conditioned diagnostic event study.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=ROOT / DEFAULT_OUTPUT)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-quality-design", type=Path, default=DEFAULT_SOURCE_QUALITY_DESIGN)
    parser.add_argument("--source-macro-board", type=Path, default=DEFAULT_SOURCE_MACRO_BOARD)
    parser.add_argument("--skip-mt5-readonly", action="store_true")
    args = parser.parse_args()

    report = build_xauusd_oil_conditioned_event_study_v0_72(
        root=args.root,
        source_quality_design_path=args.source_quality_design,
        source_macro_board_path=args.source_macro_board,
        attempt_mt5_readonly=not args.skip_mt5_readonly,
    )
    save_xauusd_oil_conditioned_event_study(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_oil_conditioned_event_study_status={report['study_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
