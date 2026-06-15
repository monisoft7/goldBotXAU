# v0_36_2 CI Parity Result

## Decision

`ci_parity_fix_complete`

v0_36_2 fixed the remaining Linux GitHub Actions parity failures for the v0_27 promotion gate CLI path handling and v0_36 forward observation orchestrator test fixture time handling.

## Root Causes

### Promotion Gate

The v0_27 promotion gate CLI used default report paths from `Path("reports") / ...`, which are cwd-relative. A clean CI invocation from a working directory other than the repository root could fail to find the committed v0_26 candidate and decision reports, returning `blocked_missing_or_invalid_v0_26_candidate_report`.

The committed locked reports were valid. The issue was deterministic path resolution, not promotion evidence.

### Forward Observation Orchestrator

The orchestrator test fixture represented the fixed `block_18_24` end boundary as ISO text `T24:00:00`. Python datetime parsing requires hours in `0..23`, so Linux CI raised `ValueError: hour must be in 0..23`.

The block label remains `block_18_24`; the fixture now represents the end boundary as next-day midnight without creating an invalid hour.

## Changed

- `src/research/xauusd_compression_expansion_promotion_gate.py`
  - resolves missing relative report paths against the repository root before blocking
  - preserves all existing report validation and promotion safety checks
- `scripts/decide_compression_expansion_promotion_gate_v0_27.py`
  - uses repo-rooted default candidate, decision, and output paths
- `tests/test_xauusd_compression_expansion_promotion_gate.py`
  - adds clean-cwd CLI/default path coverage
  - adds repo-relative report path coverage from a non-root cwd
- `tests/test_xauusd_forward_observation_orchestrator.py`
  - writes fixture block boundaries with timedelta arithmetic
  - adds coverage for block ranges ending at 24 without producing `T24`
- `reports/project_health_v0_36_2.json`
- `reports/codex_context_v0_36_2.json`
- `docs/next_codex_handoff.md`

## Validation

- targeted CI parity tests: `29 passed`
- full tests: `439 passed`
- project health: `warnings`, no failures
- context export: completed

## Safety Confirmation

- candidate rules remain locked and unchanged
- no trading strategy logic changed
- no thresholds changed
- no retune added
- no OOS repeat added
- OOS decision remains unchanged
- no demo, live, order send, order check, execution queue, recommendation, or directional output paths added
- no raw CSV market data embedded in reports
- forward observation evidence was not altered

## Next Step

Continue with approved v0_36 read-only forward observation cycles for new date ranges, no execution.
