# v0_82 Executable Fixed-Rule Candidate Design Result

- Design module: `src/research/xauusd_executable_fixed_rule_candidate_design.py`
- Design script: `scripts/build_xauusd_executable_fixed_rule_candidate_design_v0_82.py`
- Design report: `reports/xauusd_executable_fixed_rule_candidate_design_v0_82.json`
- Design version: `v0_82`
- Design status: `executable_fixed_rule_candidate_design_completed`
- Candidate id: `xauusd_ny_displacement_retest_executable_v0_82`
- Candidate family: `ny_displacement_retest_continuation`
- Source re-entry board version: `v0_81`
- Symbol: `XAUUSD`
- Intended timeframes: `M5`, `M15`
- Explicit side mapping: `true`
- Direction ambiguity resolved: `true`
- Buy rule defined: `true`
- Sell rule defined: `true`
- Order request ready: `false`
- Execution ready: `false`

Fixed-rule design:

- Long side is valid only after bullish displacement plus a controlled M5 retest/hold above the broken level.
- Short side is valid only after bearish displacement plus a controlled M5 retest/hold below the broken level.
- No side is valid when direction context is missing, ambiguous, or opposite the displacement direction.
- The design defines setup preconditions, bullish/bearish displacement, retest/hold, entry, invalidation/stop concept, target/exit concept, time stop concept, max-one-position concept, no-overlap behavior, spread/cost placeholder, missing-data behavior, and no-trade conditions.
- DXY/Oil/Yield context layers remain diagnostic only and are not trade filters in v0_82.

Anti-retune guard:

- Not a retune of rejected candidates: `true`
- Rejected candidates not modified: `true`
- Rejected candidates not reused as the same rule: `true`
- v0_26 not traded as-is: `true`
- v0_26 direction problem acknowledged: `true`

Future v0_83 plan only:

- Recommended next step: `v0_83_executable_candidate_train_validation_evaluation_no_oos`
- Train/validation only: `true`
- OOS allowed in v0_83: `false`
- Minimum train trade count gate: `60`
- Minimum validation trade count gate: `25`
- Validation profit factor gate: `1.25`
- Validation expectancy gate: `0.05R`
- Max drawdown gate: `8.0R`
- Max consecutive loss gate: `5`
- Cost sensitivity required: `true`
- Timestamp policy required: `true`
- No OOS until train/validation gates pass: `true`

Safety state:

- OOS allowed now: `false`
- Demo allowed now: `false`
- Live allowed now: `false`
- Strategy testing performed: `false`
- Train/validation performed: `false`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Existing strategy rules modified: `false`
- Rejected candidates modified: `false`
- External API called: `false`
- External data downloaded: `false`
- Dataset file created: `false`
- Market CSV created: `false`
- Data CSV touched: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Approved for strategy testing: `false`
- Approved for OOS: `false`
- Approved for demo: `false`

v0_82 is candidate design only. It creates a structured fixed-rule design artifact for one new XAUUSD candidate with explicit internal side mapping. It does not read market data for evaluation, compute performance, create trade signals, create an order path, run train/validation, run OOS, retune rejected candidates, search thresholds, run a parameter grid, modify old strategy rules, call external APIs, download data, create datasets, touch `data/*.csv`, enable demo/live execution, call order sending/checking, or output trade recommendations.
