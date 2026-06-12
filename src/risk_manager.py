"""Risk configuration validation for research-only mode."""

from __future__ import annotations

EXECUTION_FLAGS = (
    "execution_enabled",
    "demo_enabled",
    "live_enabled",
    "order_send_enabled",
)


def validate_research_risk_config(config: dict[str, object]) -> dict[str, object]:
    """Validate that execution-related flags remain disabled."""
    enabled = [flag for flag in EXECUTION_FLAGS if config.get(flag) is not False]
    if enabled:
        raise ValueError(f"Execution-related flags must remain false: {', '.join(enabled)}")

    risk_pct = config.get("max_risk_per_trade_pct")
    if not isinstance(risk_pct, (int, float)) or risk_pct < 0:
        raise ValueError("max_risk_per_trade_pct must be a non-negative number.")

    return config
