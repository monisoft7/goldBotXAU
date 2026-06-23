from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_master_trading_path_reentry_board import (  # noqa: E402
    write_master_trading_path_reentry_board,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_81 master trading path re-entry board.")
    parser.add_argument("--json", action="store_true", help="Print the generated report JSON.")
    args = parser.parse_args()

    report = write_master_trading_path_reentry_board(ROOT)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report["board_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
