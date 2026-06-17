# v0_40 Fixed Demo Risk Envelope Result

- Envelope module: `src/research/xauusd_demo_risk_envelope.py`
- Envelope script: `scripts/build_xauusd_demo_risk_envelope_v0_40.py`
- Envelope report: `reports/xauusd_demo_risk_envelope_v0_40.json`
- Source broker facts report: `reports/xauusd_broker_facts_audit_v0_39.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Decision: `demo_risk_envelope_design_ready`
- Envelope status: `completed`
- Candidate rules preserved: `true`
- Design only: `true`
- Demo execution allowed: `false`
- Order send allowed: `false`
- Order check allowed: `false`
- Broker execution path created: `false`
- Execution queue created: `false`
- Buy/sell output allowed: `false`
- Trade recommendation output allowed: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Repeated OOS review: `false`

v0_40 converted the v0_39 read-only broker facts into a conservative fixed demo risk envelope only. It did not connect to MT5, create demo/live execution, create a broker execution adapter, create a trade request, call or wrap order sending, call or wrap order checking, create an execution queue, emit directional output, emit trade recommendations, alter v0_26 candidate rules, retune, search thresholds, run a parameter grid, repeat OOS, or add any `data/*.csv`.

## Risk Envelope

- Max positions: `1`
- No martingale: `true`
- No averaging into loss: `true`
- No position scaling: `true`
- No discretionary lot increase: `true`
- Emergency stop required: `true`
- Max consecutive losses before stop: `2`
- Max daily demo loss: `2.0R`
- Max session demo loss: `1.0R`
- Max trade risk: `1.0R`
- Starting demo lot: `0.01`
- Max demo lot: `0.01`
- Lot step must match: `true`
- Symbol must match v0_39: `true`
- Broker facts must match v0_39: `true`

## Tick Value Handling

- Reported tick value: `0.1`
- Derived tick value: `1.0`
- Conservative tick value used for the design: `1.0`
- Warning: `tick_value_contract_size_mismatch`
- Blockers: none

## Verification

- Required builder command: `py -3 scripts/build_xauusd_demo_risk_envelope_v0_40.py --json --output reports/xauusd_demo_risk_envelope_v0_40.json`
- Targeted tests: `33 passed`
- Safety: execution remained disabled; candidate rules remained preserved; OOS was not repeated.

## Next Safe Step

Human review of the fixed demo risk envelope before any separate future demo preflight decision. Keep demo execution, live execution, order sending/checking, execution queues, directional output, trade recommendations, retuning, threshold search, parameter grids, and repeated OOS review disabled.
