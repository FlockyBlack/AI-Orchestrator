from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.authenticated_polymarket_connector import (
    build_authenticated_connector_capability_report,
    summarize_authenticated_connector_capability_report,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import validate_static_secret_boundary
from pm_bot.trading_core.wallet_signing_boundary import (
    build_wallet_signing_boundary_report,
    summarize_wallet_signing_boundary_report,
    validate_signing_request_for_review,
)

SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_CONTRACT = (
    "pmbot_signed_order_payload_dry_run_validation_gate.v1"
)
SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_SUMMARY_CONTRACT = (
    "pmbot_signed_order_payload_dry_run_validation_gate_summary.v1"
)
SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_VALIDATION_CONTRACT = (
    "pmbot_signed_order_payload_dry_run_validation_gate_validation.v1"
)

TASK_ID = "ORCH-PMBOT-TRADING-MVP-050-SIGNED-ORDER-PAYLOAD-DRY-RUN-VALIDATION-GATE"
SCHEMA_VERSION = "050.v1"
GATE_NAME = "signed_order_payload_dry_run_validation_gate"

STATUS_SIGNED_PAYLOAD_VALIDATION_BLOCKED = "SIGNED_PAYLOAD_VALIDATION_BLOCKED"
STATUS_SIGNING_DISABLED_REVIEW_ONLY = "SIGNING_DISABLED_REVIEW_ONLY"
STATUS_PAYLOAD_SHAPE_REVIEW_READY = "PAYLOAD_SHAPE_REVIEW_READY"
STATUS_PAYLOAD_SHAPE_INVALID = "PAYLOAD_SHAPE_INVALID"
ALLOWED_STATUSES = frozenset(
    {
        STATUS_SIGNED_PAYLOAD_VALIDATION_BLOCKED,
        STATUS_SIGNING_DISABLED_REVIEW_ONLY,
        STATUS_PAYLOAD_SHAPE_REVIEW_READY,
        STATUS_PAYLOAD_SHAPE_INVALID,
    }
)
FORBIDDEN_READY_STATUSES = frozenset(
    {
        "SIGNED_PAYLOAD_READY",
        "SIGNED_ORDER_READY",
        "ORDER_READY_FOR_SUBMISSION",
        "LIVE_READY",
        "GO_FOR_LIVE",
    }
)

FORCED_FALSE_EXECUTION_FIELDS = (
    "signing_enabled",
    "wallet_signing_enabled",
    "cryptographic_signing_enabled",
    "transaction_signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "signed_payload_present",
    "signed_order_present",
    "signature_present",
    "transaction_hash_present",
    "order_id_present",
    "fill_present",
    "execution_result_present",
    "order_submission_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "authenticated_calls_enabled",
    "network_calls_enabled",
    "would_call_authenticated_endpoint",
    "would_submit_order",
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "execution_enabling",
    "execution_enabled",
    "live_approval",
    "live_execution_allowed",
    "live_execution_enabled",
    "live_execution_performed",
    "real_order_submitted",
    "order_submitted",
    "real_signature_created",
    "wallet_used",
    "real_wallet_used",
    "external_api_calls_performed",
    "network_used",
)

FORBIDDEN_INPUT_FIELD_NAMES = frozenset(
    {
        "signature",
        "signatures",
        "signed_payload",
        "signed_order",
        "signed_order_id",
        "tx_hash",
        "tx_hashes",
        "transaction_hash",
        "transaction_hashes",
        "order_id",
        "order_ids",
        "fill_id",
        "fill_ids",
        "fill",
        "fills",
        "execution",
        "execution_id",
        "execution_result",
        "execution_results",
        "order_submission_result",
        "submitted_order",
        "submitted_order_id",
        "balance",
        "balances",
        "pnl",
        "realized_pnl",
        "unrealized_pnl",
        "profit_loss",
    }
)

FUTURE_REQUIRED_PAYLOAD_FIELD_SPECS = (
    {
        "field": "market_id_or_token_id",
        "accepted_fields": ("market_id", "token_id"),
        "expected_type": "non_empty_string",
        "description": "Future signed-order payload must identify the market or token without exposing credentials.",
    },
    {
        "field": "side",
        "accepted_fields": ("side",),
        "expected_type": "non_empty_string",
        "description": "Future payload shape records the intended side from the dry-run intent.",
    },
    {
        "field": "outcome",
        "accepted_fields": ("outcome",),
        "expected_type": "non_empty_string",
        "description": "Future payload shape records the intended outcome from the dry-run intent.",
    },
    {
        "field": "price",
        "accepted_fields": ("price",),
        "expected_type": "number",
        "description": "Future payload shape records the limit price as unsigned numeric metadata.",
    },
    {
        "field": "size",
        "accepted_fields": ("size",),
        "expected_type": "number",
        "description": "Future payload shape records the order size as unsigned numeric metadata.",
    },
    {
        "field": "notional_usd",
        "accepted_fields": ("notional_usd", "notional"),
        "expected_type": "number",
        "description": "Future payload shape records the tiny notional limit for operator review.",
    },
    {
        "field": "order_type",
        "accepted_fields": ("order_type",),
        "expected_type": "non_empty_string",
        "description": "Future payload shape records order type without constructing an executable order.",
    },
    {
        "field": "time_in_force",
        "accepted_fields": ("time_in_force", "expiry"),
        "expected_type": "non_empty_string",
        "description": "Future payload shape records time-in-force or expiry policy.",
    },
    {
        "field": "operator_approval_reference",
        "accepted_fields": ("operator_approval_reference", "operator_approval_record_id"),
        "expected_type": "non_empty_string",
        "description": "Future payload shape links a human approval reference without treating it as live approval.",
    },
    {
        "field": "risk_decision_reference",
        "accepted_fields": ("risk_decision_reference", "risk_decision_id"),
        "expected_type": "non_empty_string",
        "description": "Future payload shape links the risk decision reference.",
    },
    {
        "field": "connector_capability_reference",
        "accepted_fields": ("connector_capability_reference", "connector_capability_report_id"),
        "expected_type": "non_empty_string",
        "description": "Future payload shape links the authenticated connector scaffold capability reference.",
    },
    {
        "field": "wallet_signing_boundary_reference",
        "accepted_fields": ("wallet_signing_boundary_reference", "wallet_signing_boundary_id"),
        "expected_type": "non_empty_string",
        "description": "Future payload shape links the wallet/signing boundary refusal artifact.",
    },
)

DEFAULT_BLOCKED_REASONS = (
    "signed_order_payload_validation_gate_review_only",
    "task_050_does_not_sign_payloads",
    "task_050_does_not_generate_signed_payloads",
    "task_050_does_not_generate_signed_orders",
    "wallet_signing_enabled_false",
    "signing_enabled_false",
    "signed_payload_generation_enabled_false",
    "signed_order_generation_enabled_false",
    "order_submission_enabled_false",
    "authenticated_polymarket_enabled_false",
    "live_connector_enabled_false",
    "real_execution_unavailable",
    "live_blockers_remain_unresolved",
)

OPERATOR_REQUIRED_ACTIONS = (
    "Review payload shape only; do not provide private keys, wallet files, mnemonics, API secrets, auth tokens, signatures, signed payloads, or signed orders.",
    "Confirm the future payload fields are sufficient for a later separately approved signing task.",
    "Keep wallet signing, signed payload generation, signed order generation, authenticated Polymarket access, and order submission disabled.",
    "Use a separate future operator-approved task before any signing, live connector, or order submission implementation.",
)

FUTURE_ENABLEMENT_REQUIREMENTS = (
    "separate operator-approved live/signing task",
    "reviewed wallet custody and signing provider design",
    "redacted credential handling and audit policy",
    "authenticated connector endpoint allowlist with fully mocked tests",
    "disabled-first order adapter with refusal tests",
    "dual-control live operator approval",
    "live kill switch verified against every future execution path",
    "all live blockers resolved in separate reviewed tasks",
)


@dataclass(frozen=True)
class SignedOrderPayloadValidationGate:
    gate_id: str
    task_id: str
    schema_version: str
    gate_name: str
    status: str
    generated_at: str
    input_intent_summary: Mapping[str, Any]
    connector_capability_summary: Mapping[str, Any]
    wallet_signing_boundary_summary: Mapping[str, Any]
    signing_request_review_summary: Mapping[str, Any]
    required_payload_fields_summary: Mapping[str, Any]
    missing_fields: tuple[str, ...]
    invalid_fields: tuple[Mapping[str, Any], ...]
    blocked_reasons: tuple[str, ...]
    operator_required_actions: tuple[str, ...]
    future_enablement_requirements: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_CONTRACT
        value["input_intent_summary"] = dict(self.input_intent_summary)
        value["connector_capability_summary"] = dict(self.connector_capability_summary)
        value["wallet_signing_boundary_summary"] = dict(self.wallet_signing_boundary_summary)
        value["signing_request_review_summary"] = dict(self.signing_request_review_summary)
        value["required_payload_fields_summary"] = dict(self.required_payload_fields_summary)
        value["missing_fields"] = list(self.missing_fields)
        value["invalid_fields"] = [dict(row) for row in self.invalid_fields]
        value["blocked_reasons"] = list(self.blocked_reasons)
        value["top_blocked_reasons"] = list(self.blocked_reasons)[:5]
        value["operator_required_actions"] = list(self.operator_required_actions)
        value["future_enablement_requirements"] = list(self.future_enablement_requirements)
        value["review_only"] = True
        value["dry_run_only"] = True
        value["paper_only"] = True
        value["payload_shape_status"] = self.status
        value["payload_shape_review_ready"] = self.status == STATUS_PAYLOAD_SHAPE_REVIEW_READY
        value["missing_field_count"] = len(self.missing_fields)
        value["invalid_field_count"] = len(self.invalid_fields)
        value["resolved_blocker_count"] = 0
        value["unresolved_blocker_count"] = len(self.blocked_reasons)
        value["live_blockers_unresolved"] = True
        value["no_executable_action"] = True
        value["no_signature_returned"] = True
        value["no_signed_payload_returned"] = True
        value["no_signed_order_returned"] = True
        value["no_transaction_hash_returned"] = True
        value["no_order_id_returned"] = True
        value["no_fill_returned"] = True
        value["no_execution_result_returned"] = True
        value["no_fake_signature_generated"] = True
        value["no_fake_signed_payload_generated"] = True
        value["no_fake_signed_order_generated"] = True
        value["no_fake_order_id_generated"] = True
        value["no_fake_transaction_hash_generated"] = True
        value["no_fake_fill_generated"] = True
        value["no_fake_execution_result_generated"] = True
        value["raw_payload_echoed"] = False
        value["request_payload_echoed"] = False
        value["safety_summary"] = trading_core_safety_summary()
        value.update(_gate_safety_flags())
        return value


def build_signed_order_payload_validation_gate(
    input_intent: Mapping[str, Any] | None = None,
    *,
    connector_capability_report: Mapping[str, Any] | None = None,
    connector_capability_summary: Mapping[str, Any] | None = None,
    wallet_signing_boundary_report: Mapping[str, Any] | None = None,
    wallet_signing_boundary_summary: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    payload = dict(input_intent or {})
    connector_report = dict(
        connector_capability_report or build_authenticated_connector_capability_report(generated_at=generated_at)
    )
    connector_summary = dict(
        connector_capability_summary
        or summarize_authenticated_connector_capability_report(connector_report, generated_at=generated_at)
    )
    wallet_report = dict(
        wallet_signing_boundary_report or build_wallet_signing_boundary_report(generated_at=generated_at)
    )
    wallet_summary = dict(
        wallet_signing_boundary_summary
        or summarize_wallet_signing_boundary_report(wallet_report, generated_at=generated_at)
    )
    signing_review = validate_signing_request_for_review(
        payload,
        boundary_report=wallet_report,
        generated_at=generated_at,
    )
    signing_review_summary = {
        "contract_version": "pmbot_signed_order_payload_gate_wallet_signing_review_summary.v1",
        "status": clean_text(signing_review.get("status")),
        "signing_request_refused": signing_review.get("signing_request_refused") is True,
        "refusal_reasons": list(signing_review.get("refusal_reasons", []))[:8],
        "signature_present": False,
        "signed_payload_present": False,
        "signed_order_present": False,
        "transaction_hash_present": False,
        "order_id_present": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "order_submission_enabled": False,
        "allowed_for_live": False,
        "real_execution_available": False,
        "resolved_blocker_count": 0,
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
    }
    shape = _payload_shape_validation(payload)
    blocked_reasons = _blocked_reasons(
        payload_present=bool(payload),
        missing_fields=shape["missing_fields"],
        invalid_fields=shape["invalid_fields"],
        forbidden_field_paths=shape["forbidden_field_paths"],
        connector_summary=connector_summary,
        wallet_summary=wallet_summary,
    )
    status = _status(
        payload_present=bool(payload),
        missing_fields=shape["missing_fields"],
        invalid_fields=shape["invalid_fields"],
        forbidden_field_paths=shape["forbidden_field_paths"],
        execution_claim_field_paths=shape["execution_claim_field_paths"],
    )
    gate = SignedOrderPayloadValidationGate(
        gate_id=_stable_id(
            "signed-order-payload-validation-gate-050",
            {
                "status": status,
                "input_summary": shape["input_intent_summary"],
                "missing_fields": shape["missing_fields"],
                "invalid_fields": shape["invalid_fields"],
                "connector_summary": connector_summary.get("summary_id")
                or connector_summary.get("capability_report_id"),
                "wallet_summary": wallet_summary.get("summary_id") or wallet_summary.get("boundary_id"),
            },
        ),
        task_id=TASK_ID,
        schema_version=SCHEMA_VERSION,
        gate_name=GATE_NAME,
        status=status,
        generated_at=generated_at,
        input_intent_summary=shape["input_intent_summary"],
        connector_capability_summary=connector_summary,
        wallet_signing_boundary_summary=wallet_summary,
        signing_request_review_summary=signing_review_summary,
        required_payload_fields_summary=_required_payload_fields_summary(),
        missing_fields=tuple(shape["missing_fields"]),
        invalid_fields=tuple(shape["invalid_fields"]),
        blocked_reasons=tuple(blocked_reasons),
        operator_required_actions=OPERATOR_REQUIRED_ACTIONS,
        future_enablement_requirements=FUTURE_ENABLEMENT_REQUIREMENTS,
    ).to_dict()
    gate["validation"] = validate_signed_order_payload_validation_gate(gate, generated_at=generated_at)
    return gate


def summarize_signed_order_payload_validation_gate(
    gate: Mapping[str, Any] | None = None,
    *,
    latest_signed_order_payload_validation_gate_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if gate and gate.get("contract_version") == SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_SUMMARY_CONTRACT:
        value = dict(gate)
        if latest_signed_order_payload_validation_gate_path:
            value["latest_signed_order_payload_validation_gate_path"] = clean_text(
                latest_signed_order_payload_validation_gate_path
            )
        value.update(_gate_safety_flags())
        value["signed_order_payload_validation_gate_section_ready"] = True
        return value
    value = dict(gate or build_signed_order_payload_validation_gate(generated_at=generated_at))
    validation = (
        dict(value.get("validation", {}))
        if isinstance(value.get("validation"), Mapping)
        else validate_signed_order_payload_validation_gate(value, generated_at=generated_at)
    )
    input_summary = dict(value.get("input_intent_summary", {}))
    summary = {
        "contract_version": SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "signed-order-payload-validation-gate-summary-050",
            {
                "gate_id": value.get("gate_id"),
                "status": value.get("status"),
                "latest_path": clean_text(latest_signed_order_payload_validation_gate_path),
            },
        ),
        "schema_version": SCHEMA_VERSION,
        "gate_name": clean_text(value.get("gate_name") or GATE_NAME),
        "gate_id": clean_text(value.get("gate_id")),
        "status": clean_text(value.get("status") or STATUS_SIGNING_DISABLED_REVIEW_ONLY),
        "payload_shape_status": clean_text(value.get("payload_shape_status") or value.get("status")),
        "payload_shape_review_ready": value.get("payload_shape_review_ready") is True,
        "input_payload_present": input_summary.get("payload_present") is True,
        "required_payload_field_count": int(
            dict(value.get("required_payload_fields_summary", {})).get("required_field_count", 0) or 0
        ),
        "missing_fields": list(value.get("missing_fields", [])),
        "missing_field_count": int(value.get("missing_field_count", 0) or 0),
        "invalid_fields": [dict(row) for row in value.get("invalid_fields", []) if isinstance(row, Mapping)],
        "invalid_field_count": int(value.get("invalid_field_count", 0) or 0),
        "top_blocked_reasons": list(value.get("blocked_reasons", []))[:5],
        "blocked_reasons": list(value.get("blocked_reasons", [])),
        "operator_required_actions": list(value.get("operator_required_actions", []))[:5],
        "future_enablement_requirements": list(value.get("future_enablement_requirements", [])),
        "validation_status": clean_text(validation.get("status") or "blocked"),
        "validation_valid": validation.get("valid") is True,
        "latest_signed_order_payload_validation_gate_path": clean_text(
            latest_signed_order_payload_validation_gate_path
            or value.get("latest_signed_order_payload_validation_gate_path")
        ),
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
        "no_executable_action": True,
        "resolved_blocker_count": 0,
        "signed_order_payload_validation_gate_section_ready": True,
    }
    summary.update(_gate_safety_flags())
    return summary


def validate_signed_order_payload_validation_gate(
    gate: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(gate or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") not in {
        SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_CONTRACT,
        SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_SUMMARY_CONTRACT,
    }:
        errors.append("contract_version is not a supported signed order payload validation gate contract")
        statuses.append("invalid_contract")
    if clean_text(value.get("schema_version")) != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
        statuses.append("invalid_schema_version")
    if clean_text(value.get("gate_name")) != GATE_NAME:
        errors.append(f"gate_name must be {GATE_NAME}")
        statuses.append("invalid_gate_name")
    if clean_text(value.get("status")) not in ALLOWED_STATUSES:
        errors.append("status must remain a review-only signed payload validation gate status")
        statuses.append("unsupported_status")
    for forbidden_status in FORBIDDEN_READY_STATUSES:
        if _contains_text(value, forbidden_status):
            errors.append(f"{forbidden_status} must never be emitted by task 050")
            statuses.append("forbidden_ready_status_detected")
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
        statuses.append("review_only_missing")
    if value.get("no_executable_action") is not True:
        errors.append("no_executable_action must be true")
        statuses.append("executable_action_detected")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    for field in ("signature", "signed_payload", "signed_order", "tx_hash", "transaction_hash", "order_id"):
        if field in value:
            errors.append(f"{field} must not be returned by this dry-run validation gate")
            statuses.append("forbidden_output_key_detected")
    for path, key, nested in _walk_flags(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_execution_flag_detected")
    secret_validation = validate_static_secret_boundary(
        value,
        artifact_type="signed_order_payload_validation_gate",
        generated_at=generated_at,
    )
    if secret_validation.get("valid") is not True:
        errors.append("signed order payload validation gate violates static secret boundary")
        statuses.append("secret_boundary_blocked")
    valid = not errors
    return {
        "contract_version": SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "signed-order-payload-validation-gate-validation-050",
            {
                "gate_id": value.get("gate_id") or value.get("summary_id"),
                "status": value.get("status"),
                "errors": errors,
                "statuses": statuses,
            },
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": ["signed_order_payload_validation_gate_valid"] if valid else _dedupe(statuses),
        "errors": errors,
        "secret_boundary_validation": secret_validation,
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
        "resolved_blocker_count": 0,
        **_gate_safety_flags(),
    }


def _payload_shape_validation(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing_fields: list[str] = []
    invalid_fields: list[dict[str, Any]] = []
    field_presence: dict[str, bool] = {}
    for spec in FUTURE_REQUIRED_PAYLOAD_FIELD_SPECS:
        field = clean_text(spec["field"])
        accepted = tuple(clean_text(item) for item in spec["accepted_fields"])
        present_name = next((name for name in accepted if name in payload), "")
        present = bool(present_name)
        field_presence[field] = present
        if not present:
            missing_fields.append(field)
            continue
        invalid_reason = _field_invalid_reason(payload.get(present_name), clean_text(spec["expected_type"]))
        if invalid_reason:
            invalid_fields.append(
                {
                    "field": field,
                    "input_field": present_name,
                    "reason": invalid_reason,
                    "expected_type": clean_text(spec["expected_type"]),
                }
            )
    forbidden_field_paths = _forbidden_payload_field_paths(payload)
    execution_claim_field_paths = _execution_claim_field_paths(payload)
    for path in forbidden_field_paths:
        invalid_fields.append(
            {
                "field": "forbidden_output_or_execution_result",
                "field_path": path,
                "reason": "signed payloads, signed orders, signatures, tx hashes, order ids, fills, balances, PnL, and execution results are forbidden in task 050 input",
            }
        )
    for path in execution_claim_field_paths:
        invalid_fields.append(
            {
                "field": "forbidden_execution_claim",
                "field_path": path,
                "reason": "input must not claim enabled signing, order submission, authenticated access, live execution, or real execution",
            }
        )
    return {
        "missing_fields": _dedupe(missing_fields),
        "invalid_fields": _dedupe_invalid_fields(invalid_fields),
        "forbidden_field_paths": forbidden_field_paths,
        "execution_claim_field_paths": execution_claim_field_paths,
        "input_intent_summary": _input_intent_summary(
            payload,
            field_presence=field_presence,
            forbidden_field_paths=forbidden_field_paths,
            execution_claim_field_paths=execution_claim_field_paths,
        ),
    }


def _input_intent_summary(
    payload: Mapping[str, Any],
    *,
    field_presence: Mapping[str, bool],
    forbidden_field_paths: Sequence[str],
    execution_claim_field_paths: Sequence[str],
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_signed_order_payload_input_intent_summary.v1",
        "payload_present": bool(payload),
        "top_level_field_count": len(payload),
        "raw_payload_echoed": False,
        "request_payload_echoed": False,
        "raw_values_emitted": False,
        "field_presence": dict(field_presence),
        "future_market_identifier_present": field_presence.get("market_id_or_token_id") is True,
        "forbidden_output_field_count": len(forbidden_field_paths),
        "forbidden_execution_claim_count": len(execution_claim_field_paths),
        "secret_like_field_rejected": bool(forbidden_field_paths),
        "signing_enabled": False,
        "wallet_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "order_submission_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _required_payload_fields_summary() -> dict[str, Any]:
    specs = []
    for spec in FUTURE_REQUIRED_PAYLOAD_FIELD_SPECS:
        specs.append(
            {
                "field": spec["field"],
                "accepted_fields": list(spec["accepted_fields"]),
                "expected_type": spec["expected_type"],
                "description": spec["description"],
            }
        )
    return {
        "contract_version": "pmbot_future_signed_order_payload_required_fields.v1",
        "schema_defined_for_future_review_only": True,
        "required_field_count": len(specs),
        "required_fields": specs,
        "does_not_define_signature_material": True,
        "does_not_define_signed_payload_output": True,
        "does_not_define_signed_order_output": True,
        "does_not_define_order_submission": True,
    }


def _field_invalid_reason(value: Any, expected_type: str) -> str:
    if expected_type == "non_empty_string":
        return "" if isinstance(value, str) and bool(clean_text(value)) else "must be a non-empty string"
    if expected_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "must be numeric"
        if float(value) <= 0:
            return "must be greater than 0"
        return ""
    return ""


def _status(
    *,
    payload_present: bool,
    missing_fields: Sequence[str],
    invalid_fields: Sequence[Mapping[str, Any]],
    forbidden_field_paths: Sequence[str],
    execution_claim_field_paths: Sequence[str],
) -> str:
    if forbidden_field_paths or execution_claim_field_paths:
        return STATUS_SIGNED_PAYLOAD_VALIDATION_BLOCKED
    if missing_fields or invalid_fields:
        return STATUS_PAYLOAD_SHAPE_INVALID if payload_present else STATUS_SIGNING_DISABLED_REVIEW_ONLY
    if payload_present:
        return STATUS_PAYLOAD_SHAPE_REVIEW_READY
    return STATUS_SIGNING_DISABLED_REVIEW_ONLY


def _blocked_reasons(
    *,
    payload_present: bool,
    missing_fields: Sequence[str],
    invalid_fields: Sequence[Mapping[str, Any]],
    forbidden_field_paths: Sequence[str],
    connector_summary: Mapping[str, Any],
    wallet_summary: Mapping[str, Any],
) -> list[str]:
    reasons = list(DEFAULT_BLOCKED_REASONS)
    if not payload_present:
        reasons.insert(0, "no_payload_provided_shape_review_only_default")
    if missing_fields:
        reasons.append("future_signed_order_payload_missing_required_fields")
    if invalid_fields:
        reasons.append("future_signed_order_payload_invalid_fields")
    if forbidden_field_paths:
        reasons.append("input_contains_forbidden_signed_or_execution_result_field")
    if connector_summary.get("review_only") is not False:
        reasons.append("authenticated_connector_scaffold_review_only")
    if wallet_summary.get("review_only") is not False:
        reasons.append("wallet_signing_boundary_refuses_signing")
    return _dedupe(reasons)


def _forbidden_payload_field_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            normalized = _normalize_key(key_text)
            nested_path = f"{path}.{key_text}"
            if normalized in FORBIDDEN_INPUT_FIELD_NAMES:
                paths.append(nested_path)
            paths.extend(_forbidden_payload_field_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_forbidden_payload_field_paths(nested, f"{path}[{index}]"))
    return _dedupe(paths)


def _execution_claim_field_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORCED_FALSE_EXECUTION_FIELDS and nested is True:
                paths.append(nested_path)
            paths.extend(_execution_claim_field_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_execution_claim_field_paths(nested, f"{path}[{index}]"))
    return _dedupe(paths)


def _gate_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "manual_review_only": True,
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "execution_enabling": False,
        "execution_enabled": False,
        "live_approval": False,
        "signing_enabled": False,
        "wallet_signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "transaction_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "signed_payload_present": False,
        "signed_order_present": False,
        "signature_present": False,
        "transaction_hash_present": False,
        "order_id_present": False,
        "fill_present": False,
        "execution_result_present": False,
        "real_signature_created": False,
        "wallet_used": False,
        "real_wallet_used": False,
        "order_submission_enabled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_calls_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_endpoint_called": False,
        "live_connector_enabled": False,
        "network_calls_enabled": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "would_call_authenticated_endpoint": False,
        "would_submit_order": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "live_execution_performed": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "no_raw_secrets_parsed_or_emitted": True,
        "raw_secret_values_printed": False,
        "raw_secret_values_persisted": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


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


def _contains_text(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return clean_text(value) == needle
    if isinstance(value, Mapping):
        return any(_contains_text(nested, needle) for nested in value.values())
    if isinstance(value, list):
        return any(_contains_text(nested, needle) for nested in value)
    return False


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _dedupe_invalid_fields(values: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in values:
        canonical = json.dumps(dict(value), sort_keys=True)
        if canonical not in seen:
            seen.add(canonical)
            result.append(dict(value))
    return result


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _normalize_key(value: str) -> str:
    normalized = "".join(character if character.isalnum() else "_" for character in clean_text(value).lower())
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")
