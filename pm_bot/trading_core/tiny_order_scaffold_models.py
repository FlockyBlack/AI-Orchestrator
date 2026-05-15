from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-061-MANUAL-APPROVED-TINY-ORDER-SCAFFOLD-NO-SUBMISSION"

EXECUTION_MODE = "preflight"
MODE = "preflight / review-only"
STATUS_CREATED = "created"
STATUS_BLOCKED = "blocked"
STATUS_MISSING_SOURCE = "missing_source"
STATUS_UNAVAILABLE = "unavailable"

TINY_ORDER_CANDIDATE_CONTRACT = "pmbot_tiny_order_candidate_061.v1"
TINY_ORDER_HARD_LIMITS_CONTRACT = "pmbot_tiny_order_hard_limits_061.v1"
MANUAL_TINY_ORDER_APPROVAL_PACKET_CONTRACT = "pmbot_manual_tiny_order_approval_packet_061.v1"
TINY_ORDER_SCAFFOLD_RISK_SUMMARY_CONTRACT = "pmbot_tiny_order_scaffold_risk_summary_061.v1"
TINY_ORDER_SUBMISSION_AVAILABILITY_CONTRACT = "pmbot_tiny_order_submission_availability_061.v1"
TINY_ORDER_SCAFFOLD_BLOCKER_CONTRACT = "pmbot_tiny_order_scaffold_blocker_061.v1"
TINY_ORDER_SCAFFOLD_BLOCKERS_CONTRACT = "pmbot_tiny_order_scaffold_blockers_061.v1"
LATEST_TINY_ORDER_SCAFFOLD_STATUS_CONTRACT = "pmbot_latest_tiny_order_scaffold_status_061.v1"
TINY_ORDER_SCAFFOLD_RESULT_CONTRACT = "pmbot_tiny_order_scaffold_result_061.v1"
TINY_ORDER_SCAFFOLD_VALIDATION_CONTRACT = "pmbot_tiny_order_scaffold_validation_061.v1"

FORCED_FALSE_EXECUTION_FIELDS = (
    "candidate_is_executable",
    "signing_attempted",
    "signed_payload_generated",
    "signed_payload_available",
    "order_submission_attempted",
    "order_submission_available",
    "order_cancellation_attempted",
    "wallet_connection_attempted",
    "balance_read_attempted",
    "position_read_attempted",
    "fill_read_attempted",
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
    "live_execution_allowed",
    "live_execution_performed",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_performed",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "signed_order_payload_generated",
    "order_payload_generated",
    "real_order_submitted",
    "order_submitted",
    "real_order_cancelled",
    "balance_read_enabled",
    "position_read_enabled",
    "fill_read_enabled",
    "authenticated_endpoint_call_performed",
    "authenticated_request_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "private_key_envs_checked",
    "environment_secrets_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "credentials_values_exposed",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

FORBIDDEN_MODEL_FIELDS = frozenset(
    {
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill_id",
        "fill_price",
        "filled_size",
        "execution_status",
        "balance",
        "pnl",
        "profit",
        "realized_pnl",
        "unrealized_pnl",
        "position_opened",
        "position_closed",
        "signature",
        "signed_payload_value",
    }
)


@dataclass(frozen=True)
class TinyOrderCandidate:
    status: str
    market_symbol: str
    strategy_name: str
    source_intent_path: str
    source_signer_boundary_path: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    max_notional: float
    max_size: float
    max_price: float
    hard_limits_passed: bool
    approval_packet_created: bool
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        _normalize_common(
            value,
            contract_version=TINY_ORDER_CANDIDATE_CONTRACT,
            status=clean_text(self.status) or STATUS_MISSING_SOURCE,
            operator_summary=_candidate_operator_summary(self.status, self.hard_limits_passed),
        )
        value["candidate_created"] = value["status"] == STATUS_CREATED
        value["tiny_order_candidate_status"] = value["status"]
        value["candidate_is_review_only"] = True
        value["candidate_is_not_order_submission"] = True
        value["candidate_is_not_live_approval"] = True
        value["candidate_is_executable"] = False
        return value


@dataclass(frozen=True)
class TinyOrderHardLimits:
    status: str
    market_symbol: str
    strategy_name: str
    source_intent_path: str
    source_signer_boundary_path: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    max_notional: float
    max_size: float
    max_price: float
    hard_limits_passed: bool
    approval_packet_created: bool
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["checks"] = _hard_limit_checks(
            candidate_limit_price=self.candidate_limit_price,
            candidate_size=self.candidate_size,
            candidate_notional=self.candidate_notional,
            max_price=self.max_price,
            max_size=self.max_size,
            max_notional=self.max_notional,
        )
        _normalize_common(
            value,
            contract_version=TINY_ORDER_HARD_LIMITS_CONTRACT,
            status=clean_text(self.status) or STATUS_BLOCKED,
            operator_summary=_hard_limits_operator_summary(self.hard_limits_passed),
        )
        return value


@dataclass(frozen=True)
class ManualTinyOrderApprovalPacket:
    status: str
    market_symbol: str
    strategy_name: str
    source_intent_path: str
    source_signer_boundary_path: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    max_notional: float
    max_size: float
    max_price: float
    hard_limits_passed: bool
    approval_packet_created: bool
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["approval_packet_type"] = "manual_tiny_order_review_packet"
        value["approval_packet_structure"] = [
            "source_intent_path",
            "source_signer_boundary_path",
            "tiny_candidate_summary",
            "hard_limits",
            "risk_summary",
            "submission_availability",
            "operator_acknowledgement_state",
            "remaining_blockers",
        ]
        value["operator_may_review_packet"] = self.approval_packet_created is True
        value["operator_must_not_execute_from_packet"] = True
        value["next_operator_action"] = "review packet only; no live order available"
        _normalize_common(
            value,
            contract_version=MANUAL_TINY_ORDER_APPROVAL_PACKET_CONTRACT,
            status=clean_text(self.status) or STATUS_BLOCKED,
            operator_summary=_approval_operator_summary(self.approval_packet_created, self.hard_limits_passed),
        )
        return value


@dataclass(frozen=True)
class TinyOrderScaffoldRiskSummary:
    status: str
    market_symbol: str
    strategy_name: str
    source_intent_path: str
    source_signer_boundary_path: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    max_notional: float
    max_size: float
    max_price: float
    hard_limits_passed: bool
    approval_packet_created: bool
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in self.blockers]
        value = asdict(self)
        value["risk_summary_status"] = clean_text(self.status) or STATUS_BLOCKED
        value["hard_limit_blocker_count"] = sum(
            1 for row in blockers if clean_text(row.get("blocker_category")) == "hard_limits"
        )
        value["unresolved_blocker_count"] = len(blockers)
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in blockers[:8]]
        _normalize_common(
            value,
            contract_version=TINY_ORDER_SCAFFOLD_RISK_SUMMARY_CONTRACT,
            status=clean_text(self.status) or STATUS_BLOCKED,
            operator_summary=_risk_operator_summary(self.hard_limits_passed, len(blockers)),
        )
        return value


@dataclass(frozen=True)
class TinyOrderSubmissionAvailability:
    status: str
    market_symbol: str
    strategy_name: str
    source_intent_path: str
    source_signer_boundary_path: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    max_notional: float
    max_size: float
    max_price: float
    hard_limits_passed: bool
    approval_packet_created: bool
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["submission_status"] = STATUS_BLOCKED
        value["order_submission_blocked"] = True
        value["order_cancellation_blocked"] = True
        value["signing_blocked"] = True
        value["signed_payload_unavailable"] = True
        value["wallet_connection_blocked"] = True
        value["live_execution_blocked"] = True
        _normalize_common(
            value,
            contract_version=TINY_ORDER_SUBMISSION_AVAILABILITY_CONTRACT,
            status=STATUS_BLOCKED,
            operator_summary="Order submission and cancellation remain unavailable; this packet is review-only.",
        )
        return value


@dataclass(frozen=True)
class TinyOrderScaffoldBlocker:
    blocker_id: str
    blocker_category: str
    reason: str
    severity: str = "critical"
    resolution_status: str = "unresolved"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_ORDER_SCAFFOLD_BLOCKER_CONTRACT
        value["task_id"] = TASK_ID
        value["blocks_live_execution"] = True
        value["resolved"] = False
        value.update(tiny_order_scaffold_safety_flags())
        return value


@dataclass(frozen=True)
class LatestTinyOrderScaffoldStatus:
    status: str
    market_symbol: str
    strategy_name: str
    source_intent_path: str
    source_signer_boundary_path: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    max_notional: float
    max_size: float
    max_price: float
    hard_limits_passed: bool
    approval_packet_created: bool
    blocker_count: int
    blockers: tuple[Mapping[str, Any], ...]
    artifact_path: str
    latest_status_path: str
    operator_markdown_path: str
    tiny_order_candidate_path: str
    tiny_order_hard_limits_path: str
    manual_tiny_order_approval_packet_path: str
    tiny_order_scaffold_risk_summary_path: str
    tiny_order_submission_availability_path: str
    blockers_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        blockers = [dict(row) for row in self.blockers]
        value["market"] = clean_text(self.market_symbol).upper() or "BTC"
        value["blockers"] = blockers
        value["blocker_count"] = len(blockers)
        value["top_blocker_reasons"] = [clean_text(row.get("reason")) for row in blockers[:8]]
        value["tiny_candidate"] = _candidate_status(self.source_intent_path, self.hard_limits_passed)
        value["approval_packet"] = STATUS_CREATED if self.approval_packet_created else STATUS_BLOCKED
        value["operator_approved"] = False
        value["signing"] = STATUS_BLOCKED
        value["signed_payload_status"] = STATUS_UNAVAILABLE
        value["order_submission"] = STATUS_BLOCKED
        value["wallet"] = STATUS_BLOCKED
        value["live_execution"] = STATUS_BLOCKED
        value["next_operator_action"] = "review packet only; no live order available"
        _normalize_common(
            value,
            contract_version=LATEST_TINY_ORDER_SCAFFOLD_STATUS_CONTRACT,
            status=clean_text(self.status),
            operator_summary=_latest_operator_summary(value),
        )
        return value


@dataclass(frozen=True)
class TinyOrderScaffoldResult:
    status: str
    market_symbol: str
    strategy_name: str
    source_intent_path: str
    source_signer_boundary_path: str
    candidate_outcome: str
    candidate_side: str
    candidate_limit_price: float | None
    candidate_size: float | None
    candidate_notional: float | None
    max_notional: float
    max_size: float
    max_price: float
    hard_limits_passed: bool
    approval_packet_created: bool
    tiny_order_candidate: Mapping[str, Any]
    tiny_order_hard_limits: Mapping[str, Any]
    manual_tiny_order_approval_packet: Mapping[str, Any]
    tiny_order_scaffold_risk_summary: Mapping[str, Any]
    tiny_order_submission_availability: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    blockers: tuple[Mapping[str, Any], ...]
    artifact_paths: Mapping[str, str]
    operator_summary: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        latest_status = dict(self.latest_status)
        blockers = [dict(row) for row in self.blockers]
        value = {
            "contract_version": TINY_ORDER_SCAFFOLD_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "status": clean_text(self.status),
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "scaffold_only": True,
            "dry_run": True,
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "source_intent_path": clean_text(self.source_intent_path),
            "source_signer_boundary_path": clean_text(self.source_signer_boundary_path),
            "candidate_outcome": clean_text(self.candidate_outcome) or "not_available",
            "candidate_side": clean_text(self.candidate_side) or "not_available",
            "candidate_limit_price": self.candidate_limit_price,
            "candidate_size": self.candidate_size,
            "candidate_notional": self.candidate_notional,
            "max_notional": self.max_notional,
            "max_size": self.max_size,
            "max_price": self.max_price,
            "hard_limits_passed": self.hard_limits_passed is True,
            "approval_required": True,
            "operator_approved": False,
            "approval_packet_created": self.approval_packet_created is True,
            "candidate_is_executable": False,
            "tiny_order_candidate": dict(self.tiny_order_candidate),
            "tiny_order_hard_limits": dict(self.tiny_order_hard_limits),
            "manual_tiny_order_approval_packet": dict(self.manual_tiny_order_approval_packet),
            "tiny_order_scaffold_risk_summary": dict(self.tiny_order_scaffold_risk_summary),
            "tiny_order_submission_availability": dict(self.tiny_order_submission_availability),
            "latest_status": latest_status,
            "blockers": blockers,
            "blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": clean_text(self.operator_summary),
            "generated_at": self.generated_at,
        }
        value.update(tiny_order_scaffold_safety_flags())
        value["validation"] = validate_tiny_order_scaffold_result(value, generated_at=self.generated_at)
        return value


def tiny_order_scaffold_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "scaffold_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "approval_required": True,
        "operator_approved": False,
        "candidate_is_executable": False,
        "signing_attempted": False,
        "signed_payload_generated": False,
        "signed_payload_available": False,
        "order_submission_attempted": False,
        "order_submission_available": False,
        "order_cancellation_attempted": False,
        "wallet_connection_attempted": False,
        "balance_read_attempted": False,
        "position_read_attempted": False,
        "fill_read_attempted": False,
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
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_performed": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_order_payload_generated": False,
        "order_payload_generated": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "real_order_cancelled": False,
        "balance_read_enabled": False,
        "position_read_enabled": False,
        "fill_read_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "private_key_envs_checked": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "credentials_values_exposed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def build_tiny_order_scaffold_blockers_report(
    blockers: Sequence[Mapping[str, Any]],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    rows = [dict(row) for row in blockers]
    value = {
        "contract_version": TINY_ORDER_SCAFFOLD_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": "unresolved_blockers_present",
        "blocker_count": len(rows),
        "resolved_blocker_count": 0,
        "blockers": rows,
        "top_blocker_reasons": [clean_text(row.get("reason")) for row in rows[:8]],
        "generated_at": generated_at,
    }
    value.update(tiny_order_scaffold_safety_flags())
    return value


def validate_tiny_order_scaffold_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != TINY_ORDER_SCAFFOLD_RESULT_CONTRACT:
        errors.append(f"contract_version must be {TINY_ORDER_SCAFFOLD_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must be preflight")
        statuses.append("invalid_execution_mode")
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
        statuses.append("review_only_missing")
    if value.get("preflight_only") is not True:
        errors.append("preflight_only must be true")
        statuses.append("preflight_only_missing")
    if value.get("scaffold_only") is not True:
        errors.append("scaffold_only must be true")
        statuses.append("scaffold_only_missing")
    if value.get("approval_required") is not True:
        errors.append("approval_required must be true")
        statuses.append("approval_required_missing")
    if value.get("operator_approved") is not False:
        errors.append("operator_approved must be false")
        statuses.append("operator_approval_detected")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key in FORBIDDEN_MODEL_FIELDS:
            errors.append(f"{path}.{key} is forbidden in tiny order scaffold artifacts")
            statuses.append("forbidden_model_field_detected")
    valid = not errors
    return {
        "contract_version": TINY_ORDER_SCAFFOLD_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "tiny-order-scaffold-validation-061",
            {"status": value.get("status"), "errors": errors},
        ),
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["tiny_order_scaffold_valid"] if valid else ["tiny_order_scaffold_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **tiny_order_scaffold_safety_flags(),
    }


def _normalize_common(
    value: dict[str, Any],
    *,
    contract_version: str,
    status: str,
    operator_summary: str,
) -> None:
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    value["contract_version"] = contract_version
    value["task_id"] = TASK_ID
    value["status"] = clean_text(status) or STATUS_BLOCKED
    value["mode"] = MODE
    value["execution_mode"] = EXECUTION_MODE
    value["review_only"] = True
    value["preflight_only"] = True
    value["scaffold_only"] = True
    value["market"] = clean_text(value.get("market_symbol")).upper() or "BTC"
    value["market_symbol"] = clean_text(value.get("market_symbol")).upper() or "BTC"
    value["strategy_name"] = clean_text(value.get("strategy_name")) or "tiny-momentum"
    value["source_intent_path"] = clean_text(value.get("source_intent_path"))
    value["source_signer_boundary_path"] = clean_text(value.get("source_signer_boundary_path"))
    value["candidate_outcome"] = clean_text(value.get("candidate_outcome")) or "not_available"
    value["candidate_side"] = clean_text(value.get("candidate_side")) or "not_available"
    value["hard_limits_passed"] = value.get("hard_limits_passed") is True
    value["approval_required"] = True
    value["operator_approved"] = False
    value["approval_packet_created"] = value.get("approval_packet_created") is True
    value["candidate_is_executable"] = False
    value["blockers"] = blockers
    value["blocker_count"] = len(blockers)
    value["resolved_blocker_count"] = 0
    value["operator_summary"] = clean_text(operator_summary)
    value.update(tiny_order_scaffold_safety_flags())
    value["hard_limits_passed"] = value.get("hard_limits_passed") is True
    value["approval_packet_created"] = value.get("approval_packet_created") is True


def _hard_limit_checks(
    *,
    candidate_limit_price: float | None,
    candidate_size: float | None,
    candidate_notional: float | None,
    max_price: float,
    max_size: float,
    max_notional: float,
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "candidate_limit_price_present_and_capped",
            "passed": _positive(candidate_limit_price) and float(candidate_limit_price or 0) <= max_price,
            "observed": candidate_limit_price,
            "cap": max_price,
        },
        {
            "check_id": "candidate_size_present_and_capped",
            "passed": _positive(candidate_size) and float(candidate_size or 0) <= max_size,
            "observed": candidate_size,
            "cap": max_size,
        },
        {
            "check_id": "candidate_notional_present_and_capped",
            "passed": _positive(candidate_notional) and float(candidate_notional or 0) <= max_notional,
            "observed": candidate_notional,
            "cap": max_notional,
        },
    ]


def _candidate_status(source_intent_path: str, hard_limits_passed: bool) -> str:
    if not clean_text(source_intent_path):
        return STATUS_MISSING_SOURCE
    return STATUS_CREATED if hard_limits_passed else STATUS_BLOCKED


def _candidate_operator_summary(status: str, hard_limits_passed: bool) -> str:
    if clean_text(status) == STATUS_MISSING_SOURCE:
        return "Tiny order candidate is missing because no source intent was available."
    if hard_limits_passed:
        return "Tiny order candidate was created for manual review only and is not executable."
    return "Tiny order candidate was created but blocked by hard limits and is not executable."


def _hard_limits_operator_summary(hard_limits_passed: bool) -> str:
    if hard_limits_passed:
        return "Tiny hard limits passed for the review object; signing and submission remain blocked."
    return "Tiny hard limits did not pass; the review object cannot advance beyond preflight."


def _approval_operator_summary(approval_packet_created: bool, hard_limits_passed: bool) -> str:
    if not approval_packet_created:
        return "Manual approval packet was not created because a source candidate was unavailable."
    if hard_limits_passed:
        return "Manual approval packet was created for review only; operator_approved remains false."
    return "Manual approval packet was created as a blocked review packet; operator_approved remains false."


def _risk_operator_summary(hard_limits_passed: bool, blocker_count: int) -> str:
    if hard_limits_passed:
        return f"Hard caps passed, but {blocker_count} unresolved blockers keep live execution unavailable."
    return f"Hard caps failed or source is missing; {blocker_count} unresolved blockers keep live execution unavailable."


def _latest_operator_summary(value: Mapping[str, Any]) -> str:
    return (
        "Tiny order scaffold completed as review-only. Candidate="
        + clean_text(value.get("tiny_candidate"))
        + "; approval packet="
        + clean_text(value.get("approval_packet"))
        + "; operator_approved=false; signing, signed payload generation, order submission, "
        "wallet use, balances, positions, fills, and live execution are blocked."
    )


def _positive(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


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
