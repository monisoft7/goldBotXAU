"""Train-only strategy family selection board for v0_14 planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.research.candidate_registry import research_candidate_registry

BOARD_VERSION = "v0_13"
DEFAULT_PROFILE_PATH = Path("reports/xauusd_market_profile_v0_10.json")
DEFAULT_DIAGNOSTIC_PATH = Path("reports/xauusd_candidate_stability_v0_12.json")

REJECTED_FAMILY_BY_ID = {
    "xauusd_atr_impulse_reversion_v0_7": "atr_impulse_reversion",
    "xauusd_multi_bar_exhaustion_reversion_v0_8": "multi_bar_exhaustion_reversion",
    "xauusd_session_volatility_expansion_v0_11": "session_volatility_expansion",
}

LOCAL_FAILED_STRATEGY_FAMILIES = [
    "baseline_current_rules",
    "local_threshold_tinkering_variants",
    "productivity_signal_variants",
    "recent_only_promotion_variants",
    "old_hypothesis_lab_outputs",
    "range_break_drawdown_control",
    "old_regime_aware_families",
    "broad_scanner_pending_order_scanner",
    "speaker_tone_as_trade_signal",
    "fomc_direction_as_trade_signal",
]

SAFETY_FLAGS = {
    "demo_enabled": False,
    "live_enabled": False,
    "order_send_allowed": False,
    "execution_queue_enabled": False,
    "buy_sell_output_allowed": False,
    "strategy_logic_added": False,
    "trade_simulation_added": False,
    "oos_evaluated": False,
}


def build_strategy_family_selection_board(
    profile_path: str | Path = DEFAULT_PROFILE_PATH,
    diagnostic_path: str | Path = DEFAULT_DIAGNOSTIC_PATH,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic train-only board without strategy simulation."""

    registry_report = registry or research_candidate_registry()
    profile, missing_profile = _load_json(profile_path)
    diagnostic, missing_diagnostic = _load_json(diagnostic_path)
    missing_inputs = [name for name, missing in (("market_profile", missing_profile), ("stability_diagnostic", missing_diagnostic)) if missing]

    rejected_candidates = _rejected_candidates(registry_report)
    abandoned_families = _abandoned_families(diagnostic)
    forbidden_families = _forbidden_families(rejected_candidates, abandoned_families)
    options = _candidate_family_options(profile, diagnostic, forbidden_families)
    recommended = _select_recommended_family(options, forbidden_families)

    report = {
        "board_version": BOARD_VERSION,
        "status": "inputs_missing" if missing_inputs else "board_ready",
        "input_summary": {
            "rejected_candidates": rejected_candidates,
            "abandoned_families": abandoned_families,
            "oos_locked": True,
            "eligible_for_oos_review_count": int(registry_report.get("eligible_for_oos_review_count", 0) or 0),
            "missing_inputs": missing_inputs,
            "discovery_split": "train",
            "validation_used_for_discovery": False,
        },
        "evidence_summary": _evidence_summary(profile, diagnostic),
        "forbidden_next_families": forbidden_families,
        "candidate_family_options": options,
        "recommended_next_family": recommended["family_name"] if recommended else None,
        "recommended_v0_14_candidate_id": _candidate_id(recommended["family_name"]) if recommended else None,
        "why_this_family": recommended["rationale"] if recommended else "Required train-only inputs are missing.",
        "why_not_others": _why_not_others(options, recommended),
        "oos_policy": {
            "oos_locked": True,
            "oos_review_allowed": False,
        },
        "next_task_prompt_summary": _next_task_prompt_summary(recommended),
        "safety": SAFETY_FLAGS.copy(),
    }
    return _ensure_no_order_words(report)


def _load_json(path: str | Path) -> tuple[dict[str, Any], bool]:
    json_path = Path(path)
    if not json_path.exists():
        return {}, True
    try:
        return json.loads(json_path.read_text(encoding="utf-8")), False
    except json.JSONDecodeError:
        return {}, True


def _rejected_candidates(registry_report: dict[str, Any]) -> list[dict[str, Any]]:
    rejected: list[dict[str, Any]] = []
    for candidate in registry_report.get("candidates", []):
        if candidate.get("status") != "rejected":
            continue
        candidate_id = str(candidate["candidate_id"])
        rejected.append(
            {
                "candidate_id": candidate_id,
                "family_name": REJECTED_FAMILY_BY_ID.get(candidate_id, "unknown"),
                "status": "rejected",
                "do_not_retune": candidate.get("do_not_retune") is True,
                "eligible_for_oos_review": candidate.get("eligible_for_oos_review") is True,
            }
        )
    return rejected


def _abandoned_families(diagnostic: dict[str, Any]) -> list[str]:
    decision = diagnostic.get("diagnostic_decision", {})
    candidate = diagnostic.get("candidate", {})
    if decision.get("next_action") == "abandon_family" and candidate.get("family_name"):
        return [str(candidate["family_name"])]
    return ["session_volatility_expansion"]


def _forbidden_families(rejected_candidates: list[dict[str, Any]], abandoned_families: list[str]) -> list[str]:
    forbidden = {
        "atr_impulse_reversion",
        "multi_bar_exhaustion_reversion",
        "session_volatility_expansion",
        *abandoned_families,
        *LOCAL_FAILED_STRATEGY_FAMILIES,
    }
    for candidate in rejected_candidates:
        family_name = candidate.get("family_name")
        if family_name and family_name != "unknown":
            forbidden.add(str(family_name))
    return sorted(forbidden)


def _evidence_summary(profile: dict[str, Any], diagnostic: dict[str, Any]) -> dict[str, Any]:
    hints = profile.get("candidate_direction_hints", {})
    best_bucket = diagnostic.get("stability_summary", {}).get("best_bucket")
    worst_bucket = diagnostic.get("stability_summary", {}).get("worst_bucket")
    impulse_15 = profile.get("impulse_diagnostic", {}).get("range_to_atr_gte_1.5", {})
    block_12_18 = profile.get("block_profile", {}).get("block_12_18", {})

    return {
        "generic_impulse_bias": "weak" if hints.get("continuation_bias_detected") else "none",
        "generic_reversion_bias": "weak" if hints.get("reversion_bias_detected") else "none",
        "session_volatility_family_status": "abandoned",
        "strongest_train_observations": [
            _format_bucket_observation("best_v0_12_bucket", best_bucket),
            (
                "low volatility bucket was the only positive v0_12 ATR-regime result"
                if best_bucket and best_bucket.get("bucket") == "low_atr"
                else "v0_12 did not show a durable positive regime"
            ),
            (
                "v0_10 12-18 UTC block had elevated next-4-bar movement"
                if block_12_18
                else "v0_10 profile input unavailable"
            ),
        ],
        "weakest_train_observations": [
            _format_bucket_observation("worst_v0_12_bucket", worst_bucket),
            (
                "fixed impulse bins showed near-even continuation and reversal rates"
                if impulse_15
                else "v0_10 impulse diagnostic unavailable"
            ),
            "v0_11 failed broadly enough that the session volatility expansion family is abandoned",
        ],
    }


def _format_bucket_observation(label: str, bucket: dict[str, Any] | None) -> str:
    if not bucket:
        return f"{label}: unavailable"
    return (
        f"{label}: {bucket['bucket']} trades={bucket['trade_count']} "
        f"profit_factor={bucket['profit_factor']} final_equity_r={bucket['final_equity_r']}"
    )


def _candidate_family_options(
    profile: dict[str, Any],
    diagnostic: dict[str, Any],
    forbidden_families: list[str],
) -> list[dict[str, Any]]:
    low_atr = _bucket_by_name(diagnostic, "by_atr_regime", "low_atr")
    high_atr = _bucket_by_name(diagnostic, "by_atr_regime", "high_atr")
    extreme_atr = _bucket_by_name(diagnostic, "by_atr_regime", "extreme_atr")
    blocks = profile.get("block_profile", {})

    options = [
        {
            "family_name": "low_atr_range_expansion_followthrough",
            "rationale": "Use the only positive v0_12 ATR-regime bucket as a fresh fixed hypothesis around expansion after compressed range.",
            "risk": "The positive bucket may be a narrow artifact of the rejected v0_11 setup rather than a stable market behavior.",
            "why_not_blacklisted": "It is not a retune of v0_7, v0_8, or v0_11 and is not in the local failed-family list.",
            "train_only_basis": _bucket_basis(low_atr, "low_atr"),
            "expected_failure_mode": "Fails quickly if low-volatility compression does not retain follow-through under one fixed rule set.",
            "score_0_to_100": 82,
        },
        {
            "family_name": "asia_range_compression_london_response",
            "rationale": "Study response after quieter pre-active periods using train-only session structure, without reviving classic range-break logic.",
            "risk": "Can accidentally become the forbidden range-break family if specified around simple boundary crossing.",
            "why_not_blacklisted": "It is framed as session response behavior, not the old range-break drawdown-control family.",
            "train_only_basis": _session_basis(blocks),
            "expected_failure_mode": "Fails if the pre-active compression condition does not create a distinct active-session response.",
            "score_0_to_100": 74,
        },
        {
            "family_name": "momentum_failure_after_high_atr",
            "rationale": "Use weak high and extreme ATR behavior as a fresh hypothesis that large-range momentum may degrade afterward.",
            "risk": "Could drift back into generic impulse reversion, which v0_10 explicitly discouraged.",
            "why_not_blacklisted": "It is only acceptable if defined as high-ATR failure context, not generic impulse reversal.",
            "train_only_basis": _high_atr_basis(high_atr, extreme_atr),
            "expected_failure_mode": "Fails if high-ATR weakness is just v0_11-specific noise and has no fixed behavioral edge.",
            "score_0_to_100": 68,
        },
    ]
    for option in options:
        option["blacklisted"] = option["family_name"] in forbidden_families
    return options


def _bucket_by_name(diagnostic: dict[str, Any], breakdown_name: str, bucket_name: str) -> dict[str, Any] | None:
    for bucket in diagnostic.get("breakdowns", {}).get(breakdown_name, []):
        if bucket.get("bucket") == bucket_name:
            return bucket
    return None


def _bucket_basis(bucket: dict[str, Any] | None, label: str) -> str:
    if not bucket:
        return f"{label} train diagnostic bucket unavailable; treat as lower confidence."
    return (
        f"{label} train bucket: trades={bucket['trade_count']}, "
        f"profit_factor={bucket['profit_factor']}, expectancy={bucket['expectancy']}."
    )


def _session_basis(blocks: dict[str, Any]) -> str:
    quiet = blocks.get("block_00_06", {})
    active = blocks.get("block_12_18", {})
    if not quiet or not active:
        return "Session profile input unavailable; treat as lower confidence."
    return (
        "Train profile shows lower 00-06 UTC average range-to-ATR "
        f"({quiet.get('average_range_to_atr')}) before elevated 12-18 UTC movement "
        f"({active.get('average_next_4bar_abs_return_to_atr')})."
    )


def _high_atr_basis(high_atr: dict[str, Any] | None, extreme_atr: dict[str, Any] | None) -> str:
    parts = []
    for label, bucket in (("high_atr", high_atr), ("extreme_atr", extreme_atr)):
        parts.append(_bucket_basis(bucket, label))
    return " ".join(parts)


def _select_recommended_family(options: list[dict[str, Any]], forbidden_families: list[str]) -> dict[str, Any] | None:
    allowed = [option for option in options if option["family_name"] not in forbidden_families]
    return max(allowed, key=lambda option: option["score_0_to_100"], default=None)


def _candidate_id(family_name: str) -> str:
    return f"xauusd_{family_name}_v0_14"


def _why_not_others(options: list[dict[str, Any]], recommended: dict[str, Any] | None) -> dict[str, str]:
    if recommended is None:
        return {option["family_name"]: "No recommendation because required inputs are missing." for option in options}
    return {
        option["family_name"]: (
            "Selected as the highest-scored train-only non-blacklisted family."
            if option["family_name"] == recommended["family_name"]
            else option["risk"]
        )
        for option in options
    }


def _next_task_prompt_summary(recommended: dict[str, Any] | None) -> str:
    if recommended is None:
        return "Restore v0_10 profile and v0_12 diagnostic inputs, then rerun the v0_13 selection board."
    return (
        f"v0_14 should implement exactly one fixed train/validation candidate for "
        f"{recommended['family_name']}; keep OOS locked and do not retune rejected families."
    )


def _ensure_no_order_words(report: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(report)
    if "B" + "UY" in text or "S" + "ELL" in text:
        raise ValueError("Board report contains forbidden trade instruction text.")
    return report
