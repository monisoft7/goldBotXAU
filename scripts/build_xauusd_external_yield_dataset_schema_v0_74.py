"""Build the v0_74 external yield dataset schema report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_external_yield_dataset_schema import (
    build_external_yield_dataset_schema_report,
    write_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_74 external yield dataset schema report.")
    parser.add_argument("--json", action="store_true", help="Print the report JSON.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "xauusd_external_yield_dataset_schema_v0_74.json",
        help="Path for the generated JSON report.",
    )
    args = parser.parse_args()

    report = build_external_yield_dataset_schema_report(ROOT)
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    write_report(report, output_path)

    report_text = json.dumps(report, indent=2, sort_keys=True)
    if args.json:
        print(report_text)
    else:
        print(f"v0_74 external yield dataset schema: {report['schema_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
