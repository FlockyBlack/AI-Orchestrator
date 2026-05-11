from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .plan_contract import PlanTaskSpec, SafetyBoundary


ACCEPTED = "accepted"
BLOCKED = "blocked"
FAILED = "failed"
NEEDS_RETRY = "needs_retry"


FORBIDDEN_TRUE_FLAGS = {
    "real_trading": "real trading claimed",
    "real_order_submitted": "real order submitted",
    "wallet_used": "wallet used",
    "signing_used": "signing used",
    "private_key_used": "private key used",
    "trading_endpoint_used": "trading endpoint used",
    "real_money_used": "real money used",
    "autonomous_trading_enabled": "autonomous trading enabled",
    "daemon_created": "daemon created",
    "scheduler_created": "scheduler created",
    "background_worker_created": "background worker created",
    "authenticated_endpoint_used": "authenticated endpoint used",
    "browser_automation_used": "browser automation used",
    "openrouter_used": "OpenRouter used",
    "polymarket_api_used": "Polymarket API used",
    "unsafe_git_staging_used": "unsafe git staging used",
    "force_push_used": "force push used",
    "invented_outcomes": "invented outcomes claimed",
    "unresolved_market_marked_resolved_without_evidence": "unresolved market marked resolved without evidence",
}

FORBIDDEN_CLAIM_PATTERNS = (
    "real order submitted",
    "wallet used",
    "private key used",
    "signing key used",
    "trading endpoint used",
    "real money used",
    "autonomous trading enabled",
    "daemon created",
    "scheduler created",
    "background worker created",
    "authenticated endpoint used",
    "browser automation used",
    "openrouter used",
    "polymarket api used",
    "git add .",
    "git add -a",
    "git add --all",
    "force push used",
    "invented outcomes",
    "unresolved market marked resolved without evidence",
)


@dataclass(frozen=True)
class AcceptanceDecision:
    status: str
    accepted: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "accepted": self.accepted,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "reasons": list(self.reasons),
        }


def evaluate_task_result(
    task_spec: PlanTaskSpec,
    result_payload: Mapping[str, Any],
    safety_boundaries: tuple[SafetyBoundary, ...] | list[SafetyBoundary],
) -> AcceptanceDecision:
    shape_errors = validate_result_json_shape(result_payload)
    claim_errors = reject_forbidden_claims(result_payload)
    errors = list(shape_errors) + list(claim_errors)
    status = str(result_payload.get("status") or "").lower()

    if status in {"blocked", "requiring_operator_handoff"}:
        return AcceptanceDecision(status=BLOCKED, accepted=False, errors=tuple(errors), reasons=(status,))
    if status in {"failed", "error"}:
        return AcceptanceDecision(status=FAILED, accepted=False, errors=tuple(errors), reasons=(status,))
    if errors:
        return AcceptanceDecision(status=FAILED, accepted=False, errors=tuple(errors), reasons=("shape_or_safety_rejected",))

    docs_only = _task_allows_docs_only(task_spec)
    if not docs_only:
        if result_payload.get("validation_passed") is not True:
            return AcceptanceDecision(
                status=NEEDS_RETRY,
                accepted=False,
                errors=("validation_passed must be true",),
                reasons=("validation_required",),
            )
        if result_payload.get("safety_ok") is not True:
            return AcceptanceDecision(
                status=FAILED,
                accepted=False,
                errors=("safety_ok must be true",),
                reasons=("safety_required",),
            )

    if not _boundaries_acknowledged(safety_boundaries, result_payload):
        return AcceptanceDecision(
            status=NEEDS_RETRY,
            accepted=False,
            errors=("required safety boundaries were not acknowledged",),
            reasons=("safety_boundaries_required",),
        )

    return AcceptanceDecision(status=ACCEPTED, accepted=True)


def validate_result_json_shape(result_payload: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for field in ("task_id", "status", "validation_passed", "safety_ok"):
        if field not in result_payload:
            errors.append(f"missing result field: {field}")
    if "artifacts" in result_payload and not isinstance(result_payload["artifacts"], list):
        errors.append("artifacts must be a list when present")
    if "commands_run" in result_payload and not isinstance(result_payload["commands_run"], list):
        errors.append("commands_run must be a list when present")
    return tuple(errors)


def reject_forbidden_claims(result_payload: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    _scan_flags(result_payload, errors)
    for text in _flatten_strings(result_payload):
        lowered = text.lower()
        for pattern in FORBIDDEN_CLAIM_PATTERNS:
            if pattern in lowered and not _looks_like_negative_claim(lowered, pattern):
                errors.append(f"forbidden result claim: {pattern}")
    return tuple(dict.fromkeys(errors))


def _scan_flags(value: Any, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key in FORBIDDEN_TRUE_FLAGS and item is True:
                errors.append(FORBIDDEN_TRUE_FLAGS[normalized_key])
            _scan_flags(item, errors)
    elif isinstance(value, list):
        for item in value:
            _scan_flags(item, errors)


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


def _looks_like_negative_claim(text: str, pattern: str) -> bool:
    index = text.find(pattern)
    prefix = text[max(0, index - 24):index]
    return (
        "no " in prefix
        or "not " in prefix
        or "false" in text[max(0, index - 16): index + len(pattern) + 16]
        or "did not " in prefix
        or "without " in prefix
    )


def _task_allows_docs_only(task_spec: PlanTaskSpec) -> bool:
    mode = task_spec.execution_mode.lower()
    return mode in {"docs_only", "docs-only", "documentation"} or bool(
        task_spec.metadata.get("allow_docs_only_without_validation")
    )


def _boundaries_acknowledged(
    safety_boundaries: tuple[SafetyBoundary, ...] | list[SafetyBoundary],
    result_payload: Mapping[str, Any],
) -> bool:
    required = [boundary for boundary in safety_boundaries if boundary.required]
    if not required:
        return True
    if result_payload.get("safety_ok") is True:
        return True
    acknowledged = result_payload.get("safety_boundaries_acknowledged", [])
    if not isinstance(acknowledged, list):
        return False
    acknowledged_set = {str(value) for value in acknowledged}
    return all(boundary.boundary_id in acknowledged_set for boundary in required)
