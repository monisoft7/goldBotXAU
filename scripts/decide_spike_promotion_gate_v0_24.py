from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_spike_promotion_gate import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_OUTPUT_REPORT,
    decide_spike_promotion_gate_v0_24,
    save_spike_promotion_gate_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the v0_24 XAUUSD spike promotion gate.")
    parser.add_argument("--candidate-report", default=str(DEFAULT_CANDIDATE_REPORT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_REPORT))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = decide_spike_promotion_gate_v0_24(args.candidate_report)
    save_spike_promotion_gate_report(report, args.output)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"gate_version={report['gate_version']} decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
