# v0_29 One-Time OOS Review Result

## Decision

`oos_passed_research_validation`

v0_29 ran the one-time OOS review for `xauusd_compression_then_expansion_v0_26` using the v0_28 protocol and approval token `HUMAN_APPROVED_OOS_REVIEW_V0_29`.

Generated reports:

- `reports/xauusd_oos_review_v0_29.json`
- `reports/xauusd_oos_review_v0_29.marker.json`

## Candidate

- candidate_id: `xauusd_compression_then_expansion_v0_26`
- protocol: `reports/xauusd_oos_review_protocol_v0_28.json`
- fixed rules source: `reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json`
- rules hash: `e8744cb060337cccc4a65ce7ff08548a9edc6e14fa0f62966574faed6e168083`
- hash verification: `passed`
- candidate rules modified: `false`
- OOS status: `evaluated_passed`
- repeat OOS review allowed: `false`

## OOS Scope

Boundaries came from the v0_28 protocol and `reports/xauusd_dataset_manifest_v0_5.json`.

- OOS start: `2026-01-02T01:00:00`
- OOS end: `2026-06-11T11:45:00`
- source rows read: M1 local rows only
- derived timeframes evaluated: `M5`, `M10`
- source M1 rows read: `152607`
- OOS events evaluated: `228`
- M5 event count: `114`
- M10 event count: `114`

## OOS Result

Combined:

- primary metric rate: `0.7631578947368421`
- edge over neutral: `0.26315789473684215`
- degradation vs validation: `-0.04941743672157495`
- sample count: `228`

M5:

- primary metric rate: `0.7631578947368421`
- edge over neutral: `0.26315789473684215`
- degradation vs validation: `-0.05323423061470478`
- sample count: `114`

M10:

- primary metric rate: `0.7631578947368421`
- edge over neutral: `0.26315789473684215`
- degradation vs validation: `-0.045600642828445226`
- sample count: `114`

All fixed pass/fail criteria from the protocol passed.

## One-Time Marker

The marker `reports/xauusd_oos_review_v0_29.marker.json` was written. Repeated OOS review is blocked unless a future governance task explicitly resets the one-time marker.

## Safety Confirmation

- Demo behavior added: `false`
- Live behavior added: `false`
- Order sending or checking added: `false`
- Execution queue added: `false`
- Trade recommendation output added: `false`
- BUY/SELL output added: `false`
- Threshold search used: `false`
- Parameter grid used: `false`
- Parameter optimization used: `false`
- Retune used: `false`
- Candidate rules changed: `false`
- OOS result-driven rule modification: `false`

## Test Result

- `py -3 -m pytest -q`
- Result before OOS command: `319 passed`

## Next Step

v0_30 should be post-OOS robustness and paper-shadow protocol design only. Do not create demo, live, execution, order, or trade-instruction paths.
