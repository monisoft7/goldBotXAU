# v0_56 Session Block Directional Bias Evaluation Result

- Evaluation module: `src/research/xauusd_session_block_directional_bias_evaluation.py`
- Evaluation script: `scripts/run_xauusd_session_block_bias_eval_v0_56.py`
- Evaluation report: `reports/xauusd_session_block_bias_eval_v0_56.json`
- Evaluation status: `session_block_candidate_rejected`
- Source design version: `v0_55`
- Source profiler version: `v0_54`
- Candidate id: `session_block_directional_bias_candidate`
- Candidate rules preserved: `true`
- Evaluated candidate count: `1`
- Other v0_55 candidates evaluated: `false`
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
- Data CSV added to git: `false`

Fixed gate result:

- Train profit factor: `1.944079700461015`
- Train expectancy: `0.12169806372142332`
- Train trades: `34`
- Train max consecutive losses: `4`
- Validation profit factor: `0.0`
- Validation expectancy: `-0.38490466623989666`
- Validation trades: `3`
- Validation max consecutive losses: `3`
- Candidate passed train/validation gate: `false`
- Candidate locking allowed pre-OOS: `false`
- Rejected do not retune: `true`
- Targeted tests: `47 passed`

Gate blockers:

- `validation_profit_factor_below_fixed_gate`
- `validation_trades_below_fixed_gate`
- `validation_expectancy_not_positive`
- `validation_profit_factor_less_than_0_75_train_profit_factor`

Warnings:

- `fixed_rule_train_validation_research_only_not_oos`
- `oos_candles_on_disk_excluded_from_evaluation`
- `same_candle_stop_resolution_is_stop_first`
- `excluded_oos_candle_count:10180`
- `sample_concentration_risk:validation_trades_concentrated_in_single_month`
- `sample_concentration_risk:validation_trades_concentrated_in_single_year`
- `sample_concentration_risk:trades_concentrated_in_single_side_by_fixed_design`

Next recommended step: `stop session_block branch or return to profiler leads.`

v0_56 evaluated only the v0_55 recommended `session_block_directional_bias_candidate` using its fixed session, entry, direction, stop, and exit rules. No OOS rows were used for metrics. No retune, threshold search, parameter grid, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, or `data/*.csv` addition was introduced.
