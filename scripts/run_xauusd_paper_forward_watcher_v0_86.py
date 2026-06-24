from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_paper_forward_watcher import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_OUTPUT,
    build_xauusd_paper_forward_watcher_v0_86,
    save_xauusd_paper_forward_watcher_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_86 paper-only forward watcher report.")
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--fixture-csv", type=Path)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_paper_forward_watcher_v0_86(
        candidate_report_path=args.candidate_report,
        fixture_csv_path=args.fixture_csv,
    )
    save_xauusd_paper_forward_watcher_report(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"watch_version={report['watch_version']} watch_status={report['watch_status']}")
    return 0 if not report["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
