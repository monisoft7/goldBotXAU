from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.xauusd_low_tf_dataset_catalog import DEFAULT_MANIFEST_PATH
from src.research.xauusd_session_structure_atlas import profile_xauusd_session_structure_atlas

DEFAULT_OUTPUT_REPORT = Path("reports") / "xauusd_session_structure_atlas_v0_25.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the v0_25 XAUUSD session structure research atlas.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--pattern", default="xauusd_m*.csv")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_REPORT))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = profile_xauusd_session_structure_atlas(args.data_dir, args.manifest, args.pattern)
    report_text = json.dumps(report, indent=2, sort_keys=True)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text + "\n", encoding="utf-8")

    if args.as_json:
        print(report_text)
    else:
        print(
            "profiler_version="
            f"{report['profiler_version']} status={report['status']} next={report['recommended_next_step']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
