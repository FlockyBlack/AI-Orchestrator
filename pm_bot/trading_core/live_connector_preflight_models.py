from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-056-SUPERVISED-LIVE-CONNECTOR-AUTH-NETWORK-PREFLIGHT-NO-ORDER-SUBMISSION"

LIVE_CONNECTOR_PREFLIGHT_CONFIG_CONTRACT = "pmbot_live_connector_preflight_config_056.v1"
LIVE_CONNECTOR_PREFLIGHT_RESULT_CONTRACT = "pmbot_live_connector_preflight_result_056.v1"
CREDENTIAL_PRESENCE_REPORT_CONTRACT = "pmbot_live_connector_credential_presence_report_056.v1"
NETWORK_PREFLIGHT_RESULT_CONTRACT = "pmbot_live_connector_network_preflight_result_056.v1"
AUTH_BOUNDARY_PREFLIGHT_RESULT_CONTRACT = "pmbot_live_connector_auth_boundary_preflight_result_056.v1"
LIVE_READINESS_BLOCKER_CONTRACT = "pmbot_live_connector_readiness_blocker_056.v1"
LATEST_LIVE_CONNECTOR_PREFLIGHT_STATUS_CONTRACT = "pmbot_latest_live_connector_preflight_status_056.v1"
LIVE_CONNECTOR_PREFLIGHT_VALIDATION_CONTRACT = "pmbot_live_connector_preflight_validation_056.v1"

EXECUTION_MODE = "paper_or_preflight"
MODE = "preflight / review-only"

STATUS_NETWORK_OK = "ok"
STATUS_NETWORK_FAILED = "failed"
STATUS_NETWORK_SKIPPED = "skipped"
STATUS_AUTH_SKIPPED = "skipped"
STATUS_AUTH_CHECKED = "checked"
STATUS_AUTH_MISSING = "missing"
STATUS_AUTH_BLOCKED = "blocked"

FORCED_FALSE_EXECUTION_FIELDS = (
    "authenticated_request_performed",
    "order_submission_attempted",
    "order_cancellation_attempted",
    "signing_attempted",
    "signed_payload_generated",
    "wallet_connection_attempted",
    "wallet_spend_enabled",
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
    "wallet_enabled",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "wallet_signing_performed",
    "real_order_submitted",
    "order_submitted",
    "order_cancellation_enabled",
    "real_order_cancelled",
    "balance_read_performed",
    "position_read_performed",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)


@dataclass(frozen=True)
class LiveConnectorPreflightConfig:
    market: str
    dry_run: bool = True
    public_only: bool = True
    network_check: bool = False
    auth_check: bool = False
    artifact_dir: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CONNECTOR_PREFLIGHT_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = clean_text(self.market).upper() or "BTC"
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["dry_run"] = self.dry_run is True
        value["public_only"] = self.public_only is True
        value["network_check"] = self.network_check is True
        value["auth_check"] = self.auth_check is True
        value["operator_approval_can_enable_live"] = False
        value.update(
            live_connector_preflight_safety_flags(
                public_network_check_performed=False,
                auth_presence_check_performed=False,
            )
        )
        return value


@dataclass(frozen=True)
class CredentialPresenceReport:
    status: str
    auth_presence_check_performed: bool
    env_presence_items: tuple[Mapping[str, Any], ...]
    configured_count: int
    missing_count: int
    missing_env_vars: tuple[str, ...]
    unsafe_config_combinations: tuple[str, ...]
    operator_safe_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = CREDENTIAL_PRESENCE_REPORT_CONTRACT
        value["task_id"] = TASK_ID
        value["env_presence_items"] = [dict(row) for row in self.env_presence_items]
        value["missing_env_vars"] = list(self.missing_env_vars)
        value["unsafe_config_combinations"] = list(self.unsafe_config_combinations)
        value["redacted_presence_only"] = True
        value["raw_values_emitted"] = False
        value["actual_secret_values_exposed"] = False
        value["raw_credential_values_persisted"] = False
        value["safe_for_artifacts"] = True
        value.update(
            live_connector_preflight_safety_flags(
                public_network_check_performed=False,
                auth_presence_check_performed=self.auth_presence_check_performed,
            )
        )
        return value


@dataclass(frozen=True)
class NetworkPreflightResult:
    public_network_status: str
    public_network_check_performed: bool
    request_method: str
    gamma_status: str
    gamma_base_url_status: str
    gamma_endpoint_path: str
    gamma_status_code: int | None
    gamma_response_observed: bool
    gamma_response_snapshot_hash: str
    gamma_normalized_market_count: int
    clob_public_read_status: str
    clob_base_url_status: str
    network_error_category: str = ""
    network_error_message_redacted: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = NETWORK_PREFLIGHT_RESULT_CONTRACT
        value["task_id"] = TASK_ID
        value["request_method"] = "GET"
        value["read_only_public_get_only"] = True
        value["post_put_patch_delete_performed"] = False
        value["authenticated_endpoint_performed"] = False
        value["order_endpoint_performed"] = False
        value["safe_for_artifacts"] = True
        value.update(
            live_connector_preflight_safety_flags(
                public_network_check_performed=self.public_network_check_performed,
                auth_presence_check_performed=False,
            )
        )
        return value


@dataclass(frozen=True)
class AuthBoundaryPreflightResult:
    auth_boundary_status: str
    auth_presence_check_performed: bool
    credential_presence_report: Mapping[str, Any]
    blockers: tuple[Mapping[str, Any], ...]
    authenticated_request_performed: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = AUTH_BOUNDARY_PREFLIGHT_RESULT_CONTRACT
        value["task_id"] = TASK_ID
        value["credential_presence_report"] = dict(self.credential_presence_report)
        value["blockers"] = [dict(row) for row in self.blockers]
        value["authenticated_request_performed"] = False
        value["authenticated_trading_scope_checked"] = False
        value["raw_values_emitted"] = False
        value["actual_secret_values_exposed"] = False
        value.update(
            live_connector_preflight_safety_flags(
                public_network_check_performed=False,
                auth_presence_check_performed=self.auth_presence_check_performed,
            )
        )
        return value


@dataclass(frozen=True)
class LiveReadinessBlocker:
    blocker_id: str
    blocker_category: str
    severity: str
    reason: str
    resolution_status: str = "unresolved"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_READINESS_BLOCKER_CONTRACT
        value["blocks_live_execution"] = True
        value["resolved"] = False
        value.update(
            live_connector_preflight_safety_flags(
                public_network_check_performed=False,
                auth_presence_check_performed=False,
            )
        )
        return value


@dataclass(frozen=True)
class LatestLiveConnectorPreflightStatus:
    market: str
    status: str
    public_network_status: str
    auth_boundary_status: str
    blocker_count: int
    blockers: tuple[Mapping[str, Any], ...]
    artifact_path: str
    latest_status_path: str
    operator_markdown_path: str
    network_evidence_path: str
    credential_presence_path: str
    blockers_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LATEST_LIVE_CONNECTOR_PREFLIGHT_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["review_only"] = True
        value["preflight_only"] = True
        value["public_network"] = clean_text(self.public_network_status)
        value["auth_boundary"] = clean_text(self.auth_boundary_status)
        value["blockers"] = [dict(row) for row in self.blockers]
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in self.blockers[:8]]
        value["order_submission"] = "blocked"
        value["signing"] = "blocked"
        value["live_execution"] = "blocked"
        value["next_operator_action"] = "review preflight only, no live order available"
        value.update(
            live_connector_preflight_safety_flags(
                public_network_check_performed=self.public_network_status != STATUS_NETWORK_SKIPPED,
                auth_presence_check_performed=self.auth_boundary_status != STATUS_AUTH_SKIPPED,
            )
        )
        return value


@dataclass(frozen=True)
class LiveConnectorPreflightResult:
    market: str
    status: str
    config: Mapping[str, Any]
    network_preflight: Mapping[str, Any]
    auth_boundary: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    blockers: tuple[Mapping[str, Any], ...]
    artifact_paths: Mapping[str, str]
    operator_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        network = dict(self.network_preflight)
        auth = dict(self.auth_boundary)
        value = {
            "contract_version": LIVE_CONNECTOR_PREFLIGHT_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market).upper() or "BTC",
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "dry_run": True,
            "config": dict(self.config),
            "network_preflight": network,
            "auth_boundary": auth,
            "latest_status": dict(self.latest_status),
            "blockers": [dict(row) for row in self.blockers],
            "blocker_count": len(self.blockers),
            "resolved_blocker_count": 0,
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": clean_text(self.operator_summary),
            "generated_at": self.generated_at,
        }
        value.update(
            live_connector_preflight_safety_flags(
                public_network_check_performed=network.get("public_network_check_performed") is True,
                auth_presence_check_performed=auth.get("auth_presence_check_performed") is True,
            )
        )
        value["validation"] = validate_live_connector_preflight_result(value, generated_at=self.generated_at)
        return value


def live_connector_preflight_safety_flags(
    *,
    public_network_check_performed: bool,
    auth_presence_check_performed: bool,
) -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "public_network_check_performed": public_network_check_performed is True,
        "auth_presence_check_performed": auth_presence_check_performed is True,
        "authenticated_request_performed": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "signing_attempted": False,
        "signed_payload_generated": False,
        "wallet_connection_attempted": False,
        "wallet_spend_enabled": False,
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
        "wallet_enabled": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "wallet_signing_performed": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "order_cancellation_enabled": False,
        "real_order_cancelled": False,
        "balance_read_performed": False,
        "position_read_performed": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
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


def validate_live_connector_preflight_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != LIVE_CONNECTOR_PREFLIGHT_RESULT_CONTRACT:
        errors.append(f"contract_version must be {LIVE_CONNECTOR_PREFLIGHT_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append(f"execution_mode must be {EXECUTION_MODE}")
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
        "contract_version": LIVE_CONNECTOR_PREFLIGHT_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "live-connector-preflight-validation-056",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses) or (["live_connector_preflight_valid"] if valid else ["live_connector_preflight_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **live_connector_preflight_safety_flags(
            public_network_check_performed=value.get("public_network_check_performed") is True,
            auth_presence_check_performed=value.get("auth_presence_check_performed") is True,
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
