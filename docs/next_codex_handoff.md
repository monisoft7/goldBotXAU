# Next Codex Handoff

- Current project: goldBotXAU
- Last completed checkpoint: v0_29_1 OOS report consistency repair
- OOS: evaluated once, marker locked, and main report repaired from marker
- Current test baseline: 325 passed
- Health status: warnings only due to documented safety mentions
- Rejected candidate count: 6
- Eligible for OOS review count: 0
- Strategy status: no promoted strategy
- Execution status: disabled
- Latest candidate report: `reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json`
- Latest gate report: `reports/xauusd_compression_expansion_promotion_gate_v0_27.json`
- Latest OOS review protocol: `reports/xauusd_oos_review_protocol_v0_28.json`
- Latest OOS review result: `reports/xauusd_oos_review_v0_29.json`
- Latest OOS review marker: `reports/xauusd_oos_review_v0_29.marker.json`
- Latest OOS repair report: `reports/xauusd_oos_review_repair_v0_29_1.json`
- Latest context pack: `reports/codex_context_v0_29_1.json`
- Latest health report: `reports/project_health_v0_29_1.json`
- Latest decision: `oos_passed_research_validation`
- Next safe task: v0_30 post-OOS robustness and paper-shadow protocol design only; detailed OOS metrics were overwritten unless recovered from an external backup; do not create demo, live, execution, order, or trade-instruction paths.

## v0_29_1 Repair Result

- Repair script: `scripts/repair_xauusd_oos_review_report_v0_29_1.py`
- Repair checkpoint: `docs/checkpoints/v0_29_1_oos_report_repair_result.md`
- Repair decision: `repaired_oos_report_from_locked_marker`
- Marker/report mismatch detected: `true`
- Overwritten invalid-token report detected: `true`
- Marker decision preserved: `oos_passed_research_validation`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Repeat OOS review allowed: `false`
- Detailed OOS metrics available in repaired main report: `false`
- Recovery status: `locked_report_restored_from_marker_without_detailed_metrics`

The current main report was restored to a consistent locked state based on `reports/xauusd_oos_review_v0_29.marker.json`. It intentionally does not include detailed OOS metrics because the accidental invalid-token rerun overwrote the main report and those details were not recoverable from the current file.

## Guard Update

`scripts/run_xauusd_oos_review_v0_29.py` now blocks a repeated OOS review when the marker exists with `repeat_review_allowed: false`, and the save path avoids overwriting the existing main report with a blocked rerun result.

## Registry State

- `xauusd_compression_then_expansion_v0_26` status: `oos_passed_research_validation_pending_post_oos_protocol`
- OOS status: `evaluated_passed`
- eligible_for_oos_review: `false`
- one_time_oos_review_completed: `true`
- repeat_oos_review_allowed: `false`
- research_only: `true`

## Safety Boundary

- no repeated OOS research review
- no demo or live trading
- no order sending or order checking
- no execution queue
- no trade recommendation output
- no directional output
- no threshold search or parameter grid
- no parameter optimization
- no retune of rejected candidates
- no retune of the v0_26 compression-expansion candidate
- no OOS result-driven rule modification
- no promotion to strategy or execution semantics from the v0_29 OOS pass alone

## v0_30 Boundary

v0_30 should be post-OOS robustness and paper-shadow protocol design only. It may design review/governance steps, but must not create demo, live, order, execution, or trade-instruction paths. Treat detailed v0_29 OOS metrics as unavailable unless an external backup is explicitly recovered.
