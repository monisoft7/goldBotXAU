"""v0_46 locked candidate direction provenance audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.candidate_registry import candidate_registry_by_id

AUDIT_VERSION = "v0_46"
CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"
DEFAULT_OUTPUT = Path("reports") / "xauusd_candidate_direction_provenance_v0_46.json"

DIRECTION_RULE_VERIFIED = "direction_rule_verified_from_locked_candidate"
NO_DIRECTION_RULE_FOUND = "no_direction_rule_found_execution_blocked"
AMBIGUOUS_DIRECTION_RULE = "ambiguous_direction_rule_execution_blocked"
AUDIT_FAILED_MISSING_ARTIFACTS = "audit_failed_missing_candidate_artifacts"

EXECUTABLE_INTERNAL_SIDES = {"long", "short"}
DIRECTION_RULE_KEYS = {
    "direction_rule",
    "direction_rule_text",
    "executable_direction_rule",
    "trade_direction_rule",
    "side_rule",
}
EXECUTABLE_SIDE_MAPPING_KEYS = {
    "executable_side_mapping",
    "execution_side_mapping",
    "direction_side_mapping",
    "direction_to_side_mapping",
    "side_mapping",
}
NON_DIRECTIONAL_BEHAVIOR_KEYS = {
    "dominant_behavior",
    "forward_behavior_label",
    "hypothetical_event_outcome",
}


def default_candidate_artifact_paths(root: Path = ROOT) -> list[Path]:
    return [
        root / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json",
        root / "reports" / "xauusd_compression_expansion_decision_v0_26.json",
        root / "reports" / "xauusd_session_structure_atlas_v0_25.json",
    ]


def build_xauusd_candidate_direction_provenance_audit_v0_46(
    *,
    candidate_id: str = CANDIDATE_ID,
    root: str | Path = ROOT,
    artifact_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    artifacts = _load_candidate_artifacts(root_path, candidate_id, artifact_paths)
    candidate_artifacts = [artifact for artifact in artifacts if artifact["candidate_related"]]

    if not candidate_artifacts:
        return _report(
            candidate_id=candidate_id,
            audit_status=AUDIT_FAILED_MISSING_ARTIFACTS,
            direction_matches=[],
            mapping_matches=[],
            blockers=["locked_candidate_artifacts_missing_or_candidate_id_not_found"],
            warnings=[],
            audited_artifacts=[artifact["path"] for artifact in artifacts],
            non_directional_behavior_fields=[],
        )

    direction_matches = _find_key_matches(candidate_artifacts, DIRECTION_RULE_KEYS)
    mapping_matches = _find_key_matches(candidate_artifacts, EXECUTABLE_SIDE_MAPPING_KEYS)
    behavior_matches = _dedupe_matches(_find_key_matches(candidate_artifacts, NON_DIRECTIONAL_BEHAVIOR_KEYS))

    direction_texts = sorted(
        {str(match["value"]).strip() for match in direction_matches if str(match["value"]).strip()}
    )
    mapping_values = [match["value"] for match in mapping_matches]
    mapping, mapping_blockers = _merge_executable_side_mappings(mapping_values)

    blockers: list[str] = []
    warnings: list[str] = []
    if behavior_matches and not direction_matches:
        warnings.append("next_block_expansion_behavior_found_but_not_executable_direction_rule")

    if not direction_matches:
        blockers.append("locked_candidate_has_no_explicit_direction_rule")
    if not mapping_matches:
        blockers.append("locked_candidate_has_no_executable_side_mapping")
    blockers.extend(mapping_blockers)

    if not direction_matches and not mapping_matches:
        audit_status = NO_DIRECTION_RULE_FOUND
    elif len(direction_texts) > 1 or mapping_blockers:
        audit_status = AMBIGUOUS_DIRECTION_RULE
    elif direction_matches and mapping_matches and not mapping_blockers:
        audit_status = DIRECTION_RULE_VERIFIED
    else:
        audit_status = AMBIGUOUS_DIRECTION_RULE
        if direction_matches and not mapping_matches:
            blockers.append("direction_rule_found_without_executable_side_mapping")
        if mapping_matches and not direction_matches:
            blockers.append("executable_side_mapping_found_without_direction_rule_text")

    return _report(
        candidate_id=candidate_id,
        audit_status=audit_status,
        direction_matches=direction_matches,
        mapping_matches=mapping_matches,
        blockers=sorted(set(blockers)),
        warnings=warnings,
        audited_artifacts=[artifact["path"] for artifact in candidate_artifacts],
        non_directional_behavior_fields=[
            {"source_file": match["source_file"], "source_field": match["field"], "value": match["value"]}
            for match in behavior_matches
        ],
        executable_side_mapping=mapping,
        direction_text=direction_texts[0] if len(direction_texts) == 1 else None,
    )


def save_xauusd_candidate_direction_provenance_audit(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_candidate_artifacts(
    root: Path,
    candidate_id: str,
    artifact_paths: list[str | Path] | None,
) -> list[dict[str, Any]]:
    paths = [Path(path) for path in artifact_paths] if artifact_paths is not None else default_candidate_artifact_paths(root)
    artifacts: list[dict[str, Any]] = []
    for path in paths:
        resolved = path if path.is_absolute() else root / path
        if not resolved.exists():
            continue
        try:
            data = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            artifacts.append(
                {
                    "path": _project_path(resolved, root),
                    "data": {"json_error": str(exc)},
                    "candidate_related": False,
                }
            )
            continue
        artifacts.append(
            {
                "path": _project_path(resolved, root),
                "data": data,
                "candidate_related": _contains_candidate_id(data, candidate_id),
            }
        )

    registry_record = candidate_registry_by_id().get(candidate_id)
    if registry_record:
        artifacts.append(
            {
                "path": "src/research/candidate_registry.py",
                "data": registry_record,
                "candidate_related": True,
            }
        )
    return artifacts


def _contains_candidate_id(value: Any, candidate_id: str) -> bool:
    if isinstance(value, dict):
        if value.get("candidate_id") == candidate_id:
            return True
        return any(_contains_candidate_id(child, candidate_id) for child in value.values())
    if isinstance(value, list):
        return any(_contains_candidate_id(child, candidate_id) for child in value)
    return False


def _find_key_matches(artifacts: list[dict[str, Any]], keys: set[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for artifact in artifacts:
        for field, value in _walk_fields(artifact["data"]):
            key = field.rsplit(".", 1)[-1].replace("[]", "")
            if key in keys and _meaningful_value(value):
                matches.append(
                    {
                        "source_file": artifact["path"],
                        "field": field,
                        "value": value,
                    }
                )
    return matches


def _dedupe_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for match in matches:
        key = (str(match["source_file"]), str(match["field"]), json.dumps(match["value"], sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(match)
    return deduped


def _walk_fields(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    fields: list[tuple[str, Any]] = []
    if prefix and isinstance(value, (dict, list)):
        fields.append((prefix, value))
    if isinstance(value, dict):
        for key, child in value.items():
            field = f"{prefix}.{key}" if prefix else str(key)
            fields.extend(_walk_fields(child, field))
    elif isinstance(value, list):
        for child in value:
            field = f"{prefix}[]" if prefix else "[]"
            fields.extend(_walk_fields(child, field))
    else:
        fields.append((prefix, value))
    return fields


def _meaningful_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list)):
        return bool(value)
    return True


def _merge_executable_side_mappings(values: list[Any]) -> tuple[dict[str, Any], list[str]]:
    merged: dict[str, Any] = {}
    blockers: list[str] = []
    executable_sides: set[str] = set()

    for value in values:
        if not isinstance(value, dict):
            blockers.append("executable_side_mapping_not_structured_object")
            continue
        for key, side in value.items():
            merged[str(key)] = side
            if isinstance(side, str) and side in EXECUTABLE_INTERNAL_SIDES:
                executable_sides.add(side)
            else:
                blockers.append(f"non_executable_side_mapping_value:{key}")

    if len(executable_sides) > 1:
        blockers.append("multiple_executable_sides_found_without_single_locked_candidate_direction")
    return merged, blockers


def _report(
    *,
    candidate_id: str,
    audit_status: str,
    direction_matches: list[dict[str, Any]],
    mapping_matches: list[dict[str, Any]],
    blockers: list[str],
    warnings: list[str],
    audited_artifacts: list[str],
    non_directional_behavior_fields: list[dict[str, Any]],
    executable_side_mapping: dict[str, Any] | None = None,
    direction_text: str | None = None,
) -> dict[str, Any]:
    verified = audit_status == DIRECTION_RULE_VERIFIED
    direction_found = bool(direction_matches)
    mapping_found = bool(mapping_matches) and not any(
        blocker.startswith("non_executable_side_mapping_value") for blocker in blockers
    )
    confidence = "high" if verified else "none" if audit_status == NO_DIRECTION_RULE_FOUND else "ambiguous"
    next_step = (
        "direction provenance verified; next step is separate human review before any demo execution change"
        if verified
        else "keep demo execution blocked until an explicit locked-candidate executable direction rule exists"
    )

    return {
        "audit_version": AUDIT_VERSION,
        "audit_status": audit_status,
        "candidate_id": candidate_id,
        "candidate_rules_preserved": True,
        "direction_rule_found": direction_found,
        "direction_rule_source_files": sorted({match["source_file"] for match in direction_matches}),
        "direction_rule_source_fields": sorted({match["field"] for match in direction_matches}),
        "direction_rule_text": direction_text,
        "executable_side_mapping_found": mapping_found,
        "executable_side_mapping": executable_side_mapping or {},
        "direction_provenance_confidence": confidence,
        "demo_execution_direction_ready": verified,
        "blockers": [] if verified else blockers,
        "warnings": warnings,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
        "next_recommended_step": next_step,
        "audited_artifacts": sorted(audited_artifacts),
        "non_directional_behavior_fields": non_directional_behavior_fields,
    }


def _project_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)
