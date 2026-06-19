# Research Lab Cost Policy

Version: v0_59

This policy standardizes how goldBotXAU research reports describe cost, spread, and slippage assumptions. It does not retroactively change any historical strategy metric, candidate result, gate result, or report decision.

## Current State

The v0_58 lab integrity audit found that cost and spread terms exist in the project, but they are not applied consistently across all train/validation tools. Some fixed candidate reports include after-cost or cost-sensitivity language, and forward-observation schemas can record spread when available. There is no single globally consistent cost model detected across all research tools.

## Standard

- Every future train/validation report must explicitly state whether costs, spread, and slippage were applied.
- Reports with missing, partial, or inconsistent cost fields must include a warning.
- Marginal candidate comparisons must not be promoted as cost-standardized unless they use the same declared cost policy.
- v0_59 does not recompute, overwrite, or normalize historical strategy metrics.

## Machine Policy

- `existing_tools_apply_costs_consistently = false`
- `cost_fields_missing_or_inconsistent_warning = true`
- `historical_metrics_recomputed = false`
- `retroactive_metric_change_allowed = false`
