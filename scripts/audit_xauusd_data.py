from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.xauusd_data_auditor import audit_xauusd_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local XAUUSD M15 CSV readiness.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--pattern", default="xauusd_m15_*.csv")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = audit_xauusd_data(args.data_dir, args.pattern).to_dict()
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"auditor_version={report['auditor_version']} status={report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
