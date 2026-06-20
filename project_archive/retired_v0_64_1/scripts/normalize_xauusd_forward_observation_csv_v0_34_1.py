from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_forward_observation_schema_adapter import (
    normalize_xauusd_forward_observation_csv,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize local XAUUSD forward observation CSV schema.")
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--symbol")
    parser.add_argument("--timeframe")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    args = parser.parse_args()

    report = normalize_xauusd_forward_observation_csv(
        input_file=args.input_csv,
        output_file=args.output,
        symbol=args.symbol,
        timeframe=args.timeframe,
        project_root=ROOT,
    ).to_dict()

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"adapter_version={report['adapter_version']} adapter_status={report['adapter_status']}")
    return 0 if report["adapter_status"] == "framework_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
