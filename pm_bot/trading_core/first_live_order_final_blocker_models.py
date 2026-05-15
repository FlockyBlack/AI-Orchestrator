from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-072D-FIRST-LIVE-ORDER-FINAL-BLOCKER-REDUCER-NO-EXECUTION"
REQUIRED_BASE_HEAD = "96526ac1d9eb6529041da9f5cfc75066cfb3c6cc"

EXECUTION_MODE = "first_live_order_final_blocker_reducer"
MODE = "first live order final blocker reducer / dry-run / no execution"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

STATUS_BLOCKED = "blocked_remaining_first_live_order_final_blockers"
STATUS_UNKNOWN = "unknown_artifact_evidence"
STATUS_REVIEW_REQUIRED = "review_required_no_live_authorization"

FIRST_LIVE_ORDER_FINAL_BLOCKER_CONTRACT = "pmbot_first_live_order_final_blocker_072d.v1"
FIRST_LIVE_ORDER_FINAL_BLOCKER_GROUP_CONTRACT = "pmbot_first_live_order_final_blocker_group_072d.v1"
FIRST_LIVE_ORDER_FINAL_BLOCKER_GROUPS_CONTRACT = "pmbot_first_live_order_final_blocker_groups_072d.v1"
FIRST_LIVE_ORDER_FINAL_NEXT_ACTIONS_CONTRACT = "pmbot_first_live_order_final_next_actions_072d.v1"
FIRST_LIVE_ORDER_FINAL_SAFETY_SNAPSHOT_CONTRACT = "pmbot_first_live_order_final_safety_snapshot_072d.v1"
FIRST_LIVE_ORDER_FINAL_LATEST_STATUS_CONTRACT = "pmbot_latest_first_live_order_final_blockers_072d.v1"
FIRST_LIVE_ORDER_FINAL_RESULT_CONTRACT = "pmbot_first_live_order_final_blocker_reducer_072d.v1"
FIRST_LIVE_ORDER_FINAL_VALIDATION_CONTRACT = "pmbot_first_live_order_final_blocker_validation_072d.v1"

GROUPS = (
    ("credentials_auth", "credentials/auth"),
    ("account_balance", "account/balance"),
    ("signer", "signer"),
    ("token_selection", "token selection"),
    ("signed_payload_dry_run", "signed payload dry-run"),
    ("approval", "approval"),
    ("live_execution_authorization", "live execution authorization"),
)

GROUP_IDS = tuple(group_id for group_id, _ in GROUPS)

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "live_execution_authorized",
    "live_execution_approved",
    "live_execution_performed",
    "real_execution_available",
    "canary_executable_now",
    "operator_approved",
    "operator_approval_recorded",
    "approval_consumed",
    "first_live_order_authorized",
    "first_live_order_attempted",
    "order_generation_enabled",
    "order_payload_generated",
    "order_payload_contract_executable",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signing_enabled",
    "signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "wallet_signing_performed",
    "signer_instantiated",
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
    "authenticated_polymarket_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
    "network_trading_call_performed",
    "network_write_performed",
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
    "credential_values_hashed",
    "credential_values_transformed",
    "environment_values_read",
    "secret_files_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "account_balance_read_attempted",
    "raw_account_values_emitted",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

FORBIDDEN_RAW_ARTIFACT_FIELDS = frozenset(
    {
        "private_key",
        "seed_phrase",
        "mnemonic",
        "api_secret",
        "api_secret_value",
        "auth_token",
        "passphrase",
        "secret",
        "raw_secret",
        "raw_value",
        "masked_value",
        "signature",
        "signed_payload",
        "signed_order",
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill",
        "fills",
        "fill_id",
        "fill_price",
        "filled_size",
        "execution_status",
        "balance",
        "balances",
        "position",
        "positions",
        "pnl",
        "profit",
        "realized_pnl",
        "unrealized_pnl",
    }
)


@dataclass(frozen=True)
class FirstLiveOrderFinalBlocker:
    blocker_id: str
    group_id: str
    reason: str
    evidence_status: str
    source_artifact_keys: tuple[str, ...] = ()
    severity: str = "critical"
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = FIRST_LIVE_ORDER_FINAL_BLOCKER_CONTRACT
        value["task_id"] = TASK_ID
        value["blocker_id"] = clean_text(self.blocker_id)
        value["group_id"] = _group_id(self.group_id)
        value["group_label"] = group_label_for(value["group_id"])
        value["reason"] = clean_text(self.reason)
        value["evidence_status"] = clean_text(self.evidence_status) or STATUS_UNKNOWN
        value["source_artifact_keys"] = [clean_text(item) for item in self.source_artifact_keys if clean_text(item)]
        value["severity"] = clean_text(self.severity) or "critical"
        value["resolution_status"] = "unresolved"
        value["resolved"] = False
        value["blocks_live_execution"] = True
        value.update(first_live_order_final_blocker_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderFinalBlockerGroup:
    group_id: str
    blockers: tuple[Mapping[str, Any], ...]
    evidence_references: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in self.blockers]
        references = [dict(row) for row in self.evidence_references]
        unknown_count = sum(1 for row in blockers if clean_text(row.get("evidence_status")) == STATUS_UNKNOWN)
        value = {
            "contract_version": FIRST_LIVE_ORDER_FINAL_BLOCKER_GROUP_CONTRACT,
            "task_id": TASK_ID,
            "group_id": _group_id(self.group_id),
            "group_label": group_label_for(self.group_id),
            "status": STATUS_UNKNOWN if unknown_count else STATUS_BLOCKED,
            "remaining_blockers": blockers,
            "remaining_blocker_count": len(blockers),
            "unknown_evidence_count": unknown_count,
            "resolved_blocker_count": 0,
            "evidence_references": references,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_final_blocker_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderFinalSafetySnapshot:
    market_symbol: str
    strategy_name: str
    observed_artifacts: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": FIRST_LIVE_ORDER_FINAL_SAFETY_SNAPSHOT_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "artifact_read_boundary": "known PMBOT JSON artifacts only",
            "observed_artifacts": [dict(row) for row in self.observed_artifacts],
            "observed_artifact_count": len(self.observed_artifacts),
            "unknown_remains_unknown": True,
            "no_fake_pass": True,
            "no_submit": True,
            "no_cancel": True,
            "no_signing": True,
            "no_private_material_reads": True,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_final_blocker_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderFinalBlockerResult:
    market_symbol: str
    strategy_name: str
    artifact_observations: tuple[Mapping[str, Any], ...]
    blocker_groups: Mapping[str, Any]
    next_actions: Mapping[str, Any]
    safety_snapshot: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        groups_value = dict(self.blocker_groups)
        groups = [dict(row) for row in groups_value.get("groups", []) if isinstance(row, Mapping)]
        blockers = [
            dict(row)
            for group in groups
            for row in group.get("remaining_blockers", [])
            if isinstance(row, Mapping)
        ]
        unknown_group_ids = [
            clean_text(group.get("group_id"))
            for group in groups
            if int(group.get("unknown_evidence_count", 0) or 0) > 0
        ]
        value = {
            "contract_version": FIRST_LIVE_ORDER_FINAL_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "required_base_head": REQUIRED_BASE_HEAD,
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "dry_run": True,
            "review_only": True,
            "reducer_only": True,
            "non_executable": True,
            "unknown_remains_unknown": True,
            "no_fake_pass": True,
            "artifact_observations": [dict(row) for row in self.artifact_observations],
            "artifact_observation_count": len(self.artifact_observations),
            "blocker_groups": groups_value,
            "groups": groups,
            "required_group_ids": list(GROUP_IDS),
            "remaining_blockers": blockers,
            "remaining_blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "unknown_group_ids": unknown_group_ids,
            "unknown_group_count": len(unknown_group_ids),
            "next_actions": dict(self.next_actions),
            "safety_snapshot": dict(self.safety_snapshot),
            "latest_status": dict(self.latest_status),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": (
                "First supervised tiny live order remains blocked. 072D reduces known prep/check evidence into "
                "remaining blocker groups and never authorizes execution."
            ),
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_final_blocker_safety_flags())
        value["validation"] = validate_first_live_order_final_blocker_result(value, generated_at=self.generated_at)
        return value


def group_label_for(group_id: str) -> str:
    normalized = _group_id(group_id)
    for candidate_id, label in GROUPS:
        if candidate_id == normalized:
            return label
    return normalized


def first_live_order_final_blocker_safety_flags() -> dict[str, Any]:
    value: dict[str, Any] = {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "reducer_only": True,
        "local_artifact_read_only": True,
        "no_live_execution": True,
        "no_submit": True,
        "no_cancel": True,
        "no_signing": True,
        "no_order_submission": True,
        "no_order_cancellation": True,
        "no_wallet": True,
        "no_authenticated_trading_calls": True,
        "no_secret_reads": True,
        "unknown_remains_unknown": True,
        "no_fake_pass": True,
        "resolved_blocker_count": 0,
    }
    value.update({field: False for field in FORCED_FALSE_EXECUTION_FIELDS})
    return value


def validate_first_live_order_final_blocker_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []

    if value.get("contract_version") != FIRST_LIVE_ORDER_FINAL_RESULT_CONTRACT:
        errors.append(f"contract_version must be {FIRST_LIVE_ORDER_FINAL_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append(f"execution_mode must be {EXECUTION_MODE}")
        statuses.append("invalid_execution_mode")
    for field in ("review_only", "dry_run_only", "non_executable", "reducer_only", "unknown_remains_unknown"):
        if value.get(field) is not True:
            errors.append(f"{field} must be true")
            statuses.append(f"{field}_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    if int(value.get("remaining_blocker_count", 0) or 0) <= 0:
        errors.append("remaining_blocker_count must be positive")
        statuses.append("remaining_blockers_missing")

    group_ids = {
        clean_text(row.get("group_id"))
        for row in value.get("groups", [])
        if isinstance(row, Mapping)
    }
    for group_id in GROUP_IDS:
        if group_id not in group_ids:
            errors.append(f"required blocker group missing: {group_id}")
            statuses.append("required_group_missing")

    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")

    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must remain 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in FORBIDDEN_RAW_ARTIFACT_FIELDS:
            errors.append(f"{path}.{key} is forbidden in 072D artifacts")
            statuses.append("forbidden_raw_artifact_field_detected")

    valid = not errors
    return {
        "contract_version": FIRST_LIVE_ORDER_FINAL_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else STATUS_BLOCKED,
        "statuses": _dedupe(statuses)
        or (["first_live_order_final_blocker_reducer_valid"] if valid else ["first_live_order_final_blocker_reducer_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **first_live_order_final_blocker_safety_flags(),
    }


def _market(value: Any) -> str:
    return clean_text(value).upper() or DEFAULT_ALLOWED_MARKET


def _strategy(value: Any) -> str:
    return clean_text(value) or DEFAULT_ALLOWED_STRATEGY


def _group_id(value: Any) -> str:
    text = clean_text(value).lower().replace("/", "_").replace(" ", "_").replace("-", "_")
    return text if text in GROUP_IDS else "live_execution_authorization"


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
