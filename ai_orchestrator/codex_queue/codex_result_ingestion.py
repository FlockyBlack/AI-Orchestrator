from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .automation_dashboard import build_dashboard
from .codex_executor_contract import (
    CodexExecutionPacket,
    CodexExecutionResultEnvelope,
    expected_result_schema_for_packet,
    validate_execution_result_envelope,
)
from .plan_contract import load_plan_contract
from .plan_run_state import (
    append_event,
    increment_retry,
    load_state,
    mark_task_blocked,
    mark_task_done,
    mark_task_failed,
    mark_task_needs_retry,
    record_task_artifacts,
    save_state,
)
from .result_acceptance_policy import ACCEPTED, BLOCKED, FAILED, NEEDS_RETRY, evaluate_task_result


@dataclass(frozen=True)
class IngestedResult:
    packet: CodexExecutionPacket
    envelope: CodexExecutionResultEnvelope
    validation: dict[str, Any]
    acceptance: dict[str, Any]
    accepted_for_state_update: bool


def ingest_codex_result(packet_path: str | Path, result_json_path: str | Path, queue_root: str | Path) -> dict[str, Any]:
    result_text = Path(result_json_path).read_text(encoding="utf-8")
    return ingest_codex_result_text(packet_path, result_text, queue_root, result_json_path=str(result_json_path))


def ingest_codex_result_text(
    packet_path: str | Path,
    result_json_text: str,
    queue_root: str | Path,
    *,
    result_json_path: str = "",
) -> dict[str, Any]:
    packet_payload = json.loads(Path(packet_path).read_text(encoding="utf-8"))
    if not isinstance(packet_payload, Mapping):
        raise ValueError("packet JSON must be an object")
    packet = CodexExecutionPacket.from_dict(packet_payload)
    result_payload = json.loads(result_json_text)
    if not isinstance(result_payload, Mapping):
        raise ValueError("Codex result JSON must be an object")
    envelope_or_payload = dict(result_payload)
    ingested = validate_ingested_result(packet, envelope_or_payload, result_json_path=result_json_path)
    state_update: dict[str, Any] = {
        "state_updated": False,
        "state_action": "none",
        "state_path": packet.state_path,
        "dashboard_path": "",
    }
    if ingested.accepted_for_state_update:
        state_update = apply_ingested_result_to_state(packet, ingested, queue_root)
    report = write_ingestion_report(packet, ingested, state_update, queue_root)
    return {
        "status": report["ingestion_status"],
        "task_id": packet.task_id,
        "run_id": packet.run_id,
        "plan_id": packet.plan_id,
        "packet_id": packet.packet_id,
        "packet_path": str(packet_path),
        "result_json_path": result_json_path,
        "validation_passed": ingested.validation["valid"],
        "safety_ok": ingested.validation["safety_ok"],
        "acceptance_status": ingested.acceptance.get("status", ""),
        "state_updated": state_update["state_updated"],
        "state_action": state_update["state_action"],
        "report_paths": report["report_paths"],
        "errors": list(report["errors"]),
        "warnings": list(report["warnings"]),
        "next_operator_action": report["next_operator_action"],
    }


def validate_ingested_result(
    packet: CodexExecutionPacket | Mapping[str, Any],
    envelope_or_payload: Mapping[str, Any],
    *,
    result_json_path: str = "",
) -> IngestedResult:
    packet_obj = packet if isinstance(packet, CodexExecutionPacket) else CodexExecutionPacket.from_dict(packet)
    envelope = _coerce_envelope(packet_obj, envelope_or_payload, result_json_path=result_json_path)
    validation = validate_execution_result_envelope(envelope, packet_obj).to_dict()
    acceptance = {"status": "not_evaluated", "accepted": False, "errors": [], "warnings": [], "reasons": []}
    accepted_for_state_update = False
    if validation["valid"]:
        task_spec, safety_boundaries = _load_task_and_boundaries(packet_obj)
        decision = evaluate_task_result(task_spec, envelope.result_payload, safety_boundaries)
        acceptance = decision.to_dict()
        accepted_for_state_update = decision.status in {ACCEPTED, BLOCKED, FAILED, NEEDS_RETRY}
    return IngestedResult(
        packet=packet_obj,
        envelope=envelope,
        validation=validation,
        acceptance=acceptance,
        accepted_for_state_update=accepted_for_state_update,
    )


def apply_ingested_result_to_state(
    packet: CodexExecutionPacket | Mapping[str, Any],
    accepted_result: IngestedResult,
    queue_root: str | Path,
) -> dict[str, Any]:
    packet_obj = packet if isinstance(packet, CodexExecutionPacket) else CodexExecutionPacket.from_dict(packet)
    state = load_state(packet_obj.state_path)
    plan = load_plan_contract(_source_plan_path(packet_obj))
    decision_status = str(accepted_result.acceptance.get("status") or "")
    reasons = _decision_reasons(accepted_result.acceptance)
    artifact_paths = _artifact_paths(accepted_result)
    result_path = accepted_result.envelope.result_path
    if result_path:
        artifact_paths.insert(0, result_path)
    packet_dir = Path(packet_obj.prompt_path).parent
    for path in (packet_dir / "packet.json", packet_dir / "prompt.md", packet_dir / "expected_result_template.json"):
        if path.exists():
            artifact_paths.append(str(path))
    artifact_paths = list(dict.fromkeys(path for path in artifact_paths if path))

    if decision_status == ACCEPTED:
        mark_task_done(state, packet_obj.task_id, result_path=result_path, artifact_paths=artifact_paths)
        state_action = "marked_done"
    elif decision_status == BLOCKED:
        record_task_artifacts(state, packet_obj.task_id, artifact_paths, result_path=result_path)
        mark_task_blocked(state, packet_obj.task_id, reasons)
        state_action = "marked_blocked"
    elif decision_status == FAILED:
        record_task_artifacts(state, packet_obj.task_id, artifact_paths, result_path=result_path)
        mark_task_failed(state, packet_obj.task_id, reasons)
        state_action = "marked_failed"
    elif decision_status == NEEDS_RETRY:
        record_task_artifacts(state, packet_obj.task_id, artifact_paths, result_path=result_path)
        retry_count = increment_retry(state, packet_obj.task_id)
        task_spec, _ = _load_task_and_boundaries(packet_obj)
        if retry_count > task_spec.max_retries:
            mark_task_blocked(state, packet_obj.task_id, f"retry exceeded: {retry_count}>{task_spec.max_retries}; {reasons}")
            state_action = "marked_blocked_retry_exceeded"
        else:
            mark_task_needs_retry(state, packet_obj.task_id, reasons)
            state_action = "marked_needs_retry"
    else:
        return {
            "state_updated": False,
            "state_action": "not_updated",
            "state_path": packet_obj.state_path,
            "dashboard_path": "",
        }

    append_event(
        state,
        {
            "event": "codex_result_ingested",
            "task_id": packet_obj.task_id,
            "packet_id": packet_obj.packet_id,
            "acceptance_status": decision_status,
            "state_action": state_action,
        },
    )
    save_state(state, packet_obj.state_path, updated_by="codex_result_ingestion")
    dashboard = build_dashboard(state, plan, Path(packet_obj.state_path).parent / "dashboard")
    save_state(state, packet_obj.state_path, updated_by="codex_result_ingestion")
    return {
        "state_updated": True,
        "state_action": state_action,
        "state_path": packet_obj.state_path,
        "dashboard_path": dashboard.get("dashboard_paths", {}).get("json", ""),
    }


def write_ingestion_report(
    packet: CodexExecutionPacket | Mapping[str, Any],
    ingested: IngestedResult,
    state_update: Mapping[str, Any],
    queue_root: str | Path,
) -> dict[str, Any]:
    packet_obj = packet if isinstance(packet, CodexExecutionPacket) else CodexExecutionPacket.from_dict(packet)
    packet_dir = Path(packet_obj.prompt_path).parent
    json_path = packet_dir / "ingestion_report.json"
    md_path = packet_dir / "ingestion_report.md"
    errors = list(ingested.validation.get("errors", [])) + list(ingested.acceptance.get("errors", []))
    warnings = list(ingested.validation.get("warnings", [])) + list(ingested.acceptance.get("warnings", []))
    validation_passed = bool(ingested.validation.get("valid", False))
    acceptance_status = str(ingested.acceptance.get("status") or "not_evaluated")
    if not validation_passed:
        ingestion_status = "rejected"
        next_action = "Fix the Codex result JSON and retry ingestion; state was not advanced."
    elif acceptance_status == ACCEPTED:
        ingestion_status = "accepted"
        next_action = "Review dashboard and continue the plan when ready."
    elif acceptance_status == BLOCKED:
        ingestion_status = "blocked"
        next_action = "Review blocker reason and recover-plan if appropriate."
    elif acceptance_status == FAILED:
        ingestion_status = "failed"
        next_action = "Review failure reason before retry or recovery."
    elif acceptance_status == NEEDS_RETRY:
        ingestion_status = "needs_retry"
        next_action = "Review retry reason and continue after fixing the task result."
    else:
        ingestion_status = "rejected"
        next_action = "Inspect validation and acceptance output."

    report = {
        "schema_version": "codex_result_ingestion_report.v1",
        "run_id": packet_obj.run_id,
        "plan_id": packet_obj.plan_id,
        "task_id": packet_obj.task_id,
        "packet_id": packet_obj.packet_id,
        "adapter_mode": packet_obj.adapter_mode,
        "created_at": _utc_iso(),
        "ingestion_status": ingestion_status,
        "accepted": ingestion_status == "accepted",
        "validation": dict(ingested.validation),
        "acceptance": dict(ingested.acceptance),
        "state_update": dict(state_update),
        "result_envelope": ingested.envelope.to_dict(),
        "expected_result_template": expected_result_schema_for_packet(packet_obj),
        "artifact_paths": _artifact_paths(ingested),
        "errors": errors,
        "warnings": warnings,
        "next_operator_action": next_action,
        "safety": {
            "codex_invoked_by_ingestion": False,
            "state_marked_done_without_acceptance": False,
            "trusted_result_blindly": False,
            "daemon_created": False,
            "scheduler_created": False,
            "background_worker_created": False,
            "wallet_or_trading_used": False,
            "openrouter_used": False,
            "polymarket_api_used": False,
            "browser_automation_used": False,
        },
        "report_paths": {
            "json": str(json_path),
            "markdown": str(md_path),
        },
    }
    _write_json(json_path, report)
    _write_text(md_path, _render_report_markdown(report))
    return report


def _coerce_envelope(
    packet: CodexExecutionPacket,
    envelope_or_payload: Mapping[str, Any],
    *,
    result_json_path: str = "",
) -> CodexExecutionResultEnvelope:
    if "result_payload" in envelope_or_payload:
        payload = dict(envelope_or_payload)
        payload["result_path"] = str(payload.get("result_path") or result_json_path)
        return CodexExecutionResultEnvelope.from_dict(payload)
    payload = dict(envelope_or_payload)
    artifacts = payload.get("artifacts", [])
    return CodexExecutionResultEnvelope(
        packet_id=packet.packet_id,
        run_id=packet.run_id,
        plan_id=packet.plan_id,
        task_id=str(payload.get("task_id") or ""),
        received_at=_utc_iso(),
        adapter_mode=packet.adapter_mode,
        status=str(payload.get("status") or ""),
        result_payload=payload,
        result_path=result_json_path,
        validation_passed=payload.get("validation_passed") is True,
        safety_ok=payload.get("safety_ok") is True,
        acceptance_status="pending_ingestion",
        acceptance_reasons=(),
        artifact_paths=tuple(str(value) for value in artifacts) if isinstance(artifacts, list) else (),
    )


def _load_task_and_boundaries(packet: CodexExecutionPacket) -> tuple[Any, tuple[Any, ...]]:
    plan = load_plan_contract(_source_plan_path(packet))
    for task in plan.tasks:
        if task.task_id == packet.task_id:
            return task, plan.safety_boundaries
    raise ValueError(f"task_id not found in plan: {packet.task_id}")


def _source_plan_path(packet: CodexExecutionPacket) -> str:
    manifest = _read_json(packet.queue_manifest_path)
    source = str(manifest.get("source_plan_file") or "")
    if not source:
        raise ValueError("queue manifest missing source_plan_file")
    return source


def _artifact_paths(ingested: IngestedResult) -> list[str]:
    paths = list(ingested.envelope.artifact_paths)
    payload_artifacts = ingested.envelope.result_payload.get("artifacts", [])
    if isinstance(payload_artifacts, list):
        paths.extend(str(value) for value in payload_artifacts)
    return list(dict.fromkeys(str(path) for path in paths if str(path)))


def _decision_reasons(acceptance: Mapping[str, Any]) -> str:
    values = list(acceptance.get("errors", [])) or list(acceptance.get("reasons", []))
    return "; ".join(str(value) for value in values) or str(acceptance.get("status") or "review required")


def _render_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        f"# Codex Result Ingestion: {report['task_id']}",
        "",
        f"- run_id: `{report['run_id']}`",
        f"- packet_id: `{report['packet_id']}`",
        f"- adapter_mode: `{report['adapter_mode']}`",
        f"- ingestion_status: `{report['ingestion_status']}`",
        f"- state_action: `{report.get('state_update', {}).get('state_action', 'none')}`",
        f"- next_operator_action: {report['next_operator_action']}",
        "",
    ]
    if report["errors"]:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")
    if report["warnings"]:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
        lines.append("")
    lines.extend(
        [
            "## Safety",
            "",
            "The ingestion path validates the packet and result JSON before state updates. It does not invoke Codex, create workers, use network/auth/browser/wallet/order/trading endpoints, or mark success without acceptance.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _write_text(path, json.dumps(dict(payload), indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, content: str) -> None:
    target = _io_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _io_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    resolved = path.resolve(strict=False)
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return resolved
    return Path("\\\\?\\" + text)


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
