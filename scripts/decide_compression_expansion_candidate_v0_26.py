from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.xauusd_low_tf_dataset_catalog import DEFAULT_MANIFEST_PATH
from src.research.xauusd_compression_expansion_candidate import (
    DEFAULT_ATLAS_REPORT,
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_DECISION_REPORT,
    decide_compression_expansion_candidate_v0_26,
    save_compression_expansion_decision_reports,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the v0_26 compression expansion candidate decision.")
    parser.add_argument("--atlas-report", default=str(DEFAULT_ATLAS_REPORT))
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--pattern", default="xauusd_m*.csv")
    parser.add_argument("--output", default=str(DEFAULT_DECISION_REPORT))
    parser.add_argument("--candidate-output", default=str(DEFAULT_CANDIDATE_REPORT))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    result = decide_compression_expansion_candidate_v0_26(
        args.atlas_report,
        data_dir=args.data_dir,
        manifest_path=args.manifest,
        pattern=args.pattern,
    )
    save_compression_expansion_decision_reports(result, args.output, args.candidate_output)
    report_text = json.dumps(result.decision_report, indent=2, sort_keys=True)

    if args.as_json:
        print(report_text)
    else:
        print(
            "decision_version="
            f"{result.decision_report['decision_version']} decision={result.decision_report['decision']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
