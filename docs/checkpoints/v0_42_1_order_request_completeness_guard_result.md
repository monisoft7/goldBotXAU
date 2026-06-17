# v0_42_1 Order Request Completeness Guard Result

- Executor module: `src/execution/xauusd_limited_demo_executor.py`
- Executor report: `reports/xauusd_limited_demo_execution_v0_42.json`
- Context pack: `reports/codex_context_v0_42_1.json`
- Health report: `reports/project_health_v0_42_1.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Executor version: `v0_42`
- Checkpoint scope: execution guard only
- Candidate rules preserved: `true`

## Behavior Added

v0_42_1 adds an order request completeness guard before the protected explicit demo order send path can become attempted.

If `--allow-demo-order-send`, `--no-dry-run`, and the exact approval token are used while no complete `order_request` exists, the executor returns:

- `blocked_missing_complete_order_request`

In that status:

- `order_send_attempted`: `false`
- `order_send_called`: `false`
- `order_check_called`: `false`

The permissive `demo_order_send_allowed_but_not_called` status is no longer used for the missing or incomplete order request case.

## Required Order Request Fields

A complete explicit demo order request requires:

- `symbol`: `XAUUSD`
- `lot` or `volume`: `0.01`
- `demo_only`: `true`
- explicit side field
- explicit order type field
- explicit action field

The default dry-run report intentionally has no order request:

- `executor_status`: `dry_run_ready_no_order_sent`
- `order_request_present`: `false`
- `order_request_complete`: `false`
- `order_request_validation_status`: `missing_order_request`
- `order_request_missing_fields`: `order_request`, `symbol`, `lot`, `demo_only`, `side`, `order_type`, `action`

## Verification

Targeted tests run:

```text
py -3 -m pytest -q tests/test_xauusd_limited_demo_executor.py tests/test_codex_context_pack.py
```

Result:

```text
40 passed
```

The targeted suite verifies:

- default dry-run still returns `dry_run_ready_no_order_sent`
- missing order request with explicit send inputs returns `blocked_missing_complete_order_request`
- missing side/type/action is detected as incomplete
- blocked missing request does not call order send
- order check is not called
- live account remains blocked
- no retune, threshold search, parameter grid, or repeated OOS

## Safety Confirmation

v0_42_1 did not change candidate strategy rules, did not add a strategy, did not emit directional output, did not create recommendation output, did not retune, did not run threshold search, did not run a parameter grid, did not repeat OOS, did not add `data/*.csv`, did not run real order send, and did not call order check.

Next safe task: review the v0_42_1 guard result and keep the execution path dry-run only unless a separate future human-approved task supplies and reviews a complete explicit demo-only order request.
