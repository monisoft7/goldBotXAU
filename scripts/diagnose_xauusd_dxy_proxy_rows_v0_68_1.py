from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_dxy_proxy_quality_ranker import (
    DEFAULT_ROW_ADAPTER_OUTPUT,
    build_xauusd_dxy_proxy_row_adapter_report_v0_68_1,
    save_xauusd_dxy_proxy_row_adapter_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose v0_68_1 DXY proxy row parsing/alignment handoff.")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_ROW_ADAPTER_OUTPUT, help="Report output path.")
    parser.add_argument("--skip-mt5-readonly", action="store_true", help="Do not attempt read-only MT5 copy-rates access.")
    args = parser.parse_args()

    report = build_xauusd_dxy_proxy_row_adapter_report_v0_68_1(
        root=ROOT,
        attempt_mt5_readonly=not args.skip_mt5_readonly,
    )
    save_xauusd_dxy_proxy_row_adapter_report(report, args.output)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"xauusd_dxy_proxy_row_adapter_status={report['adapter_status']}")
        print(f"selected_parseable_proxy_symbol_or_null={report['selected_parseable_proxy_symbol_or_null']}")
        print(f"recommended_next_step={report['recommended_next_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
