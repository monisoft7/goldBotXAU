# v0_69 Oil Proxy Context Audit Result

- Audit module: `src/research/xauusd_oil_proxy_context_audit.py`
- Audit script: `scripts/run_xauusd_oil_proxy_context_audit_v0_69.py`
- Audit report: `reports/xauusd_oil_proxy_context_audit_v0_69.json`
- Audit status: `oil_proxy_context_feasibility_completed`
- Candidate symbols checked: `UKOIL`, `XBRUSD`, `BRENT`, `BRENT.fs`, `BRN`, `USOIL`, `WTI`, `XTIUSD`
- Usable proxy symbols: `BRN`, `WTI`
- Selected proxy symbol: `BRN`
- Selected proxy timeframe: `M15`
- Selection reason: `BRN M15 selected by fixed candidate/timeframe order with parseable overlapping rows`
- MT5 read-only candidate symbols available: `BRN`, `WTI`
- MT5 copied rows total: `30000`
- BRN M15 copied rows: `5000`
- BRN M15 parseable rows: `5000`
- BRN M15 first timestamp: `2024-11-22T21:00:00`
- BRN M15 last timestamp: `2026-06-18T22:45:00`
- BRN M15 overlap rows with XAUUSD: `54299`
- Safe as-of alignment feasible: `true`
- Lookahead risk detected: `false`
- Future label candidates only: `oil_strength`, `oil_weakness`, `oil_shock_up`, `oil_shock_down`, `gold_oil_inflation_pressure_aligned`, `gold_oil_safe_haven_conflict`, `oil_supply_shock_context_candidate`
- Labels used as trade blockers: `false`
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
- Targeted tests: `63 passed`
- Next recommended step: `v0_70_oil_proxy_quality_ranking_and_label_design`

v0_69 is macro-context research infrastructure only, not a strategy. It discovered usable read-only MT5 oil proxy rows for `BRN` and `WTI`, selected `BRN` M15 by fixed candidate/timeframe order, and kept all proxy row handling in memory. No persistent aligned market CSV was created and no `data/*.csv` file was touched.

The oil labels listed in this checkpoint are future context candidates only. They are not active labels, not trade blockers, not trade filters, not strategy rules, and not approval for strategy testing.
