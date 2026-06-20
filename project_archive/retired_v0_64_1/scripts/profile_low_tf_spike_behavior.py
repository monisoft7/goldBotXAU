from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.xauusd_low_tf_dataset_catalog import DEFAULT_MANIFEST_PATH
from src.research.xauusd_low_tf_spike_profiler import profile_low_tf_spike_behavior


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the diagnostic-only XAUUSD low-timeframe spike profiler.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument("--pattern", default="xauusd_m*.csv")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--output")
    args = parser.parse_args()

    report = profile_low_tf_spike_behavior(args.data_dir, args.manifest, args.pattern)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    if args.as_json:
        print(text)
    else:
        print(f"profiler_version={report['profiler_version']} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
