from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_forward_observation_orchestrator import (
    APPROVAL_TOKEN,
    DEFAULT_LEDGER,
    DEFAULT_LEDGER_OUTPUT,
    DEFAULT_PROTOCOL_OUTPUT,
    run_xauusd_forward_observation_cycle_v0_36,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one v0_36 read-only XAUUSD forward observation cycle.")
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--to-date", required=True)
    parser.add_argument("--approval-token", required=True)
    parser.add_argument("--m5-csv", type=Path)
    parser.add_argument("--export-m5-from-mt5", action="store_true")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output", type=Path, default=DEFAULT_PROTOCOL_OUTPUT)
    parser.add_argument("--ledger-output", type=Path, default=DEFAULT_LEDGER_OUTPUT)
    parser.add_argument("--prior-consolidated-report", type=Path, action="append", dest="prior_reports")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    args = parser.parse_args()

    report = run_xauusd_forward_observation_cycle_v0_36(
        from_date=args.from_date,
        to_date=args.to_date,
        approval_token=args.approval_token,
        project_root=ROOT,
        data_dir=args.data_dir,
        reports_dir=args.reports_dir,
        m5_csv=args.m5_csv,
        export_m5_from_mt5=args.export_m5_from_mt5,
        symbol=args.symbol,
        ledger_path=args.ledger,
        protocol_output_path=args.output,
        ledger_output_path=args.ledger_output,
        prior_consolidated_reports=args.prior_reports,
    )

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"orchestrator_status={report['orchestrator_status']}")
    return 0 if report["orchestrator_status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
