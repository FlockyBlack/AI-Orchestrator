from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-074A-REAL-LOCAL-CHECK-EVIDENCE-REVIEW-NO-LIVE"
SOURCE_FEATURE_BASE_HEAD = "f9e7b4de6ea2afdc110ee5a2387e375f88e46f92"
REQUIRED_BASE_HEAD = "21dede35d750311e81d31051eff60fb9902dd17c"

EXECUTION_MODE = "real_local_check_evidence_review_074a"
MODE = "real local-check evidence review / local-artifact-only / dry-run / no-live"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

STATUS_BLOCKED = "blocked_first_supervised_tiny_order_not_ready"
STATUS_REVIEW_REQUIRED = "review_required_live_blocked"
STATUS_UNKNOWN = "unknown_artifact_evidence"
STATUS_MISSING = "missing_artifact_evidence"
STATUS_UNREADABLE = "unreadable_artifact_evidence"
STATUS_EVIDENCE_PRESENT = "evidence_present_live_blocked"

GROUPS = (
    ("l2_credentials_auth", "L2 credentials/auth"),
    ("account_balance_allowance", "account/balance/allowance"),
    ("signer_private_key_diagnostic", "signer/private-key diagnostic"),
    ("token_selection", "token selection"),
    ("selected_token_payload_readiness", "selected-token payload readiness"),
    ("approval", "approval"),
    ("final_blockers", "final blockers"),
)
GROUP_IDS = tuple(group_id for group_id, _ in GROUPS)

EVIDENCE_REFERENCE_CONTRACT = "pmbot_real_local_check_evidence_reference_074a.v1"
EVIDENCE_BLOCKER_CONTRACT = "pmbot_real_local_check_evidence_blocker_074a.v1"
EVIDENCE_GROUP_CONTRACT = "pmbot_real_local_check_evidence_group_074a.v1"
EVIDENCE_GROUPS_CONTRACT = "pmbot_real_local_check_evidence_groups_074a.v1"
EVIDENCE_BLOCKERS_CONTRACT = "pmbot_real_local_check_evidence_blockers_074a.v1"
EVIDENCE_SAFETY_CONTRACT = "pmbot_real_local_check_evidence_review_safety_074a.v1"
EVIDENCE_LATEST_STATUS_CONTRACT = "pmbot_latest_real_local_check_evidence_review_074a.v1"
EVIDENCE_RESULT_CONTRACT = "pmbot_real_local_check_evidence_review_074a_result.v1"
EVIDENCE_VALIDATION_CONTRACT = "pmbot_real_local_check_evidence_review_validation_074a.v1"

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "review_executable_for_live",
    "live_execution_authorized",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "canary_executable_now",
    "first_live_order_authorized",
    "first_live_order_attempted",
    "operator_approved",
    "operator_approval_recorded",
    "approval_consumed",
    "selected_token_payload_ready_for_submit",
    "order_generation_enabled",
    "order_generation_attempted",
    "order_payload_generated",
    "order_payload_executable",
    "order_payload_signing_enabled",
    "order_payload_signing_attempted",
    "order_payload_signed",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signed_order_generated",
    "signed_payload_generation_enabled",
    "signed_payload_generation_attempted",
    "signing_enabled",
    "signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "signer_instantiated",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "wallet_signing_performed",
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
    "authenticated_trading_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
    "network_access_performed",
    "external_api_calls_performed",
    "network_trading_call_performed",
    "network_write_performed",
    "network_post_performed",
    "network_put_performed",
    "network_patch_performed",
    "network_delete_performed",
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
    "credential_values_hashed",
    "credential_values_transformed",
    "environment_values_read",
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
    "source_payload_values_embedded",
    "raw_account_values_emitted",
    "account_values_emitted",
    "fake_data_generated",
    "fake_success_inferred",
    "fake_evidence_generated",
    "fake_account_data_generated",
    "fake_order_data_generated",
    "fake_fill_data_generated",
    "fake_pnl_data_generated",
    "fake_token_data_generated",
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
        "masked_value",
        "signature",
        "signed_payload",
        "signed_order",
        "full_signed_payload",
        "raw_signed_payload",
        "full_signed_order",
        "raw_signed_order",
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
        "token_id",
        "outcome_token_id",
        "selected_token_id",
        "target_token_id",
    }
)


def real_local_check_evidence_review_safety_flags() -> dict[str, Any]:
    value: dict[str, Any] = {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "diagnosis_only": True,
        "dry_run_only": True,
        "local_artifact_only": True,
        "local_artifact_read_only": True,
        "safe_summary_only": True,
        "non_executable": True,
        "no_live_execution": True,
        "no_submit": True,
        "no_cancel": True,
        "no_signing": True,
        "no_order_submission": True,
        "no_order_cancellation": True,
        "no_wallet": True,
        "no_authenticated_trading_calls": True,
        "no_secret_reads": True,
        "no_raw_secrets": True,
        "unknown_remains_unknown": True,
        "missing_remains_missing": True,
        "no_fake_success": True,
        "no_fake_evidence": True,
        "resolved_blocker_count": 0,
    }
    value.update({field: False for field in FORCED_FALSE_EXECUTION_FIELDS})
    value["resolved_blocker_count"] = 0
    return value


@dataclass(frozen=True)
class RealLocalCheckEvidenceReference:
    source_id: str
    source_label: str
    exists: bool
    parsed: bool
    status: str
    selected_path: str
    contract_version_seen: str = ""
    evidence_fields: Mapping[str, Any] | None = None
    load_error: str = ""
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = EVIDENCE_REFERENCE_CONTRACT
        value["task_id"] = TASK_ID
        value["source_id"] = clean_text(self.source_id)
        value["source_label"] = clean_text(self.source_label)
        value["exists"] = self.exists is True
        value["parsed"] = self.parsed is True
        value["status"] = clean_text(self.status) or STATUS_UNKNOWN
        value["selected_path"] = clean_text(self.selected_path)
        value["contract_version_seen"] = clean_text(self.contract_version_seen)
        value["evidence_fields"] = dict(self.evidence_fields or {})
        value["load_error"] = clean_text(self.load_error)
        value["raw_source_payload_embedded"] = False
        value["safe_for_review"] = True
        value.update(real_local_check_evidence_review_safety_flags())
        return value


@dataclass(frozen=True)
class RealLocalCheckEvidenceBlocker:
    blocker_id: str
    group_id: str
    reason: str
    evidence_status: str
    source_ids: tuple[str, ...] = ()
    severity: str = "critical"
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        group_id = group_id_for(self.group_id)
        value = {
            "contract_version": EVIDENCE_BLOCKER_CONTRACT,
            "task_id": TASK_ID,
            "blocker_id": clean_text(self.blocker_id),
            "group_id": group_id,
            "group_label": group_label_for(group_id),
            "reason": clean_text(self.reason),
            "evidence_status": clean_text(self.evidence_status) or STATUS_UNKNOWN,
            "source_ids": [clean_text(item) for item in self.source_ids if clean_text(item)],
            "severity": clean_text(self.severity) or "critical",
            "resolution_status": "unresolved",
            "resolved": False,
            "blocks_first_supervised_tiny_order": True,
            "blocks_live_execution": True,
            "generated_at": self.generated_at,
        }
        value.update(real_local_check_evidence_review_safety_flags())
        return value


@dataclass(frozen=True)
class RealLocalCheckEvidenceGroup:
    group_id: str
    status: str
    diagnosis: str
    evidence_references: tuple[Mapping[str, Any], ...]
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        group_id = group_id_for(self.group_id)
        blockers = [dict(row) for row in self.blockers]
        references = [dict(row) for row in self.evidence_references]
        value = {
            "contract_version": EVIDENCE_GROUP_CONTRACT,
            "task_id": TASK_ID,
            "group_id": group_id,
            "group_label": group_label_for(group_id),
            "status": clean_text(self.status) or STATUS_UNKNOWN,
            "diagnosis": clean_text(self.diagnosis),
            "evidence_references": references,
            "evidence_reference_count": len(references),
            "blockers": blockers,
            "blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "generated_at": self.generated_at,
        }
        value.update(real_local_check_evidence_review_safety_flags())
        return value


@dataclass(frozen=True)
class RealLocalCheckEvidenceLatestStatus:
    market: str
    strategy: str
    groups: Sequence[Mapping[str, Any]]
    blocker_count: int
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        groups = [dict(row) for row in self.groups]
        unknown_group_ids = [
            clean_text(row.get("group_id"))
            for row in groups
            if clean_text(row.get("status")) in {STATUS_UNKNOWN, STATUS_MISSING, STATUS_UNREADABLE}
        ]
        paths = dict(self.artifact_paths)
        value = {
            "contract_version": EVIDENCE_LATEST_STATUS_CONTRACT,
            "task_id": TASK_ID,
            "required_base_head": REQUIRED_BASE_HEAD,
            "source_feature_base_head": SOURCE_FEATURE_BASE_HEAD,
            "status": STATUS_BLOCKED,
            "market": _market(self.market),
            "market_symbol": _market(self.market),
            "strategy": _strategy(self.strategy),
            "strategy_name": _strategy(self.strategy),
            "group_count": len(groups),
            "required_group_ids": list(GROUP_IDS),
            "blocking_group_count": sum(1 for row in groups if int(row.get("blocker_count", 0) or 0) > 0),
            "unknown_group_ids": unknown_group_ids,
            "unknown_group_count": len(unknown_group_ids),
            "remaining_blocker_count": int(self.blocker_count or 0),
            "resolved_blocker_count": 0,
            "live_execution_authorization": "blocked",
            "signing": "blocked",
            "order_submission": "blocked",
            "order_cancellation": "blocked",
            "artifact_path": clean_text(paths.get("result")),
            "latest_status_path": clean_text(paths.get("latest_status")),
            "evidence_groups_path": clean_text(paths.get("evidence_groups")),
            "blockers_path": clean_text(paths.get("blockers")),
            "safety_snapshot_path": clean_text(paths.get("safety_snapshot")),
            "operator_diagnosis_path": clean_text(paths.get("operator_diagnosis_md")),
            "operator_summary": (
                "Real local-check evidence was grouped for human review. The first supervised tiny order remains "
                "blocked; this artifact is not live authorization."
            ),
            "generated_at": self.generated_at,
        }
        value.update(real_local_check_evidence_review_safety_flags())
        return value


@dataclass(frozen=True)
class RealLocalCheckEvidenceReviewResult:
    market: str
    strategy: str
    artifact_root: str
    groups_artifact: Mapping[str, Any]
    blockers_artifact: Mapping[str, Any]
    safety_snapshot: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        groups_value = dict(self.groups_artifact)
        groups = [dict(row) for row in groups_value.get("groups", []) if isinstance(row, Mapping)]
        blockers = [
            dict(row)
            for group in groups
            for row in group.get("blockers", [])
            if isinstance(row, Mapping)
        ]
        value = {
            "contract_version": EVIDENCE_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "required_base_head": REQUIRED_BASE_HEAD,
            "source_feature_base_head": SOURCE_FEATURE_BASE_HEAD,
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market),
            "market_symbol": _market(self.market),
            "strategy": _strategy(self.strategy),
            "strategy_name": _strategy(self.strategy),
            "dry_run": True,
            "review_only": True,
            "diagnosis_only": True,
            "local_artifact_only": True,
            "local_artifact_read_only": True,
            "non_executable": True,
            "artifact_root": clean_text(self.artifact_root),
            "groups_artifact": groups_value,
            "groups": groups,
            "required_group_ids": list(GROUP_IDS),
            "blockers_artifact": dict(self.blockers_artifact),
            "remaining_blockers": blockers,
            "remaining_blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "safety_snapshot": dict(self.safety_snapshot),
            "latest_status": dict(self.latest_status),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": (
                "074A reviews local real-check evidence only. It diagnoses blockers but cannot submit, cancel, "
                "sign, read private material, or authorize the first supervised tiny order."
            ),
            "generated_at": self.generated_at,
        }
        value.update(real_local_check_evidence_review_safety_flags())
        value["validation"] = validate_real_local_check_evidence_review_result(value, generated_at=self.generated_at)
        return value


def group_label_for(group_id: str) -> str:
    normalized = group_id_for(group_id)
    for candidate_id, label in GROUPS:
        if candidate_id == normalized:
            return label
    return normalized


def group_id_for(value: Any) -> str:
    text = clean_text(value).lower().replace("/", "_").replace(" ", "_").replace("-", "_")
    return text if text in GROUP_IDS else "final_blockers"


def build_groups_artifact(
    *,
    groups: Sequence[Mapping[str, Any]],
    market: str,
    strategy: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    rows = [dict(row) for row in groups]
    blockers = [
        dict(blocker)
        for group in rows
        for blocker in group.get("blockers", [])
        if isinstance(blocker, Mapping)
    ]
    value = {
        "contract_version": EVIDENCE_GROUPS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "market": _market(market),
        "market_symbol": _market(market),
        "strategy": _strategy(strategy),
        "strategy_name": _strategy(strategy),
        "groups": rows,
        "group_count": len(rows),
        "required_group_ids": list(GROUP_IDS),
        "remaining_blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "generated_at": generated_at,
    }
    value.update(real_local_check_evidence_review_safety_flags())
    return value


def build_blockers_artifact(
    *,
    blockers: Sequence[Mapping[str, Any]],
    market: str,
    strategy: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    rows = [dict(row) for row in blockers]
    value = {
        "contract_version": EVIDENCE_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "market": _market(market),
        "market_symbol": _market(market),
        "strategy": _strategy(strategy),
        "strategy_name": _strategy(strategy),
        "blockers": rows,
        "blocker_count": len(rows),
        "resolved_blocker_count": 0,
        "generated_at": generated_at,
    }
    value.update(real_local_check_evidence_review_safety_flags())
    return value


def build_safety_snapshot(
    *,
    market: str,
    strategy: str,
    artifact_root: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": EVIDENCE_SAFETY_CONTRACT,
        "task_id": TASK_ID,
        "status": "real_local_check_evidence_review_safety_active",
        "market": _market(market),
        "market_symbol": _market(market),
        "strategy": _strategy(strategy),
        "strategy_name": _strategy(strategy),
        "artifact_root": clean_text(artifact_root),
        "allowed_inputs": [
            "known local PMBOT JSON artifacts",
            "073A local real-check snapshot when present",
            "commit-safe status artifacts from 064, 065D, 067C, 069A, 070B, 070C, 071D, 072C, 072D, 073B, and 073C when present",
        ],
        "forbidden_inputs": [
            "raw private keys",
            "raw API secrets",
            "wallet files",
            "browser profiles",
            "credential stores",
            "environment secret values",
        ],
        "forbidden_actions": [
            "network calls",
            "subcheck execution",
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
    value.update(real_local_check_evidence_review_safety_flags())
    return value


def validate_real_local_check_evidence_review_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != EVIDENCE_RESULT_CONTRACT:
        errors.append(f"contract_version must be {EVIDENCE_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append(f"execution_mode must be {EXECUTION_MODE}")
        statuses.append("invalid_execution_mode")
    for field in ("dry_run", "review_only", "diagnosis_only", "local_artifact_only", "local_artifact_read_only"):
        if value.get(field) is not True:
            errors.append(f"{field} must be true")
            statuses.append(f"{field}_missing")
    group_ids = [clean_text(row.get("group_id")) for row in value.get("groups", []) if isinstance(row, Mapping)]
    if tuple(group_ids) != GROUP_IDS:
        errors.append("groups must preserve the required 074A evidence group order")
        statuses.append("group_sequence_invalid")
    if int(value.get("remaining_blocker_count", 0) or 0) <= 0:
        errors.append("remaining_blocker_count must be positive; this review cannot clear live execution")
        statuses.append("remaining_blockers_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.resolved_blocker_count must remain 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in FORBIDDEN_RAW_OUTPUT_KEYS and _value_present(nested):
            errors.append(f"{path}.{key} is forbidden in 074A review output")
            statuses.append("forbidden_raw_output_field_detected")
    valid = not errors
    return {
        "contract_version": EVIDENCE_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else STATUS_BLOCKED,
        "statuses": _dedupe(statuses) or (["real_local_check_evidence_review_valid"] if valid else ["real_local_check_evidence_review_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **real_local_check_evidence_review_safety_flags(),
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


def _value_present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(clean_text(value)) and clean_text(value).lower() not in {"false", "blocked", "missing", "redacted"}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return value is True


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
