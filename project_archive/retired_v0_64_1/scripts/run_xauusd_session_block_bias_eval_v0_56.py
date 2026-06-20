from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_session_block_directional_bias_evaluation import (
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_DESIGN,
    build_xauusd_session_block_directional_bias_evaluation_v0_56,
    save_xauusd_session_block_directional_bias_evaluation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_56 XAUUSD session block fixed-rule train/validation evaluation.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-design", type=Path, default=ROOT / DEFAULT_SOURCE_DESIGN)
    parser.add_argument("--manifest", type=Path, default=ROOT / DEFAULT_MANIFEST)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--pattern", default="xauusd_m15_*.csv")
    args = parser.parse_args()

    report = build_xauusd_session_block_directional_bias_evaluation_v0_56(
        data_dir=args.data_dir,
        pattern=args.pattern,
        manifest_path=args.manifest,
        source_design_path=args.source_design,
    )
    save_xauusd_session_block_directional_bias_evaluation(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_session_block_bias_eval_status={report['evaluation_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
