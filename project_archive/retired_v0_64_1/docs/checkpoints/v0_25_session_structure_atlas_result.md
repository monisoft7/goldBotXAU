# v0_25 Session Structure Research Atlas Result

## Decision

`create_one_fixed_session_candidate_v0_26`

v0_25 profiled fixed, predeclared XAUUSD session-structure families on train/validation low-timeframe data only. No OOS rows were read or evaluated. No strategy candidate was created, and no candidate registry promotion was made.

Generated report:

- `reports/xauusd_session_structure_atlas_v0_25.json`

## Data Scope

- data files used:
  - `data/xauusd_m5_xauusd_2023-01-01_2025-12-31.csv`
  - `data/xauusd_m10_xauusd_m5_xauusd_2023_01_01_2025_12_31_2023-01-03_2025-12-31.csv`
- train rows used: `265112`
- validation rows used: `53373`
- OOS rows used: `0`
- time basis: dataset timestamp hour buckets only
- OOS-only low-timeframe files remained quarantined by the catalog.

## Families Profiled

- `asia_range_to_london_expansion`: weak
- `london_to_ny_handoff_continuation_or_reversal`: weak
- `ny_opening_range_followthrough_or_reversal`: weak
- `compression_then_expansion`: stable
- `trend_day_vs_mean_reversion_day_shape`: weak

## Strongest Family

`compression_then_expansion`

- dominant behavior: `next_block_expansion`
- train sample count: `1286`
- validation sample count: `262`
- train primary metric rate: `0.7846034214618973`
- validation primary metric rate: `0.7137404580152672`
- validation edge over neutral: `0.2137404580152672`
- validation degradation vs train: `0.07086296344663012`
- fixed degradation limit: `0.12`

This is strong enough to justify one future fixed v0_26 research candidate, but v0_25 did not create that candidate.

## Weak Families

- `asia_range_to_london_expansion` had a train expansion rate of `0.6423017107309487`, but validation fell to `0.5153846153846153`, missing the fixed edge/degradation requirements.
- `london_to_ny_handoff_continuation_or_reversal` was near neutral in both splits.
- `ny_opening_range_followthrough_or_reversal` showed validation reversal behavior, but train edge was too small.
- `trend_day_vs_mean_reversion_day_shape` changed dominant behavior between train and validation.

## Safety Confirmation

- OOS rows used: `0`
- OOS remains locked.
- No demo behavior added.
- No live behavior added.
- No order sending or order checking added.
- No execution queue added.
- No trade-direction recommendation output added.
- No threshold search or parameter grid used.
- No candidate registry promotion created.
- No rejected candidate was modified or retuned.
