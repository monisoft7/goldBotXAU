# v0_27 Compression Expansion Promotion Gate Result

## Decision

`promote_to_oos_review_candidate_pending_human_approval`

v0_27 read the v0_26 train/validation-only candidate report and v0_26 decision report, then applied a fixed conservative promotion gate. The candidate is now eligible for exactly one future OOS review only after human approval and a separate OOS review protocol. No OOS rows were read or evaluated.

Generated report:

- `reports/xauusd_compression_expansion_promotion_gate_v0_27.json`

## Candidate

- candidate_id: `xauusd_compression_then_expansion_v0_26`
- previous status: `train_validation_research_candidate_only`
- registry status: `eligible_for_oos_review_pending_human_approval`
- source family: `compression_then_expansion`
- OOS status: `locked_not_evaluated`
- human approval required before OOS: `true`

## Gate Evidence

Combined evidence:

- train sample count: `1286`
- validation sample count: `262`
- train next-block expansion rate: `0.7846034214618973`
- validation next-block expansion rate: `0.7137404580152672`
- validation edge over neutral: `0.2137404580152672`
- validation degradation vs train: `0.07086296344663012`

M5-only evidence:

- train sample count: `643`
- validation sample count: `131`
- train next-block expansion rate: `0.7791601866251944`
- validation next-block expansion rate: `0.7099236641221374`
- validation edge over neutral: `0.20992366412213737`
- validation degradation vs train: `0.06923652250305701`

M10-only evidence:

- train sample count: `643`
- validation sample count: `131`
- train next-block expansion rate: `0.7900466562986003`
- validation next-block expansion rate: `0.7175572519083969`
- validation edge over neutral: `0.21755725190839692`
- validation degradation vs train: `0.07248940439020335`

## Double-Counting Guard

The M5 and M10 counts are duplicated-like across the same underlying date range, so v0_27 did not treat the combined sample count as independent market-event confidence. The effective gate sample count used the per-timeframe minimum: train `643`, validation `131`.

Promotion passed because:

- M5-only and M10-only evidence each passed the fixed metric, edge, sample-size, and degradation checks.
- The M5/M10 validation rate gap was `0.007633587786259555`, below the fixed maximum `0.03`.
- Fixed reference and response block coverage included all expected blocks.
- No failed checks were present.

## Registry Count Effects

- eligible_for_oos_review_count: `0 -> 1`
- rejected_candidate_count: unchanged at `6`

## Safety Confirmation

- OOS rows used: `0`
- OOS remains locked.
- No demo behavior added.
- No live behavior added.
- No order sending or order checking added.
- No execution queue added.
- No trade recommendation output added.
- No threshold search or parameter grid used.
- No rejected candidate was modified or retuned.
- The v0_26 candidate rules were not changed or retuned.

## Next Step

Human approval is required before a separate v0_28 OOS review protocol. Do not run OOS in v0_27.
