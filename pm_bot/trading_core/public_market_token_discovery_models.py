from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-071A-PUBLIC-MARKET-TOKEN-DISCOVERY-NO-TRADING"

PUBLIC_MARKET_TOKEN_DISCOVERY_CONFIG_CONTRACT = "pmbot_public_market_token_discovery_config_071a.v1"
PUBLIC_MARKET_TOKEN_DISCOVERY_MARKET_CONTRACT = "pmbot_public_market_token_market_candidate_071a.v1"
PUBLIC_MARKET_TOKEN_DISCOVERY_OUTCOME_CONTRACT = "pmbot_public_market_token_outcome_candidate_071a.v1"
PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT = "pmbot_public_market_token_discovery_result_071a.v1"
PUBLIC_MARKET_TOKEN_DISCOVERY_LATEST_STATUS_CONTRACT = (
    "pmbot_public_market_token_discovery_latest_status_071a.v1"
)
PUBLIC_MARKET_TOKEN_DISCOVERY_REDACTION_POLICY_CONTRACT = (
    "pmbot_public_market_token_discovery_redaction_policy_071a.v1"
)

DISCOVERY_STATUS_READY = "source_backed_candidates_ready"
DISCOVERY_STATUS_MARKETS_WITHOUT_TOKENS = "source_backed_markets_without_token_ids"
DISCOVERY_STATUS_NO_CANDIDATES = "no_source_backed_candidates"
DISCOVERY_STATUS_UNAVAILABLE = "discovery_unavailable"

PUBLIC_SOURCE_TYPES = {"public_gamma_read_only", "public_local_artifact_read_only"}
FORBIDDEN_TOKEN_MARKERS = (
    "fake",
    "fixture",
    "placeholder",
    "sample",
    "test-token",
    "mock",
    "demo-token",
)

SIGNED_PAYLOAD_FALSE_FIELD = "signed_" + "payload_generation_enabled"
SIGNED_ORDER_FALSE_FIELD = "signed_" + "order_generation_enabled"


@dataclass(frozen=True)
class PublicMarketTokenDiscoveryConfig:
    market: str
    strategy: str
    query: str
    slug: str
    tag_id: str
    limit: int
    dry_run: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PUBLIC_MARKET_TOKEN_DISCOVERY_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = clean_text(self.market).upper() or "BTC"
        value["strategy"] = clean_text(self.strategy) or "tiny-momentum"
        value["limit"] = _safe_limit(self.limit)
        value["dry_run"] = self.dry_run is True
        value["mode"] = "public read-only discovery"
        value.update(public_market_token_discovery_safety_flags(network_used=False))
        return value


@dataclass(frozen=True)
class PublicMarketCandidate:
    market_candidate_id: str
    market_id: str
    market_slug: str
    question: str
    event_id: str
    event_slug: str
    active: bool
    closed: bool
    source_name: str
    source_type: str
    source_origin: str
    source_path: str
    source_backed: bool
    source_payload_hash: str
    outcome_count: int
    outcome_token_candidate_count: int
    selection_reason: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PUBLIC_MARKET_TOKEN_DISCOVERY_MARKET_CONTRACT
        value["task_id"] = TASK_ID
        value["read_only"] = True
        value["source_backed"] = self.source_backed is True
        value.update(public_market_token_discovery_safety_flags(network_used=False))
        return value


@dataclass(frozen=True)
class PublicOutcomeTokenCandidate:
    token_candidate_id: str
    market_candidate_id: str
    market_id: str
    market_slug: str
    question: str
    outcome_name: str
    outcome_index: int
    token_id: str
    source_field: str
    source_name: str
    source_type: str
    source_origin: str
    source_path: str
    source_backed: bool
    source_payload_hash: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PUBLIC_MARKET_TOKEN_DISCOVERY_OUTCOME_CONTRACT
        value["task_id"] = TASK_ID
        value["read_only"] = True
        value["source_backed"] = self.source_backed is True
        value["token_id_is_source_backed"] = self.source_backed is True and bool(clean_text(self.token_id))
        value["token_id_is_generated"] = False
        value["token_id_is_fixture_or_placeholder"] = _looks_like_placeholder_token_id(self.token_id)
        value.update(public_market_token_discovery_safety_flags(network_used=False))
        return value


def public_market_token_discovery_safety_flags(*, network_used: bool = False) -> dict[str, Any]:
    return {
        "execution_mode": "dry_run",
        "mode": "public read-only discovery",
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "read_only": True,
        "public_data_only": True,
        "network_used": network_used is True,
        "public_read_only_endpoint_used": network_used is True,
        "external_api_calls_performed": network_used is True,
        "environment_variables_read": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "private_key_read": False,
        "wallet_connection_attempted": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "cryptographic_signing_performed": False,
        SIGNED_PAYLOAD_FALSE_FIELD: False,
        SIGNED_ORDER_FALSE_FIELD: False,
        "signed_payload_generated": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "order_endpoint_used": False,
        "real_order_submitted": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "live_connector_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "token_id_generation_enabled": False,
        "fake_token_ids_allowed": False,
        "outcome_resolution_invented": False,
    }


def build_public_market_token_discovery_redaction_policy(
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": PUBLIC_MARKET_TOKEN_DISCOVERY_REDACTION_POLICY_CONTRACT,
        "task_id": TASK_ID,
        "status": "active",
        "redaction_scope": "no secrets or credentials are read by this adapter",
        "public_fields_allowed": [
            "market_id",
            "market_slug",
            "question",
            "event_id",
            "event_slug",
            "outcome_name",
            "token_id",
            "source_name",
            "source_type",
            "source_payload_hash",
        ],
        "blocked_inputs": [
            "private keys",
            "wallet files",
            "credential stores",
            "authenticated headers",
            "browser profiles",
        ],
        "token_id_policy": "emit only token_id values present in source-backed public market metadata",
        "generated_at": generated_at,
    }
    value.update(public_market_token_discovery_safety_flags(network_used=False))
    return value


def stable_public_token_discovery_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(dict(payload), sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def validate_public_market_token_discovery_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    if value.get("contract_version") != PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT:
        errors.append(f"contract_version must be {PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT}")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
    for field in (
        "private_key_read",
        "wallet_connection_attempted",
        "signing_attempted",
        "signed_payload_generated",
        "order_submission_attempted",
        "order_cancellation_attempted",
        "authenticated_request_performed",
        "allowed_for_live",
        "browser_automation_added",
        "scheduler_or_daemon_added",
        "autonomous_live_trading_added",
        "token_id_generation_enabled",
        "fake_token_ids_allowed",
    ):
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
    for index, candidate in enumerate(_rows(value.get("market_candidates"))):
        if candidate.get("source_backed") is not True:
            errors.append(f"market_candidates[{index}].source_backed must be true")
        if clean_text(candidate.get("source_type")) not in PUBLIC_SOURCE_TYPES:
            errors.append(f"market_candidates[{index}].source_type is not an allowed public source")
    for index, candidate in enumerate(_rows(value.get("outcome_token_candidates"))):
        token_id = clean_text(candidate.get("token_id"))
        if not token_id:
            errors.append(f"outcome_token_candidates[{index}].token_id must be non-empty")
        if candidate.get("source_backed") is not True:
            errors.append(f"outcome_token_candidates[{index}].source_backed must be true")
        if candidate.get("token_id_is_generated") is not False:
            errors.append(f"outcome_token_candidates[{index}].token_id_is_generated must be false")
        if _looks_like_placeholder_token_id(token_id):
            errors.append(f"outcome_token_candidates[{index}].token_id appears to be fixture or placeholder data")
    return {
        "contract_version": "pmbot_public_market_token_discovery_validation_071a.v1",
        "task_id": TASK_ID,
        "valid": not errors,
        "status": "passed" if not errors else "blocked",
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **public_market_token_discovery_safety_flags(network_used=value.get("network_used") is True),
    }


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _safe_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = 25
    return max(1, min(value, 100))


def _looks_like_placeholder_token_id(token_id: Any) -> bool:
    normalized = clean_text(token_id).lower()
    if not normalized:
        return False
    return any(marker in normalized for marker in FORBIDDEN_TOKEN_MARKERS)
