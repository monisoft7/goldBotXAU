from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.candidate_registry import research_candidate_registry
from src.research.xauusd_oos_review_protocol import (
    ALLOWED_FUTURE_OOS_COMMAND,
    BLOCKED_DECISION,
    HUMAN_APPROVAL_TOKEN,
    PROTOCOL_DECISION,
    SOURCE_CANDIDATE_ID,
    build_xauusd_oos_review_protocol_v0_28,
)

ROOT = Path(__file__).resolve().parents[1]
ACTUAL_GATE = ROOT / "reports" / "xauusd_compression_expansion_promotion_gate_v0_27.json"
ACTUAL_CANDIDATE = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
ACTUAL_MANIFEST = ROOT / "reports" / "xauusd_dataset_manifest_v0_5.json"


def _actual_gate_report() -> dict[str, object]:
    return json.loads(ACTUAL_GATE.read_text(encoding="utf-8"))


def _actual_candidate_report() -> dict[str, object]:
    return json.loads(ACTUAL_CANDIDATE.read_text(encoding="utf-8"))


def _actual_manifest() -> dict[str, object]:
    return json.loads(ACTUAL_MANIFEST.read_text(encoding="utf-8"))


def _write_report(path: Path, report: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def _v0_28_registry() -> dict[str, object]:
    registry = copy.deepcopy(research_candidate_registry())
    registry["eligible_for_oos_review_count"] = 1
    for candidate in registry["candidates"]:
        if candidate["candidate_id"] == SOURCE_CANDIDATE_ID:
            candidate["status"] = "eligible_for_oos_review_pending_human_approval"
            candidate["eligible_for_oos_review"] = True
            candidate["oos_status"] = "locked_not_evaluated"
            candidate["human_approval_required_before_oos"] = True
            candidate.pop("one_time_oos_review_completed", None)
            candidate.pop("repeat_oos_review_allowed", None)
            candidate.pop("v0_29_oos_decision", None)
    return registry


def _build_with_defaults(tmp_path: Path) -> dict[str, object]:
    return build_xauusd_oos_review_protocol_v0_28(
        ACTUAL_GATE,
        ACTUAL_CANDIDATE,
        ACTUAL_MANIFEST,
        tmp_path / "not_created_oos_result.json",
        registry=_v0_28_registry(),
    )


def test_builds_protocol_for_exactly_one_eligible_candidate(tmp_path: Path) -> None:
    result = _build_with_defaults(tmp_path)

    assert result["decision"] == PROTOCOL_DECISION
    assert result["candidate_id"] == SOURCE_CANDIDATE_ID
    assert result["eligibility_confirmation"]["eligible_for_oos_review_count"] == 1
    assert result["eligibility_confirmation"]["human_approval_required_before_oos"] is True
    assert result["allowed_future_oos_review"]["may_run_in_v0_28"] is False


def test_protocol_blocks_if_eligible_candidate_count_is_not_exactly_one(tmp_path: Path) -> None:
    registry = _v0_28_registry()
    registry["eligible_for_oos_review_count"] = 2
    registry["candidates"].append(
        {
            "candidate_id": "fixture_extra_candidate",
            "eligible_for_oos_review": True,
            "oos_status": "locked_not_evaluated",
            "human_approval_required_before_oos": True,
        }
    )

    result = build_xauusd_oos_review_protocol_v0_28(
        ACTUAL_GATE,
        ACTUAL_CANDIDATE,
        ACTUAL_MANIFEST,
        tmp_path / "not_created_oos_result.json",
        registry=registry,
    )

    assert result["decision"] == BLOCKED_DECISION
    assert "eligible_candidate_count_not_exactly_1" in result["blockers"]


def test_protocol_blocks_if_oos_already_evaluated(tmp_path: Path) -> None:
    gate = _actual_gate_report()
    gate["safety"]["oos_evaluated"] = True
    gate["evidence_summary"]["oos_evaluated"] = True
    gate_path = _write_report(tmp_path / "gate.json", gate)

    result = build_xauusd_oos_review_protocol_v0_28(
        gate_path,
        ACTUAL_CANDIDATE,
        ACTUAL_MANIFEST,
        tmp_path / "not_created_oos_result.json",
        registry=_v0_28_registry(),
    )

    assert result["decision"] == BLOCKED_DECISION
    assert "promotion_gate_oos_already_evaluated" in result["blockers"]
    assert result["created_metrics"]["oos_rows_evaluated"] == 0


def test_protocol_blocks_if_future_oos_result_already_exists(tmp_path: Path) -> None:
    existing_oos_result = tmp_path / "existing_oos_result.json"
    existing_oos_result.write_text("{}", encoding="utf-8")

    result = build_xauusd_oos_review_protocol_v0_28(
        ACTUAL_GATE,
        ACTUAL_CANDIDATE,
        ACTUAL_MANIFEST,
        existing_oos_result,
        registry=_v0_28_registry(),
    )

    assert result["decision"] == BLOCKED_DECISION
    assert "future_oos_result_already_exists" in result["blockers"]


def test_protocol_does_not_read_oos_rows(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    original_read_text = Path.read_text

    def guarded_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if self.suffix.lower() == ".csv":
            raise AssertionError(f"unexpected csv read: {self}")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    result = _build_with_defaults(tmp_path)

    assert result["decision"] == PROTOCOL_DECISION
    assert result["leakage_controls"]["protocol_builder_reads_oos_rows"] is False
    assert result["created_metrics"]["oos_rows_read"] == 0


def test_protocol_does_not_create_oos_metrics(tmp_path: Path) -> None:
    result = _build_with_defaults(tmp_path)
    text = json.dumps(result).lower()

    assert result["created_metrics"] == {
        "oos_performance_results_created": False,
        "oos_rows_evaluated": 0,
        "oos_rows_read": 0,
    }
    assert "profit_factor" not in text
    assert "win_rate" not in text
    assert "expectancy" not in text
    assert "average_expansion_ratio" not in text
    assert set(result["created_metrics"]) == {
        "oos_performance_results_created",
        "oos_rows_evaluated",
        "oos_rows_read",
    }


def test_protocol_does_not_modify_candidate_rules(tmp_path: Path) -> None:
    result = _build_with_defaults(tmp_path)
    candidate = _actual_candidate_report()

    assert result["fixed_rules_source"]["rules"] == candidate["fixed_rules"]
    assert result["safety"]["candidate_rules_modified"] is False
    assert result["no_retune_policy_after_oos"]["candidate_rules_may_be_changed_after_oos"] is False


def test_protocol_requires_future_explicit_human_approval(tmp_path: Path) -> None:
    result = _build_with_defaults(tmp_path)

    assert result["allowed_future_oos_review"]["approval_token_required"] == HUMAN_APPROVAL_TOKEN
    assert HUMAN_APPROVAL_TOKEN in result["allowed_future_oos_review"]["exact_command"]
    assert result["allowed_future_oos_review"]["exact_command"] == ALLOWED_FUTURE_OOS_COMMAND
    assert result["allowed_future_oos_review"]["script_created_in_v0_28"] is False


def test_protocol_uses_oos_split_boundaries_from_manifest(tmp_path: Path) -> None:
    result = _build_with_defaults(tmp_path)
    manifest = _actual_manifest()

    assert result["oos_split_boundaries"]["split_policy"]["oos_start"] == manifest["split_policy"]["oos_start"]
    assert result["oos_split_boundaries"]["out_of_sample"] == {
        "start": manifest["splits"]["out_of_sample"]["start"],
        "end": manifest["splits"]["out_of_sample"]["end"],
    }
    assert "candle_count" not in result["oos_split_boundaries"]["out_of_sample"]


def test_no_execution_order_demo_live_or_direction_semantics_are_introduced(tmp_path: Path) -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_oos_review_protocol.py",
            ROOT / "scripts" / "build_xauusd_oos_review_protocol_v0_28.py",
        ]
    ).lower()
    report_text = json.dumps(_build_with_defaults(tmp_path))

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "execution_queue_enabled\": true" not in source_text
    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text


def test_rejected_candidates_are_not_modified_or_retuned(tmp_path: Path) -> None:
    before = research_candidate_registry()
    result = _build_with_defaults(tmp_path)
    after = research_candidate_registry()

    assert result["safety"]["rejected_candidate_retuned"] is False
    assert after == before
    for candidate in after["candidates"]:
        status = str(candidate["status"])
        if status == "rejected" or status.startswith("rejected_"):
            assert candidate["do_not_retune"] is True


def test_cli_writes_v0_28_protocol_report(tmp_path: Path) -> None:
    output_path = tmp_path / "protocol.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_oos_review_protocol_v0_28.py"),
            "--future-oos-report",
            str(tmp_path / "not_created_oos_result.json"),
            "--output",
            str(output_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout)["decision"] in {PROTOCOL_DECISION, BLOCKED_DECISION}
    assert json.loads(output_path.read_text(encoding="utf-8"))["protocol_version"] == "v0_28"
    assert json.loads(output_path.read_text(encoding="utf-8"))["allowed_future_oos_review"]["script_created_in_v0_28"] is False
