from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.candidate_registry import research_candidate_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="List known XAUUSD research candidates.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = research_candidate_registry()
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"registry_version={report['registry_version']} "
            f"candidate_count={report['candidate_count']} "
            f"rejected_count={report['rejected_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
