# v0_51 Trend Pullback Expanded Retest Result

- Retest module: `src/research/xauusd_trend_pullback_expanded_retest.py`
- Retest script: `scripts/run_xauusd_trend_pullback_expanded_retest_v0_51.py`
- Retest report: `reports/xauusd_trend_pullback_expanded_retest_v0_51.json`
- Retest status: `expanded_evidence_failed`
- Candidate id: `trend_pullback_continuation_directional`
- Source candidate board version: `v0_48`
- Source stability audit version: `v0_49`
- Source data feasibility version: `v0_50`
- Candidate rules preserved: `true`
- Expanded range: `2019-01-02T06:00:00` to `2022-12-30T21:55:00`
- Train/validation-equivalent only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Candle count by timeframe: `M5=281152`, `M10=141464`
- Expanded trade count: `230`
- Expanded profit factor: `1.1861259380980205`
- Expanded expectancy: `0.0574451807402551`
- Expanded win rate: `0.5652173913043478`
- Expanded years with trades: `4`
- Max single-year trade share: `0.2782608695652174`
- Sample concentration risk: `low`
- Expanded evidence passed gate: `false`
- Gate blocker: `expanded_profit_factor_below_fixed_gate`
- Candidate locking allowed pre-OOS: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Next recommended step: `stop trend_pullback branch or broaden non-OOS research`
- Targeted tests: `41 passed`

v0_51 retested the exact fixed v0_48 `trend_pullback_continuation_directional` rule on the older range made feasible by v0_50. This was expanded train/validation-equivalent evidence only, not OOS, not a retune, and not a parameter or threshold search.

The additional evidence reduced the sample concentration issue: the retest found `230` expanded trades across `4` calendar years with low concentration risk. However, the expanded profit factor was `1.1861259380980205`, below the fixed `1.20` gate, so the candidate is not allowed to lock pre-OOS.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.
