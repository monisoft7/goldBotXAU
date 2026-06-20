"""v0_36 read-only XAUUSD forward observation cycle orchestrator."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.data.mt5_readonly_low_tf_exporter import export_xauusd_low_tf_csv
from src.data.xauusd_timeframe_resampler import resample_xauusd_timeframe_csv
from src.research.xauusd_forward_observation_consolidator import (
    build_xauusd_forward_observation_consolidation_v0_34_2,
    save_xauusd_forward_observation_consolidation,
)
from src.research.xauusd_forward_observation_ledger import (
    build_xauusd_forward_observation_ledger_v0_35,
    save_xauusd_forward_observation_ledger,
)
from src.research.xauusd_forward_observation_runner import (
    ALLOWED_TIMEFRAMES,
    CANDIDATE_ID,
    build_xauusd_forward_observation_runner_protocol_v0_33,
    save_xauusd_forward_observation_runner_protocol,
)
from src.research.xauusd_forward_observation_schema_adapter import (
    normalize_xauusd_forward_observation_csv,
)

ORCHESTRATOR_VERSION = "v0_36"
APPROVAL_TOKEN = "HUMAN_APPROVED_READONLY_FORWARD_OBSERVATION_V0_36"
DEFAULT_LEDGER = Path("reports") / "xauusd_forward_observation_ledger_v0_35.json"
DEFAULT_PROTOCOL_OUTPUT = Path("reports") / "xauusd_forward_observation_cycle_protocol_v0_36.json"
DEFAULT_LEDGER_OUTPUT = DEFAULT_LEDGER
NEXT_RECOMMENDED_STEP = (
    "run approved read-only forward observation cycles until v0_35/v0_36 ledger reaches "
    "demo preflight review requirements"
)

ExportM5 = Callable[..., Any]
ResampleM10 = Callable[..., Any]
NormalizeCsv = Callable[..., Any]


def build_xauusd_forward_observation_cycle_protocol_v0_36(
    *,
    ledger_path: str | Path = DEFAULT_LEDGER,
) -> dict[str, Any]:
    ledger, ledger_errors = _read_json_object(Path(ledger_path), "v0_35_forward_observation_ledger")
    blockers = list(ledger_errors)
    if ledger is not None:
        blockers.extend(_ledger_preflight_blockers(ledger))

    return {
        "cycle_protocol_version": ORCHESTRATOR_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "orchestrator_status": "ready_for_approved_read_only_cycle" if not blockers else "blocked",
        "approval_token_required": True,
        "approval_token_value": APPROVAL_TOKEN,
        "read_only_forward_observation_allowed": True,
        "demo_preflight_allowed": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
        "raw_market_data_embedded": False,
        "supported_timeframes": list(ALLOWED_TIMEFRAMES),
        "required_arguments": ["--from-date", "--to-date", "--approval-token"],
        "optional_arguments": ["--export-m5-from-mt5", "--m5-csv", "--symbol"],
        "workflow": [
            "confirm v0_35 ledger safety gate",
            "obtain M5 local read-only data only from an explicit local path or approved export",
            "resample M5 to M10 locally",
            "normalize M5 and M10 through v0_34_1 adapter",
            "build neutral M5 and M10 journal reports",
            "consolidate the new session summary",
            "rebuild the v0_35 ledger from prior and new consolidated summaries",
        ],
        "blockers": blockers,
        "safety_state": _safety_state(),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


def run_xauusd_forward_observation_cycle_v0_36(
    *,
    from_date: str | None,
    to_date: str | None,
    approval_token: str | None,
    project_root: str | Path = ".",
    data_dir: str | Path = "data",
    reports_dir: str | Path = "reports",
    m5_csv: str | Path | None = None,
    export_m5_from_mt5: bool = False,
    symbol: str = "XAUUSD",
    ledger_path: str | Path = DEFAULT_LEDGER,
    protocol_output_path: str | Path = DEFAULT_PROTOCOL_OUTPUT,
    ledger_output_path: str | Path = DEFAULT_LEDGER_OUTPUT,
    prior_consolidated_reports: list[str | Path] | None = None,
    export_m5_func: ExportM5 = export_xauusd_low_tf_csv,
    resample_m10_func: ResampleM10 = resample_xauusd_timeframe_csv,
    normalize_csv_func: NormalizeCsv = normalize_xauusd_forward_observation_csv,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    data_root = _resolve_under_root(root, data_dir)
    report_root = _resolve_under_root(root, reports_dir)
    ledger_file = _resolve_under_root(root, ledger_path)
    protocol_output = _resolve_under_root(root, protocol_output_path)
    ledger_output = _resolve_under_root(root, ledger_output_path)

    blockers = _argument_blockers(from_date, to_date, approval_token)
    from_text = from_date or ""
    to_text = to_date or ""
    session_label = _session_label(from_text, to_text)
    protocol = build_xauusd_forward_observation_cycle_protocol_v0_36(ledger_path=ledger_file)
    blockers.extend(protocol.get("blockers", []))

    artifacts: dict[str, Any] = {
        "protocol_report": _display_path(protocol_output, root),
        "ledger_input": _display_path(ledger_file, root),
    }
    step_reports: dict[str, Any] = {}

    if blockers:
        report = _cycle_report(
            cycle_status="blocked",
            from_date=from_text,
            to_date=to_text,
            blockers=_dedupe(blockers),
            artifacts=artifacts,
            step_reports=step_reports,
        )
        save_xauusd_forward_observation_cycle_protocol(report, protocol_output)
        return report

    m5_path: Path | None = None
    if export_m5_from_mt5:
        export_report = _to_dict(
            export_m5_func(
                symbol=symbol,
                timeframe="M5",
                from_date=from_text,
                to_date=to_text,
                data_dir=data_root,
            )
        )
        step_reports["m5_export"] = _compact_io_report(export_report)
        if export_report.get("status") != "exported" or not export_report.get("output_file"):
            blockers.append("m5_export_unavailable")
        else:
            m5_path = Path(str(export_report["output_file"]))
    else:
        m5_path = _resolve_under_root(root, m5_csv) if m5_csv is not None else _discover_m5_csv(data_root, from_text, to_text)
        if m5_path is None or not m5_path.exists():
            blockers.append("m5_forward_csv_missing_and_mt5_export_not_requested")

    if blockers:
        report = _cycle_report(
            cycle_status="blocked",
            from_date=from_text,
            to_date=to_text,
            blockers=_dedupe(blockers),
            artifacts=artifacts,
            step_reports=step_reports,
        )
        save_xauusd_forward_observation_cycle_protocol(report, protocol_output)
        return report

    assert m5_path is not None
    artifacts["m5_source_csv"] = _display_path(m5_path, root)

    resample_report = _to_dict(
        resample_m10_func(
            input_file=m5_path,
            target_timeframe="M10",
            data_dir=data_root,
            source_timeframe="M5",
        )
    )
    step_reports["m10_resample"] = _compact_io_report(resample_report)
    if resample_report.get("status") != "resampled" or not resample_report.get("output_file"):
        blockers.append("m10_resample_unavailable")

    if blockers:
        report = _cycle_report(
            cycle_status="blocked",
            from_date=from_text,
            to_date=to_text,
            blockers=_dedupe(blockers),
            artifacts=artifacts,
            step_reports=step_reports,
        )
        save_xauusd_forward_observation_cycle_protocol(report, protocol_output)
        return report

    m10_path = Path(str(resample_report["output_file"]))
    artifacts["m10_resampled_csv"] = _display_path(m10_path, root)

    m5_normalized = data_root / f"xauusd_forward_obs_m5_normalized_{session_label}_v0_36.csv"
    m10_normalized = data_root / f"xauusd_forward_obs_m10_normalized_{session_label}_v0_36.csv"
    adapter_project_root = data_root.parent if data_root.name.lower() == "data" else root
    m5_adapter = _to_dict(
        normalize_csv_func(
            input_file=m5_path,
            output_file=m5_normalized,
            symbol=symbol,
            timeframe="M5",
            project_root=adapter_project_root,
        )
    )
    m10_adapter = _to_dict(
        normalize_csv_func(
            input_file=m10_path,
            output_file=m10_normalized,
            symbol=symbol,
            timeframe="M10",
            project_root=adapter_project_root,
        )
    )
    step_reports["m5_normalize"] = _compact_io_report(m5_adapter)
    step_reports["m10_normalize"] = _compact_io_report(m10_adapter)
    if m5_adapter.get("adapter_status") != "framework_ready":
        blockers.append("m5_normalization_blocked")
    if m10_adapter.get("adapter_status") != "framework_ready":
        blockers.append("m10_normalization_blocked")

    if blockers:
        report = _cycle_report(
            cycle_status="blocked",
            from_date=from_text,
            to_date=to_text,
            blockers=_dedupe(blockers),
            artifacts=artifacts,
            step_reports=step_reports,
        )
        save_xauusd_forward_observation_cycle_protocol(report, protocol_output)
        return report

    artifacts["m5_normalized_csv"] = _display_path(m5_normalized, root)
    artifacts["m10_normalized_csv"] = _display_path(m10_normalized, root)

    m5_journal_path = report_root / f"xauusd_forward_observation_m5_cycle_{session_label}_v0_36.json"
    m10_journal_path = report_root / f"xauusd_forward_observation_m10_cycle_{session_label}_v0_36.json"
    m5_journal = build_xauusd_forward_observation_runner_protocol_v0_33(fixture_csv_path=m5_normalized)
    m10_journal = build_xauusd_forward_observation_runner_protocol_v0_33(fixture_csv_path=m10_normalized)
    save_xauusd_forward_observation_runner_protocol(m5_journal, m5_journal_path)
    save_xauusd_forward_observation_runner_protocol(m10_journal, m10_journal_path)
    step_reports["m5_journal"] = _compact_journal_report(m5_journal)
    step_reports["m10_journal"] = _compact_journal_report(m10_journal)
    if m5_journal.get("blockers") != []:
        blockers.append("m5_journal_blocked")
    if m10_journal.get("blockers") != []:
        blockers.append("m10_journal_blocked")

    if blockers:
        report = _cycle_report(
            cycle_status="blocked",
            from_date=from_text,
            to_date=to_text,
            blockers=_dedupe(blockers),
            artifacts=artifacts,
            step_reports=step_reports,
        )
        save_xauusd_forward_observation_cycle_protocol(report, protocol_output)
        return report

    artifacts["m5_journal_report"] = _display_path(m5_journal_path, root)
    artifacts["m10_journal_report"] = _display_path(m10_journal_path, root)

    consolidated_path = report_root / f"xauusd_forward_observation_consolidated_cycle_{session_label}_v0_36.json"
    consolidated = build_xauusd_forward_observation_consolidation_v0_34_2(
        input_report_paths=[m5_journal_path, m10_journal_path]
    )
    save_xauusd_forward_observation_consolidation(consolidated, consolidated_path)
    step_reports["consolidation"] = _compact_consolidated_report(consolidated)
    if consolidated.get("consolidation_status") != "completed":
        blockers.append("consolidation_blocked")

    if blockers:
        report = _cycle_report(
            cycle_status="blocked",
            from_date=from_text,
            to_date=to_text,
            blockers=_dedupe(blockers),
            artifacts=artifacts,
            step_reports=step_reports,
        )
        save_xauusd_forward_observation_cycle_protocol(report, protocol_output)
        return report

    artifacts["consolidated_report"] = _display_path(consolidated_path, root)
    default_prior_reports = [root / "reports" / "xauusd_forward_observation_consolidated_v0_34_2.json"]
    ledger_inputs = [Path(path) for path in (prior_consolidated_reports or default_prior_reports)]
    ledger_inputs.append(consolidated_path)
    ledger = build_xauusd_forward_observation_ledger_v0_35(input_consolidated_report_paths=ledger_inputs)
    save_xauusd_forward_observation_ledger(ledger, ledger_output)
    step_reports["ledger"] = _compact_ledger_report(ledger)
    artifacts["updated_ledger_report"] = _display_path(ledger_output, root)

    if ledger.get("ledger_status") != "completed":
        blockers.append("ledger_rebuild_blocked")

    report = _cycle_report(
        cycle_status="completed" if not blockers else "blocked",
        from_date=from_text,
        to_date=to_text,
        blockers=_dedupe(blockers),
        artifacts=artifacts,
        step_reports=step_reports,
        ledger_summary=_compact_ledger_report(ledger),
    )
    save_xauusd_forward_observation_cycle_protocol(report, protocol_output)
    return report


def save_xauusd_forward_observation_cycle_protocol(report: dict[str, Any], output_path: str | Path) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _argument_blockers(from_date: str | None, to_date: str | None, approval_token: str | None) -> list[str]:
    blockers: list[str] = []
    if approval_token != APPROVAL_TOKEN:
        blockers.append("approval_token_missing_or_invalid")
    if not from_date:
        blockers.append("from_date_required")
    if not to_date:
        blockers.append("to_date_required")
    if from_date and not _valid_date(from_date):
        blockers.append("from_date_invalid")
    if to_date and not _valid_date(to_date):
        blockers.append("to_date_invalid")
    if from_date and to_date and _valid_date(from_date) and _valid_date(to_date):
        if date.fromisoformat(from_date) > date.fromisoformat(to_date):
            blockers.append("date_range_not_chronological")
    return blockers


def _ledger_preflight_blockers(ledger: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if ledger.get("candidate_id") != CANDIDATE_ID:
        blockers.append("ledger_candidate_id_mismatch")
    if ledger.get("quality_gate_status") != "insufficient_samples":
        blockers.append("ledger_quality_gate_not_insufficient_samples")
    if ledger.get("demo_preflight_allowed") is not False:
        blockers.append("ledger_demo_preflight_allowed_not_false")
    for key in ("execution_allowed", "demo_allowed", "live_allowed", "order_send_allowed", "order_check_allowed"):
        if ledger.get(key) is not False:
            blockers.append(f"ledger_{key}_not_false")
    if ledger.get("repeated_oos_review") is not False:
        blockers.append("ledger_repeated_oos_review_not_false")
    if ledger.get("candidate_rules_modified") is not False:
        blockers.append("ledger_candidate_rules_modified_not_false")
    if ledger.get("raw_market_data_embedded") is not False:
        blockers.append("ledger_raw_market_data_embedded_not_false")
    return blockers


def _cycle_report(
    *,
    cycle_status: str,
    from_date: str,
    to_date: str,
    blockers: list[str],
    artifacts: dict[str, Any],
    step_reports: dict[str, Any],
    ledger_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "cycle_protocol_version": ORCHESTRATOR_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "orchestrator_status": cycle_status,
        "from_date": from_date,
        "to_date": to_date,
        "approval_token_required": True,
        "read_only_forward_observation_allowed": True,
        "demo_preflight_allowed": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
        "raw_market_data_embedded": False,
        "supported_timeframes": list(ALLOWED_TIMEFRAMES),
        "blockers": blockers,
        "artifacts": artifacts,
        "neutral_observation_summary": {
            "status": cycle_status,
            "timeframes": list(ALLOWED_TIMEFRAMES),
            "ledger": ledger_summary,
        },
        "step_reports": step_reports,
        "safety_state": _safety_state(),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


def _compact_io_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        key: report.get(key)
        for key in (
            "status",
            "adapter_status",
            "input_file",
            "output_file",
            "input_row_count",
            "output_row_count",
            "row_count",
            "errors",
            "warnings",
        )
        if key in report
    }


def _compact_journal_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "runner_status": report.get("runner_status"),
        "candidate_id": report.get("candidate_id"),
        "journal_record_count": report.get("synthetic_fixture_journal_record_count"),
        "blockers": report.get("blockers"),
        "raw_market_data_embedded": False,
    }


def _compact_consolidated_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "consolidation_status": report.get("consolidation_status"),
        "candidate_id": report.get("candidate_id"),
        "total_journal_record_count": report.get("total_journal_record_count"),
        "journal_record_count_by_timeframe": report.get("journal_record_count_by_timeframe"),
        "raw_market_data_embedded": report.get("raw_market_data_embedded"),
        "blockers": report.get("blockers"),
    }


def _compact_ledger_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "ledger_status": report.get("ledger_status"),
        "candidate_id": report.get("candidate_id"),
        "quality_gate_status": report.get("quality_gate_status"),
        "demo_preflight_allowed": report.get("demo_preflight_allowed"),
        "independent_observation_session_count": report.get("independent_observation_session_count"),
        "total_unique_journal_records": report.get("total_unique_journal_records"),
        "journal_record_count_by_timeframe": report.get("journal_record_count_by_timeframe"),
        "raw_market_data_embedded": report.get("raw_market_data_embedded"),
        "blockers": report.get("blockers"),
    }


def _read_json_object(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_missing: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{label}_invalid_json: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{label}_not_object: {path}"]
    return payload, []


def _discover_m5_csv(data_dir: Path, from_date: str, to_date: str) -> Path | None:
    exact = data_dir / f"xauusd_m5_xauusd_{from_date}_{to_date}.csv"
    if exact.exists():
        return exact
    candidates = sorted(data_dir.glob(f"xauusd_m5_*{from_date}*{to_date}*.csv"))
    return candidates[0] if candidates else None


def _resolve_under_root(root: Path, value: str | Path | None) -> Path:
    path = Path(value or ".")
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def _to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return value
    raise TypeError(f"Unsupported report object: {type(value)!r}")


def _session_label(from_date: str, to_date: str) -> str:
    text = f"{from_date}_{to_date}".lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_") or "undated"


def _valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _safety_state() -> dict[str, bool]:
    return {
        "local_read_only": True,
        "raw_market_data_embedded": False,
        "synthetic_replacement_allowed": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "execution_queue_allowed": False,
        "recommendation_output_allowed": False,
        "directional_instruction_output_allowed": False,
        "trade_recommendation_output_allowed": False,
        "new_oos_evaluation_allowed": False,
        "oos_repeat_allowed": False,
        "candidate_rules_modified": False,
        "threshold_search_allowed": False,
        "parameter_grid_allowed": False,
        "parameter_optimization_allowed": False,
        "retune_allowed": False,
        "martingale_allowed": False,
        "averaging_into_loss_allowed": False,
    }


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
