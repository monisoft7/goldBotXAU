# v0_36_3 CI Promotion Gate Result

## Decision

`ci_promotion_gate_fix_complete`

v0_36_3 fixed the remaining Linux GitHub Actions failures in `tests/test_xauusd_compression_expansion_promotion_gate.py`.

## Root Cause

The tracked v0_26 decision report stores `candidate_report_path` with Windows separators:

`reports\xauusd_compression_expansion_candidate_v0_26_train_validation.json`

The v0_27 promotion gate compared that embedded metadata path as a raw string against the default `Path("reports") / ...` value. On Windows, the separators align with local path semantics. On Linux, the backslash remains a literal character, so the otherwise valid committed v0_26 candidate/decision reports were blocked with:

`blocked_missing_or_invalid_v0_26_candidate_report`

This was a deterministic path/content validation bug, not a strategy or evidence issue.

## Changed

- `src/research/xauusd_compression_expansion_promotion_gate.py`
  - resolves relative report and output paths against the repository root
  - stops treating the decision report's embedded candidate report pathname as promotion evidence
  - preserves fixed-rule, safety, metric, timeframe, and cross-report fixed-rules validation
- `tests/test_xauusd_compression_expansion_promotion_gate.py`
  - adds clean-cwd coverage where cwd contains misleading shadow reports
  - adds temp-report coverage proving valid report content is accepted even when `candidate_report_path` is not the default path
- `reports/project_health_v0_36_3.json`
- `reports/codex_context_v0_36_3.json`
- `docs/next_codex_handoff.md`

## Validation

- targeted promotion gate tests: `16 passed`
- full tests: `441 passed`
- project health: `warnings`, no failures
- context export: completed

## Safety Confirmation

- no trading strategy logic changed
- no candidate rules changed
- no thresholds changed
- no retune added
- no OOS repeat added
- OOS decision remains unchanged
- no forward observation logic changed
- no demo, live, order send, order check, execution queue, recommendation, or directional output paths added
- no raw CSV market data embedded

## Next Step

Continue with approved v0_36 read-only forward observation cycles for new date ranges, no execution.
