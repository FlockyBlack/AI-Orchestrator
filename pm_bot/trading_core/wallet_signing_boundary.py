from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import validate_static_secret_boundary

WALLET_SIGNING_BOUNDARY_CONTRACT = "pmbot_wallet_signing_boundary_report.v1"
WALLET_SIGNING_BOUNDARY_SUMMARY_CONTRACT = "pmbot_wallet_signing_boundary_summary.v1"
WALLET_SIGNING_REQUEST_REVIEW_CONTRACT = "pmbot_wallet_signing_request_review.v1"
WALLET_SIGNING_BOUNDARY_VALIDATION_CONTRACT = "pmbot_wallet_signing_boundary_validation.v1"

SCHEMA_VERSION = "049.v1"
BOUNDARY_NAME = "wallet_signing_boundary_scaffold_dry_run_only"

STATUS_SIGNING_DISABLED_REVIEW_ONLY = "SIGNING_DISABLED_REVIEW_ONLY"
STATUS_SIGNING_REQUEST_REFUSED = "SIGNING_REQUEST_REFUSED"
STATUS_BOUNDARY_INVALID_BLOCKED = "BOUNDARY_INVALID_BLOCKED"

SAFE_ENV_CONFIG_KEYS = (
    "PMBOT_WALLET_SIGNING_ENABLED",
    "PMBOT_WALLET_ADDRESS_CONFIGURED",
    "PMBOT_SIGNING_PROVIDER_CONFIGURED",
    "PMBOT_SIGNING_DRY_RUN_ONLY",
)
ENABLEMENT_REQUEST_KEYS = frozenset({"PMBOT_WALLET_SIGNING_ENABLED"})
PRESENCE_MARKER_KEYS = frozenset(
    {"PMBOT_WALLET_ADDRESS_CONFIGURED", "PMBOT_SIGNING_PROVIDER_CONFIGURED"}
)
DRY_RUN_MARKER_KEYS = frozenset({"PMBOT_SIGNING_DRY_RUN_ONLY"})
TRUE_STRINGS = frozenset({"true", "1", "yes", "configured", "present"})
FALSE_STRINGS = frozenset({"false", "0", "no", "missing", "not_configured", "absent"})
ACCEPTED_BOOLEAN_STRINGS = tuple(sorted(TRUE_STRINGS | FALSE_STRINGS))

FORCED_FALSE_EXECUTION_FIELDS = (
    "wallet_configured",
    "wallet_signing_enabled",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "transaction_signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "order_submission_enabled",
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "execution_enabling",
    "execution_enabled",
    "live_execution_allowed",
    "live_execution_enabled",
    "live_execution_performed",
    "wallet_used",
    "real_wallet_used",
    "wallet_signing_performed",
    "cryptographic_signing_performed",
    "transaction_signing_performed",
    "real_signature_created",
    "signed_payload_created",
    "signed_order_created",
    "signed_payload_present",
    "signed_order_present",
    "signature_present",
    "transaction_hash_present",
    "order_id_present",
    "real_order_submitted",
    "order_submitted",
    "would_submit_order",
    "authenticated_endpoint_called",
    "authenticated_endpoint_call_performed",
    "external_api_calls_performed",
    "external_api_call_performed",
    "network_used",
)

DEFAULT_BLOCKED_REASONS = (
    "wallet_signing_boundary_review_only",
    "wallet_not_connected_and_not_configured_for_execution",
    "wallet_signing_enabled_false",
    "signing_enabled_false",
    "transaction_signing_enabled_false",
    "signed_payload_generation_enabled_false",
    "signed_order_generation_enabled_false",
    "authenticated_polymarket_enabled_false",
    "live_connector_enabled_false",
    "order_submission_enabled_false",
    "live_execution_not_approved",
    "real_execution_unavailable",
    "future_live_blockers_remain_unresolved",
)

OPERATOR_REQUIRED_ACTIONS = (
    "Review this scaffold as a non-executable wallet/signing boundary artifact.",
    "Do not provide private keys, seed phrases, mnemonics, wallet files, browser wallet access, API secrets, or authorization tokens to this task.",
    "Keep wallet signing, transaction signing, signed payload generation, authenticated Polymarket access, and order submission disabled.",
    "Use a separate future operator-approved task before any wallet, signing, credential, or live execution integration.",
)

FUTURE_ENABLEMENT_REQUIREMENTS = (
    "separate operator-approved wallet/signing design task",
    "dual-control live execution approval model",
    "credential and secret handling policy with redaction and audit rules",
    "wallet address verification without exposing private material",
    "signing provider approval without implementing signing in this scaffold",
    "authenticated endpoint allowlist and audit policy",
    "disabled-first order adapter with rejection tests",
    "live kill-switch wired to every future live boundary",
    "all live blockers resolved in separate reviewed tasks",
)


@dataclass(frozen=True)
class WalletSigningBoundaryReport:
    boundary_id: str
    schema_version: str
    boundary_name: str
    status: str
    generated_at: str
    config_source: str
    safe_env_config_status: Mapping[str, Any]
    wallet_readiness_status: Mapping[str, Any]
    blocked_reasons: tuple[str, ...]
    operator_required_actions: tuple[str, ...]
    future_enablement_requirements: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = WALLET_SIGNING_BOUNDARY_CONTRACT
        value["safe_env_config_status"] = dict(self.safe_env_config_status)
        value["wallet_readiness_status"] = dict(self.wallet_readiness_status)
        value["blocked_reasons"] = list(self.blocked_reasons)
        value["top_blocked_reasons"] = list(self.blocked_reasons)[:5]
        value["operator_required_actions"] = list(self.operator_required_actions)
        value["future_enablement_requirements"] = list(self.future_enablement_requirements)
        value["review_only"] = True
        value["dry_run_only"] = True
        value["paper_only"] = True
        value["wallet_configured"] = False
        value["wallet_signing_enabled"] = False
        value["signing_enabled"] = False
        value["cryptographic_signing_enabled"] = False
        value["transaction_signing_enabled"] = False
        value["signed_payload_generation_enabled"] = False
        value["signed_order_generation_enabled"] = False
        value["authenticated_polymarket_enabled"] = False
        value["live_connector_enabled"] = False
        value["order_submission_enabled"] = False
        value["allowed_for_live"] = False
        value["canary_executable_now"] = False
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["resolved_blocker_count"] = 0
        value["unresolved_blocker_count"] = len(self.blocked_reasons)
        value["no_executable_action"] = True
        value["no_raw_secrets_parsed_or_emitted"] = True
        value["raw_secret_values_printed"] = False
        value["raw_secret_values_persisted"] = False
        value["safety_summary"] = trading_core_safety_summary()
        value.update(_boundary_safety_flags())
        return value


def build_wallet_signing_boundary_report(
    config: Mapping[str, Any] | None = None,
    *,
    config_source: str = "provided_mapping",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    sanitized_config = _safe_config_status(config or {})
    wallet_readiness = _wallet_readiness_status(sanitized_config)
    blocked_reasons = _blocked_reasons(sanitized_config)
    report = WalletSigningBoundaryReport(
        boundary_id=_stable_id(
            "wallet-signing-boundary-049",
            {
                "status": STATUS_SIGNING_DISABLED_REVIEW_ONLY,
                "config_source": clean_text(config_source),
                "safe_env_config_status": sanitized_config,
                "blocked_reasons": blocked_reasons,
            },
        ),
        schema_version=SCHEMA_VERSION,
        boundary_name=BOUNDARY_NAME,
        status=STATUS_SIGNING_DISABLED_REVIEW_ONLY,
        generated_at=generated_at,
        config_source=clean_text(config_source) or "provided_mapping",
        safe_env_config_status=sanitized_config,
        wallet_readiness_status=wallet_readiness,
        blocked_reasons=tuple(blocked_reasons),
        operator_required_actions=OPERATOR_REQUIRED_ACTIONS,
        future_enablement_requirements=FUTURE_ENABLEMENT_REQUIREMENTS,
    ).to_dict()
    validation = validate_wallet_signing_boundary_report(report, generated_at=generated_at)
    report["validation"] = validation
    if validation.get("valid") is not True:
        report["status"] = STATUS_BOUNDARY_INVALID_BLOCKED
        report["validation"] = validate_wallet_signing_boundary_report(report, generated_at=generated_at)
    return report


def build_wallet_signing_boundary_report_from_env(
    environ: Mapping[str, str] | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if environ is None:
        import os

        active_environ: Mapping[str, Any] = os.environ
    else:
        active_environ = environ
    return build_wallet_signing_boundary_report(
        {key: active_environ.get(key) for key in SAFE_ENV_CONFIG_KEYS if key in active_environ},
        config_source="environment_whitelisted_non_secret_keys",
        generated_at=generated_at,
    )


def summarize_wallet_signing_boundary_report(
    report: Mapping[str, Any] | None = None,
    *,
    latest_wallet_signing_boundary_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(report or build_wallet_signing_boundary_report(generated_at=generated_at))
    validation = (
        dict(value.get("validation", {}))
        if isinstance(value.get("validation"), Mapping)
        else validate_wallet_signing_boundary_report(value, generated_at=generated_at)
    )
    safe_config = dict(value.get("safe_env_config_status", {}))
    wallet_readiness = dict(value.get("wallet_readiness_status", {}))
    summary = {
        "contract_version": WALLET_SIGNING_BOUNDARY_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "wallet-signing-boundary-summary-049",
            {
                "boundary_id": value.get("boundary_id"),
                "status": value.get("status"),
                "latest_path": clean_text(latest_wallet_signing_boundary_path),
            },
        ),
        "schema_version": SCHEMA_VERSION,
        "boundary_name": clean_text(value.get("boundary_name") or BOUNDARY_NAME),
        "boundary_id": clean_text(value.get("boundary_id")),
        "status": clean_text(value.get("status") or STATUS_SIGNING_DISABLED_REVIEW_ONLY),
        "wallet_address_status": clean_text(wallet_readiness.get("wallet_address_status") or "missing"),
        "signing_provider_status": clean_text(wallet_readiness.get("signing_provider_status") or "missing"),
        "safe_env_configured_count": int(safe_config.get("configured_count", 0) or 0),
        "raw_like_config_key_count": int(safe_config.get("raw_like_config_key_count", 0) or 0),
        "top_blocked_reasons": list(value.get("blocked_reasons", []))[:5],
        "blocked_reasons": list(value.get("blocked_reasons", [])),
        "operator_required_actions": list(value.get("operator_required_actions", []))[:5],
        "future_enablement_requirements": list(value.get("future_enablement_requirements", [])),
        "validation_status": clean_text(validation.get("status") or "blocked"),
        "validation_valid": validation.get("valid") is True,
        "latest_wallet_signing_boundary_path": clean_text(latest_wallet_signing_boundary_path),
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
        "no_executable_action": True,
        "wallet_configured": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "transaction_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "resolved_blocker_count": 0,
    }
    summary.update(_boundary_safety_flags())
    return summary


def validate_signing_request_for_review(
    signing_request: Mapping[str, Any] | None = None,
    *,
    boundary_report: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    report = dict(boundary_report or build_wallet_signing_boundary_report(generated_at=generated_at))
    request_summary = _request_shape_summary(signing_request or {})
    refusal_reasons = _dedupe(
        [
            "wallet_signing_enabled_false",
            "signing_enabled_false",
            "transaction_signing_enabled_false",
            "signed_payload_generation_enabled_false",
            "signed_order_generation_enabled_false",
            "review_only_boundary_refuses_all_signing_requests",
            *list(report.get("blocked_reasons", [])),
        ]
    )
    review = {
        "contract_version": WALLET_SIGNING_REQUEST_REVIEW_CONTRACT,
        "review_id": _stable_id(
            "wallet-signing-request-review-049",
            {
                "boundary_id": report.get("boundary_id"),
                "request_summary": request_summary,
                "refusal_reasons": refusal_reasons,
            },
        ),
        "schema_version": SCHEMA_VERSION,
        "boundary_name": BOUNDARY_NAME,
        "status": STATUS_SIGNING_REQUEST_REFUSED,
        "generated_at": generated_at,
        "request_summary": request_summary,
        "signing_request_refused": True,
        "refusal_reasons": refusal_reasons,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        "signature_present": False,
        "signed_payload_present": False,
        "signed_order_present": False,
        "transaction_hash_present": False,
        "order_id_present": False,
        "no_signature_returned": True,
        "no_signed_payload_returned": True,
        "no_signed_order_returned": True,
        "no_transaction_hash_returned": True,
        "no_order_id_returned": True,
        "request_payload_echoed": False,
        "wallet_configured": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "transaction_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "resolved_blocker_count": 0,
        "no_raw_secrets_parsed_or_emitted": True,
    }
    review.update(_boundary_safety_flags())
    validation = validate_wallet_signing_boundary_report(review, generated_at=generated_at)
    review["validation"] = validation
    return review


def validate_wallet_signing_boundary_report(
    report: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(report or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") not in {
        WALLET_SIGNING_BOUNDARY_CONTRACT,
        WALLET_SIGNING_BOUNDARY_SUMMARY_CONTRACT,
        WALLET_SIGNING_REQUEST_REVIEW_CONTRACT,
    }:
        errors.append("contract_version is not a supported wallet signing boundary contract")
        statuses.append("invalid_contract")
    if clean_text(value.get("schema_version")) != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
        statuses.append("invalid_schema_version")
    if clean_text(value.get("boundary_name")) != BOUNDARY_NAME:
        errors.append(f"boundary_name must be {BOUNDARY_NAME}")
        statuses.append("invalid_boundary_name")
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
        statuses.append("review_only_missing")
    if value.get("no_executable_action") is not True and value.get("contract_version") != WALLET_SIGNING_REQUEST_REVIEW_CONTRACT:
        errors.append("no_executable_action must be true")
        statuses.append("executable_action_detected")
    for path, key, nested in _walk_flags(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_execution_flag_detected")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    for forbidden_key in ("signature", "signed_payload", "signed_order", "transaction_hash", "signed_order_id"):
        if forbidden_key in value:
            errors.append(f"{forbidden_key} must not be returned by the review-only boundary")
            statuses.append("forbidden_output_key_detected")
    secret_validation = validate_static_secret_boundary(
        value,
        artifact_type="wallet_signing_boundary",
        generated_at=generated_at,
    )
    if secret_validation.get("valid") is not True:
        errors.append("wallet signing boundary violates static secret boundary")
        statuses.append("secret_boundary_blocked")
    valid = not errors
    if valid:
        statuses = ["wallet_signing_boundary_valid"]
    else:
        statuses = _dedupe(statuses)
    return {
        "contract_version": WALLET_SIGNING_BOUNDARY_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "wallet-signing-boundary-validation-049",
            {
                "boundary_id": value.get("boundary_id") or value.get("review_id") or value.get("summary_id"),
                "errors": errors,
                "statuses": statuses,
            },
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": statuses,
        "errors": errors,
        "secret_boundary_validation": secret_validation,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "transaction_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "real_execution_available": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "resolved_blocker_count": 0,
    }


def _safe_config_status(config: Mapping[str, Any]) -> dict[str, Any]:
    source = dict(config or {})
    rows: dict[str, dict[str, Any]] = {}
    requested_enablement = []
    configured_count = 0
    invalid_count = 0
    for key in SAFE_ENV_CONFIG_KEYS:
        configured = key in source
        parsed, invalid_reason = _parse_marker(source.get(key)) if configured else (False, "")
        if configured:
            configured_count += 1
        if invalid_reason:
            invalid_count += 1
        requested_true = configured and parsed is True
        if key in ENABLEMENT_REQUEST_KEYS and requested_true:
            requested_enablement.append(key)
        rows[key] = {
            "env_var_name": key,
            "configured": configured,
            "state": "invalid" if invalid_reason else "configured" if configured else "missing",
            "missing": not configured,
            "invalid": bool(invalid_reason),
            "accepted_values": list(ACCEPTED_BOOLEAN_STRINGS),
            "requested_true": requested_true,
            "requested_but_blocked": key in ENABLEMENT_REQUEST_KEYS and requested_true,
            "redacted_marker_status": _redacted_marker_status(key, configured=configured, parsed=parsed),
            "effective_value": False,
            "raw_value_emitted": False,
            "invalid_reason": invalid_reason,
        }
    ignored_keys = [clean_text(key) for key in source.keys() if clean_text(key) not in SAFE_ENV_CONFIG_KEYS]
    raw_like_count = len([key for key in ignored_keys if _looks_like_raw_or_secret_config_name(key)])
    return {
        "contract_version": "pmbot_wallet_signing_boundary_safe_env_config_status.v1",
        "safe_env_keys": list(SAFE_ENV_CONFIG_KEYS),
        "safe_env_rows": rows,
        "configured_count": configured_count,
        "missing_count": len(SAFE_ENV_CONFIG_KEYS) - configured_count,
        "invalid_count": invalid_count,
        "requested_enablement_keys": requested_enablement,
        "requested_enablement_count": len(requested_enablement),
        "raw_like_config_key_count": raw_like_count,
        "ignored_non_allowlisted_config_key_count": len(ignored_keys),
        "raw_like_config_key_names_emitted": False,
        "raw_values_emitted": False,
        "all_effective_execution_flags_false": True,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "allowed_for_live": False,
    }


def _wallet_readiness_status(safe_config_status: Mapping[str, Any]) -> dict[str, Any]:
    rows = dict(safe_config_status.get("safe_env_rows", {}))
    address = dict(rows.get("PMBOT_WALLET_ADDRESS_CONFIGURED", {}))
    provider = dict(rows.get("PMBOT_SIGNING_PROVIDER_CONFIGURED", {}))
    dry_run = dict(rows.get("PMBOT_SIGNING_DRY_RUN_ONLY", {}))
    return {
        "contract_version": "pmbot_wallet_signing_boundary_wallet_readiness_status.v1",
        "wallet_configured": False,
        "wallet_connected": False,
        "wallet_address_status": (
            "configured:redacted_marker_only" if address.get("requested_true") is True else "missing"
        ),
        "signing_provider_status": (
            "configured:redacted_marker_only" if provider.get("requested_true") is True else "missing"
        ),
        "signing_dry_run_only_marker_status": (
            "configured:true" if dry_run.get("requested_true") is True else "missing_or_false"
        ),
        "wallet_address_value_emitted": False,
        "signing_provider_value_emitted": False,
        "raw_secret_values_emitted": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "transaction_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "allowed_for_live": False,
        "real_execution_available": False,
    }


def _blocked_reasons(safe_config_status: Mapping[str, Any]) -> list[str]:
    reasons = list(DEFAULT_BLOCKED_REASONS)
    if int(safe_config_status.get("requested_enablement_count", 0) or 0) > 0:
        reasons.append("wallet_signing_requested_but_blocked_by_task_049")
    if int(safe_config_status.get("invalid_count", 0) or 0) > 0:
        reasons.append("wallet_signing_boundary_safe_marker_config_invalid")
    if int(safe_config_status.get("raw_like_config_key_count", 0) or 0) > 0:
        reasons.append("raw_like_wallet_or_signing_config_keys_ignored_without_values")
    return _dedupe(reasons)


def _parse_marker(value: Any) -> tuple[bool, str]:
    text = clean_text(value).lower()
    if text in TRUE_STRINGS:
        return True, ""
    if text in FALSE_STRINGS:
        return False, ""
    return False, "marker value must be one of true/false/1/0/yes/no/configured/present/missing/not_configured/absent"


def _redacted_marker_status(key: str, *, configured: bool, parsed: bool) -> str:
    if not configured:
        return "missing"
    if key in PRESENCE_MARKER_KEYS and parsed:
        return "configured:redacted_marker_only"
    if key in DRY_RUN_MARKER_KEYS and parsed:
        return "configured:true"
    if key in ENABLEMENT_REQUEST_KEYS and parsed:
        return "requested:true_effective:false"
    return "configured:false_or_not_configured"


def _request_shape_summary(signing_request: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(signing_request or {})
    secret_validation = validate_static_secret_boundary(
        _shape_only_payload(value),
        artifact_type="wallet_signing_request_shape",
    )
    return {
        "contract_version": "pmbot_wallet_signing_request_shape_summary.v1",
        "request_present": bool(value),
        "top_level_field_count": len(value),
        "top_level_field_names_emitted": False,
        "request_payload_echoed": False,
        "raw_values_emitted": False,
        "shape_secret_boundary_valid": secret_validation.get("valid") is True,
        "forbidden_secret_field_count": int(secret_validation.get("forbidden_secret_field_count", 0) or 0),
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "allowed_for_live": False,
    }


def _shape_only_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "field_count": len(value),
        "contains_nested_mapping": any(isinstance(item, Mapping) for item in value.values()),
        "contains_sequence": any(isinstance(item, (list, tuple)) for item in value.values()),
        "raw_values_emitted": False,
        "field_names_emitted": False,
    }


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
        "execution_enabled": False,
        "live_approval": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_secret_values_printed": False,
        "raw_secret_values_persisted": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "external_api_call_performed": False,
        "authenticated_polymarket_enabled": False,
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
        "wallet_configured": False,
        "wallet_required": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "real_wallet_used": False,
        "real_wallet_integration_added": False,
        "real_wallet_access_performed": False,
        "private_key_or_mnemonic_handling_added": False,
        "private_key_used": False,
        "private_key_accessed": False,
        "signing_enabled": False,
        "signing_used": False,
        "cryptographic_signing_added": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "wallet_signing_added": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "transaction_signing_added": False,
        "transaction_signing_enabled": False,
        "transaction_signing_performed": False,
        "signed_payload_generation_enabled": False,
        "signed_payload_created": False,
        "signed_payload_present": False,
        "signed_order_generation_enabled": False,
        "signed_order_created": False,
        "signed_order_present": False,
        "signature_present": False,
        "transaction_hash_present": False,
        "order_id_present": False,
        "real_signature_created": False,
        "browser_automation_added": False,
        "browser_automation_used": False,
        "scheduler_or_daemon_added": False,
        "scheduler_created": False,
        "daemon_created": False,
        "autonomous_live_trading_added": False,
        "autonomous_trading_enabled": False,
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


def _looks_like_raw_or_secret_config_name(name: str) -> bool:
    normalized = clean_text(name).upper()
    return any(
        marker in normalized
        for marker in (
            "PRIVATE_KEY",
            "PRIVKEY",
            "MNEMONIC",
            "SEED",
            "SECRET",
            "API_KEY",
            "ACCESS_TOKEN",
            "BEARER",
            "AUTH",
            "TOKEN",
            "SIGNATURE",
            "SIGNED_PAYLOAD",
            "SIGNED_ORDER",
            "WALLET_FILE",
            "WALLET_PASSWORD",
        )
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
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"
