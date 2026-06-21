from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_dxy_proxy_quality_ranker import (
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE_AUDIT,
    build_xauusd_dxy_proxy_quality_ranker_v0_66,
    save_xauusd_dxy_proxy_quality_ranker,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_66 XAUUSD DXY/USD proxy quality ranker.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=ROOT / DEFAULT_OUTPUT)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-audit", type=Path, default=DEFAULT_SOURCE_AUDIT)
    parser.add_argument("--skip-mt5-readonly-detail", action="store_true")
    args = parser.parse_args()

    report = build_xauusd_dxy_proxy_quality_ranker_v0_66(
        root=args.root,
        source_audit_path=args.source_audit,
        attempt_mt5_readonly_detail=not args.skip_mt5_readonly_detail,
    )
    save_xauusd_dxy_proxy_quality_ranker(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_dxy_proxy_quality_ranker_status={report['ranker_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
