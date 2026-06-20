from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_trend_pullback_sample_stability_audit import (
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_BOARD,
    build_xauusd_trend_pullback_stability_audit_v0_49,
    save_xauusd_trend_pullback_stability_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_49 XAUUSD trend pullback stability audit.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--manifest", type=Path, default=ROOT / "reports" / "xauusd_dataset_manifest_v0_5.json")
    parser.add_argument("--source-board", type=Path, default=ROOT / DEFAULT_SOURCE_BOARD)
    args = parser.parse_args()

    report = build_xauusd_trend_pullback_stability_audit_v0_49(
        data_dir=args.data_dir,
        manifest_path=args.manifest,
        source_board_path=args.source_board,
    )
    save_xauusd_trend_pullback_stability_audit(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_trend_pullback_stability_audit_status={report['audit_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
