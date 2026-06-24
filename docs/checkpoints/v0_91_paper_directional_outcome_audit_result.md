# v0_91 Paper Directional Outcome Audit Result

- Task: Produce the first decisive paper-only outcome audit for the v0_90 fixed directional observation layer.
- Audit module: `src/research/xauusd_paper_directional_outcome_audit.py`
- Audit script: `scripts/run_xauusd_paper_directional_outcome_audit_v0_91.py`
- Audit report: `reports/xauusd_paper_directional_outcome_audit_v0_91.json`
- Audit version: `v0_91`
- Source watch version: `v0_90`
- Audit status: `directional_outcome_audit_completed_not_promising`
- Decision: `current_direction_rule_not_promising`
- Run mode: `local_readonly_directional_outcome_audit`
- Data source status: `local_readonly_market_csv`
- Direction annotation method: `fixed_ohlc_structure_no_optimization`
- From date: `2026-01-01`
- Timeframes requested: `M5`, `M10`, `M15`
- Lookback bars: `12`
- Horizon bars: `12`
- Max scan rows: `5000`
- Max directional records: `300`
- Scanned row count: `5000`
- Directional observation count: `300`
- Null direction observation count: `4300`
- Records evaluated: `300`
- Records blocked: `0`
- Outcome counts: `favorable_move_observed=19`, `adverse_move_observed=28`, `both_favorable_and_adverse_observed=253`, `neutral_or_insufficient_move=0`, `blocked_missing_future_rows=0`
- Favorable rate: `0.906667`
- Adverse rate: `0.936667`
- Both favorable and adverse rate: `0.843333`
- Neutral rate: `0.0`
- Average close move points: `1.5966`
- Median close move points: `1.195`
- Average max favorable move points: `15.3464`
- Average max adverse move points: `13.215`
- Recommended next step: `v0_92_kill_current_direction_rule_and_request_alternatives`

v0_91 reads existing local XAUUSD CSV rows under `data/` read-only, applies the v0_90 fixed OHLC `paper_observation_direction` annotator in memory, and evaluates each non-null paper direction over the fixed 12-bar horizon with fixed 2.0 point favorable/adverse diagnostic thresholds.

The result is not promising for the current fixed paper direction rule. Although favorable movement was common, adverse movement was even more common when `both_favorable_and_adverse_observed` is counted into both rates: favorable rate `0.906667` versus adverse rate `0.936667`.

This is not a backtest, not OOS, not a promotion gate, not a strategy optimization, and not a trade recommendation. No OOS evaluation, retune, threshold search, parameter grid, optimization, external API, download, demo/live execution, executable order request, order sending, order checking, market CSV creation, persistent market dataset creation, or `data/*.csv` modification was introduced.
