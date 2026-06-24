Product: goldBotXAU Paper Forward Watcher

Goal:
Convert the existing goldBotXAU project into a practical paper-only forward observation bot for XAUUSD.

Current reality:
The strict backtest strategy path did not produce an OOS-ready trading candidate.
Do not continue research boards.
Do not retune failed candidates.
Do not run OOS.
Do not create live/demo trading.

Required behavior:
- Run from Windows PowerShell.
- Use existing project structure.
- Use MT5 read-only only if existing helpers already support it.
- Observe XAUUSD.
- Produce paper-only observations.
- Output JSON.
- Be safe to run repeatedly.
- Log observations with timestamp, symbol, timeframe, setup label, direction if any, reason, invalidation idea, and status.

Not allowed:
- No order_send.
- No order_check.
- No live trading.
- No demo trading yet.
- No API keys.
- No external downloads.
- No data/*.csv touch.
- No user-facing buy/sell recommendations.