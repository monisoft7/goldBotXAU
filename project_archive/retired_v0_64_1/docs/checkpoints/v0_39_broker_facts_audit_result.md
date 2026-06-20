# v0_39 Broker Facts Audit Result

- Audit module: `src/research/xauusd_broker_facts_audit.py`
- Audit script: `scripts/build_xauusd_broker_facts_audit_v0_39.py`
- Audit report: `reports/xauusd_broker_facts_audit_v0_39.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Decision: `broker_facts_audit_ready_for_risk_envelope_design`
- Audit status: `completed`
- Candidate rules preserved: `true`
- Design or read-only: `true`
- MT5 read-only metadata access: `true`
- MT5 initialized: `true`
- MT5 shutdown called: `true`
- Missing facts: none
- Broker fact blockers: none
- Order send created: `false`
- Order send called: `false`
- Order check created: `false`
- Order check called: `false`
- Execution queue created: `false`
- Broker execution path created: `false`
- Buy/sell output allowed: `false`
- Trade recommendation output allowed: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Repeated OOS review: `false`

v0_39 collected read-only broker metadata only. It initialized MT5 only to read symbol and account facts, then shut MT5 down. It did not create demo or live execution, a broker execution adapter, a trade request, order sending, order checking, an execution queue, directional output, trade recommendations, a strategy variant, a retune, threshold search, parameter grid, repeated OOS review, or any `data/*.csv`.

## Broker Facts Collected

- Symbol exists: `true`
- Symbol visible: `true`
- Digits: `2`
- Point: `0.01`
- Contract size: `100.0`
- Tick size: `0.01`
- Tick value: `0.1`
- Volume min: `0.01`
- Volume max: `100.0`
- Volume step: `0.01`
- Spread: `15`
- Spread float: `true`
- Trade mode: `4`
- Trade execution mode: `2`
- Filling mode: `3`
- Order mode: `127`
- Stops level: `0`
- Freeze level: `0`
- Swap long: `-12.6`
- Swap short: `-4.6`
- Account server: `MetaQuotes-Demo`
- Account currency: `USD`
- Account trade mode: `0`

## Verification

- Required builder command: `py -3 scripts/build_xauusd_broker_facts_audit_v0_39.py --symbol XAUUSD --json --output reports/xauusd_broker_facts_audit_v0_39.json`
- Targeted tests: `30 passed`
- Safety: execution remained disabled; candidate rules remained preserved; OOS was not repeated.

## Next Safe Step

Design a separate human-approved risk envelope using the read-only broker facts only. Keep demo execution, live execution, order sending/checking, execution queues, directional output, trade recommendations, retuning, threshold search, parameter grids, and repeated OOS review disabled.
