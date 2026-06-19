# Research Lab Gate Policy

Version: v0_59

This policy documents validation gate semantics. It keeps all existing gates unchanged and does not promote, retune, or create a strategy candidate.

## Current Fixed Gate

The v0_58 lab integrity audit reviewed the fixed validation trade floor of `validation_trades >= 50` for candidate promotion contexts.

## Low-Frequency Caveat

The fixed validation trade floor can reject low-frequency candidates because there is insufficient validation evidence. That outcome is not necessarily evidence of negative edge. Future reports should distinguish `insufficient_validation_sample` from `negative_edge` where the data supports that distinction.

## Standard

- Do not lower `validation_trades_min`.
- Do not lower train or validation profit-factor gates.
- Do not treat low-frequency caveats as permission to retune, threshold search, parameter grid, or run OOS.
- Continue to record low-frequency false-negative risk when relevant.

## Machine Policy

- `low_frequency_false_negative_risk_documented = true`
- `validation_trade_minimum_lowered = false`
- `gates_lowered = false`
