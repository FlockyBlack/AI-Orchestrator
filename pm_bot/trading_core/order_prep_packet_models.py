from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-072A-ORDER-PREP-PACKET-FROM-DISCOVERY-NO-SUBMIT"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

EXECUTION_MODE = "local_artifact_read_only_preflight"
MODE = "order prep packet / dry-run / no-submit"

ORDER_PREP_PACKET_RESULT_CONTRACT = "pmbot_order_prep_packet_072a_result.v1"
ORDER_PREP_PACKET_LATEST_STATUS_CONTRACT = "pmbot_latest_order_prep_packet_status_072a.v1"
ORDER_PREP_PACKET_SOURCES_CONTRACT = "pmbot_order_prep_packet_sources_072a.v1"
ORDER_PREP_PACKET_OPERATOR_REVIEW_CONTRACT = "pmbot_order_prep_packet_operator_review_072a.v1"
ORDER_PREP_PACKET_BLOCKERS_CONTRACT = "pmbot_order_prep_packet_blockers_072a.v1"
ORDER_PREP_PACKET_SAFETY_SNAPSHOT_CONTRACT = "pmbot_order_prep_packet_safety_snapshot_072a.v1"
ORDER_PREP_PACKET_VALIDATION_CONTRACT = "pmbot_order_prep_packet_validation_072a.v1"

STATUS_REVIEW_READY = "order_prep_packet_ready_for_operator_review_non_executable"
STATUS_BLOCKED = "blocked_order_prep_packet_not_ready"

SOURCE_PUBLIC_DISCOVERY_071A = "public_market_token_discovery_071a"
SOURCE_DISCOVERY_TO_TOKEN_071D = "discovery_to_token_resolver_bridge_071d"
SOURCE_FIRST_ORDER_TOKEN_070B = "first_order_market_token_resolver_070b"
SOURCE_ACCOUNT_PROBE_070C = "live_account_readonly_state_probe_070c"
SOURCE_LIVE_READONLY_071B = "live_readonly_status_aggregator_071b"
SOURCE_SIGNER_DIAGNOSTIC_069A = "guarded_signer_diagnostic_smoke_069a"
SOURCE_APPROVAL_CONTRACT_065D = "first_live_order_approval_contract_065d"
SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A = "signed_order_payload_dry_run_070a"

SOURCE_IDS = (
    SOURCE_PUBLIC_DISCOVERY_071A,
    SOURCE_DISCOVERY_TO_TOKEN_071D,
    SOURCE_FIRST_ORDER_TOKEN_070B,
    SOURCE_ACCOUNT_PROBE_070C,
    SOURCE_LIVE_READONLY_071B,
    SOURCE_SIGNER_DIAGNOSTIC_069A,
    SOURCE_APPROVAL_CONTRACT_065D,
    SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A,
)

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "order_prep_packet_executable",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "real_order_submitted",
    "order_cancellation_enabled",
    "order_cancellation_attempted",
    "order_cancellation_performed",
    "real_order_cancelled",
    "trading_endpoint_write_attempted",
    "authenticated_trading_call_performed",
    "authenticated_request_performed",
    "authenticated_endpoint_enabled",
    "authenticated_polymarket_enabled",
    "network_trading_call_performed",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "signing_enabled",
    "signing_attempted",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "full_signed_payload_emitted",
    "raw_signed_payload_emitted",
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
    "environment_secrets_read",
    "environment_variables_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "balance_values_emitted",
    "allowance_values_emitted",
    "raw_account_values_emitted",
    "raw_order_rows_emitted",
    "fill_values_emitted",
    "position_values_emitted",
    "pnl_values_emitted",
    "fake_balances_emitted",
    "fake_orders_emitted",
    "fake_fills_emitted",
    "fake_positions_emitted",
    "fake_pnl_emitted",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "canary_executable_now",
    "live_trading_enabled",
    "token_id_generated",
    "fake_token_id_generated",
    "market_id_generated",
    "fake_market_id_generated",
    "outcome_resolution_invented",
)

FORBIDDEN_OUTPUT_MARKERS = (
    "private-key-marker-072a",
    "api-secret-marker-072a",
    "passphrase-marker-072a",
    "full-signed-payload-marker-072a",
    "fake-order-id-072a",
    "fake-tx-hash-072a",
    "fake-fill-072a",
    "fake-pnl-072a",
)


@dataclass(frozen=True)
class OrderPrepPacketConfig:
    market: str
    strategy: str
    dry_run: bool
    artifact_root: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = "pmbot_order_prep_packet_config_072a.v1"
        value["task_id"] = TASK_ID
        value["market"] = _market(self.market)
        value["market_symbol"] = _market(self.market)
        value["strategy"] = _strategy(self.strategy)
        value["strategy_name"] = _strategy(self.strategy)
        value["dry_run"] = self.dry_run is True
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value.update(order_prep_packet_safety_flags())
        return value


@dataclass(frozen=True)
class OrderPrepPacketSource:
    source_id: str
    label: str
    available: bool
    selected_path: str
    status: str
    contract_version_seen: str
    load_error: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = "pmbot_order_prep_packet_source_072a.v1"
        value["task_id"] = TASK_ID
        value["safe_summary_only"] = True
        value.update(order_prep_packet_safety_flags())
        return value


@dataclass(frozen=True)
class OrderPrepPacketReadinessItem:
    readiness_id: str
    status: str
    ready: bool
    source_id: str
    source_available: bool
    source_path: str
    evidence_key: str
    blocker_id: str
    reason: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = "pmbot_order_prep_packet_readiness_item_072a.v1"
        value["task_id"] = TASK_ID
        value["blocks_packet"] = self.ready is not True
        value.update(order_prep_packet_safety_flags())
        return value


def order_prep_packet_safety_flags() -> dict[str, Any]:
    return {
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "paper_only": True,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "local_artifact_only": True,
        "local_artifact_read_only": True,
        "read_only": True,
        "safe_summary_only": True,
        "non_executable": True,
        "allowed_for_live": False,
        "order_prep_packet_executable": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "real_order_submitted": False,
        "order_cancellation_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
        "real_order_cancelled": False,
        "trading_endpoint_write_attempted": False,
        "authenticated_trading_call_performed": False,
        "authenticated_request_performed": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_polymarket_enabled": False,
        "network_trading_call_performed": False,
        "network_trading_calls_performed": 0,
        "network_access_performed": False,
        "public_network_call_performed": False,
        "polymarket_api_calls_performed": 0,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "signed_order_generation_enabled": False,
        "signed_order_generation_attempted": False,
        "full_signed_payload_emitted": False,
        "raw_signed_payload_emitted": False,
        "private_key_read": False,
        "wallet_private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "api_secret_read": False,
        "auth_token_read": False,
        "passphrase_read": False,
        "credential_values_read": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "credential_values_serialized": False,
        "environment_secrets_read": False,
        "environment_variables_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "balance_values_emitted": False,
        "allowance_values_emitted": False,
        "raw_account_values_emitted": False,
        "raw_order_rows_emitted": False,
        "fill_values_emitted": False,
        "position_values_emitted": False,
        "pnl_values_emitted": False,
        "fake_balances_emitted": False,
        "fake_orders_emitted": False,
        "fake_fills_emitted": False,
        "fake_positions_emitted": False,
        "fake_pnl_emitted": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_trading_enabled": False,
        "token_id_generated": False,
        "fake_token_id_generated": False,
        "market_id_generated": False,
        "fake_market_id_generated": False,
        "outcome_resolution_invented": False,
        "resolved_blocker_count": 0,
    }


def build_blocker(
    blocker_id: str,
    category: str,
    reason: str,
    *,
    source_id: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_order_prep_packet_blocker_072a.v1",
        "task_id": TASK_ID,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "source_id": clean_text(source_id),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_packet": True,
        "blocks_live_execution": True,
        "generated_at": generated_at,
    }
    value.update(order_prep_packet_safety_flags())
    return value


def build_safety_snapshot(*, status: str, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    value = {
        "contract_version": ORDER_PREP_PACKET_SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "safety_statement": (
            "072A reads local readiness artifacts and emits a non-executable operator review packet only; "
            "it does not submit, cancel, sign order payloads by default, connect a wallet, enable live trading, "
            "or make authenticated trading write calls."
        ),
        "generated_at": generated_at,
    }
    value.update(order_prep_packet_safety_flags())
    return value


def validate_order_prep_packet_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != ORDER_PREP_PACKET_RESULT_CONTRACT:
        errors.append(f"contract_version must be {ORDER_PREP_PACKET_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("order_prep_packet_executable") is not False:
        errors.append("order_prep_packet_executable must be false")
        statuses.append("executable_packet_detected")
    if value.get("order_submission_enabled") is not False:
        errors.append("order_submission_enabled must be false")
        statuses.append("order_submission_enabled_detected")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_detected")
    if value.get("operator_selection_required") is True and clean_text(value.get("selected_token_id")):
        errors.append("operator_selection_required must not include a selected token_id")
        statuses.append("selection_required_with_token_detected")
    if value.get("selected_token_id_present") is False and value.get("packet_blocked") is not True:
        errors.append("missing selected token_id must keep packet_blocked=true")
        statuses.append("missing_token_not_blocked")
    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("resolved_blocker_detected")
    rendered = repr(value).lower()
    for marker in FORBIDDEN_OUTPUT_MARKERS:
        if marker.lower() in rendered:
            errors.append(f"forbidden marker emitted: {marker}")
            statuses.append("forbidden_marker_detected")
    valid = not errors
    return {
        "contract_version": ORDER_PREP_PACKET_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses) or (["order_prep_packet_valid"] if valid else ["order_prep_packet_blocked"]),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **order_prep_packet_safety_flags(),
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
