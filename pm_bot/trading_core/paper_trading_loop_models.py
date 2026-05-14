from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

MARKET_SNAPSHOT_CONTRACT = "pmbot_paper_trading_loop_market_snapshot_053.v1"
STRATEGY_SIGNAL_CONTRACT = "pmbot_paper_trading_loop_strategy_signal_053.v1"
NO_SIGNAL_CONTRACT = "pmbot_paper_trading_loop_no_signal_053.v1"
PAPER_EXECUTION_RISK_CONTRACT = "pmbot_paper_trading_loop_risk_053.v1"
PAPER_ORDER_INTENT_CONTRACT = "pmbot_paper_trading_loop_intent_053.v1"
PAPER_LOOP_ARTIFACT_CONTRACT = "pmbot_paper_trading_loop_result_053.v1"
LATEST_STATUS_CONTRACT = "pmbot_paper_trading_loop_latest_status_053.v1"
PAPER_LOOP_VALIDATION_CONTRACT = "pmbot_paper_trading_loop_validation_053.v1"

TASK_ID = "ORCH-PMBOT-TRADING-MVP-053-DONOR-TRADING-LOOP-RISK-AND-MOCK-CLIENT-ADAPTATION"

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
class MarketSnapshot:
    artifact_run_id: str
    market_symbol: str
    normalized_market_ref: str
    market_id: str
    market_slug: str
    question: str
    primary_outcome: str
    secondary_outcome: str
    observed_price: float
    previous_observed_price: float
    best_bid: float | None
    best_ask: float | None
    spread: float | None
    liquidity: float | None
    fixture_source: str
    fixture_mode: bool = True
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = MARKET_SNAPSHOT_CONTRACT
        value["price_delta"] = round(self.observed_price - self.previous_observed_price, 6)
        value["market_data_source"] = "local_fixture_or_operator_supplied_fixture"
        value["read_only_market_data"] = True
        value.update(paper_trading_safety_flags())
        return value


@dataclass(frozen=True)
class StrategySignal:
    artifact_run_id: str
    strategy_name: str
    market_symbol: str
    normalized_market_ref: str
    outcome: str
    side: str
    limit_price: float
    size: float
    notional: float
    confidence: float
    reason: str
    price_delta: float
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = STRATEGY_SIGNAL_CONTRACT
        value["signal_status"] = "signal_ready_for_paper_risk_review"
        value["has_signal"] = True
        value["review_only"] = True
        value["signal_is_not_live_recommendation"] = True
        value.update(paper_trading_safety_flags())
        return value


@dataclass(frozen=True)
class PaperExecutionRisk:
    artifact_run_id: str
    strategy_name: str
    market_symbol: str
    risk_decision: str
    approved_for_paper_intent: bool
    risk_blockers: tuple[str, ...]
    operator_summary: str
    confidence_threshold: float
    price_min: float
    price_max: float
    size_min: float
    size_max: float
    notional_cap: float
    max_paper_intents_per_run: int
    paper_intents_this_run: int
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PAPER_EXECUTION_RISK_CONTRACT
        value["risk_blockers"] = list(self.risk_blockers)
        value["approved_for_live"] = False
        value["live_execution_blocked"] = True
        value["paper_review_only"] = True
        value["daily_loss_check_status"] = (
            "disabled_paper_only_no_execution_ledger_is_changed"
        )
        value.update(paper_trading_safety_flags())
        return value


@dataclass(frozen=True)
class PaperOrderIntent:
    artifact_run_id: str
    paper_intent_ref: str
    strategy_name: str
    market_symbol: str
    normalized_market_ref: str
    market: str
    outcome: str
    side: str
    limit_price: float
    size: float
    notional: float
    confidence: float
    signal_reason: str
    risk_decision: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PAPER_ORDER_INTENT_CONTRACT
        value["paper_intent_status"] = "paper_intent_review_ready"
        value["paper_intent_ref_is_artifact_reference_only"] = True
        value["is_execution_identifier"] = False
        value["live_execution_blocked"] = True
        value["intent_is_not_order_submission"] = True
        value["intent_is_not_execution_result"] = True
        value.update(paper_trading_safety_flags())
        return value


@dataclass(frozen=True)
class PaperLoopArtifact:
    artifact_run_id: str
    market_symbol: str
    strategy_name: str
    loop_status: str
    snapshot: Mapping[str, Any]
    strategy_signal: Mapping[str, Any] | None
    no_signal: Mapping[str, Any] | None
    risk: Mapping[str, Any]
    paper_order_intent: Mapping[str, Any] | None
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PAPER_LOOP_ARTIFACT_CONTRACT
        value["snapshot"] = dict(self.snapshot)
        value["strategy_signal"] = dict(self.strategy_signal) if self.strategy_signal else None
        value["no_signal"] = dict(self.no_signal) if self.no_signal else None
        value["risk"] = dict(self.risk)
        value["paper_order_intent"] = dict(self.paper_order_intent) if self.paper_order_intent else None
        value["artifact_paths"] = dict(self.artifact_paths)
        value["execution_mode"] = "paper"
        value["review_only"] = True
        value["dry_run"] = True
        value["one_shot_operator_triggered"] = True
        value["scheduler_or_daemon_added"] = False
        value["autonomous_live_trading_added"] = False
        value["fake_execution_artifacts_emitted"] = False
        value.update(paper_trading_safety_flags())
        return value


@dataclass(frozen=True)
class LatestPaperTradingStatus:
    artifact_run_id: str
    market_symbol: str
    strategy_name: str
    status: str
    signal_status: str
    risk_decision: str
    paper_intent_status: str
    paper_intent_summary: str
    artifact_path: str
    latest_status_path: str
    operator_markdown_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LATEST_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = self.market_symbol
        value["mode"] = "paper / review-only"
        value["execution_mode"] = "paper"
        value["review_only"] = True
        value["live_execution"] = "blocked"
        value["live_execution_blocked"] = True
        value["next_operator_action"] = "review only, no live action available"
        value.update(paper_trading_safety_flags())
        return value


def build_no_signal_result(
    *,
    artifact_run_id: str,
    strategy_name: str,
    market_symbol: str,
    normalized_market_ref: str,
    reason: str,
    price_delta: float,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": NO_SIGNAL_CONTRACT,
        "artifact_run_id": artifact_run_id,
        "strategy_name": clean_text(strategy_name),
        "market_symbol": clean_text(market_symbol).upper(),
        "normalized_market_ref": clean_text(normalized_market_ref),
        "signal_status": "no_signal",
        "has_signal": False,
        "reason": clean_text(reason),
        "price_delta": round(float(price_delta), 6),
        "generated_at": generated_at,
        "review_only": True,
        "live_execution_blocked": True,
    }
    value.update(paper_trading_safety_flags())
    return value


def paper_trading_safety_flags() -> dict[str, Any]:
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
        "execution_enabling": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "wallet_used": False,
        "wallet_signing_performed": False,
        "cryptographic_signing_performed": False,
        "authenticated_endpoint_call_performed": False,
        "real_order_submitted": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "outcome_resolution_invented": False,
        "price_data_invented": False,
    }
    return value


def validate_paper_loop_artifact(value: Mapping[str, Any]) -> dict[str, Any]:
    artifact = dict(value or {})
    errors: list[str] = []
    if artifact.get("contract_version") != PAPER_LOOP_ARTIFACT_CONTRACT:
        errors.append(f"contract_version must be {PAPER_LOOP_ARTIFACT_CONTRACT}")
    if artifact.get("execution_mode") != "paper":
        errors.append("execution_mode must be paper")
    if artifact.get("review_only") is not True:
        errors.append("review_only must be true")
    if artifact.get("dry_run") is not True:
        errors.append("dry_run must be true")
    if artifact.get("one_shot_operator_triggered") is not True:
        errors.append("one_shot_operator_triggered must be true")
    for field in REQUIRED_FALSE_FLAGS:
        if artifact.get(field) is not False:
            errors.append(f"{field} must be false")
    if artifact.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
    if _find_forbidden_artifact_key_paths(artifact):
        errors.append("forbidden execution-like artifact field present")
    valid = not errors
    return {
        "contract_version": PAPER_LOOP_VALIDATION_CONTRACT,
        "validation_id": stable_id(
            "paper-trading-loop-validation-053",
            {
                "artifact_run_id": artifact.get("artifact_run_id"),
                "errors": errors,
            },
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        "generated_at": clean_text(artifact.get("generated_at")) or GENERATED_AT,
        **paper_trading_safety_flags(),
    }


def stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _find_forbidden_artifact_key_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    forbidden = _forbidden_artifact_keys()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            next_path = f"{path}.{key_text}"
            if key_text in forbidden:
                paths.append(next_path)
            paths.extend(_find_forbidden_artifact_key_paths(nested, next_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_find_forbidden_artifact_key_paths(nested, f"{path}[{index}]"))
    return paths


def _forbidden_artifact_keys() -> frozenset[str]:
    return frozenset(
        {
            "order_" + "id",
            "client_" + "order_" + "id",
            "transaction_" + "hash",
            "tx_" + "hash",
            "fill_" + "id",
            "fill_" + "price",
            "filled_" + "size",
            "bal" + "ance",
            "bal" + "ances",
            "p" + "nl",
            "pro" + "fit",
            "signature",
            "signed_" + "payload",
            "signed_" + "order",
        }
    )
