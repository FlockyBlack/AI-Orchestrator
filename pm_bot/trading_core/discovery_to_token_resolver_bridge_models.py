from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-071D-DISCOVERY-TO-TOKEN-RESOLVER-BRIDGE-NO-TRADING"

EXECUTION_MODE = "preflight"
MODE = "discovery to token resolver bridge / dry-run / no-trading"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"
TARGET_RESOLVER = "first_order_market_token_resolver_070b"
TARGET_RESOLVER_CONTRACT_VERSION = "pmbot_first_order_market_token_contract_070b.v1"

DISCOVERY_TO_TOKEN_BRIDGE_CONFIG_CONTRACT = "pmbot_discovery_to_token_resolver_bridge_config_071d.v1"
DISCOVERY_TO_TOKEN_BRIDGE_CANDIDATE_CONTRACT = (
    "pmbot_discovery_to_token_resolver_bridge_candidate_071d.v1"
)
DISCOVERY_TO_TOKEN_CANDIDATE_CONTRACT = "pmbot_discovery_to_token_candidate_contract_071d.v1"
DISCOVERY_TO_TOKEN_BRIDGE_RESULT_CONTRACT = "pmbot_discovery_to_token_resolver_bridge_071d_result.v1"
DISCOVERY_TO_TOKEN_BRIDGE_LATEST_STATUS_CONTRACT = (
    "pmbot_latest_discovery_to_token_resolver_bridge_status_071d.v1"
)
DISCOVERY_TO_TOKEN_OPERATOR_SELECTION_CONTRACT = (
    "pmbot_discovery_to_token_operator_selection_required_071d.v1"
)
DISCOVERY_TO_TOKEN_SAFETY_SNAPSHOT_CONTRACT = (
    "pmbot_discovery_to_token_resolver_bridge_safety_snapshot_071d.v1"
)
DISCOVERY_TO_TOKEN_VALIDATION_CONTRACT = "pmbot_discovery_to_token_resolver_bridge_validation_071d.v1"

STATUS_READY = "target_candidate_contract_ready_review_only"
STATUS_SELECTION_REQUIRED = "operator_selection_required_multiple_source_backed_candidates"
STATUS_BLOCKED_NO_DISCOVERY = "blocked_no_latest_discovery_artifact"
STATUS_BLOCKED_NO_SOURCE_TOKEN = "blocked_no_source_backed_token_id"
STATUS_BLOCKED_INVALID_SELECTION = "blocked_invalid_operator_selection"
STATUS_BLOCKED_INVALID_TOKEN_ID = "blocked_invalid_token_id"
STATUS_BLOCKED_SCOPE_MISMATCH = "blocked_scope_mismatch"

PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT = "pmbot_public_market_token_discovery_result_071a.v1"

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
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "canary_executable_now",
    "operator_approved",
    "target_contract_executable",
    "token_id_generated",
    "fake_token_id_generated",
    "market_id_generated",
    "fake_market_id_generated",
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
    "authenticated_polymarket_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
    "network_trading_call_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "api_secret_read",
    "auth_token_read",
    "credential_values_read",
    "credential_values_printed",
    "credential_values_stored",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "environment_variables_read",
    "environment_secrets_read",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "token_id_generation_enabled",
    "fake_token_ids_allowed",
    "outcome_resolution_invented",
)

FORBIDDEN_VALUE_FIELD_NAMES = frozenset(
    {
        "private_key",
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
class DiscoveryToTokenBridgeConfig:
    market: str
    strategy: str
    dry_run: bool
    discovery_result_path: str
    discovery_artifacts_dir: str
    selected_candidate_id: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = DISCOVERY_TO_TOKEN_BRIDGE_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = _market(self.market)
        value["strategy"] = _strategy(self.strategy)
        value["dry_run"] = self.dry_run is True
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value.update(discovery_to_token_bridge_safety_flags())
        return value


@dataclass(frozen=True)
class DiscoveryToTokenResolverCandidate:
    bridge_candidate_id: str
    source_token_candidate_id: str
    market_candidate_id: str
    market_id: str
    market_slug: str
    question: str
    outcome_name: str
    outcome_index: int
    token_id: str
    token_id_format_status: str
    source_name: str
    source_type: str
    source_origin: str
    source_path: str
    source_payload_hash: str
    discovery_result_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        token_id_text = clean_text(self.token_id)
        value = asdict(self)
        value["contract_version"] = DISCOVERY_TO_TOKEN_BRIDGE_CANDIDATE_CONTRACT
        value["task_id"] = TASK_ID
        value["target_resolver"] = TARGET_RESOLVER
        value["target_resolver_contract_version"] = TARGET_RESOLVER_CONTRACT_VERSION
        value["source_backed"] = True
        value["token_id_source_backed"] = True
        value["token_id_source"] = "public_market_token_discovery_071a"
        value["token_id_present"] = bool(token_id_text)
        value["token_id_generated"] = False
        value["fake_token_id_generated"] = False
        value["token_id_is_fixture_or_placeholder"] = looks_like_placeholder_token_id(token_id_text)
        value["token_id_format_valid"] = clean_text(self.token_id_format_status) == "valid"
        value.update(discovery_to_token_bridge_safety_flags())
        return value


@dataclass(frozen=True)
class DiscoveryToTokenCandidateContract:
    status: str
    market_symbol: str
    strategy_name: str
    market_slug: str
    condition_id: str
    token_id: str
    outcome_name: str
    source_bridge_candidate_id: str
    source_token_candidate_id: str
    market_candidate_id: str
    source_payload_hash: str
    discovery_result_path: str
    token_id_format_status: str
    operator_selection_required: bool
    operator_selection_used: bool
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        token_id_text = clean_text(self.token_id)
        status = clean_text(self.status) or STATUS_BLOCKED_NO_SOURCE_TOKEN
        value = asdict(self)
        value["contract_version"] = DISCOVERY_TO_TOKEN_CANDIDATE_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = status
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["target_resolver"] = TARGET_RESOLVER
        value["target_resolver_contract_version"] = TARGET_RESOLVER_CONTRACT_VERSION
        value["market"] = _market(self.market_symbol)
        value["market_symbol"] = _market(self.market_symbol)
        value["strategy_name"] = _strategy(self.strategy_name)
        value["target_scope"] = "polymarket_btc_tiny_momentum"
        value["target_contract_only"] = True
        value["target_contract_executable"] = False
        value["market_slug"] = clean_text(self.market_slug)
        value["condition_id"] = clean_text(self.condition_id)
        value["token_id"] = token_id_text
        value["outcome_token_id"] = token_id_text
        value["outcome_name"] = clean_text(self.outcome_name)
        value["token_id_present"] = bool(token_id_text)
        value["token_id_source"] = (
            "public_market_token_discovery_071a_source_backed"
            if token_id_text
            else "blocked_no_selected_source_backed_token_id"
        )
        value["token_id_source_backed"] = bool(token_id_text)
        value["token_id_generated"] = False
        value["fake_token_id_generated"] = False
        value["market_id_generated"] = False
        value["fake_market_id_generated"] = False
        value["token_id_format_status"] = clean_text(self.token_id_format_status)
        value["token_id_format_valid"] = value["token_id_format_status"] == "valid"
        value["operator_selection_required"] = self.operator_selection_required is True
        value["operator_selection_used"] = self.operator_selection_used is True
        value["blockers"] = [dict(row) for row in self.blockers]
        value["blocker_count"] = len(value["blockers"])
        value["resolved_blocker_count"] = 0
        value["resolver_070b_cli_args"] = build_resolver_070b_cli_args(value)
        value["operator_summary"] = candidate_contract_operator_summary(value)
        value.update(discovery_to_token_bridge_safety_flags())
        return value


def discovery_to_token_bridge_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "bridge_only": True,
        "target_contract_only": True,
        "non_executable": True,
        "public_data_only": True,
        "local_artifact_only": True,
        "read_only": True,
        "network_access_performed": False,
        "public_network_call_performed": False,
        "polymarket_api_calls_performed": 0,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "operator_approved": False,
        "target_contract_executable": False,
        "token_id_generated": False,
        "fake_token_id_generated": False,
        "market_id_generated": False,
        "fake_market_id_generated": False,
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
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "authenticated_trading_call_performed": False,
        "network_trading_call_performed": False,
        "network_trading_calls_performed": 0,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "api_secret_read": False,
        "auth_token_read": False,
        "credential_values_read": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "environment_variables_read": False,
        "environment_secrets_read": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "token_id_generation_enabled": False,
        "fake_token_ids_allowed": False,
        "outcome_resolution_invented": False,
        "resolved_blocker_count": 0,
    }


def build_safety_snapshot(*, status: str, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    value = {
        "contract_version": DISCOVERY_TO_TOKEN_SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "safety_statement": (
            "071D reads local public discovery artifacts only and emits a review-only target candidate; "
            "live execution, order generation, signing, submission, cancellation, wallet use, and "
            "authenticated trading remain blocked."
        ),
        "generated_at": generated_at,
    }
    value.update(discovery_to_token_bridge_safety_flags())
    return value


def build_operator_selection_required(
    *,
    status: str,
    candidates: Sequence[Mapping[str, Any]],
    selected_candidate_id: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    selection_required = clean_text(status) == STATUS_SELECTION_REQUIRED
    value = {
        "contract_version": DISCOVERY_TO_TOKEN_OPERATOR_SELECTION_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "selection_required": selection_required,
        "selected_candidate_id": clean_text(selected_candidate_id),
        "candidate_count": len(candidates),
        "candidate_ids": [clean_text(row.get("bridge_candidate_id")) for row in candidates],
        "candidates": [dict(row) for row in candidates],
        "auto_pick_for_live": False,
        "next_operator_action": (
            "review candidates and rerun with --select-candidate-id for a review-only contract"
            if selection_required
            else "operator selection is not required for this bridge status"
        ),
        "generated_at": generated_at,
    }
    value.update(discovery_to_token_bridge_safety_flags())
    return value


def build_resolver_070b_cli_args(contract: Mapping[str, Any]) -> list[str]:
    token_id = clean_text(contract.get("token_id"))
    if not token_id:
        return []
    args = [
        "python",
        "-m",
        "pm_bot.operator_runner.first_order_market_token_resolver",
        "--market",
        _market(contract.get("market_symbol") or contract.get("market")),
        "--strategy",
        _strategy(contract.get("strategy_name")),
        "--dry-run",
        "--token-id",
        token_id,
    ]
    market_slug = clean_text(contract.get("market_slug"))
    condition_id = clean_text(contract.get("condition_id"))
    outcome_name = clean_text(contract.get("outcome_name"))
    if market_slug:
        args.extend(["--market-slug", market_slug])
    if condition_id:
        args.extend(["--condition-id", condition_id])
    if outcome_name:
        args.extend(["--outcome", outcome_name])
    return args


def validate_discovery_to_token_resolver_bridge_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    target_contract = dict(value.get("target_contract", {}))
    selection = dict(value.get("operator_selection_required", {}))
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != DISCOVERY_TO_TOKEN_BRIDGE_RESULT_CONTRACT:
        errors.append(f"contract_version must be {DISCOVERY_TO_TOKEN_BRIDGE_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if target_contract.get("contract_version") != DISCOVERY_TO_TOKEN_CANDIDATE_CONTRACT:
        errors.append(f"target_contract.contract_version must be {DISCOVERY_TO_TOKEN_CANDIDATE_CONTRACT}")
        statuses.append("invalid_target_contract")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("target_contract_only") is not True:
        errors.append("target_contract_only must be true")
        statuses.append("target_contract_only_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    if value.get("status") == STATUS_READY and not clean_text(target_contract.get("token_id")):
        errors.append("ready status requires a source-backed token_id")
        statuses.append("ready_missing_token_id")
    if value.get("status") == STATUS_READY and target_contract.get("token_id_source_backed") is not True:
        errors.append("ready status requires token_id_source_backed=true")
        statuses.append("ready_token_not_source_backed")
    if value.get("status") == STATUS_SELECTION_REQUIRED and target_contract.get("token_id"):
        errors.append("selection-required status must not auto-populate token_id")
        statuses.append("selection_required_auto_pick_detected")
    if value.get("status") == STATUS_SELECTION_REQUIRED and selection.get("selection_required") is not True:
        errors.append("selection-required status must write selection_required=true")
        statuses.append("selection_required_artifact_mismatch")
    if target_contract.get("token_id_generated") is not False:
        errors.append("target_contract.token_id_generated must be false")
        statuses.append("token_id_generation_detected")
    if target_contract.get("fake_token_id_generated") is not False:
        errors.append("target_contract.fake_token_id_generated must be false")
        statuses.append("fake_token_id_generation_detected")
    for field in REQUIRED_FALSE_FLAGS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_false_flag_detected")
    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in FORBIDDEN_VALUE_FIELD_NAMES:
            errors.append(f"{path}.{key} is forbidden in 071D bridge artifacts")
            statuses.append("forbidden_value_field_detected")
    valid = not errors
    return {
        "contract_version": DISCOVERY_TO_TOKEN_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses) or (["discovery_to_token_bridge_valid"] if valid else ["bridge_blocked"]),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **discovery_to_token_bridge_safety_flags(),
    }


def stable_bridge_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(dict(payload), sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def looks_like_placeholder_token_id(token_id: Any) -> bool:
    normalized = clean_text(token_id).lower()
    if not normalized:
        return False
    return any(marker in normalized for marker in FORBIDDEN_TOKEN_MARKERS)


def candidate_contract_operator_summary(value: Mapping[str, Any]) -> str:
    status = clean_text(value.get("status"))
    if status == STATUS_READY:
        return "A source-backed token_id was bridged into a review-only 070B target candidate contract."
    if status == STATUS_SELECTION_REQUIRED:
        return "Multiple source-backed token candidates were found; operator selection is required and no token_id was auto-picked."
    if status == STATUS_BLOCKED_NO_DISCOVERY:
        return "No 071A discovery artifact was available; no token_id was invented."
    if status == STATUS_BLOCKED_NO_SOURCE_TOKEN:
        return "Discovery artifact did not contain a usable source-backed token_id; no token_id was invented."
    if status == STATUS_BLOCKED_INVALID_SELECTION:
        return "The requested operator selection did not match a source-backed candidate."
    if status == STATUS_BLOCKED_SCOPE_MISMATCH:
        return "Requested market or strategy is outside the BTC/tiny-momentum resolver scope."
    return "Bridge is blocked before any live-capable action."


def _market(value: Any) -> str:
    return clean_text(value).upper() or DEFAULT_ALLOWED_MARKET


def _strategy(value: Any) -> str:
    return clean_text(value) or DEFAULT_ALLOWED_STRATEGY


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
