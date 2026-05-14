from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-057-AUTHENTICATED-NO-ORDER-CLOB-API-PREFLIGHT-REDACTED-BOUNDARY"
TASK_ID_059 = "ORCH-PMBOT-TRADING-MVP-059-OPTIONAL-NO-ORDER-AUTHENTICATED-GET-PREFLIGHT"

AUTHENTICATED_CLOB_PREFLIGHT_CONFIG_CONTRACT = "pmbot_authenticated_clob_preflight_config_057.v1"
REDACTED_L2_CREDENTIAL_PRESENCE_CONTRACT = "pmbot_redacted_l2_credential_presence_057.v1"
CLOB_BASE_URL_VALIDATION_CONTRACT = "pmbot_clob_base_url_validation_057.v1"
AUTH_HEADER_BOUNDARY_CHECK_CONTRACT = "pmbot_auth_header_boundary_check_057.v1"
NO_ORDER_AUTHENTICATED_REQUEST_PLAN_CONTRACT = "pmbot_no_order_authenticated_request_plan_057.v1"
LIVE_AUTH_READINESS_BLOCKER_CONTRACT = "pmbot_live_auth_readiness_blocker_057.v1"
LATEST_AUTHENTICATED_CLOB_PREFLIGHT_STATUS_CONTRACT = (
    "pmbot_latest_authenticated_clob_preflight_status_057.v1"
)
AUTHENTICATED_CLOB_PREFLIGHT_RESULT_CONTRACT = "pmbot_authenticated_clob_preflight_result_057.v1"
AUTHENTICATED_CLOB_PREFLIGHT_VALIDATION_CONTRACT = (
    "pmbot_authenticated_clob_preflight_validation_057.v1"
)
NO_ORDER_AUTHENTICATED_GET_CONFIG_CONTRACT = "pmbot_no_order_authenticated_get_config_059.v1"
REAL_AUTH_READ_ONLY_OPT_IN_STATUS_CONTRACT = "pmbot_real_auth_read_only_opt_in_status_059.v1"
SAFE_NO_ORDER_ENDPOINT_VALIDATION_CONTRACT = "pmbot_safe_no_order_endpoint_validation_059.v1"
NO_ORDER_AUTHENTICATED_GET_RESULT_CONTRACT = "pmbot_no_order_authenticated_get_result_059.v1"
LATEST_NO_ORDER_AUTHENTICATED_GET_STATUS_CONTRACT = (
    "pmbot_latest_no_order_authenticated_get_status_059.v1"
)
NO_ORDER_AUTHENTICATED_GET_VALIDATION_CONTRACT = (
    "pmbot_no_order_authenticated_get_validation_059.v1"
)

EXECUTION_MODE = "preflight"
MODE = "preflight / review-only"

STATUS_PRESENT_REDACTED = "present_redacted"
STATUS_MISSING = "missing"
STATUS_BLOCKED = "blocked"
STATUS_CHECKED = "checked"
STATUS_MOCKED = "mocked"
STATUS_SKIPPED = "skipped"
STATUS_VALID = "valid_public_url_shape"
STATUS_REAL_GET_CHECKED = "real_get_checked"

NO_ORDER_ALLOWED_METHODS = ("GET",)
NO_ORDER_BLOCKED_METHODS = ("POST", "PUT", "PATCH", "DELETE")
L2_AUTH_HEADER_ROLES = (
    "l2_api_key_header_required_redacted",
    "l2_passphrase_header_required_redacted",
    "timestamp_header_required_redacted",
    "hmac_sha256_signature_header_required_not_generated",
)

FORCED_FALSE_EXECUTION_FIELDS = (
    "authenticated_request_performed",
    "credentials_values_exposed",
    "private_key_read",
    "l1_auth_attempted",
    "api_key_derivation_attempted",
    "wallet_connection_attempted",
    "signing_attempted",
    "signed_payload_generated",
    "order_submission_attempted",
    "order_cancellation_attempted",
    "balance_read_attempted",
    "position_read_attempted",
    "live_execution_approved",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "order_submission_performed",
    "wallet_signing_enabled",
    "wallet_signing_performed",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "hmac_signature_generated",
    "auth_signature_generated",
    "order_payload_generated",
    "signed_order_payload_generated",
    "real_order_submitted",
    "order_submitted",
    "order_cancellation_enabled",
    "real_order_cancelled",
    "balance_read_enabled",
    "position_read_enabled",
    "wallet_enabled",
    "wallet_spend_enabled",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "raw_credential_values_persisted",
    "secrets_printed",
    "secrets_persisted",
    "raw_secret_values_printed",
    "raw_secret_values_persisted",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)


def no_order_authenticated_get_safety_flags(
    *,
    no_order_auth_get_requested: bool,
    real_auth_read_only_requested: bool,
    real_auth_read_only_opt_in_present: bool,
    real_authenticated_get_performed: bool,
    endpoint_safe_for_no_order_check: bool,
    auth_used: bool,
    auth_presence_check_performed: bool = True,
    auth_header_boundary_checked: bool = False,
    no_order_auth_check_performed: bool = False,
) -> dict[str, Any]:
    value = authenticated_clob_preflight_safety_flags(
        auth_presence_check_performed=auth_presence_check_performed,
        auth_header_boundary_checked=auth_header_boundary_checked,
        no_order_auth_check_performed=no_order_auth_check_performed,
    )
    value.update(
        {
            "no_order_auth_get_requested": no_order_auth_get_requested is True,
            "real_auth_read_only_requested": real_auth_read_only_requested is True,
            "real_auth_read_only_opt_in_present": real_auth_read_only_opt_in_present is True,
            "real_authenticated_get_performed": real_authenticated_get_performed is True,
            "request_method": "GET",
            "endpoint_safe_for_no_order_check": endpoint_safe_for_no_order_check is True,
            "auth_used": auth_used is True,
            "credentials_used": "redacted_presence_only",
            "credentials_values_exposed": False,
            "private_key_read": False,
            "signing_attempted": False,
            "signed_payload_generated": False,
            "order_submission_attempted": False,
            "order_cancellation_attempted": False,
            "balance_read_attempted": False,
            "position_read_attempted": False,
            "wallet_connection_attempted": False,
            "live_execution_approved": False,
            "allowed_for_live": False,
            "resolved_blocker_count": 0,
        }
    )
    return value


@dataclass(frozen=True)
class NoOrderAuthenticatedGetConfig:
    market: str
    dry_run: bool
    no_order_auth_get_requested: bool
    real_auth_read_only_requested: bool
    real_auth_read_only_opt_in_present: bool
    request_method: str
    endpoint_path_sanitized: str
    artifact_dir: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = NO_ORDER_AUTHENTICATED_GET_CONFIG_CONTRACT
        value["task_id"] = TASK_ID_059
        value["market"] = clean_text(self.market).upper() or "BTC"
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["dry_run"] = self.dry_run is True
        value["request_method"] = "GET"
        value["endpoint_path_sanitized"] = clean_text(self.endpoint_path_sanitized) or "/auth/no-order-boundary/mock-get"
        value["endpoint_path_contains_query_or_fragment"] = False
        value["operator_approval_can_enable_live"] = False
        value.update(
            no_order_authenticated_get_safety_flags(
                no_order_auth_get_requested=self.no_order_auth_get_requested,
                real_auth_read_only_requested=self.real_auth_read_only_requested,
                real_auth_read_only_opt_in_present=self.real_auth_read_only_opt_in_present,
                real_authenticated_get_performed=False,
                endpoint_safe_for_no_order_check=False,
                auth_used=False,
                auth_header_boundary_checked=False,
                no_order_auth_check_performed=self.no_order_auth_get_requested,
            )
        )
        return value


@dataclass(frozen=True)
class RealAuthReadOnlyOptInStatus:
    status: str
    real_auth_read_only_requested: bool
    real_auth_read_only_opt_in_present: bool
    env_var_name: str
    blocker_reason: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = REAL_AUTH_READ_ONLY_OPT_IN_STATUS_CONTRACT
        value["task_id"] = TASK_ID_059
        value["env_value_emitted"] = False
        value["safe_for_artifacts"] = True
        value.update(
            no_order_authenticated_get_safety_flags(
                no_order_auth_get_requested=self.real_auth_read_only_requested,
                real_auth_read_only_requested=self.real_auth_read_only_requested,
                real_auth_read_only_opt_in_present=self.real_auth_read_only_opt_in_present,
                real_authenticated_get_performed=False,
                endpoint_safe_for_no_order_check=False,
                auth_used=False,
                auth_header_boundary_checked=False,
                no_order_auth_check_performed=self.real_auth_read_only_requested,
            )
        )
        return value


@dataclass(frozen=True)
class SafeNoOrderEndpointValidation:
    status: str
    request_method: str
    endpoint_path_sanitized: str
    endpoint_safe_for_no_order_check: bool
    endpoint_blocked_reason: str
    forbidden_terms_detected: tuple[str, ...]
    allowlist_match: bool
    real_auth_read_only_requested: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SAFE_NO_ORDER_ENDPOINT_VALIDATION_CONTRACT
        value["task_id"] = TASK_ID_059
        value["request_method"] = "GET" if clean_text(self.request_method).upper() == "GET" else clean_text(self.request_method).upper()
        value["endpoint_path_sanitized"] = clean_text(self.endpoint_path_sanitized)
        value["forbidden_terms_detected"] = list(self.forbidden_terms_detected)
        value["allowlist_match"] = self.allowlist_match is True
        value["safe_for_artifacts"] = True
        value.update(
            no_order_authenticated_get_safety_flags(
                no_order_auth_get_requested=True,
                real_auth_read_only_requested=self.real_auth_read_only_requested,
                real_auth_read_only_opt_in_present=False,
                real_authenticated_get_performed=False,
                endpoint_safe_for_no_order_check=self.endpoint_safe_for_no_order_check,
                auth_used=False,
                auth_header_boundary_checked=False,
                no_order_auth_check_performed=True,
            )
        )
        return value


@dataclass(frozen=True)
class LatestNoOrderAuthenticatedGetStatus:
    market: str
    status: str
    no_order_auth_get_status: str
    no_order_auth_get_requested: bool
    real_auth_read_only_requested: bool
    real_auth_read_only_opt_in_present: bool
    real_authenticated_get_performed: bool
    request_method: str
    endpoint_path_sanitized: str
    endpoint_safe_for_no_order_check: bool
    endpoint_blocked_reason: str
    status_code: int | None
    auth_used: bool
    blocker_count: int
    blockers: tuple[Mapping[str, Any], ...]
    artifact_path: str
    latest_status_path: str
    operator_markdown_path: str
    request_plan_path: str
    endpoint_validation_path: str
    response_evidence_path: str
    blockers_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in self.blockers]
        value = asdict(self)
        value["contract_version"] = LATEST_NO_ORDER_AUTHENTICATED_GET_STATUS_CONTRACT
        value["task_id"] = TASK_ID_059
        value["market"] = clean_text(self.market).upper() or "BTC"
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["review_only"] = True
        value["preflight_only"] = True
        value["request_method"] = "GET"
        value["credentials_used"] = "redacted_presence_only"
        value["credentials_values_exposed"] = False
        value["blockers"] = blockers
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in blockers[:8]]
        value["order_submission"] = "blocked"
        value["order_cancellation"] = "blocked"
        value["signing"] = "blocked"
        value["wallet"] = "blocked"
        value["balances"] = "blocked"
        value["positions"] = "blocked"
        value["live_execution"] = "blocked"
        value.update(
            no_order_authenticated_get_safety_flags(
                no_order_auth_get_requested=self.no_order_auth_get_requested,
                real_auth_read_only_requested=self.real_auth_read_only_requested,
                real_auth_read_only_opt_in_present=self.real_auth_read_only_opt_in_present,
                real_authenticated_get_performed=self.real_authenticated_get_performed,
                endpoint_safe_for_no_order_check=self.endpoint_safe_for_no_order_check,
                auth_used=self.auth_used,
                auth_header_boundary_checked=self.no_order_auth_get_requested,
                no_order_auth_check_performed=self.no_order_auth_get_requested,
            )
        )
        return value


@dataclass(frozen=True)
class NoOrderAuthenticatedGetResult:
    market: str
    status: str
    config: Mapping[str, Any]
    real_auth_read_only_opt_in_status: Mapping[str, Any]
    safe_no_order_endpoint_validation: Mapping[str, Any]
    request_plan: Mapping[str, Any]
    response_evidence: Mapping[str, Any] | None
    latest_status: Mapping[str, Any]
    blockers: tuple[Mapping[str, Any], ...]
    artifact_paths: Mapping[str, str]
    operator_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        latest_status = dict(self.latest_status)
        response_evidence = dict(self.response_evidence or {})
        value = {
            "contract_version": NO_ORDER_AUTHENTICATED_GET_RESULT_CONTRACT,
            "task_id": TASK_ID_059,
            "market": clean_text(self.market).upper() or "BTC",
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "dry_run": True,
            "config": dict(self.config),
            "real_auth_read_only_opt_in_status": dict(self.real_auth_read_only_opt_in_status),
            "safe_no_order_endpoint_validation": dict(self.safe_no_order_endpoint_validation),
            "request_plan": dict(self.request_plan),
            "response_evidence": response_evidence,
            "latest_status": latest_status,
            "blockers": [dict(row) for row in self.blockers],
            "blocker_count": len(self.blockers),
            "resolved_blocker_count": 0,
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": clean_text(self.operator_summary),
            "generated_at": self.generated_at,
        }
        for field in (
            "no_order_auth_get_requested",
            "no_order_auth_get_status",
            "real_auth_read_only_requested",
            "real_auth_read_only_opt_in_present",
            "real_authenticated_get_performed",
            "request_method",
            "endpoint_path_sanitized",
            "endpoint_safe_for_no_order_check",
            "endpoint_blocked_reason",
            "status_code",
            "auth_used",
            "credentials_used",
            "credentials_values_exposed",
        ):
            value[field] = latest_status.get(field)
        value.update(
            no_order_authenticated_get_safety_flags(
                no_order_auth_get_requested=value.get("no_order_auth_get_requested") is True,
                real_auth_read_only_requested=value.get("real_auth_read_only_requested") is True,
                real_auth_read_only_opt_in_present=value.get("real_auth_read_only_opt_in_present") is True,
                real_authenticated_get_performed=value.get("real_authenticated_get_performed") is True,
                endpoint_safe_for_no_order_check=value.get("endpoint_safe_for_no_order_check") is True,
                auth_used=value.get("auth_used") is True,
                auth_header_boundary_checked=value.get("no_order_auth_get_requested") is True,
                no_order_auth_check_performed=value.get("no_order_auth_get_requested") is True,
            )
        )
        value["validation"] = validate_no_order_authenticated_get_result(
            value,
            generated_at=self.generated_at,
        )
        return value


@dataclass(frozen=True)
class AuthenticatedClobPreflightConfig:
    market: str
    dry_run: bool = True
    mock_auth: bool = True
    auth_presence_only: bool = False
    no_order_auth_check: bool = True
    clob_base_url_configured: bool = False
    artifact_dir: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = AUTHENTICATED_CLOB_PREFLIGHT_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = clean_text(self.market).upper() or "BTC"
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["dry_run"] = self.dry_run is True
        value["mock_auth"] = self.mock_auth is True
        value["auth_presence_only"] = self.auth_presence_only is True
        value["no_order_auth_check"] = self.no_order_auth_check is True
        value["clob_base_url_configured"] = self.clob_base_url_configured is True
        value["clob_base_url_value_emitted"] = False
        value["operator_approval_can_enable_live"] = False
        value.update(
            authenticated_clob_preflight_safety_flags(
                auth_presence_check_performed=False,
                auth_header_boundary_checked=False,
                no_order_auth_check_performed=False,
            )
        )
        return value


@dataclass(frozen=True)
class RedactedL2CredentialPresence:
    status: str
    auth_presence_check_performed: bool
    env_presence_items: tuple[Mapping[str, Any], ...]
    configured_count: int
    missing_count: int
    missing_env_vars: tuple[str, ...]
    unsafe_raw_value_detected: bool
    unsafe_raw_value_env_vars: tuple[str, ...]
    operator_safe_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = REDACTED_L2_CREDENTIAL_PRESENCE_CONTRACT
        value["task_id"] = TASK_ID
        value["env_presence_items"] = [dict(row) for row in self.env_presence_items]
        value["missing_env_vars"] = list(self.missing_env_vars)
        value["unsafe_raw_value_env_vars"] = list(self.unsafe_raw_value_env_vars)
        value["redacted_presence_only"] = True
        value["raw_values_emitted"] = False
        value["actual_secret_values_exposed"] = False
        value["raw_credential_values_persisted"] = False
        value["safe_for_artifacts"] = True
        value["private_key_envs_checked"] = False
        value["l1_private_key_material_requested"] = False
        value.update(
            authenticated_clob_preflight_safety_flags(
                auth_presence_check_performed=self.auth_presence_check_performed,
                auth_header_boundary_checked=False,
                no_order_auth_check_performed=False,
            )
        )
        return value


@dataclass(frozen=True)
class ClobBaseUrlValidation:
    status: str
    base_url_present: bool
    scheme_status: str
    host_status: str
    unsafe_sensitive_value_detected: bool
    operator_safe_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = CLOB_BASE_URL_VALIDATION_CONTRACT
        value["task_id"] = TASK_ID
        value["base_url_present"] = self.base_url_present is True
        value["unsafe_sensitive_value_detected"] = self.unsafe_sensitive_value_detected is True
        value["base_url_value_emitted"] = False
        value["base_url_host_emitted"] = False
        value["raw_values_emitted"] = False
        value["safe_for_artifacts"] = True
        value.update(
            authenticated_clob_preflight_safety_flags(
                auth_presence_check_performed=False,
                auth_header_boundary_checked=False,
                no_order_auth_check_performed=False,
            )
        )
        return value


@dataclass(frozen=True)
class AuthHeaderBoundaryCheck:
    status: str
    auth_header_boundary_checked: bool
    credential_presence_status: str
    clob_base_url_status: str
    required_header_roles: tuple[str, ...]
    blocked_methods: tuple[str, ...] = NO_ORDER_BLOCKED_METHODS
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = AUTH_HEADER_BOUNDARY_CHECK_CONTRACT
        value["task_id"] = TASK_ID
        value["required_header_roles"] = list(self.required_header_roles)
        value["allowed_methods"] = list(NO_ORDER_ALLOWED_METHODS)
        value["blocked_methods"] = list(self.blocked_methods)
        value["auth_headers_would_be_required"] = True
        value["auth_header_values_redacted"] = True
        value["header_values_emitted"] = False
        value["request_headers_materialized"] = False
        value["hmac_sha256_documented_not_computed"] = True
        value["raw_values_emitted"] = False
        value["actual_secret_values_exposed"] = False
        value["safe_for_artifacts"] = True
        value.update(
            authenticated_clob_preflight_safety_flags(
                auth_presence_check_performed=False,
                auth_header_boundary_checked=self.auth_header_boundary_checked,
                no_order_auth_check_performed=False,
            )
        )
        return value


@dataclass(frozen=True)
class NoOrderAuthenticatedRequestPlan:
    status: str
    no_order_auth_check_performed: bool
    request_method: str
    endpoint_path: str
    clob_base_url_status: str
    credential_presence_status: str
    authenticated_request_performed: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = NO_ORDER_AUTHENTICATED_REQUEST_PLAN_CONTRACT
        value["task_id"] = TASK_ID
        value["request_method"] = "GET"
        value["endpoint_path"] = clean_text(self.endpoint_path) or "/auth/no-order-boundary/mock"
        value["allowed_methods"] = list(NO_ORDER_ALLOWED_METHODS)
        value["blocked_methods"] = list(NO_ORDER_BLOCKED_METHODS)
        value["mock_auth_plan_only"] = True
        value["network_request_performed"] = False
        value["authenticated_request_performed"] = False
        value["order_endpoint_performed"] = False
        value["cancel_endpoint_performed"] = False
        value["balance_endpoint_performed"] = False
        value["position_endpoint_performed"] = False
        value["order_payload_included"] = False
        value["signed_payload_included"] = False
        value["safe_for_artifacts"] = True
        value.update(
            authenticated_clob_preflight_safety_flags(
                auth_presence_check_performed=False,
                auth_header_boundary_checked=False,
                no_order_auth_check_performed=self.no_order_auth_check_performed,
            )
        )
        return value


@dataclass(frozen=True)
class LiveAuthReadinessBlocker:
    blocker_id: str
    blocker_category: str
    severity: str
    reason: str
    resolution_status: str = "unresolved"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_AUTH_READINESS_BLOCKER_CONTRACT
        value["blocks_live_execution"] = True
        value["resolved"] = False
        value.update(
            authenticated_clob_preflight_safety_flags(
                auth_presence_check_performed=False,
                auth_header_boundary_checked=False,
                no_order_auth_check_performed=False,
            )
        )
        return value


@dataclass(frozen=True)
class LatestAuthenticatedClobPreflightStatus:
    market: str
    status: str
    auth_presence_status: str
    clob_base_url_status: str
    auth_header_boundary_status: str
    no_order_auth_check_status: str
    blocker_count: int
    blockers: tuple[Mapping[str, Any], ...]
    artifact_path: str
    latest_status_path: str
    operator_markdown_path: str
    credential_presence_path: str
    clob_base_url_validation_path: str
    auth_header_boundary_check_path: str
    no_order_authenticated_request_plan_path: str
    blockers_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in self.blockers]
        value = asdict(self)
        value["contract_version"] = LATEST_AUTHENTICATED_CLOB_PREFLIGHT_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = clean_text(self.market).upper() or "BTC"
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["review_only"] = True
        value["preflight_only"] = True
        value["blockers"] = blockers
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in blockers[:8]]
        value["auth_presence"] = clean_text(self.auth_presence_status)
        value["clob_base_url"] = clean_text(self.clob_base_url_status)
        value["auth_header_boundary"] = clean_text(self.auth_header_boundary_status)
        value["authenticated_request"] = "skipped"
        value["order_submission"] = "blocked"
        value["order_cancellation"] = "blocked"
        value["signing"] = "blocked"
        value["wallet"] = "blocked"
        value["balances"] = "blocked"
        value["positions"] = "blocked"
        value["live_execution"] = "blocked"
        value["auth_presence_detected"] = self.auth_presence_status == STATUS_PRESENT_REDACTED
        value["auth_boundary_checked"] = self.auth_header_boundary_status in {STATUS_CHECKED, STATUS_BLOCKED}
        value["next_operator_action"] = (
            "configure redacted L2 presence markers or review blockers; no live order available"
        )
        value.update(
            authenticated_clob_preflight_safety_flags(
                auth_presence_check_performed=self.auth_presence_status != STATUS_SKIPPED,
                auth_header_boundary_checked=self.auth_header_boundary_status in {STATUS_CHECKED, STATUS_BLOCKED},
                no_order_auth_check_performed=self.no_order_auth_check_status in {STATUS_MOCKED, STATUS_BLOCKED},
            )
        )
        return value


@dataclass(frozen=True)
class AuthenticatedClobPreflightResult:
    market: str
    status: str
    config: Mapping[str, Any]
    credential_presence: Mapping[str, Any]
    clob_base_url_validation: Mapping[str, Any]
    auth_header_boundary_check: Mapping[str, Any]
    no_order_authenticated_request_plan: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    blockers: tuple[Mapping[str, Any], ...]
    artifact_paths: Mapping[str, str]
    operator_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        credential_presence = dict(self.credential_presence)
        header_boundary = dict(self.auth_header_boundary_check)
        request_plan = dict(self.no_order_authenticated_request_plan)
        value = {
            "contract_version": AUTHENTICATED_CLOB_PREFLIGHT_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market).upper() or "BTC",
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "dry_run": True,
            "config": dict(self.config),
            "credential_presence": credential_presence,
            "clob_base_url_validation": dict(self.clob_base_url_validation),
            "auth_header_boundary_check": header_boundary,
            "no_order_authenticated_request_plan": request_plan,
            "latest_status": dict(self.latest_status),
            "blockers": [dict(row) for row in self.blockers],
            "blocker_count": len(self.blockers),
            "resolved_blocker_count": 0,
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": clean_text(self.operator_summary),
            "generated_at": self.generated_at,
        }
        value.update(
            authenticated_clob_preflight_safety_flags(
                auth_presence_check_performed=credential_presence.get("auth_presence_check_performed") is True,
                auth_header_boundary_checked=header_boundary.get("auth_header_boundary_checked") is True,
                no_order_auth_check_performed=request_plan.get("no_order_auth_check_performed") is True,
            )
        )
        value["validation"] = validate_authenticated_clob_preflight_result(
            value,
            generated_at=self.generated_at,
        )
        return value


def authenticated_clob_preflight_safety_flags(
    *,
    auth_presence_check_performed: bool,
    auth_header_boundary_checked: bool,
    no_order_auth_check_performed: bool,
) -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "auth_presence_check_performed": auth_presence_check_performed is True,
        "auth_header_boundary_checked": auth_header_boundary_checked is True,
        "authenticated_request_performed": False,
        "no_order_auth_check_performed": no_order_auth_check_performed is True,
        "private_key_read": False,
        "l1_auth_attempted": False,
        "api_key_derivation_attempted": False,
        "wallet_connection_attempted": False,
        "signing_attempted": False,
        "signed_payload_generated": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "balance_read_attempted": False,
        "position_read_attempted": False,
        "live_execution_approved": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_submission_performed": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "hmac_signature_generated": False,
        "auth_signature_generated": False,
        "order_payload_generated": False,
        "signed_order_payload_generated": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "order_cancellation_enabled": False,
        "real_order_cancelled": False,
        "balance_read_enabled": False,
        "position_read_enabled": False,
        "wallet_enabled": False,
        "wallet_spend_enabled": False,
        "raw_values_emitted": False,
        "credentials_values_exposed": False,
        "actual_secret_values_exposed": False,
        "raw_credential_values_persisted": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_secret_values_printed": False,
        "raw_secret_values_persisted": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def validate_authenticated_clob_preflight_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != AUTHENTICATED_CLOB_PREFLIGHT_RESULT_CONTRACT:
        errors.append(f"contract_version must be {AUTHENTICATED_CLOB_PREFLIGHT_RESULT_CONTRACT}")
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
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for path, key, nested in _walk_flags(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
    valid = not errors
    return {
        "contract_version": AUTHENTICATED_CLOB_PREFLIGHT_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "authenticated-clob-preflight-validation-057",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["authenticated_clob_preflight_valid"] if valid else ["authenticated_clob_preflight_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **authenticated_clob_preflight_safety_flags(
            auth_presence_check_performed=value.get("auth_presence_check_performed") is True,
            auth_header_boundary_checked=value.get("auth_header_boundary_checked") is True,
            no_order_auth_check_performed=value.get("no_order_auth_check_performed") is True,
        ),
    }


def validate_no_order_authenticated_get_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != NO_ORDER_AUTHENTICATED_GET_RESULT_CONTRACT:
        errors.append(f"contract_version must be {NO_ORDER_AUTHENTICATED_GET_RESULT_CONTRACT}")
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
    if value.get("request_method") != "GET":
        errors.append("request_method must be GET")
        statuses.append("unsafe_method_detected")
    if value.get("credentials_values_exposed") is not False:
        errors.append("credentials_values_exposed must be false")
        statuses.append("credential_value_exposure_detected")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    if value.get("real_authenticated_get_performed") is True:
        if value.get("real_auth_read_only_requested") is not True:
            errors.append("real authenticated GET requires real_auth_read_only_requested=true")
            statuses.append("real_get_without_flag")
        if value.get("real_auth_read_only_opt_in_present") is not True:
            errors.append("real authenticated GET requires opt-in marker")
            statuses.append("real_get_without_env_opt_in")
        if value.get("endpoint_safe_for_no_order_check") is not True:
            errors.append("real authenticated GET requires a safe no-order endpoint")
            statuses.append("real_get_unsafe_endpoint")
        if value.get("auth_used") is not True:
            errors.append("real authenticated GET must record auth_used=true")
            statuses.append("real_get_auth_used_missing")
    else:
        if value.get("auth_used") is True:
            errors.append("auth_used may be true only when real_authenticated_get_performed=true")
            statuses.append("auth_used_without_real_get")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for path, key, nested in _walk_flags(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
    valid = not errors
    return {
        "contract_version": NO_ORDER_AUTHENTICATED_GET_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "no-order-authenticated-get-validation-059",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["no_order_authenticated_get_valid"] if valid else ["no_order_authenticated_get_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **no_order_authenticated_get_safety_flags(
            no_order_auth_get_requested=value.get("no_order_auth_get_requested") is True,
            real_auth_read_only_requested=value.get("real_auth_read_only_requested") is True,
            real_auth_read_only_opt_in_present=value.get("real_auth_read_only_opt_in_present") is True,
            real_authenticated_get_performed=value.get("real_authenticated_get_performed") is True,
            endpoint_safe_for_no_order_check=value.get("endpoint_safe_for_no_order_check") is True,
            auth_used=value.get("auth_used") is True,
            auth_header_boundary_checked=value.get("no_order_auth_get_requested") is True,
            no_order_auth_check_performed=value.get("no_order_auth_get_requested") is True,
        ),
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
