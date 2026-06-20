from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_external_strategy_idea_triage import DEFAULT_OUTPUT as V0_52_OUTPUT
from src.research.xauusd_kimi_external_idea_addendum import (
    DEFAULT_OUTPUT,
    build_xauusd_kimi_external_idea_addendum_v0_52_1,
    save_xauusd_kimi_external_idea_addendum,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_52_1 Kimi external idea addendum.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-report", type=Path, default=ROOT / V0_52_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_kimi_external_idea_addendum_v0_52_1(args.source_report)
    save_xauusd_kimi_external_idea_addendum(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_kimi_external_idea_addendum_status={report['addendum_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
