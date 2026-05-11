from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from .symphony_task_contract import SymphonyTask


RESULT_ENVELOPE_SCHEMA_VERSION = "symphony_result_envelope.v1"
_FORBIDDEN_TRUE_FLAGS = {
    "real_trading": "real trading",
    "real_order_submitted": "real order submitted",
    "wallet_used": "wallet/signing/private key usage",
    "signing_used": "wallet/signing/private key usage",
    "private_key_used": "wallet/signing/private key usage",
    "trading_endpoint_used": "trading endpoint usage",
    "real_money_used": "real money",
    "autonomous_trading_enabled": "autonomous trading",
    "openrouter_used": "OpenRouter usage",
    "polymarket_api_used": "Polymarket API usage",
    "authenticated_endpoint_used": "authenticated endpoint usage",
    "browser_automation_used": "browser automation",
    "unsafe_git_staging_used": "unsafe git staging",
    "force_push_used": "force push",
    "daemon_created": "daemon creation",
    "scheduler_created": "scheduler creation",
    "background_worker_created": "background worker creation",
    "invented_outcomes": "invented outcomes",
}
_FORBIDDEN_PATTERNS = (
    "real trading",
    "real order submitted",
    "wallet used",
    "wallet signing",
    "private key used",
    "signing key used",
    "trading endpoint used",
    "real money used",
    "autonomous trading enabled",
    "openrouter used",
    "openrouter api used",
    "polymarket api used",
    "authenticated endpoint used",
    "browser automation used",
    "git add .",
    "git add -a",
    "git add --all",
    "force push used",
    "git push --force",
    "git push -f",
    "daemon created",
    "scheduler created",
    "background worker created",
    "invented outcomes",
)


@dataclass(frozen=True)
class SymphonyResultEnvelope:
    task_id: str
    status: str
    summary: str = ""
    plan_id: str = ""
    run_id: str = ""
    packet_id: str = ""
    session_id: str = ""
    received_at: str = ""
    validation_passed: bool = False
    safety_ok: bool = False
    artifacts: tuple[str, ...] = ()
    commands_run: tuple[str, ...] = ()
    proof: Mapping[str, Any] = field(default_factory=dict)
    safety: Mapping[str, Any] = field(default_factory=dict)
    result_payload: Mapping[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schema_version: str = RESULT_ENVELOPE_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SymphonyResultEnvelope":
        return cls(
            task_id=str(payload.get("task_id") or ""),
            status=str(payload.get("status") or ""),
            summary=str(payload.get("summary") or ""),
            plan_id=str(payload.get("plan_id") or ""),
            run_id=str(payload.get("run_id") or ""),
            packet_id=str(payload.get("packet_id") or ""),
            session_id=str(payload.get("session_id") or ""),
            received_at=str(payload.get("received_at") or _utc_iso()),
            validation_passed=bool(payload.get("validation_passed", False)),
            safety_ok=bool(payload.get("safety_ok", False)),
            artifacts=tuple(str(value) for value in payload.get("artifacts", [])),
            commands_run=tuple(str(value) for value in payload.get("commands_run", [])),
            proof=dict(payload.get("proof", {})) if isinstance(payload.get("proof", {}), Mapping) else {},
            safety=dict(payload.get("safety", {})) if isinstance(payload.get("safety", {}), Mapping) else {},
            result_payload=dict(payload.get("result_payload", {})) if isinstance(payload.get("result_payload", {}), Mapping) else {},
            errors=tuple(str(value) for value in payload.get("errors", [])),
            warnings=tuple(str(value) for value in payload.get("warnings", [])),
            schema_version=str(payload.get("schema_version") or RESULT_ENVELOPE_SCHEMA_VERSION),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = list(self.artifacts)
        payload["commands_run"] = list(self.commands_run)
        payload["proof"] = dict(self.proof)
        payload["safety"] = dict(self.safety)
        payload["result_payload"] = dict(self.result_payload)
        payload["errors"] = list(self.errors)
        payload["warnings"] = list(self.warnings)
        return payload


def validate_symphony_result(
    result: SymphonyResultEnvelope | Mapping[str, Any],
    task: SymphonyTask | Mapping[str, Any],
) -> dict[str, Any]:
    result_obj = result if isinstance(result, SymphonyResultEnvelope) else SymphonyResultEnvelope.from_dict(result)
    task_obj = task if isinstance(task, SymphonyTask) else SymphonyTask.from_dict(task)
    errors: list[str] = []
    warnings: list[str] = list(result_obj.warnings)
    if result_obj.task_id != task_obj.task_id:
        errors.append(f"task_id mismatch: expected {task_obj.task_id}, got {result_obj.task_id}")
    if result_obj.status not in {"completed", "blocked", "failed", "needs_retry"}:
        errors.append(f"unsupported result status: {result_obj.status or '<missing>'}")
    if result_obj.status == "completed" and result_obj.validation_passed is not True:
        errors.append("completed result must set validation_passed true")
    if result_obj.safety_ok is not True:
        errors.append("result safety_ok must be true")
    for flag, reason in _FORBIDDEN_TRUE_FLAGS.items():
        if _lookup_flag(result_obj.to_dict(), flag) is True:
            errors.append(f"unsafe result rejected: {reason}")
    for text in _flatten_strings(_strip_acknowledgements(result_obj.to_dict())):
        lowered = text.lower()
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern in lowered and not _looks_like_negative_claim(lowered, pattern):
                errors.append(f"unsafe result claim rejected: {pattern}")
    if result_obj.status == "completed":
        missing = [artifact for artifact in task_obj.expected_artifacts if artifact and artifact not in result_obj.artifacts]
        if missing:
            warnings.append("completed result does not list all expected artifacts: " + ", ".join(missing))
    return {
        "valid": not errors,
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
        "safety_ok": not errors,
    }


def map_symphony_result_to_ai_orchestrator_result(
    result: SymphonyResultEnvelope | Mapping[str, Any],
) -> dict[str, Any]:
    result_obj = result if isinstance(result, SymphonyResultEnvelope) else SymphonyResultEnvelope.from_dict(result)
    return {
        "schema_version": "codex_plan_task_result.v1",
        "task_id": result_obj.task_id,
        "plan_id": result_obj.plan_id,
        "run_id": result_obj.run_id,
        "status": result_obj.status,
        "validation_passed": result_obj.validation_passed,
        "safety_ok": result_obj.safety_ok,
        "summary": result_obj.summary,
        "artifacts": list(result_obj.artifacts),
        "commands_run": list(result_obj.commands_run),
        "proof": dict(result_obj.proof),
        "safety": dict(result_obj.safety),
        "safety_boundaries_acknowledged": True,
    }


def map_symphony_result_to_codex_ingestion_payload(
    result: SymphonyResultEnvelope | Mapping[str, Any],
) -> dict[str, Any]:
    result_obj = result if isinstance(result, SymphonyResultEnvelope) else SymphonyResultEnvelope.from_dict(result)
    payload = map_symphony_result_to_ai_orchestrator_result(result_obj)
    return {
        "packet_id": result_obj.packet_id,
        "run_id": result_obj.run_id,
        "plan_id": result_obj.plan_id,
        "task_id": result_obj.task_id,
        "received_at": result_obj.received_at or _utc_iso(),
        "adapter_mode": "codex_app_server_schema_only",
        "status": result_obj.status,
        "result_payload": payload,
        "result_path": "",
        "validation_passed": result_obj.validation_passed,
        "safety_ok": result_obj.safety_ok,
        "acceptance_status": "pending_operator_ingestion",
        "acceptance_reasons": [],
        "artifact_paths": list(result_obj.artifacts),
    }


def _lookup_flag(value: Any, flag: str) -> Any:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() == flag:
                return item
            nested = _lookup_flag(item, flag)
            if nested is not None:
                return nested
    if isinstance(value, list):
        for item in value:
            nested = _lookup_flag(item, flag)
            if nested is not None:
                return nested
    return None


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        result: list[str] = []
        for item in value.values():
            result.extend(_flatten_strings(item))
        return result
    if isinstance(value, list | tuple | set):
        result = []
        for item in value:
            result.extend(_flatten_strings(item))
        return result
    return []


def _strip_acknowledgements(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_acknowledgements(item)
            for key, item in value.items()
            if str(key) not in {"safety_boundaries_acknowledged", "forbidden_actions"}
        }
    if isinstance(value, list):
        return [_strip_acknowledgements(item) for item in value]
    return value


def _looks_like_negative_claim(text: str, pattern: str) -> bool:
    index = text.find(pattern)
    prefix = text[max(0, index - 48):index]
    sentence = text[max(0, index - 80): index + len(pattern) + 80]
    return (
        "no " in prefix
        or "not " in prefix
        or "did not " in prefix
        or "without " in prefix
        or "false" in sentence
        or "forbidden" in sentence
        or "must not" in sentence
    )


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
