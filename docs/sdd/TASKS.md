Task v0_86:
Build a paper-only forward watcher.

Files to create:
- src/research/xauusd_paper_forward_watcher.py
- scripts/run_xauusd_paper_forward_watcher_v0_86.py
- tests/test_xauusd_paper_forward_watcher.py
- reports/xauusd_paper_forward_watcher_v0_86.json
- docs/checkpoints/v0_86_paper_forward_watcher_result.md

Files to update:
- docs/next_codex_handoff.md
- scripts/print_codex_context.py
- tests/test_codex_context_pack.py

Run:
py -3 -m pytest -q tests/test_xauusd_paper_forward_watcher.py tests/test_codex_context_pack.py
py -3 scripts/run_xauusd_paper_forward_watcher_v0_86.py --json
py -3 scripts/print_codex_context.py --json
git status --short