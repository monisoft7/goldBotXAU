from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_market_context_labeler import (
    DEFAULT_OUTPUT,
    DEFAULT_V0_61_REPORT,
    build_xauusd_market_context_labels_v0_62,
    save_xauusd_market_context_labels,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_62 XAUUSD observational market-context labels.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--source-feasibility", type=Path, default=ROOT / DEFAULT_V0_61_REPORT)
    args = parser.parse_args()

    report = build_xauusd_market_context_labels_v0_62(
        data_dir=args.data_dir,
        source_feasibility_path=args.source_feasibility,
    )
    save_xauusd_market_context_labels(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_market_context_labeler_status={report['labeler_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
