from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_context_labeled_event_study import (
    DEFAULT_LABEL_REPORT,
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT,
    DEFAULT_V0_53_REPORT,
    DEFAULT_V0_55_REPORT,
    DEFAULT_V0_56_REPORT,
    DEFAULT_V0_60_REPORT,
    build_xauusd_context_labeled_event_study_v0_63,
    save_xauusd_context_labeled_event_study,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_63 XAUUSD context-labeled retrospective event study.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--manifest", type=Path, default=ROOT / DEFAULT_MANIFEST)
    parser.add_argument("--label-report", type=Path, default=ROOT / DEFAULT_LABEL_REPORT)
    parser.add_argument("--source-v0-53", type=Path, default=ROOT / DEFAULT_V0_53_REPORT)
    parser.add_argument("--source-v0-55", type=Path, default=ROOT / DEFAULT_V0_55_REPORT)
    parser.add_argument("--source-v0-56", type=Path, default=ROOT / DEFAULT_V0_56_REPORT)
    parser.add_argument("--source-v0-60", type=Path, default=ROOT / DEFAULT_V0_60_REPORT)
    args = parser.parse_args()

    report = build_xauusd_context_labeled_event_study_v0_63(
        data_dir=args.data_dir,
        manifest_path=args.manifest,
        label_report_path=args.label_report,
        source_v0_53_path=args.source_v0_53,
        source_v0_55_path=args.source_v0_55,
        source_v0_56_path=args.source_v0_56,
        source_v0_60_path=args.source_v0_60,
    )
    save_xauusd_context_labeled_event_study(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_context_labeled_event_study_status={report['context_study_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
