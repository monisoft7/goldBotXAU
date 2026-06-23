"""v0_78 external yield label design for XAUUSD macro context research.

This module defines descriptive yield and real-yield labels only. It does not
calculate labels on market data and does not create strategy signals.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


LABEL_DESIGN_VERSION = "v0_78"
LABEL_DESIGN_STATUS = "external_yield_label_design_completed"
RECOMMENDED_NEXT_STEP = "v0_79_external_yield_label_fixture_application_no_strategy"

SOURCE_SCHEMA_VERSION = "v0_74"
SOURCE_VALIDATOR_VERSION = "v0_75"
SOURCE_INGESTION_VERSION = "v0_76"
SOURCE_ALIGNMENT_VERSION = "v0_77"

RELEASE_TIMESTAMP_REQUIREMENT = (
    "Each input observation must have an explicit timezone-aware release_timestamp, "
    "or a documented official release-time assumption must be approved before any "
    "future intraday label application."
)
BACKWARD_ASOF_REQUIREMENT = (
    "Future label application may use only observations whose release_timestamp is "
    "at or before the target timestamp; forward or nearest-future joins fail closed."
)
NO_LOOKAHEAD_RULE = (
    "Observation dates alone are not availability proof. Same-day values before "
    "release_timestamp, future releases, and timezone-ambiguous releases are excluded."
)
NOT_A_TRADE_SIGNAL_WARNING = (
    "Descriptive macro-context label only; not a buy/sell signal, not a trade "
    "blocker, and not approved for strategy testing or trade filtering."
)


@dataclass(frozen=True)
class YieldLabelDefinition:
    label_name: str
    required_series: tuple[str, ...]
    required_input_fields: tuple[str, ...]
    timeframe_applicability: str
    release_timestamp_requirement: str
    safe_backward_asof_requirement: str
    no_lookahead_rule: str
    intended_interpretation_for_xauusd_macro_context: str
    not_a_trade_signal_warning: str

    def to_report_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_series"] = list(self.required_series)
        payload["required_input_fields"] = list(self.required_input_fields)
        return payload


BASE_REQUIRED_INPUT_FIELDS = (
    "series_id",
    "observation_date",
    "value",
    "source_name",
    "release_timestamp",
)


def _definition(
    label_name: str,
    required_series: tuple[str, ...],
    interpretation: str,
    extra_fields: tuple[str, ...] = (),
) -> YieldLabelDefinition:
    return YieldLabelDefinition(
        label_name=label_name,
        required_series=required_series,
        required_input_fields=BASE_REQUIRED_INPUT_FIELDS + extra_fields,
        timeframe_applicability=(
            "Daily yield or rate observations may describe future intraday XAUUSD "
            "macro context only after backward as-of eligibility is proven."
        ),
        release_timestamp_requirement=RELEASE_TIMESTAMP_REQUIREMENT,
        safe_backward_asof_requirement=BACKWARD_ASOF_REQUIREMENT,
        no_lookahead_rule=NO_LOOKAHEAD_RULE,
        intended_interpretation_for_xauusd_macro_context=interpretation,
        not_a_trade_signal_warning=NOT_A_TRADE_SIGNAL_WARNING,
    )


def build_label_definitions() -> list[dict[str, Any]]:
    definitions = [
        _definition(
            "nominal_yield_rising",
            ("DGS10", "DGS2"),
            "Nominal Treasury yield context is increasing versus a prior eligible observation.",
            ("comparison_window",),
        ),
        _definition(
            "nominal_yield_falling",
            ("DGS10", "DGS2"),
            "Nominal Treasury yield context is decreasing versus a prior eligible observation.",
            ("comparison_window",),
        ),
        _definition(
            "real_yield_rising",
            ("DFII10", "DFII5"),
            "Real yield context is increasing versus a prior eligible observation.",
            ("comparison_window",),
        ),
        _definition(
            "real_yield_falling",
            ("DFII10", "DFII5"),
            "Real yield context is decreasing versus a prior eligible observation.",
            ("comparison_window",),
        ),
        _definition(
            "yield_shock_up",
            ("DGS10", "DGS2", "DFII10"),
            "A large upward yield move is present for macro-regime description only.",
            ("fixed_shock_reference",),
        ),
        _definition(
            "yield_shock_down",
            ("DGS10", "DGS2", "DFII10"),
            "A large downward yield move is present for macro-regime description only.",
            ("fixed_shock_reference",),
        ),
        _definition(
            "gold_yield_pressure_aligned",
            ("DGS10", "DFII10"),
            "Nominal and real yield context point in the same pressure direction for gold macro review.",
            ("pressure_direction_reference",),
        ),
        _definition(
            "gold_yield_decoupling",
            ("DGS10", "DFII10"),
            "Nominal and real yield context diverge, marking a possible macro-context decoupling.",
            ("pressure_direction_reference",),
        ),
        _definition(
            "breakeven_inflation_rising",
            ("T10YIE",),
            "Inflation breakeven context is increasing versus a prior eligible observation.",
            ("comparison_window",),
        ),
        _definition(
            "breakeven_inflation_falling",
            ("T10YIE",),
            "Inflation breakeven context is decreasing versus a prior eligible observation.",
            ("comparison_window",),
        ),
        _definition(
            "fed_funds_pressure_tightening",
            ("DFF",),
            "Effective Fed funds context indicates tighter policy pressure for macro review.",
            ("comparison_window",),
        ),
        _definition(
            "fed_funds_pressure_easing",
            ("DFF",),
            "Effective Fed funds context indicates easier policy pressure for macro review.",
            ("comparison_window",),
        ),
    ]
    return [definition.to_report_dict() for definition in definitions]


def build_label_design_report() -> dict[str, Any]:
    labels = build_label_definitions()
    return {
        "label_design_version": LABEL_DESIGN_VERSION,
        "label_design_status": LABEL_DESIGN_STATUS,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "source_validator_version": SOURCE_VALIDATOR_VERSION,
        "source_ingestion_version": SOURCE_INGESTION_VERSION,
        "source_alignment_version": SOURCE_ALIGNMENT_VERSION,
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
        "real_xauusd_data_used": False,
        "aligned_dataset_created": False,
        "labels_defined": labels,
        "label_count": len(labels),
        "required_series_by_label": {
            label["label_name"]: label["required_series"] for label in labels
        },
        "release_timestamp_policy_required": True,
        "backward_asof_required": True,
        "no_lookahead_policy_confirmed": True,
        "labels_used_as_trade_blockers": False,
        "labels_used_for_strategy_testing": False,
        "approved_for_strategy_testing": False,
        "approved_for_trade_filtering": False,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "executable_candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "trade_recommendation_output": False,
        "trade_signals_output": False,
        "strategy_rules_created": False,
        "strategy_rules_modified": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "warnings": [
            "label_design_only_not_real_data_ingestion",
            "labels_are_descriptive_macro_context_only",
            "no_xauusd_alignment_or_persistent_dataset_created",
            "labels_are_not_trade_blockers_or_trade_filters",
        ],
    }
