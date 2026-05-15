from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-073A-LOCAL-REAL-CHECK-RESULT-SNAPSHOT-PACK-NO-LIVE"
REQUIRED_BASE_HEAD = "f9e7b4de6ea2afdc110ee5a2387e375f88e46f92"

MODE = "local real-check result snapshot / ingestion pack / dry-run / no-live"
EXECUTION_MODE = "local_real_check_snapshot_073a"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

UNKNOWN_STATUS = "unknown"
MISSING_STATUS = "missing"
UNREADABLE_STATUS = "unreadable"
STATUS_BLOCKED = "local_real_check_snapshot_recorded_live_blocked"

SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C = "local_real_check_bundle_072c"
SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C = "clob_l2_auth_readonly_probe_067c"
SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C = "live_account_readonly_state_probe_070c"
SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A = "guarded_signer_diagnostic_smoke_069a"
SOURCE_PUBLIC_MARKET_TOKEN_DISCOVERY_071A = "public_market_token_discovery_071a"
SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D = "discovery_to_token_resolver_bridge_071d"
SOURCE_ORDER_PREP_PACKET_072A = "order_prep_packet_072a"
SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D = "first_live_order_final_blocker_reducer_072d"

SOURCE_SEQUENCE = (
    SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C,
    SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C,
    SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C,
    SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A,
    SOURCE_PUBLIC_MARKET_TOKEN_DISCOVERY_071A,
    SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D,
    SOURCE_ORDER_PREP_PACKET_072A,
    SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,
)

NORMALIZED_STATUS_FIELDS = (
    "l2_auth_status",
    "account_readonly_status",
    "signer_diagnostic_status",
    "public_discovery_status",
    "token_bridge_status",
    "order_prep_packet_status",
    "final_blocker_status",
)

SOURCE_LABELS = {
    SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C: "072C local real-check bundle",
    SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C: "067C CLOB L2 auth read-only probe",
    SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C: "070C live account read-only state probe",
    SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A: "069A guarded signer diagnostic smoke",
    SOURCE_PUBLIC_MARKET_TOKEN_DISCOVERY_071A: "071A public market/token discovery",
    SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D: "071D discovery-to-token resolver bridge",
    SOURCE_ORDER_PREP_PACKET_072A: "072A order prep packet",
    SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D: "072D first live order final blocker reducer",
}

SNAPSHOT_SOURCE_CONTRACT = "pmbot_local_real_check_snapshot_source_073a.v1"
SNAPSHOT_SOURCES_CONTRACT = "pmbot_local_real_check_snapshot_sources_073a.v1"
SNAPSHOT_NORMALIZED_STATUS_CONTRACT = "pmbot_local_real_check_snapshot_normalized_status_073a.v1"
SNAPSHOT_NEXT_ACTION_CONTRACT = "pmbot_local_real_check_snapshot_next_action_073a.v1"
SNAPSHOT_NEXT_ACTIONS_CONTRACT = "pmbot_local_real_check_snapshot_next_actions_073a.v1"
SNAPSHOT_SAFETY_CONTRACT = "pmbot_local_real_check_snapshot_safety_snapshot_073a.v1"
SNAPSHOT_LATEST_STATUS_CONTRACT = "pmbot_latest_local_real_check_snapshot_status_073a.v1"
SNAPSHOT_RESULT_CONTRACT = "pmbot_local_real_check_snapshot_073a_result.v1"
SNAPSHOT_VALIDATION_CONTRACT = "pmbot_local_real_check_snapshot_validation_073a.v1"

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "snapshot_executable_for_live",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "first_live_order_authorized",
    "first_live_order_attempted",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "real_order_submitted",
    "order_cancellation_enabled",
    "order_cancellation_attempted",
    "order_cancellation_performed",
    "order_cancelled",
    "real_order_cancelled",
    "order_payload_signing_enabled",
    "order_payload_signing_attempted",
    "order_payload_signed",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signed_order_generated",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "wallet_signing_performed",
    "signer_instantiated",
    "signing_enabled",
    "signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "authenticated_trading_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
    "network_access_performed",
    "external_api_calls_performed",
    "network_trading_call_performed",
    "post_put_patch_delete_attempted",
    "trading_endpoint_write_attempted",
    "private_key_read",
    "wallet_private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "api_secret_read",
    "auth_token_read",
    "passphrase_read",
    "credential_values_read",
    "credential_values_printed",
    "credential_values_stored",
    "credential_values_serialized",
    "environment_variables_read",
    "environment_secrets_read",
    "secret_files_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "raw_secret_values_printed",
    "raw_secret_values_persisted",
    "raw_source_payloads_embedded",
    "raw_account_values_emitted",
    "raw_order_rows_emitted",
    "account_values_emitted",
    "fill_values_emitted",
    "position_values_emitted",
    "pnl_values_emitted",
    "fake_data_generated",
    "fake_success_inferred",
    "fake_account_data_generated",
    "fake_order_data_generated",
    "fake_fill_data_generated",
    "fake_pnl_data_generated",
    "fake_token_data_generated",
    "fake_evidence_generated",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

FORBIDDEN_RAW_OUTPUT_KEYS = frozenset(
    {
        "private_key",
        "wallet_private_key",
        "seed_phrase",
        "mnemonic",
        "api_secret",
        "api_secret_value",
        "auth_token",
        "passphrase",
        "secret",
        "raw_secret",
        "raw_value",
        "signature",
        "signed_payload",
        "signed_order",
        "full_signed_payload",
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill",
        "fills",
        "fill_id",
        "fill_price",
        "filled_size",
        "position",
        "positions",
        "pnl",
        "profit",
        "realized_pnl",
        "unrealized_pnl",
        "token_id",
        "outcome_token_id",
        "selected_token_id",
        "target_token_id",
    }
)


def local_real_check_snapshot_safety_flags() -> dict[str, Any]:
    value: dict[str, Any] = {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "dry_run_only": True,
        "review_only": True,
        "snapshot_only": True,
        "ingestion_pack_only": True,
        "local_artifact_read_only": True,
        "read_only": True,
        "safe_summary_only": True,
        "non_executable": True,
        "no_network_calls": True,
        "no_env_secret_reads": True,
        "no_subchecks_run_by_default": True,
        "unknown_remains_unknown": True,
        "missing_remains_missing": True,
        "no_fake_success": True,
        "no_fake_evidence": True,
        "no_fake_account_order_fill_pnl_token_data": True,
        "redacted_output_only": True,
        "resolved_blocker_count": 0,
    }
    value.update({field: False for field in FORCED_FALSE_EXECUTION_FIELDS})
    value["resolved_blocker_count"] = 0
    return value


@dataclass(frozen=True)
class LocalRealCheckSnapshotSource:
    source_id: str
    label: str
    required: bool
    exists: bool
    parsed: bool
    status: str
    selected_path: str
    candidate_paths: tuple[str, ...]
    file_modified_at: str = ""
    contract_version_seen: str = ""
    load_error: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SNAPSHOT_SOURCE_CONTRACT
        value["task_id"] = TASK_ID
        value["source_id"] = clean_text(self.source_id)
        value["label"] = clean_text(self.label)
        value["required"] = self.required is True
        value["exists"] = self.exists is True
        value["parsed"] = self.parsed is True
        value["status"] = clean_text(self.status) or UNKNOWN_STATUS
        value["selected_path"] = clean_text(self.selected_path)
        value["candidate_paths"] = [clean_text(path) for path in self.candidate_paths if clean_text(path)]
        value["file_modified_at"] = clean_text(self.file_modified_at)
        value["contract_version_seen"] = clean_text(self.contract_version_seen)
        value["load_error"] = clean_text(self.load_error)
        value["raw_source_payload_embedded"] = False
        value["safe_for_snapshot"] = True
        value.update(local_real_check_snapshot_safety_flags())
        return value


@dataclass(frozen=True)
class LocalRealCheckSnapshotNormalizedStatus:
    market: str
    strategy: str
    status_fields: Mapping[str, str]
    status_sources: Mapping[str, Mapping[str, Any]]
    source_statuses: Mapping[str, str]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        fields = {clean_text(key): clean_text(value) or UNKNOWN_STATUS for key, value in self.status_fields.items()}
        value = {
            "contract_version": SNAPSHOT_NORMALIZED_STATUS_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "market": _market(self.market),
            "market_symbol": _market(self.market),
            "strategy": _strategy(self.strategy),
            "strategy_name": _strategy(self.strategy),
            "status_fields": fields,
            "status_sources": {clean_text(key): dict(row) for key, row in self.status_sources.items()},
            "source_statuses": {clean_text(key): clean_text(status) or UNKNOWN_STATUS for key, status in self.source_statuses.items()},
            "missing_status_count": sum(1 for status in fields.values() if status == MISSING_STATUS),
            "unknown_status_count": sum(1 for status in fields.values() if status == UNKNOWN_STATUS),
            "artifact_paths": dict(self.artifact_paths),
            "generated_at": self.generated_at,
        }
        for field_name in NORMALIZED_STATUS_FIELDS:
            value[field_name] = fields.get(field_name, UNKNOWN_STATUS)
        value.update(local_real_check_snapshot_safety_flags())
        return value


@dataclass(frozen=True)
class LocalRealCheckSnapshotNextAction:
    action_id: str
    source_id: str
    action: str
    reason: str
    status: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SNAPSHOT_NEXT_ACTION_CONTRACT,
            "task_id": TASK_ID,
            "action_id": clean_text(self.action_id),
            "source_id": clean_text(self.source_id),
            "action": clean_text(self.action),
            "reason": clean_text(self.reason),
            "status": clean_text(self.status) or STATUS_BLOCKED,
            "allowed_in_this_task": False,
            "requires_separate_operator_task": True,
            "must_not_include_secret_values": True,
            "must_not_execute_order": True,
            "generated_at": self.generated_at,
        }
        value.update(local_real_check_snapshot_safety_flags())
        return value


@dataclass(frozen=True)
class LocalRealCheckSnapshotLatestStatus:
    market: str
    strategy: str
    normalized_status: Mapping[str, Any]
    sources: Mapping[str, Any]
    next_actions: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    include_latest_artifacts: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        normalized = dict(self.normalized_status)
        sources_value = dict(self.sources)
        source_rows = dict(sources_value.get("sources", {}))
        value = {
            "contract_version": SNAPSHOT_LATEST_STATUS_CONTRACT,
            "task_id": TASK_ID,
            "required_base_head": REQUIRED_BASE_HEAD,
            "status": STATUS_BLOCKED,
            "market": _market(self.market),
            "market_symbol": _market(self.market),
            "strategy": _strategy(self.strategy),
            "strategy_name": _strategy(self.strategy),
            "include_latest_artifacts": self.include_latest_artifacts is True,
            "source_count": len(source_rows),
            "source_present_count": sum(1 for row in source_rows.values() if dict(row).get("exists") is True),
            "source_parsed_count": sum(1 for row in source_rows.values() if dict(row).get("parsed") is True),
            "source_missing_count": sum(1 for row in source_rows.values() if dict(row).get("exists") is not True),
            "source_unreadable_count": sum(1 for row in source_rows.values() if dict(row).get("exists") is True and dict(row).get("parsed") is not True),
            "normalized_status": normalized,
            "next_action_count": int(dict(self.next_actions).get("next_action_count", 0) or 0),
            "artifact_path": clean_text(self.artifact_paths.get("result")),
            "latest_status_path": clean_text(self.artifact_paths.get("latest_status")),
            "sources_path": clean_text(self.artifact_paths.get("sources")),
            "normalized_status_path": clean_text(self.artifact_paths.get("normalized_status")),
            "next_actions_path": clean_text(self.artifact_paths.get("next_actions")),
            "safety_snapshot_path": clean_text(self.artifact_paths.get("safety_snapshot")),
            "operator_summary_path": clean_text(self.artifact_paths.get("operator_summary")),
            "operator_summary": (
                "073A recorded a redacted local result snapshot from known artifacts only; "
                "live execution remains blocked and unknown or missing evidence was not promoted to success."
            ),
            "generated_at": self.generated_at,
        }
        for field_name in NORMALIZED_STATUS_FIELDS:
            value[field_name] = clean_text(normalized.get(field_name)) or UNKNOWN_STATUS
        value.update(local_real_check_snapshot_safety_flags())
        return value


@dataclass(frozen=True)
class LocalRealCheckSnapshotResult:
    market: str
    strategy: str
    sources: Mapping[str, Any]
    normalized_status: Mapping[str, Any]
    next_actions: Mapping[str, Any]
    safety_snapshot: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    include_latest_artifacts: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        normalized = dict(self.normalized_status)
        value = {
            "contract_version": SNAPSHOT_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "required_base_head": REQUIRED_BASE_HEAD,
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market),
            "market_symbol": _market(self.market),
            "strategy": _strategy(self.strategy),
            "strategy_name": _strategy(self.strategy),
            "dry_run": True,
            "snapshot_only": True,
            "include_latest_artifacts": self.include_latest_artifacts is True,
            "sources": dict(self.sources),
            "normalized_status": normalized,
            "next_actions": dict(self.next_actions),
            "safety_snapshot": dict(self.safety_snapshot),
            "latest_status": dict(self.latest_status),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": (
                "Local real-check snapshot 073A is a redacted ingestion pack for existing local artifacts only. "
                "It does not run live checks, infer success from missing evidence, or produce executable live output."
            ),
            "generated_at": self.generated_at,
        }
        for field_name in NORMALIZED_STATUS_FIELDS:
            value[field_name] = clean_text(normalized.get(field_name)) or UNKNOWN_STATUS
        value.update(local_real_check_snapshot_safety_flags())
        value["validation"] = validate_local_real_check_snapshot_result(value, generated_at=self.generated_at)
        return value


def build_sources_artifact(
    sources: Mapping[str, Mapping[str, Any]],
    *,
    artifact_root: str,
    include_latest_artifacts: bool,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    source_rows = {clean_text(key): dict(row) for key, row in sources.items()}
    value = {
        "contract_version": SNAPSHOT_SOURCES_CONTRACT,
        "task_id": TASK_ID,
        "status": "snapshot_sources_recorded",
        "artifact_root": clean_text(artifact_root),
        "include_latest_artifacts": include_latest_artifacts is True,
        "source_sequence": list(SOURCE_SEQUENCE),
        "sources": source_rows,
        "source_count": len(source_rows),
        "source_present_count": sum(1 for row in source_rows.values() if row.get("exists") is True),
        "source_missing_count": sum(1 for row in source_rows.values() if row.get("exists") is not True),
        "source_parsed_count": sum(1 for row in source_rows.values() if row.get("parsed") is True),
        "raw_source_payloads_embedded": False,
        "generated_at": generated_at,
    }
    value.update(local_real_check_snapshot_safety_flags())
    return value


def build_next_actions_artifact(
    actions: Sequence[Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    rows = [dict(row) for row in actions]
    value = {
        "contract_version": SNAPSHOT_NEXT_ACTIONS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "next_actions": rows,
        "next_action_count": len(rows),
        "all_actions_require_separate_operator_task": True,
        "no_action_allowed_to_execute": True,
        "generated_at": generated_at,
    }
    value.update(local_real_check_snapshot_safety_flags())
    return value


def build_safety_snapshot(
    *,
    market: str,
    strategy: str,
    include_latest_artifacts: bool,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": SNAPSHOT_SAFETY_CONTRACT,
        "task_id": TASK_ID,
        "status": "local_real_check_snapshot_safety_active",
        "market": _market(market),
        "market_symbol": _market(market),
        "strategy": _strategy(strategy),
        "strategy_name": _strategy(strategy),
        "include_latest_artifacts": include_latest_artifacts is True,
        "allowed_inputs": [
            "known PMBOT local JSON artifacts from 067C, 069A, 070C, 071A, 071D, 072A, 072C, and 072D",
            "latest status artifacts when include_latest_artifacts=true",
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
            "subcheck execution by default",
            "wallet connection",
            "order payload signing",
            "order submission",
            "order cancellation",
            "authenticated trading write calls",
            "live execution enablement",
        ],
        "raw_source_payloads_embedded": False,
        "generated_at": generated_at,
    }
    value.update(local_real_check_snapshot_safety_flags())
    return value


def validate_local_real_check_snapshot_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != SNAPSHOT_RESULT_CONTRACT:
        errors.append(f"contract_version must be {SNAPSHOT_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append(f"execution_mode must be {EXECUTION_MODE}")
        statuses.append("invalid_execution_mode")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_not_false")
    if value.get("snapshot_executable_for_live") is not False:
        errors.append("snapshot_executable_for_live must be false")
        statuses.append("snapshot_executable_for_live_not_false")
    normalized = dict(value.get("normalized_status", {}))
    for field_name in NORMALIZED_STATUS_FIELDS:
        if not clean_text(value.get(field_name)) and not clean_text(normalized.get(field_name)):
            errors.append(f"{field_name} must be present")
            statuses.append("normalized_status_missing")
    source_rows = dict(dict(value.get("sources", {})).get("sources", {}))
    if set(source_rows) and tuple(source_rows) != SOURCE_SEQUENCE:
        errors.append("sources must preserve the required 073A source sequence")
        statuses.append("source_sequence_invalid")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must remain 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in FORBIDDEN_RAW_OUTPUT_KEYS:
            errors.append(f"{path}.{key} is forbidden in 073A snapshot output")
            statuses.append("forbidden_raw_output_field_detected")
    valid = not errors
    return {
        "contract_version": SNAPSHOT_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "validation_id": _stable_id(
            "local-real-check-snapshot-validation-073a",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses) or (["local_real_check_snapshot_valid"] if valid else ["local_real_check_snapshot_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **local_real_check_snapshot_safety_flags(),
    }


def _market(value: Any) -> str:
    return clean_text(value).upper() or DEFAULT_MARKET


def _strategy(value: Any) -> str:
    return clean_text(value) or DEFAULT_STRATEGY


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
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
