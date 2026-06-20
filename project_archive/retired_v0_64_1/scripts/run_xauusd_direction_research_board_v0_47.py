from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_executable_direction_research_board import (
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_FILTER_REPORT,
    build_xauusd_direction_research_board_v0_47,
    save_xauusd_direction_research_board,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_47 XAUUSD executable direction research board.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--manifest", type=Path, default=ROOT / "reports" / "xauusd_dataset_manifest_v0_5.json")
    parser.add_argument("--source-filter-report", type=Path, default=ROOT / DEFAULT_SOURCE_FILTER_REPORT)
    args = parser.parse_args()

    report = build_xauusd_direction_research_board_v0_47(
        data_dir=args.data_dir,
        manifest_path=args.manifest,
        source_filter_report_path=args.source_filter_report,
    )
    save_xauusd_direction_research_board(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_direction_research_board_status={report['board_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
