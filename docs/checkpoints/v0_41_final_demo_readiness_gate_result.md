# v0_41 Final Demo Readiness Gate Result

- Gate module: `src/research/xauusd_final_demo_readiness_gate.py`
- Gate script: `scripts/build_xauusd_final_demo_readiness_gate_v0_41.py`
- Gate report: `reports/xauusd_final_demo_readiness_gate_v0_41.json`
- Source reports:
  - `reports/xauusd_demo_preflight_review_v0_37.json`
  - `reports/xauusd_demo_broker_safety_preflight_v0_38.json`
  - `reports/xauusd_broker_facts_audit_v0_39.json`
  - `reports/xauusd_demo_risk_envelope_v0_40.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Decision: `final_demo_readiness_gate_passed_pending_human_authorization`
- Gate status: `completed`
- Candidate rules preserved: `true`
- Final blockers: none
- Human authorization required: `true`
- Future separate limited demo execution design may be considered: `true`
- Demo allowed: `false`
- Execution allowed: `false`
- Order send allowed: `false`
- Order check allowed: `false`
- Broker execution path allowed: `false`
- Buy/sell output allowed: `false`
- Trade recommendation output allowed: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Repeated OOS review: `false`

v0_41 is a final governance gate only. It validates the v0_37 demo preflight review, v0_38 safety preflight design, v0_39 broker facts audit, and v0_40 fixed risk envelope together. It did not connect to MT5, create demo/live execution, create a broker adapter, call or wrap order sending, call or wrap order checking, create an execution queue, alter candidate rules, retune, search thresholds, run a parameter grid, repeat OOS, emit directional output, emit trade recommendations, or add any `data/*.csv`.

Accepted warning:

- `tick_value_contract_size_mismatch`
- Reported tick value: `0.1`
- Derived tick value: `1.0`
- Conservative tick value accepted: `1.0`

Fixed demo risk summary:

- Starting demo lot `0.01`
- Max demo lot `0.01`
- Max positions `1`
- Stop after `2` consecutive losses
- Max daily demo loss `2.0R`
- Max session demo loss `1.0R`
- No martingale, no averaging into loss, no position scaling

Targeted tests:

```powershell
py -3 -m pytest -q tests/test_xauusd_final_demo_readiness_gate.py tests/test_codex_context_pack.py
```

Result: `40 passed`.

Project health:

- `reports/project_health_v0_41.json`
- Status: warnings only, no failures

Context pack:

- `reports/codex_context_v0_41.json`

Next recommended step:

- Human authorization may consider a separate limited demo execution design. This gate does not permit execution.
