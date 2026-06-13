from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_oos_review_protocol import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_DATASET_MANIFEST,
    DEFAULT_FUTURE_OOS_REPORT,
    DEFAULT_OUTPUT_REPORT,
    DEFAULT_PROMOTION_GATE_REPORT,
    build_xauusd_oos_review_protocol_v0_28,
    save_xauusd_oos_review_protocol_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0_28 XAUUSD OOS review protocol without running OOS.")
    parser.add_argument("--promotion-gate-report", default=str(DEFAULT_PROMOTION_GATE_REPORT))
    parser.add_argument("--candidate-report", default=str(DEFAULT_CANDIDATE_REPORT))
    parser.add_argument("--dataset-manifest", default=str(DEFAULT_DATASET_MANIFEST))
    parser.add_argument("--future-oos-report", default=str(DEFAULT_FUTURE_OOS_REPORT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_REPORT))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = build_xauusd_oos_review_protocol_v0_28(
        promotion_gate_report_path=args.promotion_gate_report,
        candidate_report_path=args.candidate_report,
        dataset_manifest_path=args.dataset_manifest,
        future_oos_report_path=args.future_oos_report,
    )
    save_xauusd_oos_review_protocol_report(report, args.output)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"protocol_version={report['protocol_version']} decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
