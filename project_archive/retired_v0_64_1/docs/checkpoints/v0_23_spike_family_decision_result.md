# v0_23 Spike Family Decision Result

## Decision

`create_fixed_candidate_from_stable_profile_group`

v0_23 read `reports/xauusd_low_tf_spike_profile_v0_22.json` and found stable train/validation behavior available from the v0_22 diagnostic profile. One fixed research-only candidate was created from the strongest stable group. No threshold search, parameter grid, retuning, or OOS evaluation was performed.

Generated reports:

- `reports/xauusd_spike_family_decision_v0_23.json`
- `reports/xauusd_spike_fixed_candidate_v0_23_train_validation.json`

## Fixed Candidate

- candidate_id: `xauusd_low_tf_spike_m5_hour_11_fade_v0_23`
- status: `train_validation_research_candidate_only`
- source profile: `xauusd_low_tf_spike_profile_v0_22`
- source timeframe: `M5`
- spike size bucket: `range_to_atr_1_5_to_2_0`
- session bucket: `block_06_12`
- hour bucket: `11`
- observed behavior label: `fade`
- forward horizon: `3` bars
- OOS status: `locked_not_evaluated`
- eligible for OOS review: `false`

## Train / Validation Evidence

Train:

- sample count: `902`
- 3-bar fade rate: `0.5283018867924528`
- 3-bar continuation rate: `0.4716981132075472`

Validation:

- sample count: `142`
- 3-bar fade rate: `0.5319148936170213`
- 3-bar continuation rate: `0.46808510638297873`

Selection policy:

- selected from v0_22 stable groups only
- largest validation sample count
- then largest train sample count
- then smallest 3-bar tendency-rate gap
- deterministic labels as final tie-breakers

## Safety Confirmation

- OOS rows used: `0`
- OOS remains locked.
- No demo behavior added.
- No live behavior added.
- No order sending or order checking added.
- No execution queue added.
- No trade-direction recommendation output added.
- No rejected candidate was modified or retuned.
- No threshold search or broad parameter optimization was performed.

## Next Step

Future v0_24 should evaluate whether this research-only candidate deserves a fixed train/validation promotion gate definition. Do not open OOS. If a promotion gate cannot be defined without new search or threshold tuning, reject the v0_23 spike candidate and move to a non-spike research family.
