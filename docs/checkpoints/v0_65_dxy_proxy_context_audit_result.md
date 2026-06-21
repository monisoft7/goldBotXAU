# v0_65 DXY Proxy Context Audit Result

- Audit module: `src/research/xauusd_dxy_proxy_context_audit.py`
- Audit script: `scripts/run_xauusd_dxy_proxy_context_audit_v0_65.py`
- Audit report: `reports/xauusd_dxy_proxy_context_audit_v0_65.json`
- Audit status: `dxy_proxy_context_feasibility_completed`
- Candidate symbols checked: `DXYN`, `DXYZ`, `GDXY`, `USDX`
- Usable proxy symbols: `DXYN`, `DXYZ`, `GDXY`, `USDX`
- Selected proxy symbol: `DXYN`
- XAUUSD timeframes available: `M1`, `M5`, `M10`, `M15`
- Proxy timeframes available: `M5`, `M15` for each usable candidate via MT5 read-only discovery
- Safe as-of alignment feasible: `true`
- Lookahead risk detected: `false`
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
- Data CSV added to git: `false`
- Targeted tests: `59 passed`
- Next recommended step: `v0_66_dxy_asof_alignment_if_proxy_feasible`

v0_65 is research infrastructure only. It audits whether one of the prior v0_61 DXY/USD proxy symbols can be observed locally or through MT5 read-only market-data access and whether the proxy timestamps overlap XAUUSD enough for future backward as-of alignment.

The current environment exposed all four candidate symbols through MT5 read-only copy-rates access. The audit found overlapping M5/M15 windows with local XAUUSD data and selected `DXYN` as the first feasible proxy by fixed candidate order. This is not a trading rule, not a filter, not an executable candidate, and not approval for strategy testing.

Future v0_66 work may build a bounded as-of alignment artifact if this report remains the source of truth. Any alignment must use only proxy values timestamped at or before the XAUUSD candle timestamp. Forward or nearest-future joins remain disallowed.
