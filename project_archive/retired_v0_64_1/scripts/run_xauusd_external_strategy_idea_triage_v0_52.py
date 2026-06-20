from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_external_strategy_idea_triage import (
    DEFAULT_OUTPUT,
    build_xauusd_external_strategy_idea_triage_v0_52,
    save_xauusd_external_strategy_idea_triage,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_52 XAUUSD external strategy idea intake triage.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_external_strategy_idea_triage_v0_52()
    save_xauusd_external_strategy_idea_triage(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_external_strategy_idea_triage_status={report['triage_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
