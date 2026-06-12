# Failed Strategy Registry

All families below are blacklisted for the clean `goldBotXAU` project.

## baseline_current_rules
- family_name: baseline_current_rules
- why_excluded: Existing baseline did not produce enough reliable evidence for active deployment and belongs to the old multiGold track.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: Reuse only neutral plumbing or validation ideas, not the rule family.

## local threshold tinkering variants
- family_name: local threshold tinkering variants
- why_excluded: Local parameter edits risk overfitting and did not establish a robust profitable edge.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: no
- notes: Do not restart threshold-tweaking loops in the new project.

## productivity/signal variants
- family_name: productivity/signal variants
- why_excluded: Attempts to increase signal count harmed quality or failed promotion gates.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: no
- notes: Signal frequency is not a substitute for edge.

## recent-only promotion variants
- family_name: recent-only promotion variants
- why_excluded: Recent-window promotion logic risks cherry-picking and did not prove durable out-of-sample behavior.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: no
- notes: New work must use explicit train/test and out-of-sample validation.

## old hypothesis lab outputs
- family_name: old hypothesis lab outputs
- why_excluded: The old hypothesis lab did not produce a promotable strategy family.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: Reuse only negative findings and metric discipline.

## range-break drawdown-control family
- family_name: range-break drawdown-control family
- why_excluded: Drawdown-control variants failed to create an acceptable active candidate.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: Risk concepts may be reused, but not the family.

## old regime-aware families
- family_name: old regime-aware families
- why_excluded: Regime-aware families failed promotion and did not become an active candidate.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: Regime labels may inform diagnostics only after a base strategy exists.

## broad scanner/pending-order scanner
- family_name: broad scanner/pending-order scanner
- why_excluded: Broad scanning expands scope and execution risk before a clean single-strategy backtest exists.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: no
- notes: Keep `goldBotXAU` focused on one XAUUSD strategy.

## speaker tone as trade signal
- family_name: speaker tone as trade signal
- why_excluded: Speaker tone is contextual intelligence only and is not validated as a trade signal.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: May be retained as non-signal research context only.

## FOMC direction as trade signal
- family_name: FOMC direction as trade signal
- why_excluded: FOMC direction summaries are descriptive context and not validated as predictive trade rules.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: FOMC context must not produce trade-direction output.
