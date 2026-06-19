# v0_57 Volatility Regime Lead Viability Result

- Audit module: `src/research/xauusd_volatility_regime_lead_viability_audit.py`
- Audit script: `scripts/audit_xauusd_volatility_regime_lead_v0_57.py`
- Audit report: `reports/xauusd_volatility_regime_lead_viability_v0_57.json`
- Audit status: `volatility_lead_viability_completed`
- Source profiler version: `v0_54`
- Source design version: `v0_55`
- Source rejected eval version: `v0_56`
- Lead id: `volatility_regime_profile`
- Session block branch rejected: `true`
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

Viability result:

- Volatility lead viability decision: `volatility_lead_unstable_or_too_weak_reject`
- Validation sample sufficiency: `sufficient`
- Validation total regime observations: `131`
- Fixed elevated-regime validation observations: `116`
- Can produce at least 50 validation trades under fixed rules: `true`
- Candidate design feasible for v0_58: `false`
- Recommended v0_58 candidate design: `{}`
- Sample concentration risk: `high`
- Concentration blocker: `validation_fixed_elevated_regime_observations_concentrated_in_single_year`
- Train dominant regime: `medium_high_volatility_quartile`
- Validation dominant regime: `high_volatility_quartile`
- Fixed elevated group sign: `positive_same_day_bias` in train and validation
- Targeted tests: `48 passed`

Warnings:

- `viability_audit_only_not_backtest_candidate`
- `oos_rows_explicitly_excluded`
- `no_profitability_claim_made`
- `volatility_regime_train_validation_dominant_bucket_differs`
- `sample_concentration_risk:validation_fixed_elevated_regime_observations_concentrated_in_single_year`

Next recommended step: `stop profiler-lead branch or broaden non-OOS research.`

v0_57 audited the v0_54 volatility-regime profile as a viability audit only. The elevated fixed v0_54 volatility labels had enough validation observations and same-sign train/validation behavior, but validation evidence was concentrated entirely in one year, the dominant regime differed between train and validation, and v0_58 candidate-design feasibility stayed false. No fixed v0_58 volatility candidate was created or recommended.

No OOS run, repeated OOS review, retune, threshold search, parameter grid, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, profitability claim, or `data/*.csv` addition was introduced.
