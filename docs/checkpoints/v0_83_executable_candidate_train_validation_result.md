# v0_83 Executable Candidate Train/Validation Evaluation Result

- Evaluation module: `src/research/xauusd_executable_candidate_train_validation.py`
- Evaluation script: `scripts/run_xauusd_executable_candidate_train_validation_v0_83.py`
- Evaluation report: `reports/xauusd_executable_candidate_train_validation_v0_83.json`
- Evaluation version: `v0_83`
- Evaluation status: `executable_candidate_train_validation_failed`
- Candidate id: `xauusd_ny_displacement_retest_executable_v0_82`
- Source design version: `v0_82`
- Train/validation only: `true`
- OOS used: `false`
- OOS allowed now: `false`
- Candidate promotable to OOS review: `false`
- Targeted tests: `76 passed`

Fixed-rule result:

- Train trades: `443`
- Validation trades: `80`
- Train win rate: `0.46952595936794583`
- Validation win rate: `0.4625`
- Train profit factor: `1.2090379041619788`
- Validation profit factor: `1.189712471424468`
- Train expectancy R: `0.10335784421797319`
- Validation expectancy R: `0.09679576294770034`
- Train max drawdown R: `17.00780599375519`
- Validation max drawdown R: `8.087901279760274`
- Train max consecutive losses: `9`
- Validation max consecutive losses: `6`

Gate result:

- Minimum train trade count gate: passed
- Minimum validation trade count gate: passed
- Validation profit factor gate: failed
- Validation expectancy gate R: passed
- Train max drawdown gate R: failed
- Validation max drawdown gate R: failed
- Train max consecutive loss gate: failed
- Validation max consecutive loss gate: failed
- Cost sensitivity required: passed

Failure reasons:

- `validation_profit_factor_gate`
- `train_max_drawdown_gate_R`
- `validation_max_drawdown_gate_R`
- `train_max_consecutive_loss_gate`
- `validation_max_consecutive_loss_gate`

Safety state:

- Trade recommendation output: `false`
- Live allowed: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Executable order request created: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Existing strategy rules modified: `false`
- Rejected candidates modified: `false`
- v0_26 traded as-is: `false`
- External API called: `false`
- External data downloaded: `false`
- Dataset file created: `false`
- Market CSV created: `false`
- Data CSV touched: `false`

v0_83 evaluated the fixed v0_82 NY displacement/retest candidate on existing approved train/validation XAUUSD data only. OOS stayed closed, no order path was created, and no candidate rules were changed after seeing results.

Recommended next step: `v0_84_candidate_failure_postmortem_no_retune`
