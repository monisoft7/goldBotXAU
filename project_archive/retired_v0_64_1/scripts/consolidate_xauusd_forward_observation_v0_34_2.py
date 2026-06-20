from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_forward_observation_consolidator import (
    DEFAULT_ADAPTER_PROTOCOL,
    DEFAULT_INPUT_REPORTS,
    DEFAULT_OUTPUT,
    DEFAULT_RUNNER_PROTOCOL,
    build_xauusd_forward_observation_consolidation_v0_34_2,
    save_xauusd_forward_observation_consolidation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolidate v0_34_2 local forward observation journal reports.")
    parser.add_argument("--adapter-protocol", type=Path, default=DEFAULT_ADAPTER_PROTOCOL)
    parser.add_argument("--runner-protocol", type=Path, default=DEFAULT_RUNNER_PROTOCOL)
    parser.add_argument("--input-report", type=Path, action="append", dest="input_reports")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_forward_observation_consolidation_v0_34_2(
        adapter_protocol_path=args.adapter_protocol,
        runner_protocol_path=args.runner_protocol,
        input_report_paths=args.input_reports or DEFAULT_INPUT_REPORTS,
    )
    save_xauusd_forward_observation_consolidation(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"consolidation_status={report['consolidation_status']}")
    return 0 if report["consolidation_status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
