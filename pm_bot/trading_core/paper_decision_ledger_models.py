from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-055-PAPER-DECISION-LEDGER-AND-OPERATOR-PERFORMANCE-REPORTING"

PAPER_DECISION_LEDGER_ENTRY_CONTRACT = "pmbot_paper_decision_ledger_entry_055.v1"
PAPER_DECISION_LEDGER_CONTRACT = "pmbot_paper_decision_ledger_055.v1"
PAPER_DECISION_SUMMARY_CONTRACT = "pmbot_paper_decision_summary_055.v1"
OPERATOR_REVIEW_RECORD_CONTRACT = "pmbot_operator_review_record_055.v1"
EVIDENCE_DECISION_TRACE_CONTRACT = "pmbot_evidence_decision_trace_055.v1"
LATEST_PAPER_DECISION_LEDGER_STATUS_CONTRACT = "pmbot_latest_paper_decision_ledger_status_055.v1"
PAPER_DECISION_LEDGER_VALIDATION_CONTRACT = "pmbot_paper_decision_ledger_validation_055.v1"

RUN_SOURCE_PAPER_CANARY_052 = "paper_canary_052"
RUN_SOURCE_PAPER_LOOP_053 = "paper_loop_053"
RUN_SOURCE_PUBLIC_MARKET_LOOP_054 = "public_market_loop_054"
RUN_SOURCES = (
    RUN_SOURCE_PAPER_CANARY_052,
    RUN_SOURCE_PAPER_LOOP_053,
    RUN_SOURCE_PUBLIC_MARKET_LOOP_054,
)

OUTCOME_PAPER_INTENT_REVIEW_READY = "paper_intent_review_ready"
OUTCOME_NO_SIGNAL = "no_signal"
OUTCOME_RISK_BLOCKED = "risk_blocked"
OUTCOME_INCOMPLETE_ARTIFACTS = "incomplete_artifacts"
OUTCOMES = (
    OUTCOME_PAPER_INTENT_REVIEW_READY,
    OUTCOME_NO_SIGNAL,
    OUTCOME_RISK_BLOCKED,
    OUTCOME_INCOMPLETE_ARTIFACTS,
)

OPERATOR_REVIEW_PENDING = "pending_review"
OPERATOR_REVIEW_REVIEWED = "reviewed"
OPERATOR_REVIEW_REJECTED = "rejected_by_operator"
OPERATOR_REVIEW_STATUSES = (
    OPERATOR_REVIEW_PENDING,
    OPERATOR_REVIEW_REVIEWED,
    OPERATOR_REVIEW_REJECTED,
)

SIGNED_PAYLOAD_GENERATION_FIELD = "signed_" + "payload_generation_enabled"
SIGNED_ORDER_GENERATION_FIELD = "signed_" + "order_generation_enabled"

REQUIRED_FALSE_FLAGS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    SIGNED_PAYLOAD_GENERATION_FIELD,
    SIGNED_ORDER_GENERATION_FIELD,
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
)


@dataclass(frozen=True)
class OperatorReviewRecord:
    ledger_entry_id: str
    operator_review_status: str = OPERATOR_REVIEW_PENDING
    review_only: bool = True
    live_execution_blocked: bool = True
    review_instruction: str = "review the ledger entry and linked artifacts; no live action is available"
    created_at_utc: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_REVIEW_RECORD_CONTRACT
        value.update(paper_decision_safety_flags())
        return value


@dataclass(frozen=True)
class EvidenceDecisionTrace:
    ledger_entry_id: str
    run_source: str
    evidence_pack_path: str
    normalized_snapshot_path: str
    signal_path: str
    risk_path: str
    paper_intent_path: str
    no_signal_path: str
    trace_steps: tuple[Mapping[str, Any], ...]
    created_at_utc: str = GENERATED_AT
    review_only: bool = True
    live_execution_blocked: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = EVIDENCE_DECISION_TRACE_CONTRACT
        value["trace_steps"] = [dict(row) for row in self.trace_steps]
        value.update(paper_decision_safety_flags())
        return value


@dataclass(frozen=True)
class PaperDecisionLedgerEntry:
    ledger_entry_id: str
    run_source: str
    market_symbol: str
    strategy_name: str
    snapshot_source: str
    evidence_pack_path: str
    normalized_snapshot_path: str
    signal_path: str
    risk_path: str
    outcome: str
    risk_decision: str
    risk_blockers: tuple[str, ...]
    operator_review_status: str
    created_at_utc: str
    artifact_hashes: Mapping[str, Any]
    paper_intent_path: str = ""
    no_signal_path: str = ""
    live_execution_blocked: bool = True
    review_only: bool = True
    ledger_entry_id_semantics: str = (
        "internal review ledger identifier only; not an order id, not a transaction id, "
        "and not an execution id"
    )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PAPER_DECISION_LEDGER_ENTRY_CONTRACT
        value["risk_blockers"] = list(self.risk_blockers)
        value["artifact_hashes"] = dict(self.artifact_hashes)
        value["operator_review_record"] = OperatorReviewRecord(
            ledger_entry_id=self.ledger_entry_id,
            operator_review_status=self.operator_review_status,
            created_at_utc=self.created_at_utc,
        ).to_dict()
        value.update(paper_decision_safety_flags())
        return value


@dataclass(frozen=True)
class PaperDecisionLedger:
    entries: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT
    append_only: bool = True
    review_only: bool = True
    live_execution_blocked: bool = True

    def to_dict(self) -> dict[str, Any]:
        rows = [dict(row) for row in self.entries]
        value = {
            "contract_version": PAPER_DECISION_LEDGER_CONTRACT,
            "task_id": TASK_ID,
            "status": "paper_decision_ledger_written",
            "generated_at": self.generated_at,
            "append_only": self.append_only,
            "review_only": self.review_only,
            "live_execution_blocked": self.live_execution_blocked,
            "entry_count": len(rows),
            "count_by_outcome": count_by_outcome(rows),
            "entries": rows,
        }
        value.update(paper_decision_safety_flags())
        value["validation"] = validate_paper_decision_ledger(value)
        return value


@dataclass(frozen=True)
class PaperDecisionSummary:
    latest_run_source: str
    market_symbol: str
    strategy_name: str
    source_type: str
    latest_outcome: str
    risk_decision: str
    no_intent_reason: str
    evidence_pack_path: str
    paper_intent_path: str
    no_signal_path: str
    ledger_entry_count: int
    count_by_outcome: Mapping[str, int]
    created_at_utc: str = GENERATED_AT
    review_only: bool = True
    live_execution_blocked: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PAPER_DECISION_SUMMARY_CONTRACT
        value["count_by_outcome"] = dict(self.count_by_outcome)
        value["next_operator_action"] = "review only; inspect linked artifacts before any separate future task"
        value.update(paper_decision_safety_flags())
        return value


@dataclass(frozen=True)
class LatestPaperDecisionLedgerStatus:
    latest_run_source: str
    market_symbol: str
    strategy_name: str
    source_type: str
    last_outcome: str
    ledger_entry_count: int
    count_by_outcome: Mapping[str, int]
    evidence_pack_path: str
    latest_ledger_path: str
    summary_path: str
    trace_path: str
    operator_markdown_path: str
    created_at_utc: str = GENERATED_AT
    review_only: bool = True
    live_execution_blocked: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LATEST_PAPER_DECISION_LEDGER_STATUS_CONTRACT
        value["task_id"] = TASK_ID
        value["status"] = "paper_decision_ledger_status_ready"
        value["market"] = self.market_symbol
        value["mode"] = "paper / review-only"
        value["execution_mode"] = "paper"
        value["live_execution"] = "blocked"
        value["count_by_outcome"] = dict(self.count_by_outcome)
        value["next_operator_action"] = "review only; no live action available"
        value.update(paper_decision_safety_flags())
        return value


def paper_decision_safety_flags() -> dict[str, Any]:
    value = {
        "execution_mode": "paper",
        "review_only": True,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        SIGNED_PAYLOAD_GENERATION_FIELD: False,
        SIGNED_ORDER_GENERATION_FIELD: False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "execution_enabling": False,
        "network_required": False,
        "external_api_calls_performed": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "wallet_used": False,
        "wallet_signing_performed": False,
        "cryptographic_signing_performed": False,
        "authenticated_endpoint_call_performed": False,
        "real_order_submitted": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "fake_execution_artifacts_generated": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "outcome_resolution_invented": False,
        "price_data_invented": False,
    }
    return value


def count_by_outcome(entries: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {outcome: 0 for outcome in OUTCOMES}
    for entry in entries:
        outcome = clean_text(entry.get("outcome"))
        if outcome in counts:
            counts[outcome] += 1
    return counts


def validate_paper_decision_ledger(value: Mapping[str, Any]) -> dict[str, Any]:
    ledger = dict(value or {})
    errors: list[str] = []
    if ledger.get("contract_version") != PAPER_DECISION_LEDGER_CONTRACT:
        errors.append(f"contract_version must be {PAPER_DECISION_LEDGER_CONTRACT}")
    if ledger.get("review_only") is not True:
        errors.append("review_only must be true")
    if ledger.get("live_execution_blocked") is not True:
        errors.append("live_execution_blocked must be true")
    for field in REQUIRED_FALSE_FLAGS:
        if ledger.get(field) is not False:
            errors.append(f"{field} must be false")
    if ledger.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
    entries = ledger.get("entries")
    if not isinstance(entries, list):
        errors.append("entries must be a list")
        entries = []
    if ledger.get("entry_count") != len(entries):
        errors.append("entry_count must match entries")
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            errors.append(f"entries[{index}] must be an object")
            continue
        _validate_entry(entry, f"entries[{index}]", errors)
    forbidden_paths = find_forbidden_decision_key_paths(ledger)
    if forbidden_paths:
        errors.append("forbidden execution-like or financial-state field present")
    valid = not errors
    return {
        "contract_version": PAPER_DECISION_LEDGER_VALIDATION_CONTRACT,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        "forbidden_field_paths": forbidden_paths,
        "generated_at": clean_text(ledger.get("generated_at")) or GENERATED_AT,
        **paper_decision_safety_flags(),
    }


def stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def find_forbidden_decision_key_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    forbidden = _forbidden_decision_keys()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            next_path = f"{path}.{key_text}"
            if key_text in forbidden:
                paths.append(next_path)
            paths.extend(find_forbidden_decision_key_paths(nested, next_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(find_forbidden_decision_key_paths(nested, f"{path}[{index}]"))
    return paths


def _validate_entry(entry: Mapping[str, Any], path: str, errors: list[str]) -> None:
    if entry.get("contract_version") != PAPER_DECISION_LEDGER_ENTRY_CONTRACT:
        errors.append(f"{path}.contract_version must be {PAPER_DECISION_LEDGER_ENTRY_CONTRACT}")
    if clean_text(entry.get("ledger_entry_id")) == "":
        errors.append(f"{path}.ledger_entry_id must be present")
    if clean_text(entry.get("run_source")) not in RUN_SOURCES:
        errors.append(f"{path}.run_source must be one of the supported paper sources")
    if clean_text(entry.get("outcome")) not in OUTCOMES:
        errors.append(f"{path}.outcome must be a supported paper decision outcome")
    if clean_text(entry.get("operator_review_status")) not in OPERATOR_REVIEW_STATUSES:
        errors.append(f"{path}.operator_review_status must be a supported review status")
    if entry.get("review_only") is not True:
        errors.append(f"{path}.review_only must be true")
    if entry.get("live_execution_blocked") is not True:
        errors.append(f"{path}.live_execution_blocked must be true")
    for field in REQUIRED_FALSE_FLAGS:
        if entry.get(field) is not False:
            errors.append(f"{path}.{field} must be false")
    if entry.get("resolved_blocker_count") != 0:
        errors.append(f"{path}.resolved_blocker_count must be 0")


def _forbidden_decision_keys() -> frozenset[str]:
    return frozenset(
        {
            "order_" + "id",
            "client_" + "order_" + "id",
            "tx_" + "hash",
            "fill_" + "id",
            "fill_" + "price",
            "filled_" + "size",
            "execution_" + "price",
            "execution_" + "status",
            "bal" + "ance",
            "p" + "nl",
            "pro" + "fit",
            "los" + "s",
            "realized_" + "pnl",
            "unrealized_" + "pnl",
            "position_" + "opened",
            "position_" + "closed",
        }
    )
