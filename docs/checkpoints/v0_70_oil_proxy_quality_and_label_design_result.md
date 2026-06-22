# v0_70 Oil Proxy Quality and Label Design Result

- Design module: `src/research/xauusd_oil_proxy_quality_and_label_design.py`
- Design script: `scripts/run_xauusd_oil_proxy_quality_and_label_design_v0_70.py`
- Design report: `reports/xauusd_oil_proxy_quality_and_label_design_v0_70.json`
- Design status: `oil_proxy_quality_and_label_design_completed`
- Source oil audit version: `v0_69`
- Candidate symbols ranked: `BRN`, `WTI`
- Selected proxy symbol: `BRN`
- Fallback proxy symbol: `WTI`
- Selection reason: `BRN selected by highest deterministic quality score 121 using availability, timeframe support, overlap, gaps, timestamp integrity, OHLC validity, and safe as-of feasibility evidence. WTI kept as fallback with score 118.`
- Quality scores: `BRN=121`, `WTI=118`
- BRN selected timeframe: `M15`
- BRN best overlap rows: `54299`
- WTI best overlap rows: `26182`
- Safe as-of alignment feasible by symbol: `BRN=true`, `WTI=true`
- Selected proxy safe as-of alignment feasible: `true`
- Labels defined: `oil_strength`, `oil_weakness`, `oil_shock_up`, `oil_shock_down`, `gold_oil_inflation_pressure_aligned`, `gold_oil_safe_haven_conflict`, `oil_supply_shock_context_candidate`
- Label count: `7`
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
- Next recommended step: `v0_71_gold_macro_context_board_no_strategy`

v0_70 is macro-context research infrastructure only, not a strategy. It ranks the v0_69 usable oil proxies by deterministic quality evidence and keeps all row handling in memory. No persistent aligned market CSV was created and no `data/*.csv` file was touched.

The oil regime labels are definitions only. They are not active trade labels, not trade blockers, not trade filters, not entry or exit rules, not signal outputs, and not approval for strategy testing.
