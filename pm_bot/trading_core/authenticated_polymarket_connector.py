from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_authenticated_polymarket_connector_scaffold,
)

AUTHENTICATED_POLYMARKET_CONNECTOR_CONTRACT = (
    "pmbot_authenticated_polymarket_connector_scaffold_dry_run_only.v1"
)
AUTHENTICATED_POLYMARKET_CONNECTOR_CONFIG_CONTRACT = (
    "pmbot_authenticated_polymarket_connector_config_contract.v1"
)
AUTHENTICATED_POLYMARKET_CONNECTOR_VALIDATION_CONTRACT = (
    "pmbot_authenticated_polymarket_connector_preflight_validation.v1"
)
AUTHENTICATED_POLYMARKET_CONNECTOR_DRY_RUN_REQUEST_CONTRACT = (
    "pmbot_authenticated_polymarket_connector_dry_run_request.v1"
)
AUTHENTICATED_POLYMARKET_CONNECTOR_DRY_RUN_RESPONSE_CONTRACT = (
    "pmbot_authenticated_polymarket_connector_dry_run_response.v1"
)
AUTHENTICATED_POLYMARKET_CONNECTOR_SUMMARY_CONTRACT = (
    "pmbot_authenticated_polymarket_connector_scaffold_summary.v1"
)

SCHEMA_VERSION = "048.v1"
CONNECTOR_NAME = "authenticated_polymarket_connector_scaffold_dry_run_only"
STATUS_REVIEW_ONLY = "REVIEW_ONLY"
STATUS_CONFIG_REQUESTED_BUT_BLOCKED = "CONFIG_REQUESTED_BUT_BLOCKED"
STATUS_DRY_RUN_REFUSED = "DRY_RUN_REFUSED"

AUTHENTICATED_ENABLEMENT_ENV_VAR = "PMBOT_AUTHENTICATED_POLYMARKET_ENABLED"
CREDENTIAL_STATUS_ENV_VARS = (
    "PMBOT_POLYMARKET_API_KEY_CONFIGURED",
    "PMBOT_POLYMARKET_API_SECRET_CONFIGURED",
    "PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED",
)
RAW_CREDENTIAL_ENV_VARS = (
    "PMBOT_POLYMARKET_API_KEY",
    "PMBOT_POLYMARKET_API_SECRET",
    "PMBOT_POLYMARKET_FUNDER_ADDRESS",
)
KNOWN_ENV_VARS = (
    AUTHENTICATED_ENABLEMENT_ENV_VAR,
    *CREDENTIAL_STATUS_ENV_VARS,
    *RAW_CREDENTIAL_ENV_VARS,
)

TRUE_STRINGS = frozenset({"true", "1", "yes", "y"})
FALSE_STRINGS = frozenset({"false", "0", "no", "n", ""})

FORCED_FALSE_EXECUTION_FIELDS = (
    "authenticated_polymarket_enabled",
    "network_calls_enabled",
    "authenticated_calls_enabled",
    "live_connector_enabled",
    "order_submission_enabled",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "wallet_signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "real_execution_available",
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_allowed",
    "live_execution_enabled",
    "execution_enabling",
    "execution_enabled",
    "would_call_authenticated_endpoint",
    "would_submit_order",
    "real_order_submitted",
)

DEFAULT_BLOCKED_REASONS = (
    "task_048_is_scaffold_and_dry_run_contract_only",
    "authenticated_polymarket_enabled_forced_false",
    "network_calls_for_authenticated_connector_forced_false",
    "authenticated_calls_forced_false",
    "order_submission_forced_false",
    "cryptographic_signing_forced_false",
    "wallet_signing_forced_false",
    "real_execution_unavailable",
    "live_connector_blockers_remain_unresolved",
)

OPERATOR_REQUIRED_ACTIONS = (
    "Review this connector scaffold as a dry-run contract only.",
    "Do not provide raw credentials to this task or its artifacts.",
    "Do not call authenticated Polymarket endpoints from this task.",
    "Do not connect wallets, sign payloads, or submit orders from this task.",
    "Use a separate future operator-approved task for any live connector implementation.",
)

FUTURE_ENABLEMENT_REQUIREMENTS = (
    "separate operator-approved live connector task",
    "reviewed redacted credential loading policy",
    "authenticated request adapter with tests that mock all network calls",
    "explicit wallet custody and signing design before any signing implementation",
    "explicit order submission boundary and kill-switch verification",
    "operator approval model for tiny live canary execution",
)


@dataclass(frozen=True)
class AuthenticatedPolymarketCredentialStatus:
    credential_id: str
    env_var_name: str
    configured: bool
    status: str
    redacted_preview: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = "pmbot_authenticated_polymarket_credential_status.v1"
        value["raw_value_emitted"] = False
        value["value_redacted"] = True
        return value


@dataclass(frozen=True)
class AuthenticatedPolymarketConnectorConfig:
    config_id: str
    schema_version: str
    connector_name: str
    config_source: str
    generated_at: str
    enablement_env_var_name: str
    requested_authenticated_enablement: bool
    credential_statuses_redacted: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = AUTHENTICATED_POLYMARKET_CONNECTOR_CONFIG_CONTRACT
        value["credential_statuses_redacted"] = [
            dict(row) for row in self.credential_statuses_redacted
        ]
        value["review_only"] = True
        value["dry_run_only"] = True
        value["no_raw_values_emitted"] = True
        value["credentials_redacted_or_missing_only"] = True
        value["operator_request_cannot_enable_connector_in_task_048"] = True
        value.update(_connector_safety_flags())
        return value


@dataclass(frozen=True)
class AuthenticatedPolymarketConnectorDryRunRequest:
    request_id: str
    request_kind: str
    endpoint_label: str
    market_id: str
    notes: str
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = AUTHENTICATED_POLYMARKET_CONNECTOR_DRY_RUN_REQUEST_CONTRACT
        value["review_only"] = True
        value["dry_run_only"] = True
        value["no_payload_body"] = True
        value["no_order_payload"] = True
        value.update(_connector_safety_flags())
        return value


@dataclass(frozen=True)
class AuthenticatedPolymarketConnectorDryRunResponse:
    response_id: str
    request_id: str
    status: str
    refusal_reasons: tuple[str, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = AUTHENTICATED_POLYMARKET_CONNECTOR_DRY_RUN_RESPONSE_CONTRACT
        value["refusal_reasons"] = list(self.refusal_reasons)
        value["review_only"] = True
        value["dry_run_only"] = True
        value["would_call_authenticated_endpoint"] = False
        value["would_submit_order"] = False
        value["order_id"] = None
        value["fill_id"] = None
        value["execution_id"] = None
        value["generated_fake_order_id"] = False
        value["generated_fake_fill"] = False
        value["generated_fake_execution"] = False
        value["no_network_call_performed"] = True
        value["no_signed_payload_created"] = True
        value["no_order_payload_created"] = True
        value.update(_connector_safety_flags())
        return value


def build_authenticated_connector_config_from_env(
    environ: Mapping[str, str] | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if environ is None:
        import os

        active_environ: Mapping[str, Any] = os.environ
    else:
        active_environ = environ
    source = {
        env_var: active_environ.get(env_var)
        for env_var in KNOWN_ENV_VARS
        if env_var in active_environ
    }
    return build_authenticated_connector_config(
        source,
        config_source="environment_presence_redacted",
        generated_at=generated_at,
    )


def build_authenticated_connector_config(
    config: Mapping[str, Any] | None = None,
    *,
    config_source: str = "provided_mapping",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    source = {clean_text(key): value for key, value in dict(config or {}).items()}
    requested_authenticated = _parse_bool(source.get(AUTHENTICATED_ENABLEMENT_ENV_VAR))
    credential_statuses = tuple(_credential_status_rows(source))
    config_id = _stable_id(
        "authenticated-polymarket-connector-config-048",
        {
            "config_source": clean_text(config_source),
            "requested_authenticated_enablement": requested_authenticated,
            "credential_statuses_redacted": credential_statuses,
        },
    )
    return AuthenticatedPolymarketConnectorConfig(
        config_id=config_id,
        schema_version=SCHEMA_VERSION,
        connector_name=CONNECTOR_NAME,
        config_source=clean_text(config_source) or "provided_mapping",
        generated_at=generated_at,
        enablement_env_var_name=AUTHENTICATED_ENABLEMENT_ENV_VAR,
        requested_authenticated_enablement=requested_authenticated,
        credential_statuses_redacted=credential_statuses,
    ).to_dict()


def build_authenticated_connector_capability_report(
    config: Mapping[str, Any] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if config is None and environ is not None:
        config_value = build_authenticated_connector_config_from_env(environ, generated_at=generated_at)
    else:
        config_value = (
            dict(config)
            if config and config.get("contract_version") == AUTHENTICATED_POLYMARKET_CONNECTOR_CONFIG_CONTRACT
            else build_authenticated_connector_config(config, generated_at=generated_at)
        )
    requested_authenticated = config_value.get("requested_authenticated_enablement") is True
    credentials_summary = _credentials_summary(config_value.get("credential_statuses_redacted", []))
    blocked_reasons = list(DEFAULT_BLOCKED_REASONS)
    if requested_authenticated:
        blocked_reasons.insert(1, "PMBOT_AUTHENTICATED_POLYMARKET_ENABLED_requested_but_blocked_by_task_048")
    status = STATUS_CONFIG_REQUESTED_BUT_BLOCKED if requested_authenticated else STATUS_REVIEW_ONLY
    report = {
        "contract_version": AUTHENTICATED_POLYMARKET_CONNECTOR_CONTRACT,
        "schema_version": SCHEMA_VERSION,
        "connector_name": CONNECTOR_NAME,
        "capability_report_id": _stable_id(
            "authenticated-polymarket-connector-capability-048",
            {
                "config_id": config_value.get("config_id"),
                "requested_authenticated_enablement": requested_authenticated,
                "credentials_summary": credentials_summary,
                "status": status,
            },
        ),
        "status": status,
        "generated_at": generated_at,
        "config": config_value,
        "review_only": True,
        "dry_run_only": True,
        "credentials_summary": credentials_summary,
        "blocked_reasons": _dedupe(blocked_reasons),
        "operator_required_actions": list(OPERATOR_REQUIRED_ACTIONS),
        "future_enablement_requirements": list(FUTURE_ENABLEMENT_REQUIREMENTS),
        "live_blockers_unresolved": True,
        "resolved_blocker_count": 0,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "authenticated_polymarket_enabled": False,
        "network_calls_enabled": False,
        "authenticated_calls_enabled": False,
        "order_submission_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "allowed_for_live": False,
        "execution_enabling": False,
        "live_approval": False,
        "no_executable_action": True,
        "would_call_authenticated_endpoint": False,
        "would_submit_order": False,
        "real_execution_allowed": False,
        "real_execution_available_reason": "task_048_scaffold_dry_run_only",
        "safety_summary": trading_core_safety_summary(),
    }
    report.update(_connector_safety_flags())
    validation = validate_authenticated_connector_preflight(report, generated_at=generated_at)
    report["validation"] = validation
    return report


def validate_authenticated_connector_preflight(
    report: Mapping[str, Any] | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(report or build_authenticated_connector_capability_report(generated_at=generated_at))
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != AUTHENTICATED_POLYMARKET_CONNECTOR_CONTRACT:
        errors.append(f"contract_version must be {AUTHENTICATED_POLYMARKET_CONNECTOR_CONTRACT}")
        statuses.append("invalid_contract")
    if clean_text(value.get("schema_version")) != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
        statuses.append("invalid_schema_version")
    if clean_text(value.get("connector_name")) != CONNECTOR_NAME:
        errors.append(f"connector_name must be {CONNECTOR_NAME}")
        statuses.append("invalid_connector_name")
    if clean_text(value.get("status")) not in {
        STATUS_REVIEW_ONLY,
        STATUS_CONFIG_REQUESTED_BUT_BLOCKED,
    }:
        errors.append("status must remain review-only or config-requested-but-blocked")
        statuses.append("unsupported_status")
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
        statuses.append("review_only_missing")
    if value.get("dry_run_only") is not True:
        errors.append("dry_run_only must be true")
        statuses.append("dry_run_only_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("execution_flag_detected")
    for path, key, nested in _walk_flags(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_execution_flag_detected")
    credentials_summary = dict(value.get("credentials_summary", {}))
    if credentials_summary.get("credentials_redacted_or_missing_only") is not True:
        errors.append("credentials_summary.credentials_redacted_or_missing_only must be true")
        statuses.append("credential_redaction_missing")
    if credentials_summary.get("raw_values_emitted") is not False:
        errors.append("credentials_summary.raw_values_emitted must be false")
        statuses.append("raw_credential_value_emitted")
    if credentials_summary.get("actual_secret_values_exposed") is not False:
        errors.append("credentials_summary.actual_secret_values_exposed must be false")
        statuses.append("actual_secret_value_exposed")
    if value.get("network_calls_enabled") is not False or value.get("external_api_calls_performed") is not False:
        errors.append("network and external API calls must remain disabled")
        statuses.append("network_call_detected")
    secret_validation = validate_secret_boundary_authenticated_polymarket_connector_scaffold(
        value,
        generated_at=generated_at,
    )
    if secret_validation.get("valid") is not True:
        errors.append("authenticated Polymarket connector scaffold violates static secret boundary")
        statuses.append("secret_boundary_blocked")
    valid = not errors
    return {
        "contract_version": AUTHENTICATED_POLYMARKET_CONNECTOR_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "authenticated-polymarket-connector-validation-048",
            {
                "capability_report_id": value.get("capability_report_id"),
                "status": value.get("status"),
                "errors": errors,
            },
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": ["authenticated_polymarket_connector_scaffold_valid"]
        if valid
        else _dedupe(statuses),
        "errors": errors,
        "secret_boundary_validation": secret_validation,
        "resolved_blocker_count": 0,
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
        **_connector_safety_flags(),
    }


def build_authenticated_connector_dry_run_request(
    *,
    request_kind: str = "future_authenticated_endpoint_shape_review",
    endpoint_label: str = "polymarket_authenticated_endpoint_shape_only",
    market_id: str = "",
    notes: str = "Review-only request shape. No network call, signing, or order payload is available.",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    request_id = _stable_id(
        "authenticated-polymarket-connector-dry-run-request-048",
        {
            "request_kind": clean_text(request_kind),
            "endpoint_label": clean_text(endpoint_label),
            "market_id": clean_text(market_id),
            "notes": clean_text(notes),
        },
    )
    return AuthenticatedPolymarketConnectorDryRunRequest(
        request_id=request_id,
        request_kind=clean_text(request_kind),
        endpoint_label=clean_text(endpoint_label),
        market_id=clean_text(market_id),
        notes=clean_text(notes),
        generated_at=generated_at,
    ).to_dict()


def simulate_authenticated_connector_request(
    request: Mapping[str, Any] | None = None,
    *,
    config: Mapping[str, Any] | None = None,
    capability_report: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    request_value = dict(request or build_authenticated_connector_dry_run_request(generated_at=generated_at))
    report = dict(
        capability_report
        or build_authenticated_connector_capability_report(config, generated_at=generated_at)
    )
    refusal_reasons = _dedupe(
        [
            "dry_run_refused_no_authenticated_network_call",
            "task_048_does_not_submit_orders",
            "task_048_does_not_sign_payloads",
            *list(report.get("blocked_reasons", [])),
        ]
    )
    response = AuthenticatedPolymarketConnectorDryRunResponse(
        response_id=_stable_id(
            "authenticated-polymarket-connector-dry-run-response-048",
            {
                "request_id": request_value.get("request_id"),
                "capability_report_id": report.get("capability_report_id"),
                "status": STATUS_DRY_RUN_REFUSED,
                "refusal_reasons": refusal_reasons,
            },
        ),
        request_id=clean_text(request_value.get("request_id")),
        status=STATUS_DRY_RUN_REFUSED,
        refusal_reasons=tuple(refusal_reasons),
        generated_at=generated_at,
    ).to_dict()
    response["request"] = request_value
    response["capability_report_summary"] = summarize_authenticated_connector_capability_report(
        report,
        generated_at=generated_at,
    )
    response["validation"] = validate_authenticated_connector_preflight(report, generated_at=generated_at)
    return response


def summarize_authenticated_connector_capability_report(
    report: Mapping[str, Any] | None = None,
    *,
    latest_authenticated_polymarket_connector_scaffold_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if report and report.get("contract_version") == AUTHENTICATED_POLYMARKET_CONNECTOR_SUMMARY_CONTRACT:
        summary_value = dict(report)
        if latest_authenticated_polymarket_connector_scaffold_path:
            summary_value["latest_authenticated_polymarket_connector_scaffold_path"] = clean_text(
                latest_authenticated_polymarket_connector_scaffold_path
            )
        summary_value.update(_connector_safety_flags())
        summary_value["authenticated_polymarket_connector_scaffold_section_ready"] = True
        return summary_value
    value = dict(report or build_authenticated_connector_capability_report(generated_at=generated_at))
    validation = (
        dict(value.get("validation", {}))
        if isinstance(value.get("validation"), Mapping)
        else validate_authenticated_connector_preflight(value, generated_at=generated_at)
    )
    credentials = dict(value.get("credentials_summary", {}))
    summary = {
        "contract_version": AUTHENTICATED_POLYMARKET_CONNECTOR_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "authenticated-polymarket-connector-summary-048",
            {
                "capability_report_id": value.get("capability_report_id"),
                "status": value.get("status"),
                "latest_path": clean_text(latest_authenticated_polymarket_connector_scaffold_path),
            },
        ),
        "schema_version": SCHEMA_VERSION,
        "connector_name": CONNECTOR_NAME,
        "status": clean_text(value.get("status") or STATUS_REVIEW_ONLY),
        "generated_at": generated_at,
        "capability_report_id": clean_text(value.get("capability_report_id")),
        "review_only": True,
        "dry_run_only": True,
        "network_calls_enabled": False,
        "authenticated_calls_enabled": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "real_execution_available": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "authenticated_polymarket_enabled": False,
        "execution_enabling": False,
        "live_approval": False,
        "no_executable_action": True,
        "resolved_blocker_count": 0,
        "credentials_redacted_or_missing_only": credentials.get(
            "credentials_redacted_or_missing_only"
        )
        is True,
        "configured_redacted_credential_count": int(credentials.get("configured_redacted_count", 0) or 0),
        "missing_credential_count": int(credentials.get("missing_count", 0) or 0),
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "top_blocked_reasons": list(value.get("blocked_reasons", []))[:5],
        "operator_required_actions": list(value.get("operator_required_actions", []))[:5],
        "future_enablement_requirements": list(value.get("future_enablement_requirements", []))[:6],
        "validation_status": clean_text(validation.get("status") or "blocked"),
        "validation_valid": validation.get("valid") is True,
        "latest_authenticated_polymarket_connector_scaffold_path": clean_text(
            latest_authenticated_polymarket_connector_scaffold_path
            or value.get("latest_authenticated_polymarket_connector_scaffold_path")
        ),
        "authenticated_polymarket_connector_scaffold_section_ready": True,
    }
    summary.update(_connector_safety_flags())
    return summary


def _credential_status_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    credential_specs = (
        (
            "polymarket_api_key_presence",
            "PMBOT_POLYMARKET_API_KEY_CONFIGURED",
            "PMBOT_POLYMARKET_API_KEY",
        ),
        (
            "polymarket_api_secret_presence",
            "PMBOT_POLYMARKET_API_SECRET_CONFIGURED",
            "PMBOT_POLYMARKET_API_SECRET",
        ),
        (
            "polymarket_funder_address_presence",
            "PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED",
            "PMBOT_POLYMARKET_FUNDER_ADDRESS",
        ),
    )
    for credential_id, configured_env, raw_env in credential_specs:
        configured_from_flag = _parse_bool(source.get(configured_env))
        raw_presence = raw_env in source and bool(clean_text(source.get(raw_env)))
        configured = configured_from_flag or raw_presence
        status = "configured_redacted" if configured else "missing"
        source_label = "configured_flag_or_raw_presence_redacted" if configured else "not_configured"
        rows.append(
            AuthenticatedPolymarketCredentialStatus(
                credential_id=credential_id,
                env_var_name=configured_env,
                configured=configured,
                status=status,
                redacted_preview="<configured:redacted>" if configured else "<missing>",
                source=source_label,
            ).to_dict()
        )
    return rows


def _credentials_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    credential_rows = [dict(row) for row in rows if isinstance(row, Mapping)]
    configured_count = len([row for row in credential_rows if row.get("configured") is True])
    missing_count = len([row for row in credential_rows if row.get("configured") is not True])
    return {
        "contract_version": "pmbot_authenticated_polymarket_credentials_summary.v1",
        "credential_statuses_redacted": credential_rows,
        "credential_count": len(credential_rows),
        "configured_redacted_count": configured_count,
        "missing_count": missing_count,
        "statuses": [clean_text(row.get("status")) for row in credential_rows],
        "credentials_redacted_or_missing_only": True,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "raw_credential_values_persisted": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
    }


def _parse_bool(value: Any) -> bool:
    text = clean_text(value).lower()
    if text in TRUE_STRINGS:
        return True
    if text in FALSE_STRINGS:
        return False
    return False


def _connector_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "paper_only": True,
        "review_only": True,
        "dry_run_only": True,
        "network_used": False,
        "network_calls_enabled": False,
        "external_api_calls_performed": False,
        "authenticated_calls_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "would_submit_order": False,
        "real_order_submitted": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "signed_payload_generation_enabled": False,
        "signed_payload_created": False,
        "signed_payload_present": False,
        "signed_order_generation_enabled": False,
        "signed_order_created": False,
        "signed_order_present": False,
        "wallet_enabled": False,
        "real_wallet_integration_added": False,
        "real_wallet_access_performed": False,
        "private_key_or_mnemonic_handling_added": False,
        "transaction_signing_added": False,
        "transaction_signing_performed": False,
        "real_execution_available": False,
        "real_execution_allowed": False,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "live_execution_approved": False,
        "live_execution_performed": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "execution_enabling": False,
        "execution_enabled": False,
        "live_approval": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "actual_secret_values_exposed": False,
        "raw_values_emitted": False,
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
