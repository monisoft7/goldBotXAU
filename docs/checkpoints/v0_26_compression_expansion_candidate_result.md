# v0_26 Compression Expansion Candidate Result

## Decision

`create_fixed_compression_expansion_candidate`

v0_26 read `reports/xauusd_session_structure_atlas_v0_25.json` and created exactly one fixed train/validation-only research candidate from the v0_25 `compression_then_expansion` family. No OOS rows were read or evaluated, no execution semantics were added, and the candidate was not made eligible for OOS review.

Generated reports:

- `reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json`
- `reports/xauusd_compression_expansion_decision_v0_26.json`

## Candidate

- candidate_id: `xauusd_compression_then_expansion_v0_26`
- candidate_version: `v0_26`
- status: `train_validation_research_candidate_only`
- source_family: `compression_then_expansion`
- source_atlas: `xauusd_session_structure_atlas_v0_25`
- recommended_next_step: `future v0_27 fixed promotion gate`

## Fixed Rules

- Use dataset timestamp hour buckets only.
- Select the available fixed six-hour reference block with the lowest average bar range from `block_00_06`, `block_06_12`, and `block_12_18`.
- Measure whether the following fixed six-hour response block range is greater than the selected compressed reference block range.
- Use earliest fixed reference block as the deterministic tie break.
- No threshold search, parameter grid, or retuning was used.

## Train And Validation Summary

- combined train sample count: `1286`
- combined validation sample count: `262`
- train next-block expansion rate: `0.7846034214618973`
- validation next-block expansion rate: `0.7137404580152672`
- validation edge over neutral: `0.2137404580152672`
- validation degradation vs train: `0.07086296344663012`
- fixed degradation limit: `0.12`

## Timeframe Evidence

M5-only:

- train sample count: `643`
- validation sample count: `131`
- train next-block expansion rate: `0.7791601866251944`
- validation next-block expansion rate: `0.7099236641221374`
- validation degradation vs train: `0.06923652250305701`
- stability: `stable`

M10-only:

- train sample count: `643`
- validation sample count: `131`
- train next-block expansion rate: `0.7900466562986003`
- validation next-block expansion rate: `0.7175572519083969`
- validation degradation vs train: `0.07248940439020335`
- stability: `stable`

The combined counts are duplicated-like across M5 and M10, so v0_26 did not treat the combined sample count as independent market-event confidence. The candidate was allowed only because M5-only and M10-only evidence were each independently stable under the fixed train/validation checks.

## Safety Confirmation

- OOS rows used: `0`
- OOS remains locked.
- No demo behavior added.
- No live behavior added.
- No order sending or order checking added.
- No execution queue added.
- No trade recommendation output added.
- No threshold search or parameter grid used.
- No candidate registry OOS promotion created.
- No rejected candidate was modified or retuned.
