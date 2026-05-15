from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-065A-FIRST-LIVE-ORDER-BLOCKER-MATRIX-NO-EXECUTION"
DESIGN_REFERENCE_TASK_ID = "ORCH-PMBOT-TRADING-MVP-065-DESIGN-FIRST-SUPERVISED-TINY-LIVE-ORDER-RUNBOOK-NO-EXECUTION"
DESIGN_REFERENCE_BRANCH = "pmbot/design-065-first-supervised-tiny-live-order-runbook-no-execution"
DESIGN_REFERENCE_HEAD = "741b23e41fb156b194d18ef6459dc28c20659617"
REQUIRED_BASE_HEAD = "df02d6afa89854bcca494fc8b62fbbcb60cce89b"

EXECUTION_MODE = "preflight"
MODE = "first supervised tiny live order pre-implementation blocker matrix / no-execution"
DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

FIRST_LIVE_ORDER_BLOCKER_CONTRACT = "pmbot_first_live_order_blocker_065a.v1"
FIRST_LIVE_ORDER_BLOCKER_MATRIX_CONTRACT = "pmbot_first_live_order_blocker_matrix_065a.v1"
FIRST_LIVE_ORDER_PRECONDITIONS_CONTRACT = "pmbot_first_live_order_preconditions_065a.v1"
FIRST_LIVE_ORDER_ABORT_CONDITIONS_CONTRACT = "pmbot_first_live_order_abort_conditions_065a.v1"
FIRST_LIVE_ORDER_REQUIRED_ARTIFACTS_CONTRACT = "pmbot_first_live_order_required_artifacts_065a.v1"
FIRST_LIVE_ORDER_TEST_PLAN_CONTRACT = "pmbot_first_live_order_test_plan_065a.v1"
FIRST_LIVE_ORDER_LATEST_STATUS_CONTRACT = "pmbot_first_live_order_blocker_latest_status_065a.v1"
FIRST_LIVE_ORDER_RESULT_CONTRACT = "pmbot_first_live_order_blocker_matrix_result_065a.v1"
FIRST_LIVE_ORDER_VALIDATION_CONTRACT = "pmbot_first_live_order_blocker_matrix_validation_065a.v1"

STATUS_BLOCKED = "blocked_unresolved_first_live_order_preimplementation_matrix"

REQUIRED_UNRESOLVED_BLOCKER_IDS = (
    "explicit_operator_authorization_missing",
    "live_credentials_not_value_validated",
    "signer_boundary_not_implemented",
    "wallet_connection_not_implemented",
    "order_submission_not_implemented",
    "order_cancel_not_implemented",
    "live_order_ledger_not_implemented",
    "reconciliation_not_implemented",
    "response_redaction_policy_not_implemented",
    "first_live_order_task_not_authorized",
    "candidate_non_executable",
    "allowed_for_live_false",
)

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "candidate_is_executable",
    "operator_approved",
    "live_ready",
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "live_order_implemented",
    "first_live_order_authorized",
    "first_live_order_attempted",
    "order_intent_constructed",
    "order_payload_generated",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "signing_enabled",
    "wallet_signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "signer_boundary_implemented",
    "signer_available",
    "signer_instantiated",
    "signing_attempted",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "wallet_connection_implemented",
    "wallet_available",
    "wallet_enabled",
    "wallet_used",
    "wallet_connection_attempted",
    "wallet_signing_performed",
    "order_submission_implemented",
    "order_submission_enabled",
    "order_submission_available",
    "order_submission_attempted",
    "order_submitted",
    "real_order_submitted",
    "order_cancel_implemented",
    "order_cancel_enabled",
    "order_cancel_available",
    "order_cancellation_attempted",
    "order_cancelled",
    "real_order_cancelled",
    "authenticated_polymarket_enabled",
    "authenticated_endpoint_call_performed",
    "authenticated_request_performed",
    "authenticated_trading_calls_implemented",
    "real_authenticated_get_performed",
    "live_connector_enabled",
    "live_order_ledger_implemented",
    "reconciliation_implemented",
    "response_redaction_policy_implemented",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "credential_values_read",
    "credentials_values_read",
    "credential_values_serialized",
    "credential_values_printed",
    "credential_values_stored",
    "environment_values_read",
    "environment_values_serialized",
    "environment_values_printed",
    "environment_secrets_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "credentials_values_exposed",
    "balance_read_attempted",
    "position_read_attempted",
    "fill_read_attempted",
    "pnl_read_attempted",
    "invented_execution_artifacts_generated",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "live_trading_enabled",
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
        "passphrase_value",
        "secret",
        "raw_secret",
        "raw_value",
        "signature",
        "signed_payload",
        "signed_order",
        "signed_payload_value",
        "signed_order_value",
        "auth_header",
        "authorization_header",
        "raw_request",
        "raw_response",
        "wallet_address",
        "wallet_id",
        "wallet_file",
        "wallet_path",
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
        "profit",
        "realized_pnl",
        "unrealized_pnl",
    }
)


@dataclass(frozen=True)
class FirstLiveOrderBlocker:
    blocker_id: str
    blocker_category: str
    reason: str
    severity: str = "critical"
    resolution_status: str = "unresolved"
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = FIRST_LIVE_ORDER_BLOCKER_CONTRACT
        value["task_id"] = TASK_ID
        value["blocker_id"] = clean_text(self.blocker_id)
        value["blocker_category"] = clean_text(self.blocker_category)
        value["reason"] = clean_text(self.reason)
        value["severity"] = clean_text(self.severity) or "critical"
        value["resolution_status"] = "unresolved"
        value["resolved"] = False
        value["blocks_live_execution"] = True
        return value


@dataclass(frozen=True)
class FirstLiveOrderBlockerMatrix:
    market_symbol: str
    strategy_name: str
    blockers: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in self.blockers]
        value = {
            "contract_version": FIRST_LIVE_ORDER_BLOCKER_MATRIX_CONTRACT,
            "task_id": TASK_ID,
            "design_reference_task_id": DESIGN_REFERENCE_TASK_ID,
            "design_reference_branch": DESIGN_REFERENCE_BRANCH,
            "design_reference_head": DESIGN_REFERENCE_HEAD,
            "status": STATUS_BLOCKED,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "blockers": blockers,
            "blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "required_unresolved_blocker_ids": list(REQUIRED_UNRESOLVED_BLOCKER_IDS),
            "unresolved_blocker_ids": [clean_text(row.get("blocker_id")) for row in blockers],
            "operator_summary": (
                "All first-live-order implementation blockers are unresolved. This matrix is a scaffold only and "
                "cannot authorize or perform live execution."
            ),
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_blocker_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderPreconditions:
    market_symbol: str
    strategy_name: str
    preconditions: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        rows = [dict(row) for row in self.preconditions]
        value = {
            "contract_version": FIRST_LIVE_ORDER_PRECONDITIONS_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "preconditions": rows,
            "precondition_count": len(rows),
            "satisfied_precondition_count": sum(1 for row in rows if row.get("satisfied") is True),
            "missing_precondition_count": sum(1 for row in rows if row.get("satisfied") is not True),
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_blocker_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderAbortConditions:
    market_symbol: str
    strategy_name: str
    abort_conditions: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        rows = [dict(row) for row in self.abort_conditions]
        value = {
            "contract_version": FIRST_LIVE_ORDER_ABORT_CONDITIONS_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "abort_conditions": rows,
            "abort_condition_count": len(rows),
            "abort_policy": "any listed condition blocks before signing, submission, cancellation, or authenticated trading calls",
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_blocker_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderRequiredArtifacts:
    market_symbol: str
    strategy_name: str
    required_artifacts: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        rows = [dict(row) for row in self.required_artifacts]
        value = {
            "contract_version": FIRST_LIVE_ORDER_REQUIRED_ARTIFACTS_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "required_artifacts": rows,
            "required_artifact_count": len(rows),
            "commit_safe_only": True,
            "operator_private_material_allowed_in_repo": False,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_blocker_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderTestPlan:
    market_symbol: str
    strategy_name: str
    test_plan_items: tuple[Mapping[str, Any], ...]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        rows = [dict(row) for row in self.test_plan_items]
        value = {
            "contract_version": FIRST_LIVE_ORDER_TEST_PLAN_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "test_plan_items": rows,
            "test_plan_item_count": len(rows),
            "deterministic": True,
            "real_credentials_required": False,
            "network_required": False,
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_blocker_safety_flags())
        return value


@dataclass(frozen=True)
class FirstLiveOrderBlockerMatrixResult:
    market_symbol: str
    strategy_name: str
    blocker_matrix: Mapping[str, Any]
    preconditions: Mapping[str, Any]
    abort_conditions: Mapping[str, Any]
    required_artifacts: Mapping[str, Any]
    test_plan: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blocker_matrix = dict(self.blocker_matrix)
        blockers = [dict(row) for row in blocker_matrix.get("blockers", []) if isinstance(row, Mapping)]
        value = {
            "contract_version": FIRST_LIVE_ORDER_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "design_reference_task_id": DESIGN_REFERENCE_TASK_ID,
            "design_reference_branch": DESIGN_REFERENCE_BRANCH,
            "design_reference_head": DESIGN_REFERENCE_HEAD,
            "required_base_head": REQUIRED_BASE_HEAD,
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "preimplementation_only": True,
            "scaffold_only": True,
            "dry_run": True,
            "market": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "market_symbol": clean_text(self.market_symbol).upper() or DEFAULT_ALLOWED_MARKET,
            "strategy_name": clean_text(self.strategy_name) or DEFAULT_ALLOWED_STRATEGY,
            "blocker_count": len(blockers),
            "resolved_blocker_count": 0,
            "blockers": blockers,
            "blocker_matrix": blocker_matrix,
            "preconditions": dict(self.preconditions),
            "abort_conditions": dict(self.abort_conditions),
            "required_artifacts": dict(self.required_artifacts),
            "test_plan": dict(self.test_plan),
            "latest_status": dict(self.latest_status),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": (
                "First supervised tiny live order remains blocked. 065A only records pre-implementation blockers, "
                "preconditions, abort conditions, required future artifacts, and a test plan."
            ),
            "generated_at": self.generated_at,
        }
        value.update(first_live_order_blocker_safety_flags())
        value["validation"] = validate_first_live_order_blocker_matrix(value, generated_at=self.generated_at)
        return value


def first_live_order_blocker_safety_flags() -> dict[str, Any]:
    value = {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "preimplementation_only": True,
        "scaffold_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "no_live_trading": True,
        "no_wallet": True,
        "no_signing": True,
        "no_order_submission": True,
        "no_order_cancellation": True,
        "no_authenticated_trading_calls": True,
        "no_secret_reads": True,
        "no_scheduler": True,
        "no_daemon": True,
        "no_background_loop": True,
        "resolved_blocker_count": 0,
    }
    value.update({field: False for field in FORCED_FALSE_EXECUTION_FIELDS})
    return value


def validate_first_live_order_blocker_matrix(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != FIRST_LIVE_ORDER_RESULT_CONTRACT:
        errors.append(f"contract_version must be {FIRST_LIVE_ORDER_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must be preflight")
        statuses.append("invalid_execution_mode")
    for field in ("review_only", "preflight_only", "preimplementation_only", "scaffold_only", "non_executable"):
        if value.get(field) is not True:
            errors.append(f"{field} must be true")
            statuses.append(f"{field}_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    blocker_ids = {
        clean_text(row.get("blocker_id")) for row in value.get("blockers", []) if isinstance(row, Mapping)
    }
    for blocker_id in REQUIRED_UNRESOLVED_BLOCKER_IDS:
        if blocker_id not in blocker_ids:
            errors.append(f"required unresolved blocker missing: {blocker_id}")
            statuses.append("required_blocker_missing")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must remain 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in FORBIDDEN_RAW_ARTIFACT_FIELDS:
            errors.append(f"{path}.{key} is forbidden in 065A commit-safe artifacts")
            statuses.append("forbidden_raw_artifact_field_detected")
    valid = not errors
    return {
        "contract_version": FIRST_LIVE_ORDER_VALIDATION_CONTRACT,
        "validation_id": "first-live-order-blocker-matrix-065a-passed"
        if valid
        else "first-live-order-blocker-matrix-065a-blocked",
        "valid": valid,
        "status": "passed" if valid else STATUS_BLOCKED,
        "statuses": _dedupe(statuses)
        or (["first_live_order_blocker_matrix_valid"] if valid else ["first_live_order_blocker_matrix_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **first_live_order_blocker_safety_flags(),
    }


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
