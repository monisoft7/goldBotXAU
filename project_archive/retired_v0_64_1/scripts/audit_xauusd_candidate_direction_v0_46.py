from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_candidate_direction_provenance_audit import (
    CANDIDATE_ID,
    DEFAULT_OUTPUT,
    build_xauusd_candidate_direction_provenance_audit_v0_46,
    save_xauusd_candidate_direction_provenance_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit v0_46 locked XAUUSD candidate direction provenance.")
    parser.add_argument("--candidate-id", default=CANDIDATE_ID)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_xauusd_candidate_direction_provenance_audit_v0_46(candidate_id=args.candidate_id, root=ROOT)
    save_xauusd_candidate_direction_provenance_audit(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_candidate_direction_provenance_status={report['audit_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
