# v0_24 Spike Promotion Gate Result

## Decision

`reject_train_validation_candidate`

v0_24 evaluated only `reports/xauusd_spike_fixed_candidate_v0_23_train_validation.json` using a fixed, conservative train/validation promotion gate. No OOS rows were read or evaluated. No candidate rules, thresholds, or parameters were changed.

Generated report:

- `reports/xauusd_spike_promotion_gate_v0_24.json`

## Fixed Gate Result

- candidate_id: `xauusd_low_tf_spike_m5_hour_11_fade_v0_23`
- registry status: `rejected_train_validation_gate_failed`
- spike family status: `abandoned`
- eligible for OOS review: `false`
- OOS status: `locked_not_evaluated`

The candidate passed train/validation directional consistency, but failed the conservative promotion requirements:

- validation sample size: `142`, required `200`
- train 3-bar target rate: `0.5283018867924528`, required `0.55`
- validation 3-bar target rate: `0.5319148936170213`, required `0.56`
- validation 3-bar edge over neutral: `0.03191489361702127`, required `0.06`
- train forward horizon consistency failed across `1/3/6` bars
- validation forward horizon consistency failed across `1/3/6` bars

The evidence was marginal and did not justify future OOS review eligibility.

## Registry / Counts

- Candidate registry version: `v0_24`
- Candidate registry total records: `7`
- Rejected candidate count: `6`
- Eligible for OOS review count: `0`
- Rejected/do-not-retune old candidates unchanged: `5`

## Safety Confirmation

- OOS rows used: `0`
- OOS remains locked.
- No demo behavior added.
- No live behavior added.
- No order sending or order checking added.
- No execution queue added.
- No trade-direction recommendation output added.
- No rejected candidate was modified or retuned.
- No threshold search, grid search, or parameter optimization was performed.

## Tests

- Focused tests: `53 passed`
- Full suite: `264 passed`

## Next Step

Move away from the low-timeframe spike family unless a future non-retuned fixed hypothesis is separately justified before evaluation. Keep OOS locked and select a new train/validation-only research direction.
