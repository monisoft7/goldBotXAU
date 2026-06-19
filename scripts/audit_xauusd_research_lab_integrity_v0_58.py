from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_research_lab_integrity_audit import (
    DEFAULT_MANIFEST,
    DEFAULT_OUTPUT,
    build_xauusd_research_lab_integrity_audit_v0_58,
    save_xauusd_research_lab_integrity_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_58 XAUUSD research lab integrity audit.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--manifest", type=Path, default=ROOT / DEFAULT_MANIFEST)
    args = parser.parse_args()

    report = build_xauusd_research_lab_integrity_audit_v0_58(
        data_dir=args.data_dir,
        manifest_path=args.manifest,
    )
    save_xauusd_research_lab_integrity_audit(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_research_lab_integrity_status={report['audit_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
