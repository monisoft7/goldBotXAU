"""Apply the v0_64_1 reviewed low-risk cleanup plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.repository_cleanup_applier import write_repository_cleanup_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply v0_64_1 repository cleanup.")
    parser.add_argument("--apply", action="store_true", help="Move/delete approved low-risk cleanup files.")
    parser.add_argument("--json", action="store_true", help="Print the cleanup report JSON to stdout.")
    parser.add_argument(
        "--plan",
        type=Path,
        default=ROOT / "reports" / "repository_consolidation_plan_v0_64.json",
        help="Path to the v0_64 consolidation plan.",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=ROOT / "project_archive" / "retired_v0_64_1",
        help="Archive root for retired/generated historical artifacts.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports" / "repository_cleanup_applied_v0_64_1.json",
        help="Output report path.",
    )
    args = parser.parse_args()

    report = write_repository_cleanup_report(
        ROOT,
        plan_path=args.plan,
        archive_root=args.archive_root,
        output_path=args.output,
        apply=args.apply,
    )
    report_text = json.dumps(report, indent=2, sort_keys=True)
    if args.json:
        print(report_text)
    else:
        print(
            f"{report['cleanup_status']} "
            f"archived={report['files_archived_count']} "
            f"deleted={report['files_deleted_count']} "
            f"archive_root={report['archive_root']}"
        )
    return 1 if report["cleanup_status"] == "cleanup_blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
