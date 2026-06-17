# v0_43 Signal-to-Order-Request Builder Result

- Builder module: `src/execution/xauusd_signal_to_order_request_builder.py`
- Builder script: `scripts/build_xauusd_signal_order_request_v0_43.py`
- Builder report: `reports/xauusd_signal_order_request_v0_43.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Builder version: `v0_43`
- Candidate rules preserved: `true`
- Scope: dry-run-only signal-to-order-request builder

## Result

The v0_43 builder validates the locked v0_26 candidate context, v0_41 readiness gate, v0_40 risk envelope, and v0_42 limited demo executor report. It then evaluates an internal signal snapshot/provider and either creates a complete internal demo-only order request or reports that no qualified signal exists now.

Default CLI run:

```text
py -3 scripts/build_xauusd_signal_order_request_v0_43.py --symbol XAUUSD --lot 0.01 --dry-run --json --output reports/xauusd_signal_order_request_v0_43.json
```

Default report status:

- `builder_status`: `no_qualified_signal_now`
- `signal_evaluated`: `true`
- `signal_qualified`: `false`
- `signal_reason`: `no_current_signal_snapshot_supplied`
- `order_request_present`: `false`
- `order_request_complete`: `false`
- `order_request_validation_status`: `missing_order_request`
- `order_send_called`: `false`
- `order_check_called`: `false`
- `live_allowed`: `false`

## Order Request Contract

When an internal qualified locked-candidate signal is supplied, v0_43 can build a dry-run-only order request with:

- `symbol`: `XAUUSD`
- `lot`: `0.01`
- `demo_only`: `true`
- `side`
- `order_type`
- `action`
- `risk_reference`
- `stop_loss` or `stop_distance`
- `take_profit` or `exit_rule`
- `candidate_id`: `xauusd_compression_then_expansion_v0_26`

The request is internal execution data only. It is not user-facing trade recommendation output.

## Verification

Targeted tests run:

```text
py -3 -m pytest -q tests/test_xauusd_signal_to_order_request_builder.py tests/test_codex_context_pack.py
```

Result:

```text
35 passed
```

The targeted suite verifies no-signal, qualified mocked signal, incomplete request blocking, macro event blocking, no order send, no order check, live blocked, lot above `0.01` blocked, candidate id mismatch blocked, no retune, no threshold search, no parameter grid, no repeated OOS, and v0_43 context-pack inclusion.

## Safety Confirmation

v0_43 did not change v0_26 candidate rules, did not add a strategy, did not retune, did not search thresholds, did not run a parameter grid, did not repeat OOS, did not call order send, did not call order check, did not enable live trading, did not create an automatic loop, did not create a scheduler, did not create user-facing trade recommendation output, and did not add `data/*.csv`.

Next safe task: review the dry-run v0_43 builder report and only consider a separate future demo-execution task after a complete internal order request has been built and human-reviewed.
