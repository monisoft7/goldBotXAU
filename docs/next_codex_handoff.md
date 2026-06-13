# Next Codex Handoff

- Current project: goldBotXAU
- Last completed checkpoint: v0_31 read-only paper-shadow journal simulator framework
- OOS: evaluated once, marker locked, repeated review disallowed
- Current test baseline: 344 passed
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
- Latest paper-shadow journal protocol: `reports/xauusd_paper_shadow_journal_protocol_v0_31.json`
- Latest context pack: `reports/codex_context_v0_31.json`
- Latest health report: `reports/project_health_v0_31.json`
- Latest decision: `framework_ready_not_started`
- Next safe task: v0_32 read-only forward observation data export plan, no execution

## v0_31 Journal Framework Result

- Journal module: `src/research/xauusd_paper_shadow_journal.py`
- Journal script: `scripts/build_xauusd_paper_shadow_journal_v0_31.py`
- Journal checkpoint: `docs/checkpoints/v0_31_paper_shadow_journal_result.md`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Journal status: `framework_ready_not_started`
- Data source status: `synthetic_fixtures_only`
- Real market observation started: `false`
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`
- Repeated OOS review: `false`
- Candidate rules modified: `false`

v0_31 built only a synthetic-fixture journal framework. It did not run OOS, did not evaluate real market data, did not start forward observation, did not retune, did not change candidate rules, and did not create a new strategy variant.

## Journal Record Schema

- timestamp
- candidate_id
- observed_reference_block
- observed_response_block
- compression_label
- expansion_observed
- rule_match_status
- observation_status
- notes

Records are neutral observations only. Allowed record language centers on observation, rule match, expansion observed, no expansion observed, and journal record.

## Source Governance State

- v0_30 governance report: `reports/xauusd_post_oos_governance_v0_30.json`
- governance status: `post_oos_governance_created_design_only`
- paper-shadow protocol status before v0_31: `design_only_not_started`
- source OOS marker decision: `oos_passed_research_validation`
- repeat OOS review allowed: `false`
- detailed OOS metrics available: `false`

The detailed v0_29 OOS metrics remain unavailable because the main OOS report was overwritten by an accidental invalid-token rerun before v0_29_1 restored the locked marker decision. Do not recreate those metrics by rerunning OOS.

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
- no recommendation output
- no directional output
- no threshold search or parameter grid
- no parameter optimization
- no retune of rejected candidates
- no retune of the v0_26 compression-expansion candidate
- no OOS result-driven rule modification
- no promotion to strategy or execution semantics from the v0_29 OOS pass alone

## v0_32 Boundary

v0_32 may design a read-only forward observation data export plan only. It must not create demo, live, order, execution, broker, account, queue, recommendation, or directional-instruction paths. It should plan how future observation data would be exported for journal records, with manual review required before any later phase.
