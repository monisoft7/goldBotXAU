from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_oil_proxy_context_audit import (
    DEFAULT_OUTPUT,
    build_xauusd_oil_proxy_context_audit_v0_69,
    save_xauusd_oil_proxy_context_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v0_69 XAUUSD Brent/Oil proxy context feasibility audit.")
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=ROOT / DEFAULT_OUTPUT)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--skip-mt5-readonly-discovery", action="store_true")
    args = parser.parse_args()

    report = build_xauusd_oil_proxy_context_audit_v0_69(
        root=args.root,
        attempt_mt5_readonly_discovery=not args.skip_mt5_readonly_discovery,
    )
    save_xauusd_oil_proxy_context_audit(report, args.output)

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"xauusd_oil_proxy_context_audit_status={report['audit_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
