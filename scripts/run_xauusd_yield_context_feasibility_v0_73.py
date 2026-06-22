"""Run the v0_73 XAUUSD yield context feasibility audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_yield_context_feasibility import build_yield_context_feasibility_report, write_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_73 yield context feasibility audit.")
    parser.add_argument("--json", action="store_true", help="Print the report JSON.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "xauusd_yield_context_feasibility_v0_73.json",
        help="Path for the generated JSON report.",
    )
    args = parser.parse_args()

    report = build_yield_context_feasibility_report(ROOT)
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    write_report(report, output_path)

    report_text = json.dumps(report, indent=2, sort_keys=True)
    if args.json:
        print(report_text)
    else:
        print(f"v0_73 yield context feasibility audit: {report['audit_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
