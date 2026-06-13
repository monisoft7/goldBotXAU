from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.xauusd_timeframe_resampler import resample_xauusd_timeframe_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Resample local XAUUSD M1 or M5 CSV candles to M10.")
    parser.add_argument("--input", required=True, dest="input_file")
    parser.add_argument("--target-timeframe", default="M10", choices=["M10"])
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = resample_xauusd_timeframe_csv(
        input_file=args.input_file,
        target_timeframe=args.target_timeframe,
        data_dir=args.data_dir,
    ).to_dict()

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"resampler_version={report['resampler_version']} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
