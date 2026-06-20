# v0_22 Low-Timeframe Spike Profile Result

## Result

v0_22 is complete as diagnostic research only. It added a split-aware low-timeframe dataset catalog and a low-timeframe spike behavior profiler that reads the existing `reports/xauusd_dataset_manifest_v0_5.json` split policy.

Generated report:

- `reports/xauusd_low_tf_spike_profile_v0_22.json`

## Split Safety

- OOS remains locked.
- OOS rows used by the profiler: `0`
- OOS-only files are quarantined.
- Mixed files containing OOS are quarantined entirely.
- Train/validation files can be profiled.

Local low-timeframe catalog result:

- usable files: `2`
- quarantined files: `3`
- usable source timeframes: `M5`, `M10`
- train rows profiled: `265112`
- validation rows profiled: `53373`

Quarantined files:

- `xauusd_m10_xauusd_m1_xauusd_2026_01_01_2026_06_11_2026-01-02_2026-06-11.csv` classified `oos_only`
- `xauusd_m1_xauusd_2026-01-01_2026-01-02.csv` classified `oos_only`
- `xauusd_m1_xauusd_2026-01-01_2026-06-11.csv` classified `oos_only`

## Profile Summary

- spike events profiled: `53490`
- train spike events: `45344`
- validation spike events: `8146`
- stable diagnostic groups found: `10`
- stability rule: fixed timeframe, spike bucket, session, and hour group must have at least `30` train and `30` validation samples, matching train/validation 3-bar tendency, and no more than `0.20` rate gap.

The stable groups were concentrated in fixed M10/M5 low-timeframe spike buckets and showed matching train/validation fade tendency in those fixed groups. This is not a strategy and does not include entries, exits, execution logic, or trade-direction output.

## v0_23 Recommendation

v0_23 may consider one fixed, predeclared strategy candidate derived from the strongest stable group, but only if the candidate definition is frozen before evaluation and does not retune rejected families. If the next task cannot define one fixed candidate without threshold searching, abandon this family or keep it diagnostic-only.

## Safety Confirmation

- No demo behavior added.
- No live behavior added.
- No order sending or order checking added.
- No execution queue added.
- No trade-direction recommendation output added.
- No rejected candidate was modified or retuned.
- No strategy candidate was created in v0_22.
