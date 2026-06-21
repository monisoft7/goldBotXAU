# v0_66 DXY Proxy Quality Ranker Result

- Ranker module: `src/research/xauusd_dxy_proxy_quality_ranker.py`
- Ranker script: `scripts/run_xauusd_dxy_proxy_quality_ranker_v0_66.py`
- Ranker report: `reports/xauusd_dxy_proxy_quality_ranker_v0_66.json`
- Ranker status: `dxy_proxy_quality_ranking_completed`
- Source audit version: `v0_65`
- Candidate symbols ranked: `DXYN`, `DXYZ`, `GDXY`, `USDX`
- Selected proxy symbol: `DXYN`
- Selection reason: `DXYN selected because it has the highest safe proxy quality score`
- Ranking order: `DXYN` score `84`, `USDX` score `78`, `DXYZ` score `66`, `GDXY` score `66`
- Safe as-of alignment feasible by symbol: `DXYN=true`, `DXYZ=true`, `GDXY=true`, `USDX=true`
- Selected proxy safe as-of alignment feasible: `true`
- Lookahead risk detected: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Future label candidates preserved: `dollar_strength`, `dollar_weakness`, `dollar_shock`, `gold_dxy_decoupling`, `dxy_trend_aligned`, `dxy_trend_conflict`
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
- Targeted tests: `60 passed`
- Next recommended step: `v0_67_dxy_regime_label_design_if_proxy_quality_passes`

v0_66 is research infrastructure only. It ranks the four v0_65 DXY/USD proxy candidates using fixed deterministic quality scoring over availability, supported timeframes, row count, timestamp coverage, XAUUSD overlap, gap severity, timestamp integrity, OHLC integrity, spread/tick-volume observability, and symbol selection stability.

The v0_65 report selected `DXYN` by fixed candidate order. v0_66 does not preserve that assumption blindly: `DXYN` remains selected because it scored highest under the fixed ranker, mainly from its larger historical XAUUSD overlap and broad timestamp coverage. Candidate order remains only a tie-breaker after equal total score.

The as-of alignment design is in-memory only. Future alignment must use backward joins where each proxy timestamp is less than or equal to the XAUUSD candle timestamp. Forward and nearest-future joins remain disallowed, and no aligned market CSV was created.
