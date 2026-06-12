"""Deterministic XAUUSD M15 dataset manifest and split builder."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_m15_csvs
from src.data.xauusd_data_auditor import audit_xauusd_data

MANIFEST_VERSION = "v0_5"
TIMEFRAME = "M15"
TRAIN_END = "2025-06-30T23:59:59"
VALIDATION_START = "2025-07-01T00:00:00"
VALIDATION_END = "2025-12-31T23:59:59"
OOS_START = "2026-01-01T00:00:00"


@dataclass(frozen=True)
class DatasetManifest:
    manifest_version: str
    status: str
    dataset: dict[str, Any]
    quality: dict[str, Any]
    splits: dict[str, dict[str, Any]]
    split_policy: dict[str, str]
    readiness: dict[str, Any]
    safety: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def build_xauusd_dataset_manifest(
    data_dir: str | Path = "data",
    pattern: str = "xauusd_m15_*.csv",
) -> DatasetManifest:
    audit = audit_xauusd_data(data_dir, pattern).to_dict()
    records: list[dict[str, float | str]] = []
    load_error: str | None = None

    if audit["status"] != "no_local_data_found":
        try:
            records = load_xauusd_m15_csvs(data_dir, pattern).records
        except ValueError as exc:
            load_error = str(exc)

    splits = _empty_splits()
    if records:
        splits = _build_splits(records)

    blocker_reasons = _blocker_reasons(audit, splits, load_error)
    ready = not blocker_reasons
    warnings = list(audit["warnings"])
    if _split_warning_needed(splits, records):
        warnings.append("One or more split periods are not covered by the local dataset.")

    if audit["status"] == "no_local_data_found":
        status = "no_local_data_found"
    elif audit["status"] == "data_invalid" or load_error:
        status = "manifest_invalid"
    elif ready and warnings:
        status = "manifest_has_warnings"
    elif ready:
        status = "manifest_ready"
    else:
        status = "manifest_has_warnings"

    dataset = {
        "symbol_scope": "XAUUSD_ONLY",
        "timeframe": TIMEFRAME,
        "file_count": audit["file_count"],
        "candle_count": audit["candle_count"],
        "start_timestamp": audit["start_timestamp"],
        "end_timestamp": audit["end_timestamp"],
        "detected_timeframe_minutes": audit["detected_timeframe_minutes"],
        "auditor_status": audit["status"],
        "usable_for_backtest": audit["usable_for_backtest"],
    }
    quality = {
        "duplicate_timestamp_count": audit["duplicate_timestamp_count"],
        "invalid_ohlc_count": audit["invalid_ohlc_count"],
        "non_positive_price_count": audit["non_positive_price_count"],
        "missing_bar_count": audit["missing_bar_count"],
        "large_gap_count": audit["large_gap_count"],
        "weekend_gap_count": audit["weekend_gap_count"],
        "flat_candle_count": audit["flat_candle_count"],
        "warnings": warnings,
        "errors": [*audit["errors"], *([load_error] if load_error else [])],
    }

    return DatasetManifest(
        manifest_version=MANIFEST_VERSION,
        status=status,
        dataset=dataset,
        quality=quality,
        splits=splits,
        split_policy=_split_policy(),
        readiness={
            "ready_for_strategy_research": ready,
            "blocker_reasons": blocker_reasons,
            "warnings": warnings,
        },
        safety={
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
            "strategy_logic_added": False,
        },
    )


def save_manifest(manifest: DatasetManifest, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.to_json() + "\n", encoding="utf-8")
    return path


def _build_splits(records: list[dict[str, float | str]]) -> dict[str, dict[str, Any]]:
    timestamps = [datetime.fromisoformat(str(record["timestamp"])) for record in records]
    total = len(timestamps)
    train_end = datetime.fromisoformat(TRAIN_END)
    validation_start = datetime.fromisoformat(VALIDATION_START)
    validation_end = datetime.fromisoformat(VALIDATION_END)
    oos_start = datetime.fromisoformat(OOS_START)

    buckets = {
        "train": [stamp for stamp in timestamps if stamp <= train_end],
        "validation": [stamp for stamp in timestamps if validation_start <= stamp <= validation_end],
        "out_of_sample": [stamp for stamp in timestamps if stamp >= oos_start],
    }
    return {
        name: _split_summary(values, total, fallback_start, fallback_end)
        for name, values, fallback_start, fallback_end in [
            ("train", buckets["train"], None, TRAIN_END),
            ("validation", buckets["validation"], VALIDATION_START, VALIDATION_END),
            ("out_of_sample", buckets["out_of_sample"], OOS_START, None),
        ]
    }


def _split_summary(
    timestamps: list[datetime],
    dataset_total: int,
    fallback_start: str | None,
    fallback_end: str | None,
) -> dict[str, Any]:
    count = len(timestamps)
    return {
        "start": timestamps[0].isoformat() if timestamps else fallback_start,
        "end": timestamps[-1].isoformat() if timestamps else fallback_end,
        "candle_count": count,
        "pct_of_dataset": round(count / dataset_total, 6) if dataset_total else 0.0,
    }


def _blocker_reasons(audit: dict[str, Any], splits: dict[str, dict[str, Any]], load_error: str | None) -> list[str]:
    blockers: list[str] = []
    if audit["status"] == "no_local_data_found":
        blockers.append("no_local_data_found")
    if load_error:
        blockers.append("local_csv_load_failed")
    if audit["usable_for_backtest"] is not True:
        blockers.append("auditor_not_usable_for_backtest")
    if audit["duplicate_timestamp_count"]:
        blockers.append("duplicate_timestamps")
    if audit["invalid_ohlc_count"]:
        blockers.append("invalid_ohlc")
    if audit["non_positive_price_count"]:
        blockers.append("non_positive_prices")
    for split_name in ("train", "validation", "out_of_sample"):
        if splits[split_name]["candle_count"] <= 0:
            blockers.append(f"missing_{split_name}_period")
    return blockers


def _split_warning_needed(splits: dict[str, dict[str, Any]], records: list[dict[str, float | str]]) -> bool:
    return bool(records) and any(splits[name]["candle_count"] <= 0 for name in splits)


def _empty_splits() -> dict[str, dict[str, Any]]:
    return {
        "train": {"start": None, "end": TRAIN_END, "candle_count": 0, "pct_of_dataset": 0.0},
        "validation": {"start": VALIDATION_START, "end": VALIDATION_END, "candle_count": 0, "pct_of_dataset": 0.0},
        "out_of_sample": {"start": OOS_START, "end": None, "candle_count": 0, "pct_of_dataset": 0.0},
    }


def _split_policy() -> dict[str, str]:
    return {
        "method": "fixed_chronological_split",
        "train_end": TRAIN_END,
        "validation_start": VALIDATION_START,
        "validation_end": VALIDATION_END,
        "oos_start": OOS_START,
        "leakage_prevention": "chronological_only_no_shuffle",
    }
