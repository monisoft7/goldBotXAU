"""Split-aware catalog for local low-timeframe XAUUSD CSV files."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_csv

CATALOG_VERSION = "v0_22"
DEFAULT_MANIFEST_PATH = Path("reports") / "xauusd_dataset_manifest_v0_5.json"
LOW_TF_PATTERN = "xauusd_m*.csv"
LOW_TIMEFRAMES = {"M1", "M5", "M10"}
USABLE_CLASSES = {"train_only", "validation_only", "train_validation"}
QUARANTINED_CLASSES = {"oos_only", "mixed_contains_oos"}


@dataclass(frozen=True)
class LowTfCatalogEntry:
    path: str
    filename: str
    source_timeframe: str | None
    split_classification: str
    row_count: int
    train_row_count: int
    validation_row_count: int
    oos_row_count: int
    start_timestamp: str | None
    end_timestamp: str | None
    usable_for_profiler: bool
    quarantine_reason: str | None
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_low_tf_dataset_catalog(
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    pattern: str = LOW_TF_PATTERN,
) -> dict[str, Any]:
    """Classify local low-timeframe CSVs without allowing OOS rows into profiling."""
    manifest = _load_manifest(manifest_path)
    split_policy = manifest.get("split_policy", {})
    root = Path(data_dir)
    files = sorted(path for path in root.glob(pattern) if _infer_timeframe(path) in LOW_TIMEFRAMES) if root.exists() else []
    entries = [_catalog_entry(path, split_policy) for path in files]
    usable_entries = [entry for entry in entries if entry.usable_for_profiler]
    quarantined_entries = [entry for entry in entries if entry.split_classification in QUARANTINED_CLASSES]

    return {
        "catalog_version": CATALOG_VERSION,
        "manifest_path": str(Path(manifest_path)),
        "split_policy": split_policy,
        "data_dir": str(root),
        "low_timeframe_pattern": pattern,
        "file_count": len(entries),
        "usable_file_count": len(usable_entries),
        "quarantined_file_count": len(quarantined_entries),
        "train_validation_row_count": sum(entry.train_row_count + entry.validation_row_count for entry in usable_entries),
        "entries": [entry.to_dict() for entry in entries],
        "safety": {
            "oos_locked": True,
            "oos_rows_available_for_profiler": False,
            "quarantines_oos_only_files": True,
            "quarantines_mixed_oos_files": True,
        },
    }


def load_profiler_rows_from_catalog(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    """Load only train/validation rows from catalog-approved files."""
    split_policy = catalog["split_policy"]
    rows: list[dict[str, Any]] = []
    for entry in catalog.get("entries", []):
        if entry.get("usable_for_profiler") is not True:
            continue
        source_timeframe = entry.get("source_timeframe")
        for row in load_xauusd_csv(entry["path"]):
            split_name = _split_name(str(row["timestamp"]), split_policy)
            if split_name not in {"train", "validation"}:
                continue
            rows.append(
                {
                    "source_file": entry["filename"],
                    "source_timeframe": source_timeframe,
                    "split": split_name,
                    "timestamp": str(row["timestamp"]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0.0)),
                }
            )
    return sorted(rows, key=lambda row: (str(row["source_timeframe"]), str(row["timestamp"])))


def _catalog_entry(path: Path, split_policy: dict[str, str]) -> LowTfCatalogEntry:
    timeframe = _infer_timeframe(path)
    try:
        rows = load_xauusd_csv(path)
        split_counts = {"train": 0, "validation": 0, "out_of_sample": 0, "unusable": 0}
        for row in rows:
            split_counts[_split_name(str(row["timestamp"]), split_policy)] += 1
        classification = _classification(split_counts)
        quarantine_reason = _quarantine_reason(classification)
        return LowTfCatalogEntry(
            path=str(path),
            filename=path.name,
            source_timeframe=timeframe,
            split_classification=classification,
            row_count=len(rows),
            train_row_count=split_counts["train"],
            validation_row_count=split_counts["validation"],
            oos_row_count=split_counts["out_of_sample"],
            start_timestamp=str(rows[0]["timestamp"]) if rows else None,
            end_timestamp=str(rows[-1]["timestamp"]) if rows else None,
            usable_for_profiler=classification in USABLE_CLASSES,
            quarantine_reason=quarantine_reason,
            errors=[],
        )
    except Exception as exc:
        return LowTfCatalogEntry(
            path=str(path),
            filename=path.name,
            source_timeframe=timeframe,
            split_classification="unusable",
            row_count=0,
            train_row_count=0,
            validation_row_count=0,
            oos_row_count=0,
            start_timestamp=None,
            end_timestamp=None,
            usable_for_profiler=False,
            quarantine_reason="csv_unusable_for_low_tf_profile",
            errors=[str(exc)],
        )


def _load_manifest(manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _infer_timeframe(path: Path) -> str | None:
    match = re.search(r"(^|_)m(1|5|10|15)(_|$)", path.stem.lower())
    if not match:
        return None
    return f"M{match.group(2)}"


def _split_name(timestamp: str, split_policy: dict[str, str]) -> str:
    candle_time = datetime.fromisoformat(timestamp)
    if candle_time <= datetime.fromisoformat(split_policy["train_end"]):
        return "train"
    if datetime.fromisoformat(split_policy["validation_start"]) <= candle_time <= datetime.fromisoformat(
        split_policy["validation_end"]
    ):
        return "validation"
    if candle_time >= datetime.fromisoformat(split_policy["oos_start"]):
        return "out_of_sample"
    return "unusable"


def _classification(split_counts: dict[str, int]) -> str:
    if split_counts["unusable"] > 0 or sum(split_counts.values()) == 0:
        return "unusable"
    has_train = split_counts["train"] > 0
    has_validation = split_counts["validation"] > 0
    has_oos = split_counts["out_of_sample"] > 0
    if has_oos and not has_train and not has_validation:
        return "oos_only"
    if has_oos:
        return "mixed_contains_oos"
    if has_train and has_validation:
        return "train_validation"
    if has_train:
        return "train_only"
    if has_validation:
        return "validation_only"
    return "unusable"


def _quarantine_reason(classification: str) -> str | None:
    if classification == "oos_only":
        return "oos_only_file_blocked_from_profiler"
    if classification == "mixed_contains_oos":
        return "mixed_file_contains_oos_blocked_from_profiler"
    if classification == "unusable":
        return "unusable_low_tf_file"
    return None
