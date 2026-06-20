"""Build the v0_64 repository consolidation plan report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.repository_consolidation_plan import (
    build_repository_consolidation_plan,
    write_repository_consolidation_plan,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0_64 repository consolidation plan.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "repository_consolidation_plan_v0_64.json",
        help="Output report path.",
    )
    parser.add_argument("--json", action="store_true", help="Print the report JSON to stdout.")
    args = parser.parse_args()

    if args.json:
        report = build_repository_consolidation_plan(ROOT)
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        report = write_repository_consolidation_plan(ROOT, args.output)
        print(
            "wrote "
            f"{args.output.relative_to(ROOT)} "
            f"with {report['files_scanned_count']} files scanned and "
            f"{report['failed_experiments_indexed_count']} failed experiments indexed"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
