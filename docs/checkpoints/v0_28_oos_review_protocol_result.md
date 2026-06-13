# v0_28 OOS Review Protocol Result

## Decision

`create_oos_review_protocol_pending_future_human_approval`

v0_28 created a metadata-only OOS review protocol for `xauusd_compression_then_expansion_v0_26`. It did not open, read, or evaluate OOS rows, and it did not create OOS performance results.

Generated report:

- `reports/xauusd_oos_review_protocol_v0_28.json`

## Candidate

- candidate_id: `xauusd_compression_then_expansion_v0_26`
- source gate: `reports/xauusd_compression_expansion_promotion_gate_v0_27.json`
- source fixed rules: `reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json`
- source manifest: `reports/xauusd_dataset_manifest_v0_5.json`
- eligible_for_oos_review_count: `1`
- OOS status: `locked_not_evaluated`
- human approval required before OOS: `true`

## Protocol Scope

The protocol defines the future one-time OOS review boundary only. It records:

- fixed candidate rules and rules hash
- OOS split boundaries from the dataset manifest
- exact allowed future command
- pass/fail criteria
- leakage controls
- one-time-review policy
- no-retune policy after OOS
- actions if OOS passes
- actions if OOS fails

Allowed future command after explicit human approval:

```powershell
py -3 scripts/run_xauusd_oos_review_v0_29.py --protocol reports/xauusd_oos_review_protocol_v0_28.json --approval-token HUMAN_APPROVED_OOS_REVIEW_V0_29 --json --output reports/xauusd_oos_review_v0_29.json
```

The future runner was not created in v0_28.

## OOS Boundaries

From `reports/xauusd_dataset_manifest_v0_5.json`:

- split method: `fixed_chronological_split`
- leakage prevention: `chronological_only_no_shuffle`
- train end: `2025-06-30T23:59:59`
- validation start: `2025-07-01T00:00:00`
- validation end: `2025-12-31T23:59:59`
- policy OOS start: `2026-01-01T00:00:00`
- manifest out-of-sample start: `2026-01-02T01:00:00`
- manifest out-of-sample end: `2026-06-11T11:45:00`

## Safety Confirmation

- OOS rows read: `0`
- OOS rows evaluated: `0`
- OOS performance results created: `false`
- Candidate rules modified: `false`
- Threshold search used: `false`
- Parameter grid used: `false`
- Rejected candidates retuned: `false`
- Demo behavior added: `false`
- Live behavior added: `false`
- Order sending or checking added: `false`
- Execution queue added: `false`
- Trade recommendation output added: `false`
- BUY/SELL output added: `false`

## Test Result

- `py -3 -m pytest -q`
- Result: `307 passed`

## Next Step

v0_29 should run the one-time OOS review only if explicit human approval is given for that action. Without approval, OOS remains locked.
