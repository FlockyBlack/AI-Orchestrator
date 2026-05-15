from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-070C-LIVE-ACCOUNT-READONLY-STATE-PROBE-NO-ORDERS"

MODE = "live account read-only state probe / no orders"
EXECUTION_MODE = "live_account_readonly_state_probe"

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

POLYMARKET_WALLET_ADDRESS_ENV = "POLYMARKET_WALLET_ADDRESS"
POLYMARKET_SIGNATURE_TYPE_ENV = "POLYMARKET_SIGNATURE_TYPE"
POLYMARKET_FUNDER_ADDRESS_ENV = "POLYMARKET_FUNDER_ADDRESS"
ACCOUNT_CONFIG_ENV_VARS = (
    POLYMARKET_WALLET_ADDRESS_ENV,
    POLYMARKET_SIGNATURE_TYPE_ENV,
    POLYMARKET_FUNDER_ADDRESS_ENV,
)

FORBIDDEN_SECRET_ENV_VARS_NOT_READ = (
    "POLYMARKET_PRIVATE_KEY",
    "POLYMARKET_WALLET_PRIVATE_KEY",
    "PMBOT_POLYMARKET_PRIVATE_KEY",
    "PMBOT_WALLET_PRIVATE_KEY",
    "PRIVATE_KEY",
    "WALLET_PRIVATE_KEY",
    "MNEMONIC",
    "SEED_PHRASE",
)

SUPPORTED_SDK_MODULES = ("py_clob_client_v2", "py_clob_client")
READONLY_SDK_METHODS = ("get_orders", "get_balance_allowance")
READONLY_HTTP_METHOD = "GET"
BLOCKED_HTTP_METHODS = ("POST", "PUT", "PATCH", "DELETE")

STATUS_BLOCKED_MISSING_CREDENTIALS = "blocked_missing_l2_credentials"
STATUS_BLOCKED_DEPENDENCY_MISSING = "blocked_sdk_unavailable"
STATUS_BLOCKED_CREDENTIAL_OBJECT_ERROR = "blocked_sdk_credentials_object_error"
STATUS_BLOCKED_CLIENT_INIT_ERROR = "blocked_sdk_client_init_error"
STATUS_BLOCKED_SDK_REQUIRES_SIGNER = "blocked_sdk_requires_signer_without_private_key"
STATUS_BLOCKED_METHOD_UNAVAILABLE = "blocked_method_unavailable"
STATUS_BLOCKED_PROBE_FAILED = "blocked_account_state_probe_failed"
STATUS_SUCCEEDED_LIVE_BLOCKED = "account_state_probe_succeeded_live_blocked"

CREDENTIAL_PRESENCE_CONTRACT = "pmbot_live_account_readonly_state_credential_presence_070c.v1"
ACCOUNT_STATUS_CONTRACT = "pmbot_live_account_readonly_state_account_status_070c.v1"
SDK_STATUS_CONTRACT = "pmbot_live_account_readonly_state_sdk_status_070c.v1"
PROBE_ATTEMPT_CONTRACT = "pmbot_live_account_readonly_state_probe_attempt_070c.v1"
DIAGNOSTICS_CONTRACT = "pmbot_live_account_readonly_state_diagnostics_070c.v1"
REDACTION_POLICY_CONTRACT = "pmbot_live_account_readonly_state_redaction_policy_070c.v1"
LATEST_STATUS_CONTRACT = "pmbot_latest_live_account_readonly_state_status_070c.v1"
RESULT_CONTRACT = "pmbot_live_account_readonly_state_probe_result_070c.v1"
VALIDATION_CONTRACT = "pmbot_live_account_readonly_state_validation_070c.v1"

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
    "wallet_private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "l1_auth_attempted",
    "api_key_derivation_attempted",
    "api_key_creation_attempted",
    "post_put_patch_delete_attempted",
    "trading_endpoint_write_attempted",
    "raw_order_rows_emitted",
    "raw_account_values_emitted",
    "balance_values_emitted",
    "allowance_values_emitted",
    "position_values_emitted",
    "fill_values_emitted",
    "pnl_values_emitted",
    "fake_balances_emitted",
    "fake_orders_emitted",
    "fake_positions_emitted",
    "fake_fills_emitted",
    "fake_pnl_emitted",
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


def live_account_readonly_state_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "dry_run_only": True,
        "review_only": True,
        "probe_is_readonly": True,
        "probe_is_l2_auth_only": True,
        "account_state_probe": True,
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
        "wallet_private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "l1_auth_attempted": False,
        "api_key_derivation_attempted": False,
        "api_key_creation_attempted": False,
        "post_put_patch_delete_attempted": False,
        "trading_endpoint_write_attempted": False,
        "raw_order_rows_emitted": False,
        "raw_account_values_emitted": False,
        "balance_values_emitted": False,
        "allowance_values_emitted": False,
        "position_values_emitted": False,
        "fill_values_emitted": False,
        "pnl_values_emitted": False,
        "fake_balances_emitted": False,
        "fake_orders_emitted": False,
        "fake_positions_emitted": False,
        "fake_fills_emitted": False,
        "fake_pnl_emitted": False,
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
class LiveAccountCredentialPresence:
    l2_env_presence_items: tuple[Mapping[str, Any], ...]
    account_config_presence_items: tuple[Mapping[str, Any], ...]
    configured_l2_count: int
    missing_l2_count: int
    missing_l2_env_vars: tuple[str, ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        missing = [clean_text(item) for item in self.missing_l2_env_vars if clean_text(item)]
        value = {
            "contract_version": CREDENTIAL_PRESENCE_CONTRACT,
            "task_id": TASK_ID,
            "status": "present_redacted" if not missing else "missing",
            "required_l2_env_vars": list(REQUIRED_L2_CREDENTIAL_ENV_VARS),
            "account_config_env_vars_presence_checked": list(ACCOUNT_CONFIG_ENV_VARS),
            "forbidden_secret_env_vars_not_read": list(FORBIDDEN_SECRET_ENV_VARS_NOT_READ),
            "l2_env_presence_items": [dict(row) for row in self.l2_env_presence_items],
            "account_config_presence_items": [
                dict(row) for row in self.account_config_presence_items
            ],
            "configured_l2_count": int(self.configured_l2_count),
            "missing_l2_count": int(self.missing_l2_count),
            "missing_l2_env_vars": missing,
            "presence_only_in_artifacts": True,
            "l2_required_env_values_loaded_in_memory": not missing,
            "account_config_values_redacted": True,
            "private_key_env_read": False,
            "raw_values_emitted": False,
            "actual_secret_values_exposed": False,
            "raw_credential_values_persisted": False,
            "credential_values_serialized": False,
            "credential_values_printed": False,
            "credential_values_stored": False,
            "safe_for_artifacts": True,
            "generated_at": self.generated_at,
        }
        value.update(live_account_readonly_state_safety_flags())
        return value


@dataclass(frozen=True)
class LiveAccountRedactedStatus:
    wallet_address_present: bool
    wallet_address_redacted: str
    signature_type_present: bool
    signature_type_redacted: str
    funder_address_present: bool
    funder_address_redacted: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": ACCOUNT_STATUS_CONTRACT,
            "task_id": TASK_ID,
            "status": "account_config_detected_redacted"
            if any(
                (
                    self.wallet_address_present,
                    self.signature_type_present,
                    self.funder_address_present,
                )
            )
            else "account_config_not_detected",
            "wallet_address_present": self.wallet_address_present is True,
            "wallet_address_status": "present_redacted"
            if self.wallet_address_present
            else "missing",
            "wallet_address_redacted": clean_text(self.wallet_address_redacted),
            "signature_type_present": self.signature_type_present is True,
            "signature_type_status": "present_redacted"
            if self.signature_type_present
            else "missing",
            "signature_type_redacted": clean_text(self.signature_type_redacted),
            "funder_address_present": self.funder_address_present is True,
            "funder_address_status": "present_redacted"
            if self.funder_address_present
            else "missing",
            "funder_address_redacted": clean_text(self.funder_address_redacted),
            "wallet_connection_attempted": False,
            "private_key_read": False,
            "raw_account_values_emitted": False,
            "safe_for_artifacts": True,
            "generated_at": self.generated_at,
        }
        value.update(live_account_readonly_state_safety_flags())
        return value


@dataclass(frozen=True)
class LiveAccountSdkStatus:
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
        value.update(live_account_readonly_state_safety_flags())
        return value


@dataclass(frozen=True)
class LiveAccountReadOnlyProbeAttempt:
    probe_name: str
    sdk_method: str
    status: str
    attempted: bool
    succeeded: bool
    method_available: bool
    request_method: str = READONLY_HTTP_METHOD
    open_order_count: int | None = None
    open_order_count_available: bool = False
    response_shape: str = ""
    account_value_fields_available: tuple[str, ...] = ()
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
        value["method_available"] = self.method_available is True
        value["request_method"] = READONLY_HTTP_METHOD
        value["request_method_allowed"] = True
        value["blocked_http_methods"] = list(BLOCKED_HTTP_METHODS)
        value["open_order_count_available"] = self.open_order_count_available is True
        value["account_value_fields_available"] = [
            clean_text(item) for item in self.account_value_fields_available if clean_text(item)
        ]
        value["response_value_fields_redacted"] = [
            clean_text(item)
            for item in self.response_value_fields_redacted
            if clean_text(item)
        ]
        value["raw_response_emitted"] = False
        value["raw_order_rows_emitted"] = False
        value["numeric_account_values_emitted"] = False
        value["error_message_raw_emitted"] = False
        value["safe_for_artifacts"] = True
        value.update(live_account_readonly_state_safety_flags())
        return value


@dataclass(frozen=True)
class LiveAccountReadOnlyDiagnostics:
    market: str
    strategy: str
    credential_presence: Mapping[str, Any]
    account_status: Mapping[str, Any]
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
            "account_status": dict(self.account_status),
            "sdk_status": dict(self.sdk_status),
            "probe_attempts": [dict(row) for row in self.probe_attempts],
            "probe_attempt_count": len(self.probe_attempts),
            "blockers": [dict(row) for row in self.blockers],
            "blocker_count": len(self.blockers),
            "safe_for_artifacts": True,
            "generated_at": self.generated_at,
        }
        value.update(live_account_readonly_state_safety_flags())
        return value


@dataclass(frozen=True)
class LiveAccountReadOnlyLatestStatus:
    market: str
    strategy: str
    status: str
    credential_presence_status: str
    sdk_status: str
    selected_sdk_module: str
    account_status: str
    wallet_address_status: str
    signature_type_status: str
    funder_address_status: str
    wallet_address_redacted: str
    signature_type_redacted: str
    funder_address_redacted: str
    open_orders_status: str
    open_order_count: int | None
    balance_allowance_status: str
    balance_allowance_availability_status: str
    account_state_probe_attempted: bool
    account_state_probe_performed: bool
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
        value["credential_presence_status"] = clean_text(self.credential_presence_status)
        value["sdk_status"] = clean_text(self.sdk_status)
        value["selected_sdk_module"] = clean_text(self.selected_sdk_module)
        value["account_status"] = clean_text(self.account_status)
        value["wallet_address_status"] = clean_text(self.wallet_address_status)
        value["signature_type_status"] = clean_text(self.signature_type_status)
        value["funder_address_status"] = clean_text(self.funder_address_status)
        value["wallet_address_redacted"] = clean_text(self.wallet_address_redacted)
        value["signature_type_redacted"] = clean_text(self.signature_type_redacted)
        value["funder_address_redacted"] = clean_text(self.funder_address_redacted)
        value["open_orders_status"] = clean_text(self.open_orders_status)
        value["balance_allowance_status"] = clean_text(self.balance_allowance_status)
        value["balance_allowance_availability_status"] = clean_text(
            self.balance_allowance_availability_status
        )
        value["account_state_probe_attempted"] = self.account_state_probe_attempted is True
        value["account_state_probe_performed"] = self.account_state_probe_performed is True
        value["blockers"] = blockers
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in blockers[:8]]
        value["read_only_probe"] = "performed" if self.account_state_probe_performed else "not_performed"
        value["order_submission"] = "blocked"
        value["order_cancellation"] = "blocked"
        value["signing"] = "blocked"
        value["wallet_connection"] = "blocked"
        value["live_execution"] = "blocked"
        value["credentials_output"] = "redacted_presence_only"
        value["account_values_output"] = "redacted_availability_only"
        value["next_operator_action"] = _next_operator_action(self.status)
        value.update(live_account_readonly_state_safety_flags())
        return value


@dataclass(frozen=True)
class LiveAccountReadOnlyProbeResult:
    market: str
    strategy: str
    status: str
    credential_presence: Mapping[str, Any]
    account_status: Mapping[str, Any]
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
            "account_status": dict(self.account_status),
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
            "wallet_address_status",
            "signature_type_status",
            "funder_address_status",
            "wallet_address_redacted",
            "signature_type_redacted",
            "funder_address_redacted",
            "open_orders_status",
            "open_order_count",
            "balance_allowance_status",
            "balance_allowance_availability_status",
            "account_state_probe_attempted",
            "account_state_probe_performed",
        ):
            value[key] = latest_status.get(key)
        value["redacted_account_status"] = latest_status.get("account_status")
        value["sdk_probe_status"] = latest_status.get("sdk_status")
        value.update(live_account_readonly_state_safety_flags())
        value["validation"] = validate_live_account_readonly_state_result(
            value,
            generated_at=self.generated_at,
        )
        return value


def build_redaction_policy(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    value = {
        "contract_version": REDACTION_POLICY_CONTRACT,
        "task_id": TASK_ID,
        "policy": (
            "L2 API credential values are used only in memory for SDK authentication. "
            "Account config markers are redacted, and account values are summarized as "
            "counts or availability only."
        ),
        "required_l2_env_vars": list(REQUIRED_L2_CREDENTIAL_ENV_VARS),
        "account_config_env_vars_presence_checked": list(ACCOUNT_CONFIG_ENV_VARS),
        "forbidden_secret_env_vars_not_read": list(FORBIDDEN_SECRET_ENV_VARS_NOT_READ),
        "redacted_fields": [
            "api key value",
            "api secret value",
            "api passphrase value",
            "wallet address full value",
            "funder address full value",
            "raw SDK responses",
            "raw order rows",
            "numeric account balance and allowance values",
            "positions, fills, and PnL values",
        ],
        "artifact_allowed_outputs": [
            "env var names",
            "presence booleans",
            "redacted wallet/funder display values",
            "sanitized signature type display",
            "SDK/module names",
            "safe read-only method names",
            "open order count",
            "balance/allowance field availability",
            "sanitized error class/message",
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
    value.update(live_account_readonly_state_safety_flags())
    return value


def build_blocker(blocker_id: str, category: str, reason: str) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_live_account_readonly_state_blocker_070c.v1",
        "task_id": TASK_ID,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "severity": "critical",
        "reason": clean_text(reason),
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
    }
    value.update(live_account_readonly_state_safety_flags())
    return value


def validate_live_account_readonly_state_result(
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
        errors.append("execution_mode must match live_account_readonly_state_probe")
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
        if value.get("account_state_probe_performed") is not True:
            errors.append("successful status requires account_state_probe_performed=true")
            statuses.append("success_without_readonly_probe")
    if value.get("status") in {
        STATUS_BLOCKED_DEPENDENCY_MISSING,
        STATUS_BLOCKED_METHOD_UNAVAILABLE,
        STATUS_BLOCKED_SDK_REQUIRES_SIGNER,
    } and value.get("account_state_probe_performed") is True:
        errors.append("blocked dependency/method/signer statuses cannot set probe_performed=true")
        statuses.append("blocked_status_with_probe_performed")
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
            "live-account-readonly-state-validation-070c",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["live_account_readonly_state_probe_valid"] if valid else ["live_account_readonly_state_probe_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **live_account_readonly_state_safety_flags(),
    }


def _next_operator_action(status: str) -> str:
    normalized = clean_text(status)
    if normalized == STATUS_BLOCKED_MISSING_CREDENTIALS:
        return "configure the three L2 API env vars; do not add private keys for this probe"
    if normalized == STATUS_BLOCKED_DEPENDENCY_MISSING:
        return "install or expose the official Polymarket Python CLOB SDK in a separately approved dependency task"
    if normalized == STATUS_BLOCKED_METHOD_UNAVAILABLE:
        return "review SDK method names; unavailable methods must remain method_unavailable, not fabricated"
    if normalized == STATUS_BLOCKED_SDK_REQUIRES_SIGNER:
        return "stop here; this task does not read private keys or instantiate signers"
    if normalized == STATUS_SUCCEEDED_LIVE_BLOCKED:
        return "review redacted account-state diagnostics; live trading remains disabled"
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
