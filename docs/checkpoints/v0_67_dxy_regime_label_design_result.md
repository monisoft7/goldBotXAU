# v0_67 DXY Regime Label Design Result

- Label design module: `src/research/xauusd_dxy_regime_label_design.py`
- Label design script: `scripts/run_xauusd_dxy_regime_label_design_v0_67.py`
- Label design report: `reports/xauusd_dxy_regime_label_design_v0_67.json`
- Label design status: `dxy_regime_label_design_completed`
- Source proxy ranker version: `v0_66`
- Selected proxy symbol: `DXYN`
- Secondary proxy symbol: `USDX`
- Labels defined: `dxy_strength`, `dxy_weakness`, `dxy_shock_up`, `dxy_shock_down`, `gold_dxy_normal_inverse_behavior`, `gold_dxy_decoupling`, `dxy_gold_pressure_aligned`, `dxy_gold_pressure_conflict`
- Label count: `8`
- Sample label counts if available: `{}`
- Safe as-of alignment required: `true`
- Lookahead risk detected: `false`
- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Next recommended step: `v0_68_dxy_conditioned_event_study_no_strategy_if_labels_pass`

v0_67 defines DXY regime labels as descriptive research context only. Each label definition records the required input fields, timeframe applicability, safe as-of requirement, no-lookahead rule, intended interpretation, and a warning that the label is not an entry, exit, sizing rule, filter, blocker, or recommendation.

No aligned market CSV was created, no `data/*.csv` file was touched, and no persistent row-level aligned dataset was exported. Optional sample label counting is aggregate-only and in memory.
