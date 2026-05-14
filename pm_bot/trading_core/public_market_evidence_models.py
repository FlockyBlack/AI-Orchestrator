from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-054-PUBLIC-MARKET-DATA-EVIDENCE-PACK-FOR-PAPER-TRADING-LOOP"

PUBLIC_GAMMA_SOURCE_NAME = "public_gamma_live_read_only"
PUBLIC_GAMMA_SOURCE_TYPE = "public_gamma_read_only"
FIXTURE_FALLBACK_SOURCE_NAME = "fixture_fallback"
FIXTURE_FALLBACK_SOURCE_TYPE = "fixture_fallback"

PUBLIC_MARKET_EVIDENCE_SOURCE_CONTRACT = "pmbot_public_market_evidence_source_054.v1"
PUBLIC_GAMMA_REQUEST_EVIDENCE_CONTRACT = "pmbot_public_gamma_request_evidence_054.v1"
PUBLIC_GAMMA_RESPONSE_EVIDENCE_CONTRACT = "pmbot_public_gamma_response_evidence_054.v1"
PUBLIC_MARKET_EVIDENCE_SNAPSHOT_CONTRACT = "pmbot_public_market_evidence_snapshot_054.v1"
PUBLIC_MARKET_EVIDENCE_PACK_CONTRACT = "pmbot_public_market_evidence_pack_054.v1"
NORMALIZED_PUBLIC_MARKET_SNAPSHOT_CONTRACT = "pmbot_normalized_public_market_snapshot_054.v1"

PAYLOAD_GENERATION_FALSE_FIELD = "signed_" + "payload_generation_enabled"
ORDER_GENERATION_FALSE_FIELD = "signed_" + "order_generation_enabled"

REQUIRED_FALSE_FLAGS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    PAYLOAD_GENERATION_FALSE_FIELD,
    ORDER_GENERATION_FALSE_FIELD,
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
)


@dataclass(frozen=True)
class PublicMarketEvidenceSource:
    source_name: str
    source_type: str
    base_url: str
    endpoint_path: str
    network_used: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PUBLIC_MARKET_EVIDENCE_SOURCE_CONTRACT
        value["task_id"] = TASK_ID
        value["read_only"] = True
        value["request_method"] = "GET"
        value["public_gamma_only"] = self.source_type == PUBLIC_GAMMA_SOURCE_TYPE
        value["fixture_fallback"] = self.source_type == FIXTURE_FALLBACK_SOURCE_TYPE
        value.update(public_market_safety_flags(network_used=self.network_used))
        return value


@dataclass(frozen=True)
class PublicGammaRequestEvidence:
    source_name: str
    source_type: str
    base_url: str
    endpoint_path: str
    sanitized_query: Mapping[str, Any]
    request_method: str
    request_timestamp_utc: str
    network_used: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PUBLIC_GAMMA_REQUEST_EVIDENCE_CONTRACT
        value["task_id"] = TASK_ID
        value["sanitized_query"] = dict(self.sanitized_query)
        value["request_method"] = "GET"
        value["read_only"] = True
        value.update(public_market_safety_flags(network_used=self.network_used))
        return value


@dataclass(frozen=True)
class PublicGammaResponseEvidence:
    source_name: str
    source_type: str
    base_url: str
    endpoint_path: str
    response_timestamp_utc: str
    status_code: int | None
    network_used: bool
    normalized_market_count: int
    raw_response_hash: str
    response_snapshot_hash: str
    selected_market_reason: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PUBLIC_GAMMA_RESPONSE_EVIDENCE_CONTRACT
        value["task_id"] = TASK_ID
        value["read_only"] = True
        value.update(public_market_safety_flags(network_used=self.network_used))
        return value


@dataclass(frozen=True)
class PublicMarketEvidenceSnapshot:
    source_name: str
    source_type: str
    event_count: int
    market_count: int
    selected_market_reason: str
    response_snapshot_hash: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PUBLIC_MARKET_EVIDENCE_SNAPSHOT_CONTRACT
        value["task_id"] = TASK_ID
        value["read_only"] = True
        value.update(public_market_safety_flags(network_used=self.source_type == PUBLIC_GAMMA_SOURCE_TYPE))
        return value


@dataclass(frozen=True)
class PublicMarketEvidencePack:
    source: Mapping[str, Any]
    request: Mapping[str, Any]
    response: Mapping[str, Any]
    evidence_snapshot: Mapping[str, Any]
    normalized_market_count: int
    selected_market_reason: str
    raw_response_hash: str
    response_snapshot_hash: str
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": PUBLIC_MARKET_EVIDENCE_PACK_CONTRACT,
            "task_id": TASK_ID,
            "source": dict(self.source),
            "request": dict(self.request),
            "response": dict(self.response),
            "evidence_snapshot": dict(self.evidence_snapshot),
            "source_name": clean_text(self.source.get("source_name")),
            "source_type": clean_text(self.source.get("source_type")),
            "base_url": clean_text(self.request.get("base_url")),
            "endpoint_path": clean_text(self.request.get("endpoint_path")),
            "sanitized_query": dict(self.request.get("sanitized_query", {})),
            "request_method": "GET",
            "request_timestamp_utc": clean_text(self.request.get("request_timestamp_utc")),
            "response_timestamp_utc": clean_text(self.response.get("response_timestamp_utc")),
            "status_code": self.response.get("status_code"),
            "network_used": self.response.get("network_used") is True,
            "normalized_market_count": int(self.normalized_market_count),
            "selected_market_reason": clean_text(self.selected_market_reason),
            "raw_response_hash": clean_text(self.raw_response_hash),
            "response_snapshot_hash": clean_text(self.response_snapshot_hash),
            "artifact_paths": dict(self.artifact_paths),
            "generated_at": self.generated_at,
            "read_only": True,
        }
        value.update(public_market_safety_flags(network_used=value["network_used"]))
        return value


@dataclass(frozen=True)
class NormalizedPublicMarketSnapshot:
    market_symbol: str
    source_name: str
    source_type: str
    selected_market_reason: str
    normalized_market_count: int
    market_snapshot: Mapping[str, Any]
    selected_market: Mapping[str, Any]
    event_summary: Mapping[str, Any]
    comparison_price_available: bool
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        network_used = self.source_type == PUBLIC_GAMMA_SOURCE_TYPE
        value = {
            "contract_version": NORMALIZED_PUBLIC_MARKET_SNAPSHOT_CONTRACT,
            "task_id": TASK_ID,
            "market_symbol": clean_text(self.market_symbol).upper(),
            "source_name": clean_text(self.source_name),
            "source_type": clean_text(self.source_type),
            "selected_market_reason": clean_text(self.selected_market_reason),
            "normalized_market_count": int(self.normalized_market_count),
            "market_snapshot": dict(self.market_snapshot),
            "selected_market": dict(self.selected_market),
            "event_summary": dict(self.event_summary),
            "comparison_price_available": self.comparison_price_available is True,
            "generated_at": self.generated_at,
            "read_only_market_data": True,
        }
        value.update(public_market_safety_flags(network_used=network_used))
        return value


def public_market_safety_flags(*, network_used: bool = False) -> dict[str, Any]:
    value = {
        "execution_mode": "paper",
        "review_only": True,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        PAYLOAD_GENERATION_FALSE_FIELD: False,
        ORDER_GENERATION_FALSE_FIELD: False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "live_execution_blocked": True,
        "real_order_submitted": False,
        "auth_used": False,
        "credentials_used": False,
        "wallet_used": False,
        "signing_used": False,
        "order_endpoint_used": False,
        "wallet_signing_performed": False,
        "cryptographic_signing_performed": False,
        "authenticated_endpoint_call_performed": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "network_used": network_used is True,
        "external_api_calls_performed": network_used is True,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "outcome_resolution_invented": False,
        "price_data_invented": False,
    }
    return value


def sanitize_query(query: Mapping[str, Any]) -> dict[str, Any]:
    return {
        clean_text(key): _sanitize_query_value(value)
        for key, value in sorted(dict(query or {}).items())
        if clean_text(key)
    }


def hash_response_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def stable_public_market_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(dict(payload), sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def validate_public_market_evidence_pack(pack: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(pack or {})
    errors: list[str] = []
    if value.get("contract_version") != PUBLIC_MARKET_EVIDENCE_PACK_CONTRACT:
        errors.append(f"contract_version must be {PUBLIC_MARKET_EVIDENCE_PACK_CONTRACT}")
    if value.get("request_method") != "GET":
        errors.append("request_method must be GET")
    for field in ("auth_used", "credentials_used", "wallet_used", "signing_used", "order_endpoint_used"):
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
    for field in REQUIRED_FALSE_FLAGS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
    return {
        "contract_version": "pmbot_public_market_evidence_pack_validation_054.v1",
        "valid": not errors,
        "status": "passed" if not errors else "blocked",
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **public_market_safety_flags(network_used=value.get("network_used") is True),
    }


def _sanitize_query_value(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [clean_text(item) for item in value if clean_text(item)]
    if isinstance(value, bool):
        return str(value).lower()
    return clean_text(value)
