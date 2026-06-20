# v0_36_1 CI Path Normalization Result

## Decision

`ci_path_normalization_complete`

v0_36_1 fixed Linux CI portability for the v0_29 OOS review validation path handling only.

## Root Cause

The v0_28 OOS protocol stores several locked repo-relative paths with Windows backslashes, including `reports\xauusd_oos_review_v0_29.json`. On Windows, `Path("reports\\...")` resolves as the expected repo-relative path. On Linux, the same string is treated as a literal filename containing backslashes.

That caused protocol validation and source report loading to block before OOS fixture evaluation, which then produced downstream missing-key assertions in tests that expected a completed OOS review report.

## Changed

- `src/research/xauusd_oos_review.py`
  - normalizes protocol path strings by treating `\` and `/` as equivalent repo-relative separators
  - validates allowed script and result paths against stable POSIX-style logical paths
  - loads protocol source reports through normalized logical paths
  - writes report path strings with forward slashes for stable report output
- `tests/test_xauusd_oos_review.py`
  - adds explicit POSIX-style and Windows-style protocol path variants
  - verifies successful OOS fixture review and stable forward-slash report path strings

## Validation

- targeted OOS tests: `15 passed`
- full tests: `436 passed`
- project health: `warnings`, no failures

## Safety Confirmation

- repeated OOS remains locked and forbidden
- candidate rules remain locked
- no strategy logic changed
- no thresholds changed
- no retune added
- no candidate rule changes added
- no demo, live, order send, order check, execution queue, recommendation, or directional output paths added
- no market data modified
- no raw CSV data embedded
- no forward observation results changed

## Next Step

Continue with approved v0_36 read-only forward observation cycles for new date ranges, no execution.
