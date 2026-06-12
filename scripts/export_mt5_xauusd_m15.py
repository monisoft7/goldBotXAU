from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.mt5_readonly_xauusd_exporter import export_xauusd_m15_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Export local MT5 XAUUSD M15 candles to CSV.")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--to-date", required=True)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = export_xauusd_m15_csv(
        symbol=args.symbol,
        from_date=args.from_date,
        to_date=args.to_date,
        data_dir=args.data_dir,
    ).to_dict()

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"exporter_version={report['exporter_version']} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
