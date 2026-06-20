from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_candidate_direction_provenance_audit import (
    AMBIGUOUS_DIRECTION_RULE,
    CANDIDATE_ID,
    DIRECTION_RULE_VERIFIED,
    NO_DIRECTION_RULE_FOUND,
    build_xauusd_candidate_direction_provenance_audit_v0_46,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_artifact(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "reports" / "candidate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _audited(tmp_path: Path, payload: dict[str, object]) -> dict[str, object]:
    path = _write_artifact(tmp_path, payload)
    return build_xauusd_candidate_direction_provenance_audit_v0_46(
        candidate_id=CANDIDATE_ID,
        root=tmp_path,
        artifact_paths=[path],
    )


def test_fixture_with_clear_direction_rule_passes_as_verified(tmp_path: Path) -> None:
    report = _audited(
        tmp_path,
        {
            "candidate_id": CANDIDATE_ID,
            "fixed_rules": {
                "direction_rule": "Qualified locked setup uses explicit internal side long.",
                "executable_side_mapping": {"qualified_locked_setup": "long"},
            },
        },
    )

    assert report["audit_status"] == DIRECTION_RULE_VERIFIED
    assert report["direction_rule_found"] is True
    assert report["executable_side_mapping_found"] is True
    assert report["demo_execution_direction_ready"] is True
    assert report["direction_rule_text"] == "Qualified locked setup uses explicit internal side long."
    assert report["executable_side_mapping"] == {"qualified_locked_setup": "long"}
    assert report["blockers"] == []


def test_fixture_with_no_direction_rule_blocks(tmp_path: Path) -> None:
    report = _audited(
        tmp_path,
        {
            "candidate_id": CANDIDATE_ID,
            "fixed_rules": {
                "forward_behavior_label": "next_block_expansion",
                "hypothetical_event_outcome": "response block range exceeds compressed reference block range",
            },
        },
    )

    assert report["audit_status"] == NO_DIRECTION_RULE_FOUND
    assert report["direction_rule_found"] is False
    assert report["executable_side_mapping_found"] is False
    assert report["demo_execution_direction_ready"] is False
    assert "locked_candidate_has_no_explicit_direction_rule" in report["blockers"]
    assert "locked_candidate_has_no_executable_side_mapping" in report["blockers"]
    assert report["warnings"] == ["next_block_expansion_behavior_found_but_not_executable_direction_rule"]


def test_fixture_with_ambiguous_direction_blocks(tmp_path: Path) -> None:
    report = _audited(
        tmp_path,
        {
            "candidate_id": CANDIDATE_ID,
            "fixed_rules": {
                "direction_rule": "Qualified locked setup may use either internal side depending on unstated context.",
                "executable_side_mapping": {"case_a": "long", "case_b": "short"},
            },
        },
    )

    assert report["audit_status"] == AMBIGUOUS_DIRECTION_RULE
    assert report["direction_rule_found"] is True
    assert report["executable_side_mapping_found"] is True
    assert report["demo_execution_direction_ready"] is False
    assert "multiple_executable_sides_found_without_single_locked_candidate_direction" in report["blockers"]


def test_report_includes_source_file_and_field_provenance(tmp_path: Path) -> None:
    report = _audited(
        tmp_path,
        {
            "candidate_id": CANDIDATE_ID,
            "candidate": {
                "fixed_rules": {
                    "direction_rule_text": "Qualified locked setup uses explicit internal side short.",
                    "executable_side_mapping": {"qualified_locked_setup": "short"},
                }
            },
        },
    )

    assert report["direction_rule_source_files"] == ["reports/candidate.json"]
    assert report["direction_rule_source_fields"] == ["candidate.fixed_rules.direction_rule_text"]
    assert report["direction_rule_text"] == "Qualified locked setup uses explicit internal side short."


def test_order_send_and_order_check_are_not_called(tmp_path: Path) -> None:
    report = _audited(tmp_path, {"candidate_id": CANDIDATE_ID, "fixed_rules": {}})

    assert report["order_send_called"] is False
    assert report["order_check_called"] is False


def test_live_remains_blocked(tmp_path: Path) -> None:
    report = _audited(tmp_path, {"candidate_id": CANDIDATE_ID, "fixed_rules": {}})

    assert report["live_allowed"] is False
    assert report["demo_execution_direction_ready"] is False


def test_no_retune_threshold_search_parameter_grid_or_repeated_oos(tmp_path: Path) -> None:
    report = _audited(tmp_path, {"candidate_id": CANDIDATE_ID, "fixed_rules": {}})

    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["repeated_oos_review"] is False


def test_real_locked_candidate_blocks_without_fabricated_side() -> None:
    report = build_xauusd_candidate_direction_provenance_audit_v0_46(candidate_id=CANDIDATE_ID, root=ROOT)

    assert report["audit_status"] == NO_DIRECTION_RULE_FOUND
    assert report["direction_rule_found"] is False
    assert report["executable_side_mapping_found"] is False
    assert report["executable_side_mapping"] == {}
    assert report["demo_execution_direction_ready"] is False
    assert "locked_candidate_has_no_explicit_direction_rule" in report["blockers"]
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False


def test_cli_writes_required_report(tmp_path: Path) -> None:
    output_path = tmp_path / "xauusd_candidate_direction_provenance_v0_46.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_xauusd_candidate_direction_v0_46.py"),
            "--candidate-id",
            CANDIDATE_ID,
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["audit_version"] == "v0_46"
    assert output_report["audit_status"] == NO_DIRECTION_RULE_FOUND
    assert output_report["demo_execution_direction_ready"] is False
