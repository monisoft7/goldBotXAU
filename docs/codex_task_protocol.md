# Codex Task Protocol

Use this protocol for small, scoped Codex tasks in goldBotXAU.

## Starting Context

- Start from `docs/codex_operating_notes.md` and `docs/next_codex_handoff.md`.
- Keep tasks small and checkpoint-oriented.
- Modify the minimum files needed for the requested change.

## Safety Rules

- Do not open out-of-sample unless explicitly approved.
- Never add demo trading, live trading, `order_send`, `order_check`, or an execution queue.
- Never output BUY/SELL recommendations or trade-direction signals.
- Do not retune rejected candidates.
- After every candidate, update the registry and checkpoint docs.

## Test Protocol

- Run targeted tests first when a change touches a focused area.
- Run the full relevant suite before handing off.
- Prefer compact JSON reports for research and diagnostics.

## Handoff Format

Return:

- Files changed
- Tests run and result
- Safety confirmation
