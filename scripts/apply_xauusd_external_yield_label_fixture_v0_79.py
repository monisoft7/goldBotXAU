"""Apply v0_79 external yield labels to controlled fixture data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_external_yield_label_fixture_application import (
    build_label_fixture_application_report,
)

REPORT_PATH = ROOT / "reports" / "xauusd_external_yield_label_fixture_application_v0_79.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply v0_79 external yield labels to synthetic fixture records only."
    )
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    args = parser.parse_args()

    report = build_label_fixture_application_report()
    report_text = json.dumps(report, indent=2, sort_keys=True)
    REPORT_PATH.write_text(report_text + "\n", encoding="utf-8")

    if args.json:
        print(report_text)
    else:
        print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
