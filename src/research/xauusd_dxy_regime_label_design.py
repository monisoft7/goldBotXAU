"""v0_67 DXY regime label definitions for XAUUSD research context."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

LABEL_DESIGN_VERSION = "v0_67"
SOURCE_PROXY_RANKER_VERSION = "v0_66"
DEFAULT_SOURCE_RANKER = Path("reports") / "xauusd_dxy_proxy_quality_ranker_v0_66.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_dxy_regime_label_design_v0_67.json"
COMPLETED = "dxy_regime_label_design_completed"
SELECTED_PROXY_SYMBOL = "DXYN"
SECONDARY_PROXY_SYMBOL = "USDX"
RECOMMENDED_NEXT_STEP = "v0_68_dxy_conditioned_event_study_no_strategy_if_labels_pass"

LABEL_NAMES = [
    "dxy_strength",
    "dxy_weakness",
    "dxy_shock_up",
    "dxy_shock_down",
    "gold_dxy_normal_inverse_behavior",
    "gold_dxy_decoupling",
    "dxy_gold_pressure_aligned",
    "dxy_gold_pressure_conflict",
]

SAFETY_FALSE_FLAGS = [
    "lookahead_risk_detected",
    "labels_used_as_trade_blockers",
    "labels_used_for_strategy_testing",
    "aligned_dataset_created",
    "data_csv_touched",
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
    "oos_used",
    "repeated_oos_review",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "executable_candidate_created",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
]


def build_xauusd_dxy_regime_label_design_v0_67(
    *,
    root: str | Path = ".",
    source_ranker_path: str | Path = DEFAULT_SOURCE_RANKER,
    sample_rows: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a design-only DXY regime label report without market dataset export."""
    root_path = Path(root)
    source_path = _resolve(root_path, source_ranker_path)
    source_ranker = _read_json(source_path)
    source_status = _source_status(source_ranker)
    sample_counts = aggregate_sample_label_counts(sample_rows or [])

    report: dict[str, Any] = {
        "label_design_version": LABEL_DESIGN_VERSION,
        "label_design_status": COMPLETED,
        "source_proxy_ranker_version": SOURCE_PROXY_RANKER_VERSION,
        "source_proxy_ranker_status": source_status,
        "source_proxy_ranker_report": str(source_path.as_posix()),
        "selected_proxy_symbol": SELECTED_PROXY_SYMBOL,
        "secondary_proxy_symbol": SECONDARY_PROXY_SYMBOL,
        "labels_defined": label_definitions(),
        "label_count": len(LABEL_NAMES),
        "sample_label_counts_if_available": sample_counts,
        "safe_asof_alignment_required": True,
        "train_validation_only": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "safety": _safety_flags(),
    }
    report.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return report


def save_xauusd_dxy_regime_label_design(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def label_definitions() -> list[dict[str, Any]]:
    common = {
        "timeframe_applicability": ["M5", "M10", "M15"],
        "safe_asof_requirement": (
            "Proxy context must be joined backward in memory so the proxy timestamp is less than "
            "or equal to the XAUUSD timestamp."
        ),
        "no_lookahead_rule": (
            "The label may use only XAUUSD and proxy fields available at or before the labeled XAUUSD timestamp."
        ),
        "not_a_trade_signal_warning": (
            "Descriptive research context only; not an entry, exit, sizing, filter, blocker, or recommendation."
        ),
    }
    return [
        {
            **common,
            "label_name": "dxy_strength",
            "required_input_fields": ["xauusd_timestamp", "proxy_timestamp", "selected_proxy_symbol", "dxy_return_context"],
            "intended_interpretation": "The selected DXY proxy shows a strengthening USD regime over a fixed research window.",
        },
        {
            **common,
            "label_name": "dxy_weakness",
            "required_input_fields": ["xauusd_timestamp", "proxy_timestamp", "selected_proxy_symbol", "dxy_return_context"],
            "intended_interpretation": "The selected DXY proxy shows a weakening USD regime over a fixed research window.",
        },
        {
            **common,
            "label_name": "dxy_shock_up",
            "required_input_fields": ["xauusd_timestamp", "proxy_timestamp", "selected_proxy_symbol", "dxy_shock_context"],
            "intended_interpretation": "The selected DXY proxy shows an unusually sharp upward move versus predeclared context.",
        },
        {
            **common,
            "label_name": "dxy_shock_down",
            "required_input_fields": ["xauusd_timestamp", "proxy_timestamp", "selected_proxy_symbol", "dxy_shock_context"],
            "intended_interpretation": "The selected DXY proxy shows an unusually sharp downward move versus predeclared context.",
        },
        {
            **common,
            "label_name": "gold_dxy_normal_inverse_behavior",
            "required_input_fields": [
                "xauusd_timestamp",
                "proxy_timestamp",
                "selected_proxy_symbol",
                "xauusd_return_context",
                "dxy_return_context",
            ],
            "intended_interpretation": "Gold and the selected DXY proxy moved in the conventional inverse direction.",
        },
        {
            **common,
            "label_name": "gold_dxy_decoupling",
            "required_input_fields": [
                "xauusd_timestamp",
                "proxy_timestamp",
                "selected_proxy_symbol",
                "xauusd_return_context",
                "dxy_return_context",
            ],
            "intended_interpretation": "Gold and the selected DXY proxy did not show the conventional inverse relationship.",
        },
        {
            **common,
            "label_name": "dxy_gold_pressure_aligned",
            "required_input_fields": [
                "xauusd_timestamp",
                "proxy_timestamp",
                "selected_proxy_symbol",
                "xauusd_pressure_context",
                "dxy_pressure_context",
            ],
            "intended_interpretation": "DXY and XAUUSD pressure context point to a consistent descriptive macro state.",
        },
        {
            **common,
            "label_name": "dxy_gold_pressure_conflict",
            "required_input_fields": [
                "xauusd_timestamp",
                "proxy_timestamp",
                "selected_proxy_symbol",
                "xauusd_pressure_context",
                "dxy_pressure_context",
            ],
            "intended_interpretation": "DXY and XAUUSD pressure context disagree, indicating descriptive cross-market tension.",
        },
    ]


def aggregate_sample_label_counts(sample_rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Count already-present boolean label columns without creating row-level labels."""
    counts: Counter[str] = Counter()
    for row in sample_rows:
        _assert_sample_row_asof_safe(row)
        for label_name in LABEL_NAMES:
            if row.get(label_name) is True:
                counts[label_name] += 1
    return {label_name: counts[label_name] for label_name in LABEL_NAMES if counts[label_name] > 0}


def _assert_sample_row_asof_safe(row: dict[str, Any]) -> None:
    xau_ts = str(row.get("xauusd_timestamp") or "")
    proxy_ts = str(row.get("proxy_timestamp") or "")
    if xau_ts and proxy_ts and proxy_ts > xau_ts:
        raise ValueError("future proxy timestamp is not allowed for DXY regime labels")


def _safety_flags() -> dict[str, bool]:
    flags = {
        "research_only": True,
        "definitions_only": True,
        "trade_signals_output": False,
        "strategy_rules_created": False,
        "persistent_market_dataset_created": False,
        "train_validation_only": True,
    }
    flags.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return flags


def _source_status(source_ranker: Any) -> str:
    if isinstance(source_ranker, dict) and source_ranker.get("ranker_version") == SOURCE_PROXY_RANKER_VERSION:
        return str(source_ranker.get("ranker_status") or "unknown")
    return "missing_or_invalid_v0_66_source_ranker"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate
