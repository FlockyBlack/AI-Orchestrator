from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-067C-CLOB-L2-AUTH-READONLY-PROBE-NO-ORDERS"

MODE = "clob l2 authenticated read-only probe / no orders"
EXECUTION_MODE = "clob_l2_auth_readonly_probe"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"
DEFAULT_CLOB_HOST = "https://clob.polymarket.com"
POLYGON_CHAIN_ID = 137

POLYMARKET_API_KEY_ENV = "POLYMARKET_API_KEY"
POLYMARKET_API_SECRET_ENV = "POLYMARKET_API_SECRET"
POLYMARKET_API_PASSPHRASE_ENV = "POLYMARKET_API_PASSPHRASE"
REQUIRED_L2_CREDENTIAL_ENV_VARS = (
    POLYMARKET_API_KEY_ENV,
    POLYMARKET_API_SECRET_ENV,
    POLYMARKET_API_PASSPHRASE_ENV,
)

FORBIDDEN_ENV_VARS_NOT_READ = (
    "POLYMARKET_PRIVATE_KEY",
    "POLYMARKET_WALLET_ADDRESS",
    "POLYMARKET_SIGNATURE_TYPE",
    "POLYMARKET_FUNDER_ADDRESS",
)

SUPPORTED_SDK_MODULES = ("py_clob_client_v2", "py_clob_client")
READONLY_SDK_METHODS = ("get_orders", "get_balance_allowance")
READONLY_HTTP_METHOD = "GET"
BLOCKED_HTTP_METHODS = ("POST", "PUT", "PATCH", "DELETE")

STATUS_BLOCKED_MISSING_CREDENTIALS = "blocked_missing_l2_credentials"
STATUS_BLOCKED_DEPENDENCY_MISSING = "blocked_dependency_missing"
STATUS_BLOCKED_CREDENTIAL_OBJECT_ERROR = "blocked_sdk_credentials_object_error"
STATUS_BLOCKED_CLIENT_INIT_ERROR = "blocked_sdk_client_init_error"
STATUS_BLOCKED_SDK_REQUIRES_SIGNER = "blocked_sdk_requires_signer_without_private_key"
STATUS_BLOCKED_METHOD_MISSING = "blocked_method_missing"
STATUS_BLOCKED_PROBE_FAILED = "blocked_auth_readonly_probe_failed"
STATUS_SUCCEEDED_LIVE_BLOCKED = "authenticated_readonly_probe_succeeded_live_blocked"

CREDENTIAL_PRESENCE_CONTRACT = "pmbot_clob_l2_auth_readonly_credential_presence_067c.v1"
SDK_STATUS_CONTRACT = "pmbot_clob_l2_auth_readonly_sdk_status_067c.v1"
PROBE_ATTEMPT_CONTRACT = "pmbot_clob_l2_auth_readonly_probe_attempt_067c.v1"
DIAGNOSTICS_CONTRACT = "pmbot_clob_l2_auth_readonly_probe_diagnostics_067c.v1"
REDACTION_POLICY_CONTRACT = "pmbot_clob_l2_auth_readonly_probe_redaction_policy_067c.v1"
LATEST_STATUS_CONTRACT = "pmbot_latest_clob_l2_auth_readonly_probe_status_067c.v1"
RESULT_CONTRACT = "pmbot_clob_l2_auth_readonly_probe_result_067c.v1"
VALIDATION_CONTRACT = "pmbot_clob_l2_auth_readonly_probe_validation_067c.v1"

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "live_execution_approved",
    "real_execution_available",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "real_order_submitted",
    "order_cancellation_enabled",
    "order_cancellation_attempted",
    "order_cancelled",
    "real_order_cancelled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_performed",
    "signer_instantiated",
    "signing_enabled",
    "signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "order_payload_generated",
    "signed_order_generation_enabled",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "l1_auth_attempted",
    "api_key_derivation_attempted",
    "api_key_creation_attempted",
    "post_put_patch_delete_attempted",
    "trading_endpoint_write_attempted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "raw_credential_values_persisted",
    "credential_values_serialized",
    "credential_values_printed",
    "credential_values_stored",
    "credential_values_hashed",
    "credential_values_transformed",
    "secrets_printed",
    "secrets_persisted",
    "raw_secret_values_printed",
    "raw_secret_values_persisted",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)


def clob_l2_auth_readonly_probe_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "dry_run_only": True,
        "review_only": True,
        "probe_is_readonly": True,
        "probe_is_l2_auth_only": True,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "real_order_submitted": False,
        "order_cancellation_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancelled": False,
        "real_order_cancelled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "signer_instantiated": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "order_payload_generated": False,
        "signed_order_generation_enabled": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "l1_auth_attempted": False,
        "api_key_derivation_attempted": False,
        "api_key_creation_attempted": False,
        "post_put_patch_delete_attempted": False,
        "trading_endpoint_write_attempted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "raw_credential_values_persisted": False,
        "credential_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "credential_values_hashed": False,
        "credential_values_transformed": False,
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


@dataclass(frozen=True)
class ClobL2CredentialPresence:
    env_presence_items: tuple[Mapping[str, Any], ...]
    configured_count: int
    missing_count: int
    missing_env_vars: tuple[str, ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        missing = [clean_text(item) for item in self.missing_env_vars if clean_text(item)]
        value = {
            "contract_version": CREDENTIAL_PRESENCE_CONTRACT,
            "task_id": TASK_ID,
            "status": "present_redacted" if not missing else "missing",
            "required_env_vars": list(REQUIRED_L2_CREDENTIAL_ENV_VARS),
            "forbidden_env_vars_not_read": list(FORBIDDEN_ENV_VARS_NOT_READ),
            "env_presence_items": [dict(row) for row in self.env_presence_items],
            "configured_count": int(self.configured_count),
            "missing_count": int(self.missing_count),
            "missing_env_vars": missing,
            "presence_only_in_artifacts": True,
            "l2_required_env_values_loaded_in_memory": not missing,
            "private_key_env_read": False,
            "wallet_address_env_read": False,
            "raw_values_emitted": False,
            "actual_secret_values_exposed": False,
            "raw_credential_values_persisted": False,
            "credential_values_serialized": False,
            "credential_values_printed": False,
            "credential_values_stored": False,
            "safe_for_artifacts": True,
            "generated_at": self.generated_at,
        }
        value.update(clob_l2_auth_readonly_probe_safety_flags())
        return value


@dataclass(frozen=True)
class ClobL2SdkStatus:
    status: str
    sdk_available: bool
    selected_sdk_module: str
    attempted_sdk_modules: tuple[str, ...]
    client_class_available: bool
    api_creds_class_available: bool
    open_orders_method_available: bool
    balance_allowance_method_available: bool
    l2_credentials_object_created: bool
    sdk_client_created: bool
    sdk_requires_signer_without_private_key: bool
    error_type: str = ""
    error_message_sanitized: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SDK_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["attempted_sdk_modules"] = list(self.attempted_sdk_modules)
        value["supported_sdk_modules"] = list(SUPPORTED_SDK_MODULES)
        value["safe_readonly_methods"] = list(READONLY_SDK_METHODS)
        value["request_method_allowlist"] = [READONLY_HTTP_METHOD]
        value["blocked_http_methods"] = list(BLOCKED_HTTP_METHODS)
        value["error_message_raw_emitted"] = False
        value["safe_for_artifacts"] = True
        value.update(clob_l2_auth_readonly_probe_safety_flags())
        return value


@dataclass(frozen=True)
class ClobL2ReadOnlyProbeAttempt:
    probe_name: str
    sdk_method: str
    status: str
    attempted: bool
    succeeded: bool
    request_method: str = READONLY_HTTP_METHOD
    open_order_count: int | None = None
    response_shape: str = ""
    response_value_fields_redacted: tuple[str, ...] = ()
    error_type: str = ""
    error_message_sanitized: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PROBE_ATTEMPT_CONTRACT
        value["task_id"] = TASK_ID
        value["probe_name"] = clean_text(self.probe_name)
        value["sdk_method"] = clean_text(self.sdk_method)
        value["status"] = clean_text(self.status)
        value["attempted"] = self.attempted is True
        value["succeeded"] = self.succeeded is True
        value["request_method"] = READONLY_HTTP_METHOD
        value["request_method_allowed"] = True
        value["blocked_http_methods"] = list(BLOCKED_HTTP_METHODS)
        value["response_value_fields_redacted"] = [
            clean_text(item) for item in self.response_value_fields_redacted if clean_text(item)
        ]
        value["raw_response_emitted"] = False
        value["raw_order_rows_emitted"] = False
        value["numeric_account_values_emitted"] = False
        value["error_message_raw_emitted"] = False
        value["safe_for_artifacts"] = True
        value.update(clob_l2_auth_readonly_probe_safety_flags())
        return value


@dataclass(frozen=True)
class ClobL2AuthReadOnlyDiagnostics:
    market: str
    strategy: str
    credential_presence: Mapping[str, Any]
    sdk_status: Mapping[str, Any]
    probe_attempts: tuple[Mapping[str, Any], ...]
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": DIAGNOSTICS_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market).upper() or DEFAULT_MARKET,
            "strategy": clean_text(self.strategy) or DEFAULT_STRATEGY,
            "credential_presence": dict(self.credential_presence),
            "sdk_status": dict(self.sdk_status),
            "probe_attempts": [dict(row) for row in self.probe_attempts],
            "probe_attempt_count": len(self.probe_attempts),
            "blockers": [dict(row) for row in self.blockers],
            "blocker_count": len(self.blockers),
            "safe_for_artifacts": True,
            "generated_at": self.generated_at,
        }
        value.update(clob_l2_auth_readonly_probe_safety_flags())
        return value


@dataclass(frozen=True)
class ClobL2AuthReadOnlyLatestStatus:
    market: str
    strategy: str
    status: str
    auth_verified: bool
    credential_presence_status: str
    sdk_status: str
    selected_sdk_module: str
    open_order_count: int | None
    balance_allowance_probe_status: str
    l2_authenticated_readonly_probe_attempted: bool
    l2_authenticated_readonly_probe_performed: bool
    blocker_count: int
    blockers: tuple[Mapping[str, Any], ...]
    artifact_path: str
    latest_status_path: str
    diagnostics_path: str
    redaction_policy_path: str
    operator_summary_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in self.blockers]
        value = asdict(self)
        value["contract_version"] = LATEST_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = clean_text(self.market).upper() or DEFAULT_MARKET
        value["strategy"] = clean_text(self.strategy) or DEFAULT_STRATEGY
        value["status"] = clean_text(self.status)
        value["auth_verified"] = self.auth_verified is True
        value["credential_presence_status"] = clean_text(self.credential_presence_status)
        value["sdk_status"] = clean_text(self.sdk_status)
        value["selected_sdk_module"] = clean_text(self.selected_sdk_module)
        value["balance_allowance_probe_status"] = clean_text(self.balance_allowance_probe_status)
        value["l2_authenticated_readonly_probe_attempted"] = (
            self.l2_authenticated_readonly_probe_attempted is True
        )
        value["l2_authenticated_readonly_probe_performed"] = (
            self.l2_authenticated_readonly_probe_performed is True
        )
        value["blockers"] = blockers
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in blockers[:8]]
        value["read_only_probe"] = "verified" if self.auth_verified else "not_verified"
        value["order_submission"] = "blocked"
        value["order_cancellation"] = "blocked"
        value["signing"] = "blocked"
        value["wallet"] = "blocked"
        value["live_execution"] = "blocked"
        value["credentials_output"] = "redacted_presence_only"
        value["next_operator_action"] = _next_operator_action(self.status)
        value.update(clob_l2_auth_readonly_probe_safety_flags())
        return value


@dataclass(frozen=True)
class ClobL2AuthReadOnlyProbeResult:
    market: str
    strategy: str
    status: str
    credential_presence: Mapping[str, Any]
    sdk_status: Mapping[str, Any]
    diagnostics: Mapping[str, Any]
    redaction_policy: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    blockers: tuple[Mapping[str, Any], ...]
    artifact_paths: Mapping[str, str]
    operator_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        latest_status = dict(self.latest_status)
        value = {
            "contract_version": RESULT_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market).upper() or DEFAULT_MARKET,
            "strategy": clean_text(self.strategy) or DEFAULT_STRATEGY,
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "dry_run": True,
            "credential_presence": dict(self.credential_presence),
            "sdk_status": dict(self.sdk_status),
            "diagnostics": dict(self.diagnostics),
            "redaction_policy": dict(self.redaction_policy),
            "latest_status": latest_status,
            "blockers": [dict(row) for row in self.blockers],
            "blocker_count": len(self.blockers),
            "resolved_blocker_count": 0,
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": clean_text(self.operator_summary),
            "generated_at": self.generated_at,
        }
        for key in (
            "auth_verified",
            "credential_presence_status",
            "selected_sdk_module",
            "open_order_count",
            "balance_allowance_probe_status",
            "l2_authenticated_readonly_probe_attempted",
            "l2_authenticated_readonly_probe_performed",
        ):
            value[key] = latest_status.get(key)
        value["sdk_probe_status"] = latest_status.get("sdk_status")
        value.update(clob_l2_auth_readonly_probe_safety_flags())
        value["validation"] = validate_clob_l2_auth_readonly_probe_result(
            value,
            generated_at=self.generated_at,
        )
        return value


def build_redaction_policy(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    value = {
        "contract_version": REDACTION_POLICY_CONTRACT,
        "task_id": TASK_ID,
        "policy": "Credential values are used only in memory for SDK L2 authentication and are never logged or written.",
        "required_env_vars": list(REQUIRED_L2_CREDENTIAL_ENV_VARS),
        "forbidden_env_vars_not_read": list(FORBIDDEN_ENV_VARS_NOT_READ),
        "redacted_fields": [
            "api key value",
            "api secret value",
            "api passphrase value",
            "L2 HMAC signature value",
            "raw SDK responses",
            "numeric account balance and allowance values",
        ],
        "artifact_allowed_outputs": [
            "env var names",
            "presence booleans",
            "SDK/module names",
            "safe read-only method names",
            "open order count",
            "redacted status and sanitized error class/message",
        ],
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "raw_credential_values_persisted": False,
        "credential_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "credential_values_hashed": False,
        "credential_values_transformed": False,
        "safe_for_artifacts": True,
        "generated_at": generated_at,
    }
    value.update(clob_l2_auth_readonly_probe_safety_flags())
    return value


def build_blocker(blocker_id: str, category: str, reason: str) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_clob_l2_auth_readonly_probe_blocker_067c.v1",
        "task_id": TASK_ID,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "severity": "critical",
        "reason": clean_text(reason),
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
    }
    value.update(clob_l2_auth_readonly_probe_safety_flags())
    return value


def validate_clob_l2_auth_readonly_probe_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != RESULT_CONTRACT:
        errors.append(f"contract_version must be {RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must match clob_l2_auth_readonly_probe")
        statuses.append("invalid_execution_mode")
    if value.get("probe_is_readonly") is not True:
        errors.append("probe_is_readonly must be true")
        statuses.append("readonly_flag_missing")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_not_false")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    if value.get("status") == STATUS_SUCCEEDED_LIVE_BLOCKED:
        if value.get("auth_verified") is not True:
            errors.append("successful status requires auth_verified=true")
            statuses.append("success_without_auth_verified")
        if value.get("l2_authenticated_readonly_probe_performed") is not True:
            errors.append("successful status requires l2_authenticated_readonly_probe_performed=true")
            statuses.append("success_without_readonly_probe")
    if value.get("status") in {
        STATUS_BLOCKED_DEPENDENCY_MISSING,
        STATUS_BLOCKED_METHOD_MISSING,
        STATUS_BLOCKED_SDK_REQUIRES_SIGNER,
    } and value.get("auth_verified") is True:
        errors.append("blocked dependency/method/signer statuses cannot set auth_verified=true")
        statuses.append("blocked_status_with_auth_verified")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
    valid = not errors
    return {
        "contract_version": VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "clob-l2-auth-readonly-probe-validation-067c",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["clob_l2_auth_readonly_probe_valid"] if valid else ["clob_l2_auth_readonly_probe_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **clob_l2_auth_readonly_probe_safety_flags(),
    }


def _next_operator_action(status: str) -> str:
    normalized = clean_text(status)
    if normalized == STATUS_BLOCKED_MISSING_CREDENTIALS:
        return "configure the three L2 API env vars; do not add private keys for this probe"
    if normalized == STATUS_BLOCKED_DEPENDENCY_MISSING:
        return "install or expose the official Polymarket Python CLOB SDK in a separately approved dependency task"
    if normalized == STATUS_BLOCKED_METHOD_MISSING:
        return "review SDK method names before enabling another read-only probe"
    if normalized == STATUS_BLOCKED_SDK_REQUIRES_SIGNER:
        return "stop here; this task does not read private keys or instantiate signers"
    if normalized == STATUS_SUCCEEDED_LIVE_BLOCKED:
        return "review redacted diagnostics; live trading remains disabled"
    return "review diagnostics; no order, wallet, or signing action is available"


def _walk_fields(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            rows.append((path, key_text, nested))
            rows.extend(_walk_fields(nested, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_fields(nested, f"{path}[{index}]"))
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
