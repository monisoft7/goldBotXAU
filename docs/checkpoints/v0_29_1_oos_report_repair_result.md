# v0_29_1 OOS Report Repair Result

## Decision

`repaired_oos_report_from_locked_marker`

v0_29_1 repaired the consistency mismatch between:

- `reports/xauusd_oos_review_v0_29.marker.json`
- `reports/xauusd_oos_review_v0_29.json`

The marker is preserved as the locked one-time OOS source of truth.

## Repair Summary

- candidate_id: `xauusd_compression_then_expansion_v0_26`
- marker decision preserved: `oos_passed_research_validation`
- repeated OOS review allowed: `false`
- overwritten report detected: `true`
- detailed OOS metrics available in repaired main report: `false`
- recovery status: `locked_report_restored_from_marker_without_detailed_metrics`
- repair report: `reports/xauusd_oos_review_repair_v0_29_1.json`
- restored main report: `reports/xauusd_oos_review_v0_29.json`

The current main report was rewritten from the marker into a locked, consistent report. Original detailed OOS metrics may have been overwritten by the accidental invalid-token rerun. Because they were not recoverable from the current main report, v0_29_1 did not invent or recreate metrics.

## Guard Update

`scripts/run_xauusd_oos_review_v0_29.py` now respects the locked marker state before approval-token handling can overwrite the main report. The save path also refuses to persist a non-final blocked report over an existing locked OOS main report when the marker has `repeat_review_allowed: false`.

## Next Step

v0_30 should remain post-OOS robustness and paper-shadow protocol design only, with caution that detailed OOS metrics were overwritten unless recovered from an external backup.

## Safety Confirmation

- Demo behavior added: `false`
- Live behavior added: `false`
- Order sending or checking added: `false`
- Execution queue added: `false`
- Trade recommendation output added: `false`
- Directional output added: `false`
- Threshold search used: `false`
- Parameter grid used: `false`
- Parameter optimization used: `false`
- Retune used: `false`
- Candidate rules changed: `false`
- Repeated OOS research review: `false`
