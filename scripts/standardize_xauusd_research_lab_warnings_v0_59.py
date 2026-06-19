from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_research_lab_warning_standardization import (
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_REPORT,
    build_xauusd_research_lab_warning_standardization_v0_59,
    save_xauusd_research_lab_warning_standardization,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Standardize v0_58 XAUUSD research lab warnings.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-report", type=Path, default=DEFAULT_SOURCE_REPORT)
    args = parser.parse_args()

    report = build_xauusd_research_lab_warning_standardization_v0_59(
        source_report_path=args.source_report,
        root=ROOT,
    )
    save_xauusd_research_lab_warning_standardization(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_research_lab_warning_standardization_status={report['standardization_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
