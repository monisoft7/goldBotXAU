# v0_72 Oil-Conditioned Event Study Result

- Study module: `src/research/xauusd_oil_conditioned_event_study.py`
- Study script: `scripts/run_xauusd_oil_conditioned_event_study_v0_72.py`
- Study report: `reports/xauusd_oil_conditioned_event_study_v0_72.json`
- Study version: `v0_72`
- Source oil quality/design version: `v0_70`
- Source macro context board version: `v0_71`
- Selected oil proxy: `BRN`
- Fallback oil proxy: `WTI`
- Prior research versions considered: `v0_53`, `v0_56`, `v0_60`, `v0_63`, `v0_68`, `v0_71`
- Labels evaluated: `oil_strength`, `oil_weakness`, `oil_shock_up`, `oil_shock_down`, `gold_oil_inflation_pressure_aligned`, `gold_oil_safe_haven_conflict`, `oil_supply_shock_context_candidate`
- Study status: `oil_conditioned_event_study_completed_no_clear_leads`
- Event count: `30`
- Clear lead count: `0`
- Recommended next step: `v0_73_yield_real_yield_context_feasibility_no_strategy`
- BRN M15 copied rows: `10000`
- BRN M15 parseable rows: `10000`
- BRN first timestamp: `2022-12-06T20:00:00`
- BRN last timestamp: `2026-06-22T22:45:00`
- Strongest diagnostic observations: `oil_strength` descriptive-only slice with `12` events; `oil_weakness` descriptive-only slice with `2` events; `oil_shock_down` and `oil_supply_shock_context_candidate` descriptive-only slices with `1` event each
- Targeted tests: `66 passed`

Safety state:

- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
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
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Lookahead risk detected: `false`

v0_72 is diagnostic research only. It does not create strategy rules, trade filters, blockers, signals, execution logic, OOS review, retune work, threshold search, parameter grids, or persistent aligned market CSV datasets.
