from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.btc_market_analysis_order_intent import (
    ANALYSIS_READY_FOR_DRY_RUN_INTENT,
    INTENT_CANDIDATE_READY,
)
from pm_bot.trading_core.live_credentials_auth_boundary import summarize_live_credentials_status
from pm_bot.trading_core.risk_limit_control_plane import DECISION_ALLOW_DRY_RUN, summarize_risk_limit_decision
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, mapping_rows, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_live_order_submission_boundary_receipt,
    validate_secret_boundary_live_order_submission_boundary_summary,
)

LIVE_ORDER_SUBMISSION_BOUNDARY_RECEIPT_CONTRACT = (
    "pmbot_live_order_submission_boundary_receipt.v1"
)
LIVE_ORDER_SUBMISSION_BOUNDARY_SUMMARY_CONTRACT = (
    "pmbot_live_order_submission_boundary_summary.v1"
)
LIVE_ORDER_SUBMISSION_BOUNDARY_VALIDATION_CONTRACT = (
    "pmbot_live_order_submission_boundary_validation.v1"
)

BOUNDARY_NAME = "live_order_submission_boundary_dry_run_adapter"
STATUS_DRY_RUN_REVIEW_READY = "dry_run_submission_boundary_review_ready"
STATUS_BLOCKED = "blocked"
STATUS_BLOCKED_LIVE_EXECUTION_VIOLATION = "blocked_live_execution_violation"

LIVE_REFUSAL_REASONS = (
    "ORDER_SUBMISSION_DISABLED",
    "AUTHENTICATED_ENDPOINTS_DISABLED",
    "SIGNING_DISABLED",
    "WALLET_DISABLED",
    "LIVE_EXECUTION_NOT_APPROVED",
    "REAL_EXECUTION_UNAVAILABLE",
    "CANARY_NOT_EXECUTABLE",
)

FORCED_FALSE_EXECUTION_FIELDS = (
    "would_submit_order",
    "order_submission_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "wallet_signing_enabled",
    "wallet_enabled",
    "allowed_for_live",
    "live_execution_approved",
    "real_execution_available",
    "canary_executable_now",
    "live_connector_enabled",
    "real_order_submitted",
    "order_submitted",
    "real_order_placement_performed",
    "authenticated_endpoint_called",
    "authenticated_endpoint_call_performed",
    "authenticated_endpoint_used",
    "wallet_used",
    "real_wallet_used",
    "private_key_used",
    "signing_used",
    "real_signature_created",
    "cryptographic_signing_performed",
    "wallet_signing_performed",
    "transaction_signing_performed",
    "network_used",
    "external_api_calls_performed",
    "external_api_call_performed",
    "live_execution_allowed",
    "live_execution_enabled",
    "live_execution_performed",
)


@dataclass(frozen=True)
class LiveOrderSubmissionBoundaryReceipt:
    receipt_id: str
    schema_version: str
    boundary_name: str
    status: str
    market_id: str
    market_slug: str
    asset: str
    side: str
    outcome: str
    dry_run_order_intent_summary: Mapping[str, Any]
    risk_decision_summary: Mapping[str, Any]
    auth_boundary_summary: Mapping[str, Any]
    operator_context_summary: Mapping[str, Any]
    kill_switch_summary: Mapping[str, Any]
    live_blockers_summary: Mapping[str, Any]
    authenticated_endpoint_required: bool
    signing_required_for_future_live: bool
    wallet_required_for_future_live: bool
    allowed_for_dry_run_review: bool
    refusal_reasons: tuple[str, ...]
    blocker_reasons: tuple[str, ...]
    created_at: str
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_ORDER_SUBMISSION_BOUNDARY_RECEIPT_CONTRACT
        value["dry_run_order_intent_summary"] = dict(self.dry_run_order_intent_summary)
        value["risk_decision_summary"] = dict(self.risk_decision_summary)
        value["auth_boundary_summary"] = dict(self.auth_boundary_summary)
        value["operator_context_summary"] = dict(self.operator_context_summary)
        value["kill_switch_summary"] = dict(self.kill_switch_summary)
        value["live_blockers_summary"] = dict(self.live_blockers_summary)
        value["refusal_reasons"] = list(self.refusal_reasons)
        value["blocker_reasons"] = list(self.blocker_reasons)
        value["authenticated_endpoint_enabled"] = False
        value["authenticated_endpoints_enabled"] = False
        value["signing_enabled"] = False
        value["cryptographic_signing_enabled"] = False
        value["wallet_signing_enabled"] = False
        value["wallet_enabled"] = False
        value["would_submit_order"] = False
        value["order_submission_enabled"] = False
        value["allowed_for_live"] = False
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["canary_executable_now"] = False
        value["live_connector_enabled"] = False
        value["order_submission_claimed"] = False
        value["fill_claimed"] = False
        value["execution_claimed"] = False
        value["dry_run_submission_boundary_ready"] = self.status == STATUS_DRY_RUN_REVIEW_READY
        value["boundary_is_not_live_approval"] = True
        value["receipt_is_not_order_submission"] = True
        value["safe_for_operator_review"] = self.allowed_for_dry_run_review is True
        value["safety_summary"] = trading_core_safety_summary()
        value.update(_boundary_safety_flags())
        return value


def build_live_order_submission_boundary_receipt(
    *,
    btc_dry_run_order_intent: Mapping[str, Any] | None = None,
    dry_run_order_intent_plan: Mapping[str, Any] | None = None,
    btc_analysis_summary: Mapping[str, Any] | None = None,
    risk_decision: Mapping[str, Any] | None = None,
    risk_decision_summary: Mapping[str, Any] | None = None,
    risk_control_plane_summary: Mapping[str, Any] | None = None,
    live_credentials_auth_boundary: Mapping[str, Any] | None = None,
    live_credentials_auth_boundary_summary: Mapping[str, Any] | None = None,
    operator_approval_packet: Mapping[str, Any] | None = None,
    operator_intent_packet: Mapping[str, Any] | None = None,
    operator_context: Mapping[str, Any] | None = None,
    kill_switch_context: Mapping[str, Any] | None = None,
    blocker_matrix: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    btc_result = dict(btc_dry_run_order_intent or {})
    analysis = dict(btc_result.get("analysis", {}))
    intent_plan = dict(dry_run_order_intent_plan or btc_result.get("order_intent_plan", {}))
    intent = _intent_from_plan(intent_plan)
    analysis_summary = _dry_run_intent_summary(
        btc_analysis_summary=btc_analysis_summary,
        btc_result=btc_result,
        analysis=analysis,
        intent_plan=intent_plan,
        intent=intent,
        generated_at=generated_at,
    )
    active_risk_decision = dict(risk_decision or btc_result.get("risk_decision", {}) or {})
    active_risk_summary = _risk_summary(
        risk_decision_summary=risk_decision_summary or btc_result.get("risk_decision_summary", {}),
        risk_decision=active_risk_decision,
        risk_control_plane_summary=risk_control_plane_summary or btc_result.get("risk_control_plane_summary", {}),
    )
    active_auth_summary = _auth_summary(
        live_credentials_auth_boundary=live_credentials_auth_boundary,
        live_credentials_auth_boundary_summary=(
            live_credentials_auth_boundary_summary
            or btc_result.get("live_credentials_boundary_status", {})
            or analysis_summary
        ),
        generated_at=generated_at,
    )
    operator_summary = _operator_summary(
        operator_approval_packet=operator_approval_packet,
        operator_intent_packet=operator_intent_packet,
        operator_context=operator_context,
    )
    kill_summary = _kill_switch_summary(kill_switch_context)
    blockers_summary = _live_blockers_summary(blocker_matrix)

    dry_run_blockers = _dry_run_blockers(
        analysis_summary=analysis_summary,
        risk_summary=active_risk_summary,
        auth_summary=active_auth_summary,
        intent=intent,
    )
    execution_violations = _execution_flag_violations(
        {
            "btc_dry_run_order_intent": btc_result,
            "dry_run_order_intent_plan": intent_plan,
            "risk_decision": active_risk_decision,
            "risk_decision_summary": active_risk_summary,
            "auth_boundary_summary": active_auth_summary,
            "operator_context": operator_summary,
            "kill_switch_context": kill_summary,
            "blocker_matrix": blockers_summary,
        }
    )
    if int(blockers_summary.get("resolved_blocker_count", 0) or 0) > 0:
        dry_run_blockers.append("LIVE_BLOCKER_MATRIX_HAS_RESOLVED_ROWS")

    allowed_for_dry_run_review = not dry_run_blockers and not execution_violations
    if execution_violations:
        status = STATUS_BLOCKED_LIVE_EXECUTION_VIOLATION
    elif dry_run_blockers:
        status = STATUS_BLOCKED
    else:
        status = STATUS_DRY_RUN_REVIEW_READY

    future_live_requires_order_boundary = bool(intent) and _looks_like_btc_intent(analysis_summary, intent)
    live_blocker_reasons = _dedupe(
        [
            *dry_run_blockers,
            *execution_violations,
            *LIVE_REFUSAL_REASONS,
            *[
                clean_text(row.get("blocker_category") or row.get("blocker_id"))
                for row in mapping_rows(blockers_summary.get("top_blockers"))
            ],
        ]
    )
    refusal_reasons = _dedupe([*execution_violations, *(dry_run_blockers or LIVE_REFUSAL_REASONS)])
    receipt_id = _stable_id(
        "live-order-submission-boundary-041",
        {
            "boundary_name": BOUNDARY_NAME,
            "status": status,
            "intent_id": analysis_summary.get("intent_id"),
            "market_id": analysis_summary.get("market_id"),
            "risk_decision_status": active_risk_summary.get("risk_decision_status"),
            "auth_boundary_status": active_auth_summary.get("live_credentials_boundary_status"),
            "refusal_reasons": refusal_reasons,
            "blocker_reasons": live_blocker_reasons,
        },
    )
    receipt = LiveOrderSubmissionBoundaryReceipt(
        receipt_id=receipt_id,
        schema_version="041.v1",
        boundary_name=BOUNDARY_NAME,
        status=status,
        market_id=clean_text(analysis_summary.get("market_id")),
        market_slug=clean_text(analysis_summary.get("market_slug")),
        asset=clean_text(analysis_summary.get("asset")),
        side=clean_text(analysis_summary.get("side")),
        outcome=clean_text(analysis_summary.get("outcome")),
        dry_run_order_intent_summary=analysis_summary,
        risk_decision_summary=active_risk_summary,
        auth_boundary_summary=active_auth_summary,
        operator_context_summary=operator_summary,
        kill_switch_summary=kill_summary,
        live_blockers_summary=blockers_summary,
        authenticated_endpoint_required=future_live_requires_order_boundary,
        signing_required_for_future_live=future_live_requires_order_boundary,
        wallet_required_for_future_live=future_live_requires_order_boundary,
        allowed_for_dry_run_review=allowed_for_dry_run_review,
        refusal_reasons=tuple(refusal_reasons),
        blocker_reasons=tuple(live_blocker_reasons),
        created_at=generated_at,
        generated_at=generated_at,
    ).to_dict()
    validation = validate_live_order_submission_boundary_receipt(receipt, generated_at=generated_at)
    receipt["validation"] = validation
    if validation.get("valid") is not True and receipt["status"] == STATUS_DRY_RUN_REVIEW_READY:
        receipt["status"] = STATUS_BLOCKED_LIVE_EXECUTION_VIOLATION
        receipt["allowed_for_dry_run_review"] = False
        receipt["dry_run_submission_boundary_ready"] = False
        receipt["safe_for_operator_review"] = False
        receipt["refusal_reasons"] = _dedupe(
            list(receipt.get("refusal_reasons", [])) + ["BOUNDARY_RECEIPT_VALIDATION_FAILED"]
        )
        receipt["blocker_reasons"] = _dedupe(
            list(receipt.get("blocker_reasons", [])) + ["BOUNDARY_RECEIPT_VALIDATION_FAILED"]
        )
        receipt["validation"] = validate_live_order_submission_boundary_receipt(
            receipt,
            generated_at=generated_at,
        )
    return receipt


def summarize_live_order_submission_boundary_receipt(
    receipt: Mapping[str, Any] | None = None,
    *,
    latest_live_order_submission_boundary_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(receipt or {})
    validation = (
        dict(value.get("validation", {}))
        if isinstance(value.get("validation"), Mapping)
        else validate_live_order_submission_boundary_receipt(value, generated_at=generated_at)
        if value
        else {"valid": False, "status": "not_available", "errors": ["receipt not provided"]}
    )
    summary = {
        "contract_version": LIVE_ORDER_SUBMISSION_BOUNDARY_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "live-order-submission-boundary-summary-041",
            {
                "receipt_id": value.get("receipt_id"),
                "status": value.get("status"),
                "latest_path": clean_text(latest_live_order_submission_boundary_path),
            },
        ),
        "generated_at": generated_at,
        "boundary_name": clean_text(value.get("boundary_name") or BOUNDARY_NAME),
        "receipt_id": clean_text(value.get("receipt_id")),
        "status": clean_text(value.get("status") or "not_available"),
        "dry_run_review_ready": value.get("allowed_for_dry_run_review") is True,
        "allowed_for_dry_run_review": value.get("allowed_for_dry_run_review") is True,
        "market_id": clean_text(value.get("market_id")),
        "market_slug": clean_text(value.get("market_slug")),
        "asset": clean_text(value.get("asset")),
        "side": clean_text(value.get("side")),
        "outcome": clean_text(value.get("outcome")),
        "would_submit_order": False,
        "order_submission_enabled": False,
        "authenticated_endpoint_required": value.get("authenticated_endpoint_required") is True,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "signing_required_for_future_live": value.get("signing_required_for_future_live") is True,
        "signing_enabled": False,
        "wallet_required_for_future_live": value.get("wallet_required_for_future_live") is True,
        "wallet_enabled": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
        "top_refusal_reasons": list(value.get("refusal_reasons", []))[:5],
        "top_blocker_reasons": list(value.get("blocker_reasons", []))[:8],
        "validation_status": clean_text(validation.get("status") or "blocked"),
        "validation_error_count": len(validation.get("errors", [])),
        "latest_live_order_submission_boundary_path": clean_text(latest_live_order_submission_boundary_path),
        "section_ready": bool(value),
        "execution_enabling": False,
        "review_only": True,
        "boundary_is_not_live_approval": True,
        "receipt_is_not_order_submission": True,
    }
    summary.update(_boundary_safety_flags())
    summary_validation = validate_secret_boundary_live_order_submission_boundary_summary(
        summary,
        generated_at=generated_at,
    )
    summary["live_order_submission_boundary_summary_secret_boundary_validation"] = summary_validation
    if summary_validation.get("valid") is not True:
        summary["status"] = STATUS_BLOCKED_LIVE_EXECUTION_VIOLATION
        summary["dry_run_review_ready"] = False
        summary["allowed_for_dry_run_review"] = False
    return summary


def validate_live_order_submission_boundary_receipt(
    receipt: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(receipt or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != LIVE_ORDER_SUBMISSION_BOUNDARY_RECEIPT_CONTRACT:
        errors.append(f"contract_version must be {LIVE_ORDER_SUBMISSION_BOUNDARY_RECEIPT_CONTRACT}")
        statuses.append("invalid_contract")
    if clean_text(value.get("schema_version")) != "041.v1":
        errors.append("schema_version must be 041.v1")
        statuses.append("invalid_schema_version")
    if clean_text(value.get("boundary_name")) != BOUNDARY_NAME:
        errors.append(f"boundary_name must be {BOUNDARY_NAME}")
        statuses.append("invalid_boundary_name")
    if not clean_text(value.get("receipt_id")):
        errors.append("receipt_id must be present")
        statuses.append("missing_receipt_id")
    status = clean_text(value.get("status"))
    if status not in {STATUS_DRY_RUN_REVIEW_READY, STATUS_BLOCKED, STATUS_BLOCKED_LIVE_EXECUTION_VIOLATION}:
        errors.append("status must be a supported boundary status")
        statuses.append("invalid_status")
    if status == STATUS_DRY_RUN_REVIEW_READY and value.get("allowed_for_dry_run_review") is not True:
        errors.append("dry-run review ready status requires allowed_for_dry_run_review true")
        statuses.append("dry_run_review_not_allowed")
    if status != STATUS_DRY_RUN_REVIEW_READY and value.get("allowed_for_dry_run_review") is not False:
        errors.append("blocked boundary status requires allowed_for_dry_run_review false")
        statuses.append("blocked_status_review_allowed")
    if value.get("boundary_is_not_live_approval") is not True:
        errors.append("boundary_is_not_live_approval must be true")
        statuses.append("live_approval_claim_detected")
    if value.get("receipt_is_not_order_submission") is not True:
        errors.append("receipt_is_not_order_submission must be true")
        statuses.append("order_submission_claim_detected")

    for path, key, nested in _walk_flags(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for field in (
        "authenticated_endpoint_required",
        "signing_required_for_future_live",
        "wallet_required_for_future_live",
    ):
        if not isinstance(value.get(field), bool):
            errors.append(f"{field} must be boolean")
            statuses.append("invalid_future_requirement_flag")

    secret_validation = validate_secret_boundary_live_order_submission_boundary_receipt(
        value,
        generated_at=generated_at,
    )
    forbidden_paths = list(secret_validation.get("forbidden_secret_field_paths", []))
    if secret_validation.get("valid") is not True:
        errors.append("live order submission boundary receipt violates static secret boundary")
        statuses.append("secret_boundary_blocked")
    if value.get("fill_claimed") is not False or value.get("execution_claimed") is not False:
        errors.append("receipt must not claim fills or execution")
        statuses.append("execution_claim_detected")

    valid = not errors
    if valid:
        statuses = ["live_order_submission_boundary_receipt_valid"]
    else:
        statuses = _dedupe(statuses)
    return {
        "contract_version": LIVE_ORDER_SUBMISSION_BOUNDARY_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "live-order-submission-boundary-validation-041",
            {
                "receipt_id": value.get("receipt_id"),
                "status": value.get("status"),
                "errors": errors,
                "forbidden_paths": forbidden_paths,
            },
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": statuses,
        "errors": errors,
        "forbidden_secret_field_paths": forbidden_paths,
        "secret_boundary_validation": secret_validation,
        "would_submit_order": False,
        "order_submission_enabled": False,
        "authenticated_endpoint_enabled": False,
        "signing_enabled": False,
        "wallet_enabled": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
    }


def _dry_run_intent_summary(
    *,
    btc_analysis_summary: Mapping[str, Any] | None,
    btc_result: Mapping[str, Any],
    analysis: Mapping[str, Any],
    intent_plan: Mapping[str, Any],
    intent: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(btc_analysis_summary or btc_result.get("summary", {}) or {})
    market_id = clean_text(provided.get("intent_market_id") or intent.get("market_id") or analysis.get("market_id"))
    market_slug = clean_text(
        provided.get("intent_market_slug") or intent.get("market_slug") or analysis.get("market_slug")
    )
    side = clean_text(intent.get("side_label") or provided.get("side") or "track_primary_outcome")
    outcome = clean_text(intent.get("outcome") or intent.get("outcome_label") or side)
    asset = clean_text(intent.get("market_tag") or provided.get("asset") or ("BTC" if intent else ""))
    if "is_btc_related" in analysis:
        is_btc_related = analysis.get("is_btc_related") is True
    else:
        is_btc_related = (
            clean_text(asset).upper() in {"BTC", "BITCOIN"}
            or "btc" in f"{market_id} {market_slug}".lower()
            or "bitcoin" in f"{market_id} {market_slug}".lower()
        )
    return {
        "contract_version": "pmbot_live_order_submission_boundary_intent_summary.v1",
        "generated_at": generated_at,
        "intent_present": bool(intent),
        "intent_id": clean_text(intent.get("intent_id")),
        "analysis_id": clean_text(analysis.get("analysis_id") or provided.get("analysis_id")),
        "intent_plan_id": clean_text(intent_plan.get("intent_plan_id") or provided.get("intent_plan_id")),
        "btc_market_analysis_status": clean_text(
            provided.get("btc_market_analysis_status")
            or analysis.get("analysis_status")
            or "not_evaluated"
        ),
        "btc_intent_candidate_status": clean_text(
            provided.get("btc_intent_candidate_status")
            or intent_plan.get("intent_candidate_status")
            or "not_evaluated"
        ),
        "dry_run_order_intent_status": clean_text(
            provided.get("dry_run_order_intent_status")
            or intent_plan.get("dry_run_order_intent_status")
            or "not_evaluated"
        ),
        "market_id": market_id,
        "market_slug": market_slug,
        "market_status": clean_text(analysis.get("market_status") or provided.get("market_status") or "unknown"),
        "is_btc_related": is_btc_related,
        "stale": analysis.get("stale") is True,
        "asset": asset,
        "side": side,
        "outcome": outcome,
        "notional_usd": intent.get("notional_usd", provided.get("intent_notional_usd")),
        "limit_price": intent.get("limit_price", provided.get("intent_limit_price")),
        "quantity": intent.get("quantity"),
        "dry_run_only": intent.get("dry_run_only") is True if intent else True,
        "analysis_is_not_live_recommendation": True,
        "order_intent_is_not_order_submission": True,
        "executable_submission_payload_present": False,
        "execution_enabling": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
    }


def _risk_summary(
    *,
    risk_decision_summary: Mapping[str, Any] | None,
    risk_decision: Mapping[str, Any],
    risk_control_plane_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    provided = dict(risk_decision_summary or {})
    control = dict(risk_control_plane_summary or {})
    summarized = summarize_risk_limit_decision(risk_decision) if risk_decision else {}
    status = clean_text(
        provided.get("risk_decision_status")
        or provided.get("latest_decision_status")
        or summarized.get("latest_decision_status")
        or control.get("latest_decision_status")
        or "not_evaluated"
    )
    return {
        "contract_version": "pmbot_live_order_submission_boundary_risk_summary.v1",
        "decision_id": clean_text(
            provided.get("risk_decision_id") or provided.get("decision_id") or risk_decision.get("decision_id")
        ),
        "risk_decision_status": status,
        "allowed_for_dry_run": (
            provided.get("allowed_for_dry_run") is True
            or summarized.get("allowed_for_dry_run") is True
            or control.get("allowed_for_dry_run") is True
        ),
        "allowed_for_live": False,
        "latest_violations_count": int(
            provided.get("latest_violations_count")
            or summarized.get("latest_violations_count")
            or len(mapping_rows(risk_decision.get("violations")))
            or 0
        ),
        "latest_halt_reasons_count": int(
            provided.get("latest_halt_reasons_count")
            or summarized.get("latest_halt_reasons_count")
            or len(mapping_rows(risk_decision.get("halt_reasons")))
            or 0
        ),
        "live_block_reasons": list(risk_decision.get("live_block_reasons", []))
        if isinstance(risk_decision.get("live_block_reasons"), list)
        else [],
        "human_summary": clean_text(risk_decision.get("human_summary") or summarized.get("human_summary")),
        "risk_control_plane_status": clean_text(control.get("risk_control_plane_status")),
        "risk_limits_enforced_for_order_intents": control.get("risk_limits_enforced_for_order_intents") is True,
        "order_submission_enabled": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
    }


def _auth_summary(
    *,
    live_credentials_auth_boundary: Mapping[str, Any] | None,
    live_credentials_auth_boundary_summary: Mapping[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(live_credentials_auth_boundary_summary or {})
    if live_credentials_auth_boundary is not None:
        provided = summarize_live_credentials_status(live_credentials_auth_boundary, generated_at=generated_at)
    if not provided:
        provided = summarize_live_credentials_status(generated_at=generated_at)
    return {
        "contract_version": "pmbot_live_order_submission_boundary_auth_summary.v1",
        "live_credentials_boundary_status": clean_text(
            provided.get("live_credentials_boundary_status")
            or provided.get("decision_status")
            or "not_evaluated"
        ),
        "live_credentials_configured": provided.get("live_credentials_configured") is True,
        "live_mode_explicitly_requested": provided.get("live_mode_explicitly_requested") is True,
        "live_auth_ready_for_future_tiny_canary_review": (
            provided.get("live_auth_ready_for_future_tiny_canary_review") is True
        ),
        "redacted_credential_status_ready": provided.get("redacted_credential_status_ready") is not False,
        "required_credentials_count": int(provided.get("required_credentials_count", 0) or 0),
        "missing_credentials_count": int(provided.get("missing_credentials_count", 0) or 0),
        "secrets_redacted": provided.get("secrets_redacted") is not False,
        "actual_secret_values_exposed": provided.get("actual_secret_values_exposed") is True,
        "safe_for_artifacts": provided.get("safe_for_artifacts") is not False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "order_submission_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_signing_enabled": False,
        "wallet_enabled": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
    }


def _operator_summary(
    *,
    operator_approval_packet: Mapping[str, Any] | None,
    operator_intent_packet: Mapping[str, Any] | None,
    operator_context: Mapping[str, Any] | None,
) -> dict[str, Any]:
    approval = dict(operator_approval_packet or {})
    intent = dict(operator_intent_packet or {})
    context = dict(operator_context or {})
    review_ready = (
        approval.get("operator_review_ready") is True
        or intent.get("operator_intent_packet_review_ready") is True
        or context.get("operator_review_ready") is True
    )
    return {
        "contract_version": "pmbot_live_order_submission_boundary_operator_context_summary.v1",
        "operator_context_present": bool(approval or intent or context),
        "operator_review_ready": review_ready,
        "operator_approval_packet_status": clean_text(
            approval.get("operator_packet_status") or context.get("operator_approval_packet_status")
        ),
        "operator_intent_packet_status": clean_text(
            intent.get("intent_packet_status") or context.get("operator_intent_packet_status")
        ),
        "operator_intent_is_not_live_approval": True,
        "operator_signed_intent_is_human_acknowledgement_only": (
            intent.get("operator_signed_intent_is_human_acknowledgement_only") is True
            or context.get("operator_signed_intent_is_human_acknowledgement_only") is True
        ),
        "human_acknowledgement_only": (
            intent.get("operator_signed_intent_is_human_acknowledgement_only") is True
            or context.get("human_acknowledgement_only") is True
        ),
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _kill_switch_summary(kill_switch_context: Mapping[str, Any] | None) -> dict[str, Any]:
    value = dict(kill_switch_context or {})
    verified_for_live = value.get("verified_for_live") is True or value.get("kill_switch_verified_for_live") is True
    blocks_live = value.get("blocks_live_execution") is not False and not verified_for_live
    return {
        "contract_version": "pmbot_live_order_submission_boundary_kill_switch_summary.v1",
        "kill_switch_context_present": bool(value),
        "kill_switch_verified_for_live": False,
        "kill_switch_blocks_live_execution": blocks_live,
        "current_kill_switch_state": clean_text(
            value.get("current_kill_switch_state")
            or value.get("status")
            or ("blocks_live" if blocks_live else "not_live_verified")
        ),
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _live_blockers_summary(blocker_matrix: Mapping[str, Any] | None) -> dict[str, Any]:
    matrix = dict(blocker_matrix or {})
    blockers = [dict(row) for row in mapping_rows(matrix.get("blockers"))]
    unresolved = [row for row in blockers if clean_text(row.get("resolution_status")) != "resolved"]
    resolved = [row for row in blockers if clean_text(row.get("resolution_status")) == "resolved"]
    top = [
        {
            "blocker_id": clean_text(row.get("blocker_id")),
            "blocker_category": clean_text(row.get("blocker_category") or row.get("blocker_name")),
            "severity": clean_text(row.get("severity") or "critical"),
            "resolution_status": clean_text(row.get("resolution_status") or "unresolved"),
        }
        for row in blockers[:8]
    ]
    return {
        "contract_version": "pmbot_live_order_submission_boundary_live_blockers_summary.v1",
        "blocker_matrix_present": bool(matrix),
        "blocker_matrix_status": clean_text(matrix.get("status") or "not_provided"),
        "blocker_count": int(matrix.get("blocker_count", len(blockers)) or 0),
        "critical_blocker_count": int(matrix.get("critical_blocker_count", len(unresolved)) or 0),
        "unresolved_blocker_count": int(matrix.get("unresolved_blocker_count", len(unresolved)) or 0),
        "resolved_blocker_count": int(matrix.get("resolved_blocker_count", len(resolved)) or 0),
        "all_blockers_unresolved": matrix.get("all_blockers_unresolved") is True
        or (bool(unresolved) and not resolved),
        "top_blockers": top,
        "live_execution_available": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
    }


def _dry_run_blockers(
    *,
    analysis_summary: Mapping[str, Any],
    risk_summary: Mapping[str, Any],
    auth_summary: Mapping[str, Any],
    intent: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if not intent:
        blockers.append("MISSING_DRY_RUN_ORDER_INTENT")
    if clean_text(analysis_summary.get("btc_market_analysis_status")) != ANALYSIS_READY_FOR_DRY_RUN_INTENT:
        blockers.append(
            "BTC_MARKET_ANALYSIS_NOT_READY:"
            + clean_text(analysis_summary.get("btc_market_analysis_status") or "not_evaluated")
        )
    if clean_text(analysis_summary.get("dry_run_order_intent_status")) != INTENT_CANDIDATE_READY:
        blockers.append(
            "BTC_DRY_RUN_ORDER_INTENT_NOT_READY:"
            + clean_text(analysis_summary.get("dry_run_order_intent_status") or "not_evaluated")
        )
    if analysis_summary.get("is_btc_related") is not True:
        blockers.append("NON_BTC_MARKET")
    if clean_text(analysis_summary.get("market_status")) not in {"open", "not_evaluated", ""}:
        blockers.append("MARKET_NOT_OPEN_OR_UNRESOLVED:" + clean_text(analysis_summary.get("market_status")))
    if analysis_summary.get("stale") is True:
        blockers.append("STALE_MARKET_DATA")
    if clean_text(risk_summary.get("risk_decision_status")) != DECISION_ALLOW_DRY_RUN:
        blockers.append("RISK_DECISION_NOT_ALLOW_DRY_RUN:" + clean_text(risk_summary.get("risk_decision_status")))
    if risk_summary.get("allowed_for_dry_run") is not True:
        blockers.append("RISK_NOT_ALLOWED_FOR_DRY_RUN")
    if auth_summary.get("actual_secret_values_exposed") is True:
        blockers.append("AUTH_BOUNDARY_EXPOSED_SECRET_VALUES")
    if auth_summary.get("secrets_redacted") is not True:
        blockers.append("AUTH_BOUNDARY_NOT_REDACTED")
    if auth_summary.get("safe_for_artifacts") is not True:
        blockers.append("AUTH_BOUNDARY_NOT_SAFE_FOR_ARTIFACTS")
    return _dedupe(blockers)


def _intent_from_plan(intent_plan: Mapping[str, Any]) -> dict[str, Any]:
    order_intent = intent_plan.get("order_intent")
    return dict(order_intent) if isinstance(order_intent, Mapping) else {}


def _looks_like_btc_intent(summary: Mapping[str, Any], intent: Mapping[str, Any]) -> bool:
    text = " ".join(
        clean_text(value).lower()
        for value in (
            summary.get("asset"),
            summary.get("market_id"),
            summary.get("market_slug"),
            intent.get("market_tag"),
            intent.get("market_category"),
        )
    )
    return "btc" in text or "bitcoin" in text


def _execution_flag_violations(inputs: Mapping[str, Any]) -> list[str]:
    violations = []
    for path, key, value in _walk_flags(inputs):
        if key in FORCED_FALSE_EXECUTION_FIELDS and value is True:
            violations.append(f"LIVE_EXECUTION_FLAG_TRUE:{path}.{key}")
    return _dedupe(violations)


def _boundary_safety_flags() -> dict[str, Any]:
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
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "secrets_redacted": True,
        "actual_secret_values_exposed": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "external_api_call_performed": False,
        "authenticated_endpoint_added": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_endpoint_called": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_endpoint_used": False,
        "order_submission_enabled": False,
        "would_submit_order": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "wallet_required": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "real_wallet_used": False,
        "real_wallet_integration_added": False,
        "real_wallet_access_performed": False,
        "private_key_or_mnemonic_handling_added": False,
        "private_key_used": False,
        "signing_enabled": False,
        "signing_used": False,
        "cryptographic_signing_added": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "wallet_signing_added": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "transaction_signing_added": False,
        "transaction_signing_performed": False,
        "real_signature_created": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "live_execution_performed": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _walk_flags(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            nested_path = f"{path}.{key_text}"
            rows.append((path, key_text, nested))
            rows.extend(_walk_flags(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_flags(nested, f"{path}[{index}]"))
    return rows


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
