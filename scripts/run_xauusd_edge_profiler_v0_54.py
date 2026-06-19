from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_edge_profiler import (
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_BOARD,
    build_xauusd_edge_profiler_v0_54,
    save_xauusd_edge_profiler,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_54 XAUUSD empirical edge profiler.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--manifest", type=Path, default=ROOT / DEFAULT_MANIFEST)
    parser.add_argument("--source-board", type=Path, default=ROOT / DEFAULT_SOURCE_BOARD)
    args = parser.parse_args()

    report = build_xauusd_edge_profiler_v0_54(
        data_dir=args.data_dir,
        manifest_path=args.manifest,
        source_board_path=args.source_board,
    )
    save_xauusd_edge_profiler(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_edge_profiler_status={report['profiler_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
