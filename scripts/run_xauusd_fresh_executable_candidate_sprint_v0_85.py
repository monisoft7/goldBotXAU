from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_fresh_executable_candidate_sprint import (  # noqa: E402
    write_xauusd_fresh_executable_candidate_sprint_v0_85,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_85 fresh executable candidate sprint.")
    parser.add_argument("--json", action="store_true", help="Print the generated report JSON.")
    args = parser.parse_args()

    report = write_xauusd_fresh_executable_candidate_sprint_v0_85(ROOT)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report["sprint_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
