# v0_84 Trading Decision Sprint Result

- Sprint module: `src/research/xauusd_trading_decision_sprint.py`
- Sprint script: `scripts/run_xauusd_trading_decision_sprint_v0_84.py`
- Sprint report: `reports/xauusd_trading_decision_sprint_v0_84.json`
- Sprint version: `v0_84`
- Sprint status: `trading_decision_sprint_failed_close_candidate`
- Source candidate id: `xauusd_ny_displacement_retest_executable_v0_82`
- Source design version: `v0_82`
- Source evaluation version: `v0_83`
- Baseline v0_83 status: `executable_candidate_train_validation_failed`
- Selected rescue decision: `ny_core_only_variant`
- Rescue variant evaluated count: `1`
- Passed all train/validation gates: `false`
- Candidate promotable to OOS review: `false`
- Candidate closed: `true`

Train-only diagnostics selected exactly one rescue attempt. Edge-window train damage was concentrated outside the fixed 13:00-16:00 UTC NY core, while side diagnostics and close re-entry clustering did not justify long-only, short-only, or overtrading variants. The rescue was frozen before validation evaluation.

Rescue variant result:

- Train trades: `288`
- Validation trades: `51`
- Validation profit factor: `1.1688868170386062`
- Validation expectancy R: `0.09225452097594823`
- Train max drawdown R: `12.353942652329835`
- Validation max drawdown R: `6.18`
- Train max consecutive losses: `10`
- Validation max consecutive losses: `6`

Failed gates:

- `validation_profit_factor_gate`
- `train_max_drawdown_gate_R`
- `train_max_consecutive_loss_gate`
- `validation_max_consecutive_loss_gate`

Safety state:

- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Executable order request created: `false`
- Trade recommendation output: `false`
- User-facing buy/sell signal output: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Broad search performed: `false`
- Existing strategy rules modified: `false`
- Rejected candidates modified: `false`
- v0_26 traded as-is: `false`
- External API called: `false`
- External data downloaded: `false`
- Dataset file created: `false`
- Market CSV created: `false`
- Data CSV touched: `false`

Recommended next step: `v0_85_fresh_executable_candidate_family_selection_sprint`

v0_84 is the hard stop for this candidate family. It did not run OOS, loosen gates, retune thresholds, run a parameter grid, create a demo/live/order path, touch `data/*.csv`, or output trade recommendations.
