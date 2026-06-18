# v0_46 Candidate Direction Provenance Audit Result

- Audit module: `src/research/xauusd_candidate_direction_provenance_audit.py`
- Audit script: `scripts/audit_xauusd_candidate_direction_v0_46.py`
- Audit report: `reports/xauusd_candidate_direction_provenance_v0_46.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Audit version: `v0_46`
- Audit status: `no_direction_rule_found_execution_blocked`
- Direction rule found: `false`
- Direction rule source files: none
- Direction rule source fields: none
- Direction rule text: none
- Executable side mapping found: `false`
- Executable side mapping: none
- Direction provenance confidence: `none`
- Demo execution direction ready: `false`
- Blockers: `locked_candidate_has_no_executable_side_mapping`, `locked_candidate_has_no_explicit_direction_rule`
- Warning: `next_block_expansion_behavior_found_but_not_executable_direction_rule`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Candidate rules preserved: `true`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Repeated OOS review: `false`
- Targeted tests: `37 passed`

v0_46 audited the existing locked v0_26 candidate artifacts and registry record for an already-existing deterministic direction rule. The artifacts contain the fixed compression-then-expansion behavior rule, including `next_block_expansion`, but they do not encode an executable internal side mapping.

Demo execution direction readiness remains blocked. This audit did not create or infer a side, did not change v0_26 candidate rules, did not retune, did not search thresholds, did not run a parameter grid, did not repeat OOS, did not add `data/*.csv`, did not call order sending, did not call order checking, did not enable live trading, did not create a scheduler, and did not create an execution queue.

Next recommended step: keep demo execution blocked until an explicit locked-candidate executable direction rule exists.
