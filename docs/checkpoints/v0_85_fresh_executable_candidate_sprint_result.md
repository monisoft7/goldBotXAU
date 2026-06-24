# v0_85 Fresh Executable Candidate Sprint Result

- Sprint module: `src/research/xauusd_fresh_executable_candidate_sprint.py`
- Sprint script: `scripts/run_xauusd_fresh_executable_candidate_sprint_v0_85.py`
- Sprint report: `reports/xauusd_fresh_executable_candidate_sprint_v0_85.json`
- Sprint version: `v0_85`
- Sprint status: `fresh_executable_candidate_sprint_failed_all_candidates`
- Source closed candidate id: `xauusd_ny_displacement_retest_executable_v0_82`
- Source closure version: `v0_84`
- Candidate count: `3`
- Max candidate count allowed: `3`
- Passing candidates: none
- Selected candidate: none
- Passed all train/validation gates: `false`
- Candidate promotable to OOS review: `false`

Candidates evaluated once:

- `xauusd_ny_opening_range_breakout_executable_v0_85_a`: train trades `642`, validation trades `130`; failed `validation_profit_factor_gate`, `validation_expectancy_gate_R`, `train_max_drawdown_gate_R`, `validation_max_drawdown_gate_R`, `train_max_consecutive_loss_gate`, `validation_max_consecutive_loss_gate`, and `cost_sensitivity_required`.
- `xauusd_london_to_ny_liquidity_sweep_reversal_executable_v0_85_b`: train trades `412`, validation trades `68`; failed `validation_profit_factor_gate`, `validation_expectancy_gate_R`, `train_max_drawdown_gate_R`, `validation_max_drawdown_gate_R`, `train_max_consecutive_loss_gate`, `validation_max_consecutive_loss_gate`, and `cost_sensitivity_required`.
- `xauusd_impulse_pullback_continuation_executable_v0_85_c`: train trades `596`, validation trades `112`; failed `train_max_drawdown_gate_R` and `train_max_consecutive_loss_gate`.

Safety state:

- Train/validation only: `true`
- OOS used: `false`
- Demo execution allowed: `false`
- Live allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Executable order request created: `false`
- Trade recommendation output: `false`
- User-facing buy/sell signal output: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Broad search performed: `false`
- Validation used for parameter choice: `false`
- Existing strategy rules modified: `false`
- Rejected candidates modified: `false`
- v0_26 traded as-is: `false`
- Closed v0_82 rescued again: `false`
- External API called: `false`
- External data downloaded: `false`
- Dataset file created: `false`
- Market CSV created: `false`
- Data CSV touched: `false`

Recommended next step: `v0_86_strategy_family_review_or_stop`

v0_85 evaluated exactly three fresh fixed-rule executable candidate families on existing train/validation data only. No candidate passed all fixed gates, so no failed candidate is promotable to OOS review.
