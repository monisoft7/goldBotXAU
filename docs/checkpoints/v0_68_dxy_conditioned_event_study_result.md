# v0_68 DXY-Conditioned Event Study Result

- Study module: `src/research/xauusd_dxy_conditioned_event_study.py`
- Study script: `scripts/run_xauusd_dxy_conditioned_event_study_v0_68.py`
- Study report: `reports/xauusd_dxy_conditioned_event_study_v0_68.json`
- Study status: `dxy_conditioned_event_study_blocked_missing_data`
- Source proxy ranker version: `v0_66`
- Source label design version: `v0_67`
- Selected proxy symbol: `DXYN`
- Secondary proxy symbol: `USDX`
- Prior research versions considered: `v0_53`, `v0_56`, `v0_60`, `v0_63`
- Labels evaluated: `dxy_strength`, `dxy_weakness`, `dxy_shock_up`, `dxy_shock_down`, `gold_dxy_normal_inverse_behavior`, `gold_dxy_decoupling`, `dxy_gold_pressure_aligned`, `dxy_gold_pressure_conflict`
- Event count: `0`
- Clear lead count: `0`
- Clear leads: none
- Blocker: `selected_proxy_rows_unavailable`
- Read-only proxy summary: DXYN and USDX were visible in the MT5 symbol list, but no parseable DXYN M15 proxy rows were available for safe backward as-of conditioning in this run
- Targeted tests: `62 passed`
- Recommended next step: `v0_69_yield_or_brent_context_feasibility_before_new_strategy`

Safety state:

- Train/validation only: `true`
- OOS used: `false`
- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Lookahead risk detected: `false`
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

v0_68 is diagnostic research only. It considers prior train/validation research observations from the requested source versions where report samples are available, and it fails closed when selected proxy rows cannot be safely observed and aligned in memory. It does not rerun old candidates as strategies, does not change candidate rules, does not create entry or exit decisions, and does not approve DXY labels for filtering.

No persistent aligned market CSV was created, no `data/*.csv` file was touched, and no row-level aligned dataset was exported.
