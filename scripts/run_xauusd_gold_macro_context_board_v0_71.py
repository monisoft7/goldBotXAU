from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_gold_macro_context_board import write_gold_macro_context_board


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_71 gold macro context board.")
    parser.add_argument("--json", action="store_true", help="Print the generated report JSON.")
    parser.add_argument("--output", type=Path, help="Optional output report path.")
    args = parser.parse_args()

    report = write_gold_macro_context_board(ROOT, args.output)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"gold macro context board {report['board_status']}: {report['next_research_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
