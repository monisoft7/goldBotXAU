from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.xauusd_dataset_manifest import build_xauusd_dataset_manifest, save_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the XAUUSD M15 dataset manifest.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--pattern", default="xauusd_m15_*.csv")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--output")
    args = parser.parse_args()

    manifest = build_xauusd_dataset_manifest(args.data_dir, args.pattern)
    output = manifest.to_json()
    if args.output:
        save_manifest(manifest, args.output)
    if args.as_json:
        print(output)
    else:
        data = manifest.to_dict()
        print(f"manifest_version={data['manifest_version']} status={data['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
