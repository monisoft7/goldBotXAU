from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_oil_proxy_quality_and_label_design import (
    DEFAULT_AUDIT_REPORT,
    DEFAULT_OUTPUT_REPORT,
    build_and_write_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_70 oil proxy quality ranking and label design report.")
    parser.add_argument("--audit-report", type=Path, default=ROOT / DEFAULT_AUDIT_REPORT)
    parser.add_argument("--output", type=Path, default=ROOT / DEFAULT_OUTPUT_REPORT)
    parser.add_argument("--json", action="store_true", help="Print the generated report JSON.")
    args = parser.parse_args()

    report = build_and_write_report(args.audit_report, args.output)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            "Built "
            f"{args.output} with status={report['design_status']} "
            f"selected_proxy={report['selected_proxy_symbol_or_null']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
