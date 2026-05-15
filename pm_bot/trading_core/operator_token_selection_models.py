from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-073B-OPERATOR-TOKEN-SELECTION-PACKET-NO-TRADING"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

EXECUTION_MODE = "local_artifact_read_only_preflight"
MODE = "operator token selection packet / dry-run / no-trading"

OPERATOR_TOKEN_SELECTION_CONFIG_CONTRACT = "pmbot_operator_token_selection_config_073b.v1"
OPERATOR_TOKEN_SELECTION_CANDIDATE_CONTRACT = "pmbot_operator_token_selection_candidate_073b.v1"
OPERATOR_TOKEN_SELECTION_PACKET_CONTRACT = "pmbot_operator_token_selection_packet_073b.v1"
OPERATOR_TOKEN_SELECTION_RESULT_CONTRACT = "pmbot_operator_token_selection_packet_073b_result.v1"
OPERATOR_TOKEN_SELECTION_LATEST_STATUS_CONTRACT = "pmbot_latest_operator_token_selection_status_073b.v1"
OPERATOR_TOKEN_SELECTION_CANDIDATES_CONTRACT = "pmbot_operator_token_selection_candidates_073b.v1"
OPERATOR_TOKEN_SELECTION_SAFETY_SNAPSHOT_CONTRACT = "pmbot_operator_token_selection_safety_snapshot_073b.v1"
OPERATOR_TOKEN_SELECTION_VALIDATION_CONTRACT = "pmbot_operator_token_selection_validation_073b.v1"

STATUS_NO_CANDIDATES = "no_candidates"
STATUS_SELECTION_REQUIRED = "selection_required"
STATUS_SELECTED_SOURCE_BACKED = "selected_source_backed_candidate"
STATUS_SELECTED_OPERATOR_UNVERIFIED = "selected_operator_provided_unverified"
STATUS_INVALID_SELECTION = "invalid_selection"

VALID_STATUSES = {
    STATUS_NO_CANDIDATES,
    STATUS_SELECTION_REQUIRED,
    STATUS_SELECTED_SOURCE_BACKED,
    STATUS_SELECTED_OPERATOR_UNVERIFIED,
    STATUS_INVALID_SELECTION,
}

SOURCE_PUBLIC_DISCOVERY_071A = "public_market_token_discovery_071a"
SOURCE_DISCOVERY_TO_TOKEN_071D = "discovery_to_token_resolver_bridge_071d"
SOURCE_IDS = (SOURCE_PUBLIC_DISCOVERY_071A, SOURCE_DISCOVERY_TO_TOKEN_071D)

FORBIDDEN_TOKEN_MARKERS = (
    "fake",
    "fixture",
    "placeholder",
    "sample",
    "test-token",
    "mock",
    "demo-token",
)

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "token_selection_executable",
    "token_selection_executed",
    "auto_selected_for_live",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "canary_executable_now",
    "operator_approved_for_live",
    "order_generation_enabled",
    "order_generation_attempted",
    "order_payload_generated",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signing_enabled",
    "signing_attempted",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
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
    "authenticated_polymarket_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
    "network_trading_call_performed",
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
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "live_trading_enabled",
    "token_id_generated",
    "fake_token_id_generated",
    "token_id_generation_enabled",
    "fake_token_ids_allowed",
    "market_id_generated",
    "fake_market_id_generated",
    "outcome_resolution_invented",
)

FORBIDDEN_VALUE_FIELD_NAMES = frozenset(
    {
        "private_key",
        "wallet_private_key",
        "seed_phrase",
        "mnemonic",
        "api_secret",
        "auth_token",
        "passphrase",
        "secret",
        "raw_value",
        "signature",
        "signed_payload",
        "signed_order",
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill_id",
        "fill_price",
        "filled_size",
        "execution_status",
        "balance",
        "balances",
        "position",
        "positions",
        "pnl",
        "realized_pnl",
        "unrealized_pnl",
    }
)


@dataclass(frozen=True)
class OperatorTokenSelectionConfig:
    market: str
    strategy: str
    dry_run: bool
    artifact_root: str
    discovery_result_path: str
    bridge_result_path: str
    candidate_index: str
    token_id_provided: bool
    market_slug_provided: bool
    condition_id_provided: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_TOKEN_SELECTION_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = _market(self.market)
        value["market_symbol"] = _market(self.market)
        value["strategy"] = _strategy(self.strategy)
        value["strategy_name"] = _strategy(self.strategy)
        value["dry_run"] = self.dry_run is True
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value.update(operator_token_selection_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorTokenSelectionCandidate:
    candidate_index: int
    display_index: int
    candidate_id: str
    source_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    bridge_candidate_id: str
    source_token_candidate_id: str
    market_candidate_id: str
    market_id: str
    market_slug: str
    condition_id: str
    question: str
    outcome_name: str
    outcome_index: int
    token_id: str
    token_id_format_status: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        token_id_text = clean_text(self.token_id)
        value = asdict(self)
        value["contract_version"] = OPERATOR_TOKEN_SELECTION_CANDIDATE_CONTRACT
        value["task_id"] = TASK_ID
        value["source_ids"] = [clean_text(item) for item in self.source_ids if clean_text(item)]
        value["source_paths"] = [clean_text(item) for item in self.source_paths if clean_text(item)]
        value["source_backed"] = True
        value["token_id_source_backed"] = True
        value["token_id_present"] = bool(token_id_text)
        value["token_id_format_valid"] = clean_text(self.token_id_format_status) == "valid"
        value["token_id_generated"] = False
        value["fake_token_id_generated"] = False
        value["token_id_is_fixture_or_placeholder"] = looks_like_placeholder_token_id(token_id_text)
        value["operator_selectable"] = value["token_id_format_valid"] is True
        value.update(operator_token_selection_safety_flags())
        return value


def operator_token_selection_safety_flags() -> dict[str, Any]:
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
        "public_data_only": True,
        "safe_summary_only": True,
        "non_executable": True,
        "allowed_for_live": False,
        "token_selection_executable": False,
        "token_selection_executed": False,
        "auto_selected_for_live": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "operator_approved_for_live": False,
        "order_generation_enabled": False,
        "order_generation_attempted": False,
        "order_payload_generated": False,
        "signed_payload_generated": False,
        "signed_order_payload_generated": False,
        "signed_order_generation_enabled": False,
        "signed_order_generation_attempted": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
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
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "authenticated_trading_call_performed": False,
        "network_trading_call_performed": False,
        "network_trading_calls_performed": 0,
        "network_access_performed": False,
        "public_network_call_performed": False,
        "polymarket_api_calls_performed": 0,
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
        "environment_variables_read": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "live_trading_enabled": False,
        "token_id_generated": False,
        "fake_token_id_generated": False,
        "token_id_generation_enabled": False,
        "fake_token_ids_allowed": False,
        "market_id_generated": False,
        "fake_market_id_generated": False,
        "outcome_resolution_invented": False,
        "resolved_blocker_count": 0,
    }


def build_safety_snapshot(*, status: str, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    value = {
        "contract_version": OPERATOR_TOKEN_SELECTION_SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "safety_statement": (
            "073B reads local public discovery and bridge artifacts only and emits a non-executable "
            "operator token selection packet. It never invents token IDs, generates orders, signs, submits, "
            "cancels, connects a wallet, reads secrets, or performs authenticated trading calls."
        ),
        "generated_at": generated_at,
    }
    value.update(operator_token_selection_safety_flags())
    return value


def validate_operator_token_selection_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    packet = dict(value.get("packet", {}))
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(value.get("status"))
    selected_token_id = clean_text(value.get("selected_token_id"))

    if value.get("contract_version") != OPERATOR_TOKEN_SELECTION_RESULT_CONTRACT:
        errors.append(f"contract_version must be {OPERATOR_TOKEN_SELECTION_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if packet.get("contract_version") != OPERATOR_TOKEN_SELECTION_PACKET_CONTRACT:
        errors.append(f"packet.contract_version must be {OPERATOR_TOKEN_SELECTION_PACKET_CONTRACT}")
        statuses.append("invalid_packet_contract")
    if status not in VALID_STATUSES:
        errors.append("status must be one of the 073B operator token selection statuses")
        statuses.append("invalid_status")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_detected")
    if value.get("token_selection_executable") is not False:
        errors.append("token_selection_executable must be false")
        statuses.append("executable_selection_detected")
    if value.get("token_id_generated") is not False:
        errors.append("token_id_generated must be false")
        statuses.append("token_id_generation_detected")
    if value.get("fake_token_id_generated") is not False:
        errors.append("fake_token_id_generated must be false")
        statuses.append("fake_token_id_generation_detected")
    if status == STATUS_NO_CANDIDATES and int(value.get("source_backed_candidate_count", 0) or 0) != 0:
        errors.append("no_candidates status requires zero source-backed candidates")
        statuses.append("no_candidates_count_mismatch")
    if status == STATUS_SELECTION_REQUIRED and selected_token_id:
        errors.append("selection_required status must not include selected_token_id")
        statuses.append("selection_required_selected_token_detected")
    if status == STATUS_SELECTION_REQUIRED and int(value.get("source_backed_candidate_count", 0) or 0) <= 0:
        errors.append("selection_required status requires at least one source-backed candidate")
        statuses.append("selection_required_missing_candidates")
    if status == STATUS_SELECTED_SOURCE_BACKED and value.get("selected_token_source_backed") is not True:
        errors.append("selected_source_backed_candidate requires selected_token_source_backed=true")
        statuses.append("selected_source_not_source_backed")
    if status == STATUS_SELECTED_SOURCE_BACKED and not selected_token_id:
        errors.append("selected_source_backed_candidate requires selected_token_id")
        statuses.append("selected_source_missing_token")
    if status == STATUS_SELECTED_OPERATOR_UNVERIFIED:
        if value.get("operator_provided") is not True:
            errors.append("selected_operator_provided_unverified requires operator_provided=true")
            statuses.append("operator_provided_missing")
        if value.get("selected_token_source_backed") is not False:
            errors.append("selected_operator_provided_unverified requires selected_token_source_backed=false")
            statuses.append("unverified_source_backed_mismatch")
        if not selected_token_id:
            errors.append("selected_operator_provided_unverified requires selected_token_id")
            statuses.append("unverified_missing_token")
    if status == STATUS_INVALID_SELECTION and selected_token_id:
        errors.append("invalid_selection status must not include selected_token_id")
        statuses.append("invalid_selection_selected_token_detected")

    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("resolved_blocker_detected")
        if key in FORBIDDEN_VALUE_FIELD_NAMES:
            errors.append(f"{path}.{key} is forbidden in 073B artifacts")
            statuses.append("forbidden_value_field_detected")
    for candidate_index, candidate in enumerate(_rows(value.get("source_backed_candidates"))):
        token_id = clean_text(candidate.get("token_id"))
        if candidate.get("source_backed") is not True:
            errors.append(f"source_backed_candidates[{candidate_index}].source_backed must be true")
            statuses.append("candidate_not_source_backed")
        if candidate.get("token_id_generated") is not False:
            errors.append(f"source_backed_candidates[{candidate_index}].token_id_generated must be false")
            statuses.append("candidate_token_generated")
        if looks_like_placeholder_token_id(token_id):
            errors.append(f"source_backed_candidates[{candidate_index}].token_id appears placeholder-like")
            statuses.append("placeholder_candidate_detected")
    valid = not errors
    return {
        "contract_version": OPERATOR_TOKEN_SELECTION_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["operator_token_selection_packet_valid"]
            if valid
            else ["operator_token_selection_packet_blocked"]
        ),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **operator_token_selection_safety_flags(),
    }


def stable_operator_token_selection_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(dict(payload), sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def looks_like_placeholder_token_id(token_id: Any) -> bool:
    normalized = clean_text(token_id).lower()
    if not normalized:
        return False
    return any(marker in normalized for marker in FORBIDDEN_TOKEN_MARKERS)


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


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
