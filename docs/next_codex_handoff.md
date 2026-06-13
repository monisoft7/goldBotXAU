# Next Codex Handoff

- Current project: goldBotXAU
- Last completed checkpoint: v0_30 post-OOS governance and paper-shadow protocol design
- OOS: evaluated once, marker locked, repeated review disallowed
- Current test baseline: 334 passed
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
- Latest post-OOS governance report: `reports/xauusd_post_oos_governance_v0_30.json`
- Latest context pack: `reports/codex_context_v0_30.json`
- Latest health report: `reports/project_health_v0_30.json`
- Latest decision: `post_oos_governance_created_design_only`
- Next safe task: v0_31 build read-only paper-shadow journal simulator, no execution

## v0_30 Governance Result

- Governance script: `scripts/build_xauusd_post_oos_governance_v0_30.py`
- Governance checkpoint: `docs/checkpoints/v0_30_post_oos_governance_result.md`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Source OOS marker decision: `oos_passed_research_validation`
- Detailed OOS metrics available: `false`
- Repeat OOS review allowed: `false`
- Governance status: `post_oos_governance_created_design_only`
- Paper-shadow protocol status: `design_only_not_started`
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`

v0_30 did not run OOS, did not evaluate new data, did not retune, did not change candidate rules, did not create a new variant, and did not start paper-shadow observation. It only created a governance checklist and future paper-shadow design criteria.

## Source OOS State

- v0_29 marker: `reports/xauusd_oos_review_v0_29.marker.json`
- marker decision: `oos_passed_research_validation`
- repeat OOS review allowed: `false`
- v0_29_1 repair report: `reports/xauusd_oos_review_repair_v0_29_1.json`
- repair status: `locked_report_restored_from_marker_without_detailed_metrics`
- detailed OOS metrics available in repaired main report: `false`

The detailed v0_29 OOS metrics remain unavailable because the main OOS report was overwritten by an accidental invalid-token rerun before v0_29_1 restored the locked marker decision. Do not recreate those metrics by rerunning OOS.

## Future Paper-Shadow Prerequisites

- locked candidate rules
- read-only market data
- no order path
- journal-only observations
- risk notes only
- manual review required
- no retune, threshold search, parameter grid, or parameter optimization
- no new variant from the OOS result

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

## v0_31 Boundary

v0_31 may build a read-only paper-shadow journal simulator only. It must not create demo, live, order, execution, or trade-instruction paths. The simulator should be journal-only, observation-only, use locked candidate rules, and require manual review before any later phase.
