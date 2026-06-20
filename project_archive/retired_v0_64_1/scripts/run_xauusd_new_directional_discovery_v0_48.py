from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_new_directional_strategy_discovery_board import (
    DEFAULT_OUTPUT,
    build_xauusd_new_directional_strategy_discovery_board_v0_48,
    save_xauusd_new_directional_strategy_discovery_board,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_48 XAUUSD new directional strategy discovery board.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--manifest", type=Path, default=ROOT / "reports" / "xauusd_dataset_manifest_v0_5.json")
    args = parser.parse_args()

    report = build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=args.data_dir,
        manifest_path=args.manifest,
    )
    save_xauusd_new_directional_strategy_discovery_board(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_new_directional_discovery_status={report['board_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
