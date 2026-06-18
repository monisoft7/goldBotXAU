# v0_49 Trend Pullback Sample Stability Audit Result

- Audit module: `src/research/xauusd_trend_pullback_sample_stability_audit.py`
- Audit script: `scripts/audit_xauusd_trend_pullback_stability_v0_49.py`
- Audit report: `reports/xauusd_trend_pullback_stability_audit_v0_49.json`
- Source board version: `v0_48`
- Candidate id: `trend_pullback_continuation_directional`
- Candidate rules preserved: `true`
- Audit status: `completed`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Train profit factor: `1.8816690460357557`
- Train expectancy: `0.2045491371207446`
- Train trades: `164`
- Validation profit factor: `4.1448723516886234`
- Validation expectancy: `0.4564440182058163`
- Validation trades: `16`
- Validation trade minimum: `25`
- Validation trade count passed: `false`
- Sample concentration risk: `high`
- Sample concentration reasons: `validation_trade_count_below_fixed_minimum`, `validation_trades_concentrated_in_single_session_or_block`
- Fixed cost sensitivity available: `true`
- Fixed cost R per trade: `0.05`
- Edge broken by fixed cost: `false`
- Stability decision: `promising_but_insufficient_validation_sample`
- Candidate locking allowed pre-OOS: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `38 passed`
- Blocker: `validation_trade_count_below_fixed_minimum_blocks_candidate_locking`
- Warnings: `audit_only_no_oos_no_demo_promotion`, `candidate_rules_reconstructed_from_v0_48_fixed_family_rule`, `sample_concentration_risk:validation_trade_count_below_fixed_minimum`, `sample_concentration_risk:validation_trades_concentrated_in_single_session_or_block`
- Next recommended step: `collect more train/validation-equivalent evidence or stop; do not lock candidate or run OOS`

v0_49 audited the v0_48 best candidate without changing its fixed rule. The audit reconstructed the same `trend_pullback_continuation_directional` train/validation trades from existing local data only and matched the v0_48 source metrics.

The candidate remains promising but insufficient. Train and validation PF/expectancy are positive and the fixed 0.05R cost sensitivity does not break the edge, but validation has only `16` trades versus the fixed `25` minimum. Candidate locking, OOS, demo execution, and live execution remain blocked.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.
