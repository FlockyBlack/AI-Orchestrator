from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-071B-LIVE-READONLY-PROBE-RESULT-UNIFICATION-NO-ORDERS"

MODE = "local live read-only status aggregation / no orders"
EXECUTION_MODE = "live_readonly_status_aggregator"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"
UNKNOWN_STATUS = "unknown"

SOURCE_067C = "clob_l2_auth_readonly_probe_067c"
SOURCE_070C = "live_account_readonly_state_probe_070c"
SOURCE_067E = "telegram_wallet_auth_status_067e"

STATUS_FIELDS = (
    "l2_auth_status",
    "open_orders_status",
    "balance_status",
    "allowance_status",
    "wallet_address_status",
    "funder_status",
    "signature_type_status",
)

SOURCE_INDEX_CONTRACT = "pmbot_live_readonly_status_source_index_071b.v1"
SOURCE_CONTRACT = "pmbot_live_readonly_status_source_071b.v1"
STATUS_FIELD_CONTRACT = "pmbot_live_readonly_status_field_071b.v1"
LATEST_STATUS_CONTRACT = "pmbot_latest_live_readonly_status_071b.v1"
RESULT_CONTRACT = "pmbot_live_readonly_status_aggregator_071b_result.v1"
SAFETY_SNAPSHOT_CONTRACT = "pmbot_live_readonly_status_safety_snapshot_071b.v1"
VALIDATION_CONTRACT = "pmbot_live_readonly_status_validation_071b.v1"

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
    "wallet_connection_enabled",
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
    "environment_variables_read",
    "environment_secrets_read",
    "secrets_read",
    "credential_values_read",
    "credential_values_serialized",
    "credential_values_printed",
    "credential_values_stored",
    "credential_values_hashed",
    "credential_values_transformed",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "raw_credential_values_persisted",
    "secrets_printed",
    "secrets_persisted",
    "raw_secret_values_printed",
    "raw_secret_values_persisted",
    "network_access_performed",
    "external_api_calls_performed",
    "authenticated_endpoint_call_performed",
    "authenticated_request_performed",
    "real_authenticated_get_performed",
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
    "fake_balance_added",
    "fake_pnl_added",
    "fake_trades_added",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)


def live_readonly_status_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "dry_run_only": True,
        "review_only": True,
        "local_artifact_read_only": True,
        "schema_model_adapter_only": True,
        "no_network_calls_by_default": True,
        "unknown_means_unknown": True,
        "no_fake_data": True,
        "no_fake_balances_pnl_orders": True,
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
        "wallet_connection_enabled": False,
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
        "environment_variables_read": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "credential_values_read": False,
        "credential_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "credential_values_hashed": False,
        "credential_values_transformed": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "raw_credential_values_persisted": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_secret_values_printed": False,
        "raw_secret_values_persisted": False,
        "network_access_performed": False,
        "external_api_calls_performed": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "real_authenticated_get_performed": False,
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
        "fake_balance_added": False,
        "fake_pnl_added": False,
        "fake_trades_added": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


@dataclass(frozen=True)
class LiveReadonlyStatusSource:
    source_id: str
    label: str
    source_kind: str
    required: bool
    available: bool
    selected_path: str
    candidate_paths: tuple[str, ...]
    status: str
    contract_version_seen: str = ""
    load_error: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SOURCE_CONTRACT
        value["task_id"] = TASK_ID
        value["source_id"] = clean_text(self.source_id)
        value["label"] = clean_text(self.label)
        value["source_kind"] = clean_text(self.source_kind)
        value["required"] = self.required is True
        value["available"] = self.available is True
        value["selected_path"] = clean_text(self.selected_path)
        value["candidate_paths"] = [clean_text(path) for path in self.candidate_paths if clean_text(path)]
        value["status"] = clean_text(self.status) or UNKNOWN_STATUS
        value["contract_version_seen"] = clean_text(self.contract_version_seen)
        value["load_error"] = clean_text(self.load_error)
        value["raw_source_payload_embedded"] = False
        value["safe_for_artifacts"] = True
        value.update(live_readonly_status_safety_flags())
        return value


@dataclass(frozen=True)
class LiveReadonlyStatusField:
    field_name: str
    status: str
    source_id: str
    source_path: str
    evidence_key: str
    note: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = STATUS_FIELD_CONTRACT
        value["task_id"] = TASK_ID
        value["field_name"] = clean_text(self.field_name)
        value["status"] = clean_text(self.status) or UNKNOWN_STATUS
        value["source_id"] = clean_text(self.source_id) or "none"
        value["source_path"] = clean_text(self.source_path)
        value["evidence_key"] = clean_text(self.evidence_key)
        value["note"] = clean_text(self.note)
        value["raw_value_emitted"] = False
        value["numeric_account_value_emitted"] = False
        value["safe_for_artifacts"] = True
        value.update(live_readonly_status_safety_flags())
        return value


@dataclass(frozen=True)
class LiveReadonlyLatestStatus:
    market: str
    strategy: str
    status: str
    fields: Mapping[str, Mapping[str, Any]]
    sources: Mapping[str, Mapping[str, Any]]
    source_paths: Mapping[str, str]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        fields = {clean_text(key): dict(value) for key, value in self.fields.items()}
        value = {
            "contract_version": LATEST_STATUS_CONTRACT,
            "task_id": TASK_ID,
            "market": clean_text(self.market).upper() or DEFAULT_MARKET,
            "strategy": clean_text(self.strategy) or DEFAULT_STRATEGY,
            "status": clean_text(self.status) or "live_readonly_status_aggregated",
            "fields": fields,
            "sources": {clean_text(key): dict(row) for key, row in self.sources.items()},
            "source_paths": {clean_text(key): clean_text(path) for key, path in self.source_paths.items()},
            "artifact_paths": dict(self.artifact_paths),
            "source_available_count": sum(1 for row in self.sources.values() if row.get("available") is True),
            "unknown_status_count": sum(
                1 for field in fields.values() if field.get("status") == UNKNOWN_STATUS
            ),
            "l2_auth_status": _field_status(fields, "l2_auth_status"),
            "open_orders_status": _field_status(fields, "open_orders_status"),
            "balance_status": _field_status(fields, "balance_status"),
            "allowance_status": _field_status(fields, "allowance_status"),
            "wallet_address_status": _field_status(fields, "wallet_address_status"),
            "funder_status": _field_status(fields, "funder_status"),
            "signature_type_status": _field_status(fields, "signature_type_status"),
            "generated_at": self.generated_at,
        }
        value.update(live_readonly_status_safety_flags())
        value["validation"] = validate_live_readonly_latest_status(value, generated_at=self.generated_at)
        return value


@dataclass(frozen=True)
class LiveReadonlyStatusAggregatorResult:
    market: str
    strategy: str
    latest_status: Mapping[str, Any]
    sources: Mapping[str, Any]
    safety_snapshot: Mapping[str, Any]
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
            "status": clean_text(latest_status.get("status")) or "live_readonly_status_aggregated",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "dry_run": True,
            "latest_status": latest_status,
            "sources": dict(self.sources),
            "safety_snapshot": dict(self.safety_snapshot),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": clean_text(self.operator_summary),
            "generated_at": self.generated_at,
        }
        for field_name in STATUS_FIELDS:
            value[field_name] = latest_status.get(field_name, UNKNOWN_STATUS)
        value.update(live_readonly_status_safety_flags())
        value["validation"] = validate_live_readonly_latest_status(latest_status, generated_at=self.generated_at)
        return value


def build_live_readonly_status_safety_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    value = {
        "contract_version": SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "status": "safe_local_readonly_aggregation",
        "allowed_inputs": [
            "067C latest CLOB L2 auth read-only probe artifact",
            "070C latest live account read-only state probe artifact, when present",
            "067E latest Telegram wallet/auth status artifact, when present",
        ],
        "forbidden_inputs": [
            "raw private keys",
            "raw API secrets",
            "raw passphrases",
            "wallet files",
            "browser profiles",
            "credential stores",
            "environment secret values",
        ],
        "forbidden_actions": [
            "network calls",
            "wallet connection",
            "signing",
            "order submission",
            "order cancellation",
            "authenticated write calls",
            "live execution enablement",
        ],
        "raw_source_payloads_embedded": False,
        "generated_at": generated_at,
    }
    value.update(live_readonly_status_safety_flags())
    return value


def build_source_index(
    sources: Mapping[str, Mapping[str, Any]],
    *,
    artifact_root: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    source_rows = {clean_text(key): dict(value) for key, value in sources.items()}
    value = {
        "contract_version": SOURCE_INDEX_CONTRACT,
        "task_id": TASK_ID,
        "status": "sources_indexed",
        "artifact_root": clean_text(artifact_root),
        "sources": source_rows,
        "source_count": len(source_rows),
        "source_available_count": sum(1 for row in source_rows.values() if row.get("available") is True),
        "raw_source_payloads_embedded": False,
        "generated_at": generated_at,
    }
    value.update(live_readonly_status_safety_flags())
    return value


def validate_live_readonly_latest_status(
    status: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(status or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != LATEST_STATUS_CONTRACT:
        errors.append(f"contract_version must be {LATEST_STATUS_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must match live_readonly_status_aggregator")
        statuses.append("invalid_execution_mode")
    for field_name in STATUS_FIELDS:
        if not clean_text(value.get(field_name)):
            errors.append(f"{field_name} must be present")
            statuses.append("missing_status_field")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if field == "resolved_blocker_count":
            continue
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS:
            if key == "resolved_blocker_count":
                if nested != 0:
                    errors.append(f"{path}.{key} must be 0")
                    statuses.append("nested_resolved_blocker_detected")
            elif nested is not False:
                errors.append(f"{path}.{key} must be false")
                statuses.append("nested_unsafe_execution_flag_detected")
    valid = not errors
    return {
        "contract_version": VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "live-readonly-status-validation-071b",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses) or (["live_readonly_status_valid"] if valid else ["live_readonly_status_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **live_readonly_status_safety_flags(),
    }


def _field_status(fields: Mapping[str, Mapping[str, Any]], field_name: str) -> str:
    return clean_text(dict(fields.get(field_name, {})).get("status")) or UNKNOWN_STATUS


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
