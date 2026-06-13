from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_paper_shadow_journal import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_GOVERNANCE_REPORT,
    DEFAULT_OUTPUT,
    build_xauusd_paper_shadow_journal_protocol_v0_31,
    save_xauusd_paper_shadow_journal_protocol,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_31 read-only paper-shadow journal protocol.")
    parser.add_argument("--governance-report", type=Path, default=DEFAULT_GOVERNANCE_REPORT)
    parser.add_argument("--candidate-report", type=Path, default=DEFAULT_CANDIDATE_REPORT)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_paper_shadow_journal_protocol_v0_31(
        governance_report_path=args.governance_report,
        candidate_report_path=args.candidate_report,
    )
    save_xauusd_paper_shadow_journal_protocol(report, args.output)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"protocol_version={report['protocol_version']} journal_status={report['journal_status']}")
    return 0 if not report["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
