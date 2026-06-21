from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_dxy_regime_label_design import (
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_RANKER,
    build_xauusd_dxy_regime_label_design_v0_67,
    save_xauusd_dxy_regime_label_design,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_67 XAUUSD DXY regime label design.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=ROOT / DEFAULT_OUTPUT)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-ranker", type=Path, default=DEFAULT_SOURCE_RANKER)
    args = parser.parse_args()

    report = build_xauusd_dxy_regime_label_design_v0_67(
        root=args.root,
        source_ranker_path=args.source_ranker,
    )
    save_xauusd_dxy_regime_label_design(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_dxy_regime_label_design_status={report['label_design_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
