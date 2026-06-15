from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_compression_expansion_promotion_gate import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_DECISION_REPORT,
    DEFAULT_OUTPUT_REPORT,
    decide_compression_expansion_promotion_gate_v0_27,
    save_compression_expansion_promotion_gate_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the v0_27 XAUUSD compression-expansion promotion gate.")
    parser.add_argument("--candidate-report", default=str(ROOT / DEFAULT_CANDIDATE_REPORT))
    parser.add_argument("--decision-report", default=str(ROOT / DEFAULT_DECISION_REPORT))
    parser.add_argument("--output", default=str(ROOT / DEFAULT_OUTPUT_REPORT))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = decide_compression_expansion_promotion_gate_v0_27(args.candidate_report, args.decision_report)
    save_compression_expansion_promotion_gate_report(report, args.output)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"gate_version={report['gate_version']} decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
