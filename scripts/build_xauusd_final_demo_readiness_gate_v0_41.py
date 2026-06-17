from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_final_demo_readiness_gate import (
    DEFAULT_OUTPUT,
    DEFAULT_V0_37_REPORT,
    DEFAULT_V0_38_REPORT,
    DEFAULT_V0_39_REPORT,
    DEFAULT_V0_40_REPORT,
    build_xauusd_final_demo_readiness_gate_v0_41,
    save_xauusd_final_demo_readiness_gate,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_41 XAUUSD final demo readiness gate.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--v0-37-report", type=Path, default=DEFAULT_V0_37_REPORT)
    parser.add_argument("--v0-38-report", type=Path, default=DEFAULT_V0_38_REPORT)
    parser.add_argument("--v0-39-report", type=Path, default=DEFAULT_V0_39_REPORT)
    parser.add_argument("--v0-40-report", type=Path, default=DEFAULT_V0_40_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_final_demo_readiness_gate_v0_41(
        v0_37_report_path=args.v0_37_report,
        v0_38_report_path=args.v0_38_report,
        v0_39_report_path=args.v0_39_report,
        v0_40_report_path=args.v0_40_report,
    )
    save_xauusd_final_demo_readiness_gate(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"final_demo_readiness_gate_decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
