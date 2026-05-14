from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-060-SIGNER-BOUNDARY-UNSIGNED-VS-SIGNED-PAYLOAD-SEPARATION"

EXECUTION_MODE = "preflight"
MODE = "preflight / review-only"

LIVE_CANDIDATE_ORDER_INTENT_CONTRACT = "pmbot_live_candidate_order_intent_060.v1"
UNSIGNED_ORDER_PAYLOAD_PLAN_CONTRACT = "pmbot_unsigned_order_payload_plan_060.v1"
SIGNING_BOUNDARY_STATUS_CONTRACT = "pmbot_signing_boundary_status_060.v1"
SIGNED_PAYLOAD_AVAILABILITY_CONTRACT = "pmbot_signed_payload_availability_060.v1"
ORDER_SUBMISSION_AVAILABILITY_CONTRACT = "pmbot_order_submission_availability_060.v1"
SIGNER_BOUNDARY_BLOCKER_CONTRACT = "pmbot_signer_boundary_blocker_060.v1"
SIGNER_BOUNDARY_BLOCKERS_CONTRACT = "pmbot_signer_boundary_blockers_060.v1"
SIGNER_BOUNDARY_PREFLIGHT_RESULT_CONTRACT = "pmbot_signer_boundary_preflight_result_060.v1"
LATEST_SIGNER_BOUNDARY_PREFLIGHT_STATUS_CONTRACT = (
    "pmbot_latest_signer_boundary_preflight_status_060.v1"
)
SIGNER_BOUNDARY_PREFLIGHT_VALIDATION_CONTRACT = (
    "pmbot_signer_boundary_preflight_validation_060.v1"
)

STATUS_CREATED = "created"
STATUS_MISSING_SOURCE = "missing_source"
STATUS_BLOCKED = "blocked"
STATUS_UNAVAILABLE = "unavailable"
UNSIGNED_PLAN_STATUS = "schema_only_non_executable"

FORCED_FALSE_EXECUTION_FIELDS = (
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "wallet_connection_attempted",
    "signer_config_present",
    "signer_instantiated",
    "signing_attempted",
    "signed_payload_generated",
    "signed_payload_available",
    "order_submission_attempted",
    "order_submission_available",
    "order_cancellation_attempted",
    "balance_read_attempted",
    "position_read_attempted",
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
    "live_execution_allowed",
    "live_execution_performed",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_performed",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "signed_order_payload_generated",
    "order_payload_generated",
    "real_order_submitted",
    "order_submitted",
    "real_order_cancelled",
    "balance_read_enabled",
    "position_read_enabled",
    "authenticated_endpoint_call_performed",
    "authenticated_request_performed",
    "private_key_envs_checked",
    "environment_secrets_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "credentials_values_exposed",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

FORBIDDEN_MODEL_FIELDS = frozenset(
    {
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill_id",
        "fill_price",
        "filled_size",
        "execution_price",
        "execution_status",
        "balance",
        "pnl",
        "profit",
        "realized_pnl",
        "unrealized_pnl",
        "position_opened",
        "position_closed",
        "signature",
        "signed_payload_value",
    }
)


@dataclass(frozen=True)
class LiveCandidateOrderIntent:
    status: str
    source_paper_intent_path: str
    market_symbol: str
    strategy_name: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    source_contract_version: str = ""
    source_paper_intent_status: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANDIDATE_ORDER_INTENT_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = clean_text(self.status) or STATUS_MISSING_SOURCE
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["review_only"] = True
        value["preflight_only"] = True
        value["source_paper_intent_path"] = clean_text(self.source_paper_intent_path)
        value["market_symbol"] = clean_text(self.market_symbol).upper() or "BTC"
        value["strategy_name"] = clean_text(self.strategy_name) or "tiny-momentum"
        value["candidate_outcome"] = clean_text(self.candidate_outcome) or "not_available"
        value["candidate_side"] = clean_text(self.candidate_side) or "not_available"
        value["live_candidate_intent_status"] = value["status"]
        value["candidate_intent_created"] = value["status"] == STATUS_CREATED
        value["candidate_intent_is_review_only"] = True
        value["candidate_intent_is_not_order_submission"] = True
        value["candidate_intent_is_not_live_approval"] = True
        value["candidate_intent_is_non_executable"] = True
        value["non_executable_order_plan_status"] = "review_only_non_executable"
        value["operator_summary"] = _candidate_operator_summary(value)
        value.update(signer_boundary_safety_flags(unsigned_plan_created=False))
        return value


@dataclass(frozen=True)
class UnsignedOrderPayloadPlan:
    status: str
    source_paper_intent_path: str
    market_symbol: str
    strategy_name: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    unsigned_plan_created: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = UNSIGNED_ORDER_PAYLOAD_PLAN_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = clean_text(self.status) or UNSIGNED_PLAN_STATUS
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["review_only"] = True
        value["preflight_only"] = True
        value["source_paper_intent_path"] = clean_text(self.source_paper_intent_path)
        value["market_symbol"] = clean_text(self.market_symbol).upper() or "BTC"
        value["strategy_name"] = clean_text(self.strategy_name) or "tiny-momentum"
        value["candidate_outcome"] = clean_text(self.candidate_outcome) or "not_available"
        value["candidate_side"] = clean_text(self.candidate_side) or "not_available"
        value["unsigned_plan_status"] = value["status"]
        value["unsigned_plan_created"] = self.unsigned_plan_created is True
        value["unsigned_plan_is_executable"] = False
        value["schema_only"] = True
        value["schema_only_non_executable"] = True
        value["payload_materialized"] = False
        value["real_clob_payload_materialized"] = False
        value["ready_for_signing"] = False
        value["contains_private_key_material"] = False
        value["contains_wallet_material"] = False
        value["contains_auth_headers"] = False
        value["payload_plan_fields"] = [
            "market_symbol",
            "strategy_name",
            "candidate_outcome",
            "candidate_side",
            "candidate_limit_price",
            "candidate_size",
            "candidate_notional",
            "operator_review_note",
        ]
        value["operator_summary"] = (
            "Unsigned plan is schema-only and non-executable; no signable payload is created."
        )
        value.update(signer_boundary_safety_flags(unsigned_plan_created=value["unsigned_plan_created"]))
        return value


@dataclass(frozen=True)
class SigningBoundaryStatus:
    status: str = STATUS_BLOCKED
    signer_config_present: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SIGNING_BOUNDARY_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = STATUS_BLOCKED
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["review_only"] = True
        value["preflight_only"] = True
        value["signer_status"] = STATUS_BLOCKED
        value["signer_config_present"] = False
        value["signer_available"] = False
        value["signer_blocked"] = True
        value["wallet_blocked"] = True
        value["operator_summary"] = "Signer boundary is blocked; no signer config, wallet, or signing is available."
        value.update(signer_boundary_safety_flags(unsigned_plan_created=False))
        return value


@dataclass(frozen=True)
class SignedPayloadAvailability:
    status: str = STATUS_UNAVAILABLE
    signed_payload_available: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SIGNED_PAYLOAD_AVAILABILITY_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = STATUS_UNAVAILABLE
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["review_only"] = True
        value["preflight_only"] = True
        value["signed_payload_status"] = STATUS_UNAVAILABLE
        value["signed_payload_available"] = False
        value["signed_payload_unavailable"] = True
        value["operator_summary"] = "Signed payload is unavailable; generation is blocked by the signer boundary."
        value.update(signer_boundary_safety_flags(unsigned_plan_created=False))
        return value


@dataclass(frozen=True)
class OrderSubmissionAvailability:
    status: str = STATUS_BLOCKED
    order_submission_available: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = ORDER_SUBMISSION_AVAILABILITY_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = STATUS_BLOCKED
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["review_only"] = True
        value["preflight_only"] = True
        value["order_submission_status"] = STATUS_BLOCKED
        value["order_submission_available"] = False
        value["order_submission_blocked"] = True
        value["operator_summary"] = "Order submission is blocked; no submit or cancel path is available."
        value.update(signer_boundary_safety_flags(unsigned_plan_created=False))
        return value


@dataclass(frozen=True)
class SignerBoundaryBlocker:
    blocker_id: str
    blocker_category: str
    reason: str
    severity: str = "critical"
    resolution_status: str = "unresolved"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SIGNER_BOUNDARY_BLOCKER_CONTRACT
        value["task_id"] = TASK_ID
        value["blocks_live_execution"] = True
        value["resolved"] = False
        value.update(signer_boundary_safety_flags(unsigned_plan_created=False))
        return value


@dataclass(frozen=True)
class LatestSignerBoundaryPreflightStatus:
    status: str
    source_paper_intent_path: str
    market_symbol: str
    strategy_name: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    live_candidate_intent_status: str
    unsigned_plan_status: str
    signer_status: str
    signed_payload_status: str
    order_submission_status: str
    unsigned_plan_created: bool
    blocker_count: int
    blockers: tuple[Mapping[str, Any], ...]
    artifact_path: str
    latest_status_path: str
    operator_markdown_path: str
    live_candidate_order_intent_path: str
    unsigned_order_payload_plan_path: str
    signing_boundary_status_path: str
    signed_payload_availability_path: str
    order_submission_availability_path: str
    blockers_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in self.blockers]
        value = asdict(self)
        value["contract_version"] = LATEST_SIGNER_BOUNDARY_PREFLIGHT_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = clean_text(self.status)
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["review_only"] = True
        value["preflight_only"] = True
        value["market"] = clean_text(self.market_symbol).upper() or "BTC"
        value["market_symbol"] = clean_text(self.market_symbol).upper() or "BTC"
        value["strategy_name"] = clean_text(self.strategy_name) or "tiny-momentum"
        value["source_paper_intent_path"] = clean_text(self.source_paper_intent_path)
        value["candidate_outcome"] = clean_text(self.candidate_outcome) or "not_available"
        value["candidate_side"] = clean_text(self.candidate_side) or "not_available"
        value["unsigned_plan_created"] = self.unsigned_plan_created is True
        value["unsigned_plan_is_executable"] = False
        value["signer_config_present"] = False
        value["signed_payload_available"] = False
        value["order_submission_available"] = False
        value["blocker_count"] = len(blockers)
        value["blockers"] = blockers
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in blockers[:8]]
        value["live_candidate_intent"] = clean_text(self.live_candidate_intent_status)
        value["unsigned_payload_plan"] = clean_text(self.unsigned_plan_status)
        value["signer"] = STATUS_BLOCKED
        value["order_submission"] = STATUS_BLOCKED
        value["wallet"] = STATUS_BLOCKED
        value["live_execution"] = STATUS_BLOCKED
        value["next_operator_action"] = "review signer boundary only, no live order available"
        value["operator_summary"] = _latest_operator_summary(value)
        value.update(signer_boundary_safety_flags(unsigned_plan_created=value["unsigned_plan_created"]))
        return value


@dataclass(frozen=True)
class SignerBoundaryPreflightResult:
    status: str
    source_paper_intent_path: str
    market_symbol: str
    strategy_name: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    live_candidate_order_intent: Mapping[str, Any]
    unsigned_order_payload_plan: Mapping[str, Any]
    signing_boundary_status: Mapping[str, Any]
    signed_payload_availability: Mapping[str, Any]
    order_submission_availability: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    blockers: tuple[Mapping[str, Any], ...]
    artifact_paths: Mapping[str, str]
    operator_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        latest_status = dict(self.latest_status)
        blockers = [dict(row) for row in self.blockers]
        value = {
            "contract_version": SIGNER_BOUNDARY_PREFLIGHT_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "dry_run": True,
            "source_paper_intent_path": clean_text(self.source_paper_intent_path),
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "candidate_outcome": clean_text(self.candidate_outcome) or "not_available",
            "candidate_side": clean_text(self.candidate_side) or "not_available",
            "candidate_limit_price": self.candidate_limit_price,
            "candidate_size": self.candidate_size,
            "candidate_notional": self.candidate_notional,
            "unsigned_plan_created": latest_status.get("unsigned_plan_created") is True,
            "unsigned_plan_is_executable": False,
            "signer_config_present": False,
            "private_key_read": False,
            "seed_phrase_read": False,
            "mnemonic_read": False,
            "wallet_connection_attempted": False,
            "signer_instantiated": False,
            "signing_attempted": False,
            "signed_payload_generated": False,
            "signed_payload_available": False,
            "order_submission_attempted": False,
            "order_submission_available": False,
            "order_cancellation_attempted": False,
            "balance_read_attempted": False,
            "position_read_attempted": False,
            "live_execution_approved": False,
            "allowed_for_live": False,
            "resolved_blocker_count": 0,
            "live_candidate_order_intent": dict(self.live_candidate_order_intent),
            "unsigned_order_payload_plan": dict(self.unsigned_order_payload_plan),
            "signing_boundary_status": dict(self.signing_boundary_status),
            "signed_payload_availability": dict(self.signed_payload_availability),
            "order_submission_availability": dict(self.order_submission_availability),
            "latest_status": latest_status,
            "blockers": blockers,
            "blocker_count": len(blockers),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": clean_text(self.operator_summary),
            "generated_at": self.generated_at,
        }
        value.update(signer_boundary_safety_flags(unsigned_plan_created=value["unsigned_plan_created"]))
        value["validation"] = validate_signer_boundary_preflight_result(value, generated_at=self.generated_at)
        return value


def signer_boundary_safety_flags(*, unsigned_plan_created: bool) -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "unsigned_plan_created": unsigned_plan_created is True,
        "unsigned_plan_is_executable": False,
        "signer_config_present": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "wallet_connection_attempted": False,
        "signer_instantiated": False,
        "signing_attempted": False,
        "signed_payload_generated": False,
        "signed_payload_available": False,
        "order_submission_attempted": False,
        "order_submission_available": False,
        "order_cancellation_attempted": False,
        "balance_read_attempted": False,
        "position_read_attempted": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_performed": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_order_payload_generated": False,
        "order_payload_generated": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "real_order_cancelled": False,
        "balance_read_enabled": False,
        "position_read_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "private_key_envs_checked": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "credentials_values_exposed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def build_signer_boundary_blockers_report(
    blockers: Sequence[Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    rows = [dict(row) for row in blockers]
    value = {
        "contract_version": SIGNER_BOUNDARY_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": "unresolved_blockers_present",
        "blocker_count": len(rows),
        "resolved_blocker_count": 0,
        "blockers": rows,
        "top_blocker_reasons": [clean_text(row.get("reason")) for row in rows[:8]],
        "generated_at": generated_at,
    }
    value.update(signer_boundary_safety_flags(unsigned_plan_created=False))
    return value


def validate_signer_boundary_preflight_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != SIGNER_BOUNDARY_PREFLIGHT_RESULT_CONTRACT:
        errors.append(f"contract_version must be {SIGNER_BOUNDARY_PREFLIGHT_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must be preflight")
        statuses.append("invalid_execution_mode")
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
        statuses.append("review_only_missing")
    if value.get("preflight_only") is not True:
        errors.append("preflight_only must be true")
        statuses.append("preflight_only_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    if value.get("unsigned_plan_is_executable") is not False:
        errors.append("unsigned_plan_is_executable must be false")
        statuses.append("unsafe_unsigned_plan_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for path, key, nested in _walk_flags(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key in FORBIDDEN_MODEL_FIELDS:
            errors.append(f"{path}.{key} is forbidden in signer boundary artifacts")
            statuses.append("forbidden_model_field_detected")
    valid = not errors
    return {
        "contract_version": SIGNER_BOUNDARY_PREFLIGHT_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "signer-boundary-preflight-validation-060",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["signer_boundary_preflight_valid"] if valid else ["signer_boundary_preflight_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **signer_boundary_safety_flags(unsigned_plan_created=value.get("unsigned_plan_created") is True),
    }


def _candidate_operator_summary(value: Mapping[str, Any]) -> str:
    if value.get("status") == STATUS_CREATED:
        return (
            "Live candidate intent was derived for review from a paper intent; it is not executable "
            "and cannot be submitted."
        )
    return "Live candidate intent is missing because no source paper intent was available."


def _latest_operator_summary(value: Mapping[str, Any]) -> str:
    return (
        "Signer boundary preflight completed as review-only. Live candidate intent="
        + clean_text(value.get("live_candidate_intent_status"))
        + "; unsigned plan="
        + clean_text(value.get("unsigned_plan_status"))
        + "; signer, signed payload generation, order submission, wallet use, balances, positions, "
        "and live execution are blocked."
    )


def _walk_flags(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            rows.append((path, key_text, nested))
            rows.extend(_walk_flags(nested, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_flags(nested, f"{path}[{index}]"))
    return rows


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
