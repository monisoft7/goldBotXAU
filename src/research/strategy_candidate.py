"""Research candidate definitions for harness plumbing."""

from __future__ import annotations

from dataclasses import dataclass, field

FORBIDDEN_FAMILIES = {
    "baseline_current_rules",
    "local threshold tinkering variants",
    "productivity/signal variants",
    "recent-only promotion variants",
    "old hypothesis lab outputs",
    "range-break drawdown-control family",
    "old regime-aware families",
    "broad scanner / pending-order scanner",
    "speaker tone as trade signal",
    "FOMC direction as trade signal",
}


@dataclass(frozen=True)
class ResearchCandidate:
    candidate_id: str
    candidate_name: str
    candidate_version: str
    family_name: str
    description: str
    allowed_splits: tuple[str, ...] = ("train", "validation")
    forbidden_families_check: bool = True
    is_null_candidate: bool = False

    def validate(self) -> None:
        if self.forbidden_families_check and self.family_name in FORBIDDEN_FAMILIES:
            raise ValueError(f"Forbidden strategy family rejected: {self.family_name}")
        if "out_of_sample" in self.allowed_splits:
            raise ValueError("Candidate cannot request locked out-of-sample data.")

    def run_on_split(self, candles: list[dict[str, float | str]], split_name: str) -> list[float]:
        raise NotImplementedError("Concrete research candidates must implement split evaluation.")

    def parameters(self) -> dict[str, float | int | str]:
        return {}


@dataclass(frozen=True)
class NullResearchCandidate(ResearchCandidate):
    candidate_id: str = "null_research_harness_test"
    candidate_name: str = "Null Research Harness Test"
    candidate_version: str = "v0_6"
    family_name: str = "null_research_harness_test"
    description: str = "Plumbing-only candidate that emits no trade outcomes."
    allowed_splits: tuple[str, ...] = field(default=("train", "validation"))
    forbidden_families_check: bool = True
    is_null_candidate: bool = True

    def run_on_split(self, candles: list[dict[str, float | str]], split_name: str) -> list[float]:
        self.validate()
        if split_name not in self.allowed_splits:
            raise ValueError(f"Split not allowed for candidate: {split_name}")
        return []
