from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_forward_observation_ledger import (
    DEFAULT_INPUT_REPORTS,
    DEFAULT_OUTPUT,
    build_xauusd_forward_observation_ledger_v0_35,
    save_xauusd_forward_observation_ledger,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_35 XAUUSD forward observation sample ledger.")
    parser.add_argument("--input-report", type=Path, action="append", dest="input_reports")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_forward_observation_ledger_v0_35(
        input_consolidated_report_paths=args.input_reports or DEFAULT_INPUT_REPORTS,
    )
    save_xauusd_forward_observation_ledger(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"ledger_status={report['ledger_status']}")
    return 0 if report["ledger_status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
