from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_dxy_conditioned_event_study import (
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_LABEL_DESIGN,
    DEFAULT_SOURCE_RANKER,
    build_xauusd_dxy_conditioned_event_study_v0_68,
    save_xauusd_dxy_conditioned_event_study,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_68 XAUUSD DXY-conditioned diagnostic event study.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=ROOT / DEFAULT_OUTPUT)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-ranker", type=Path, default=DEFAULT_SOURCE_RANKER)
    parser.add_argument("--source-label-design", type=Path, default=DEFAULT_SOURCE_LABEL_DESIGN)
    parser.add_argument("--skip-mt5-readonly", action="store_true")
    args = parser.parse_args()

    report = build_xauusd_dxy_conditioned_event_study_v0_68(
        root=args.root,
        source_ranker_path=args.source_ranker,
        source_label_design_path=args.source_label_design,
        attempt_mt5_readonly=not args.skip_mt5_readonly,
    )
    save_xauusd_dxy_conditioned_event_study(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_dxy_conditioned_event_study_status={report['study_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
