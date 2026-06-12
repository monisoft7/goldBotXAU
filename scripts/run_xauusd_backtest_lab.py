from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.engine import build_lab_report
from src.data.xauusd_csv_loader import load_xauusd_m15_csvs


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local XAUUSD backtest lab loader.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--pattern", default="xauusd_m15_*.csv")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    load_result = load_xauusd_m15_csvs(Path(args.data_dir), args.pattern)
    status = "local_data_loaded" if load_result.files else "no_local_data_found"
    report = build_lab_report(
        status=status,
        candle_count=len(load_result.records),
        file_count=len(load_result.files),
    ).to_dict()

    output = json.dumps(report, indent=2, sort_keys=True)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
