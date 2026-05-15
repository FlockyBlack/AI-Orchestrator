from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-066-LIVE-ORDER-LEDGER-RECONCILIATION-SCAFFOLD-NO-EXECUTION"

EXECUTION_MODE = "preflight"
MODE = "live order ledger reconciliation scaffold / schema-only / review-only"
STATUS_SCHEMA_ONLY = "live_order_ledger_schema_only_live_blocked"

LIVE_ORDER_LEDGER_SCHEMA_CONTRACT = "pmbot_live_order_ledger_schema_066.v1"
LIVE_ORDER_RECONCILIATION_PLAN_CONTRACT = "pmbot_live_order_reconciliation_plan_066.v1"
LIVE_ORDER_RESPONSE_REDACTION_POLICY_CONTRACT = "pmbot_live_order_response_redaction_policy_066.v1"
LIVE_ORDER_FAILURE_LEDGER_SCHEMA_CONTRACT = "pmbot_live_order_failure_ledger_schema_066.v1"
LIVE_ORDER_NO_FAKE_EXECUTION_POLICY_CONTRACT = "pmbot_live_order_no_fake_execution_policy_066.v1"
LIVE_ORDER_LEDGER_LATEST_STATUS_CONTRACT = "pmbot_latest_live_order_ledger_scaffold_status_066.v1"
LIVE_ORDER_LEDGER_SCAFFOLD_RESULT_CONTRACT = "pmbot_live_order_ledger_scaffold_result_066.v1"
LIVE_ORDER_LEDGER_VALIDATION_CONTRACT = "pmbot_live_order_ledger_scaffold_validation_066.v1"

FORCED_FALSE_EXECUTION_FIELDS = (
    "authenticated_fetch_enabled",
    "live_order_ledger_executable",
    "allowed_for_live",
    "live_ready",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "canary_executable_now",
    "real_execution_available",
    "operator_approved",
    "candidate_is_executable",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_available",
    "order_cancellation_attempted",
    "order_cancellation_available",
    "wallet_enabled",
    "wallet_used",
    "wallet_connection_attempted",
    "wallet_signing_enabled",
    "wallet_signing_performed",
    "signing_enabled",
    "signing_attempted",
    "signed_payload_generation_enabled",
    "signed_payload_generated",
    "signed_payload_available",
    "signed_order_generation_enabled",
    "signed_order_payload_generated",
    "order_payload_generated",
    "real_order_submitted",
    "order_submitted",
    "real_order_cancelled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "authenticated_endpoint_call_performed",
    "authenticated_request_performed",
    "balance_read_attempted",
    "balance_read_enabled",
    "position_read_attempted",
    "position_read_enabled",
    "fill_read_attempted",
    "fill_read_enabled",
    "pnl_read_attempted",
    "pnl_read_enabled",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "environment_secrets_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "actual_secret_values_exposed",
    "credentials_values_exposed",
    "raw_response_persisted",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

FORBIDDEN_ARTIFACT_KEYS = frozenset(
    {
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
        "signature",
        "signed_payload",
        "signed_order",
        "signed_payload_value",
        "signed_order_value",
    }
)


@dataclass(frozen=True)
class LiveOrderLedgerSchema:
    market_symbol: str
    strategy_name: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": LIVE_ORDER_LEDGER_SCHEMA_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_SCHEMA_ONLY,
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "schema_only": True,
            "ledger_schema_only": True,
            "no_real_records": True,
            "no_synthetic_records": True,
            "record_count": 0,
            "ledger_rows": [],
            "field_specs": _ledger_field_specs(),
            "required_empty_collections": ["ledger_rows"],
            "operator_summary": (
                "Schema placeholder only. No live order rows, no synthetic execution rows, and no account "
                "runtime values are emitted."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_order_ledger_safety_flags())
        return value


@dataclass(frozen=True)
class LiveOrderReconciliationPlan:
    market_symbol: str
    strategy_name: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": LIVE_ORDER_RECONCILIATION_PLAN_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_SCHEMA_ONLY,
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "descriptive_only": True,
            "reconciliation_plan_only": True,
            "runtime_collection_enabled": False,
            "runtime_collection_steps": [],
            "plan_steps": [
                _plan_step(
                    "capture_operator_packet_reference",
                    "Record the future supervised operator packet reference after a separately approved task exists.",
                ),
                _plan_step(
                    "attach_redacted_response_reference",
                    "Store only a redacted response reference after a separate policy-approved capture path exists.",
                ),
                _plan_step(
                    "compare_local_status_labels",
                    "Compare future local status labels to operator-reviewed evidence without retrieving account data.",
                ),
                _plan_step(
                    "record_unresolved_discrepancies",
                    "Describe unresolved discrepancies for operator review without inferring outcomes or money impact.",
                ),
            ],
            "operator_summary": (
                "Descriptive reconciliation plan only. It defines review steps and performs no authenticated "
                "retrieval, no order action, and no account-runtime collection."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_order_ledger_safety_flags())
        return value


@dataclass(frozen=True)
class LiveOrderResponseRedactionPolicy:
    market_symbol: str
    strategy_name: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": LIVE_ORDER_RESPONSE_REDACTION_POLICY_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_SCHEMA_ONLY,
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "redaction_policy_exists": True,
            "redaction_required": True,
            "raw_response_storage_enabled": False,
            "raw_response_persisted": False,
            "raw_values_emitted": False,
            "allowed_response_material": [
                "redacted_response_reference",
                "operator_review_status_label",
                "schema_version_label",
                "review_note_without_runtime_values",
            ],
            "blocked_response_material": [
                "runtime identifiers",
                "cryptographic material",
                "account runtime values",
                "raw authenticated responses",
            ],
            "operator_summary": (
                "Policy exists before any future live response handling. Raw responses and runtime values are "
                "not stored by this scaffold."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_order_ledger_safety_flags())
        return value


@dataclass(frozen=True)
class LiveOrderFailureLedgerSchema:
    market_symbol: str
    strategy_name: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": LIVE_ORDER_FAILURE_LEDGER_SCHEMA_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_SCHEMA_ONLY,
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "schema_only": True,
            "failure_ledger_schema_exists": True,
            "failure_rows": [],
            "failure_row_count": 0,
            "field_specs": _failure_field_specs(),
            "operator_summary": (
                "Failure ledger schema placeholder only. It has no runtime failures and no execution records."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_order_ledger_safety_flags())
        return value


@dataclass(frozen=True)
class LiveOrderNoFakeExecutionPolicy:
    market_symbol: str
    strategy_name: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": LIVE_ORDER_NO_FAKE_EXECUTION_POLICY_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_SCHEMA_ONLY,
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "fake_execution_values_allowed": False,
            "synthetic_runtime_identifiers_allowed": False,
            "synthetic_account_values_allowed": False,
            "placeholder_runtime_values_allowed": False,
            "ledger_rows_must_remain_empty_in_this_task": True,
            "policy_rules": [
                "Do not invent runtime identifiers.",
                "Do not invent execution, account, or money-result values.",
                "Do not backfill scaffold artifacts with synthetic ledger rows.",
                "Use absent or empty schema fields instead of placeholder runtime values.",
            ],
            "operator_summary": (
                "No fake execution policy is active. The scaffold emits schemas and policies only, not fake "
                "execution data."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_order_ledger_safety_flags())
        return value


@dataclass(frozen=True)
class LatestLiveOrderLedgerScaffoldStatus:
    market_symbol: str
    strategy_name: str
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        paths = dict(self.artifact_paths)
        value = {
            "contract_version": LIVE_ORDER_LEDGER_LATEST_STATUS_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_SCHEMA_ONLY,
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "schema_only": True,
            "ledger_record_count": 0,
            "failure_record_count": 0,
            "redaction_policy_exists": True,
            "failure_ledger_schema_exists": True,
            "reconciliation_plan_descriptive_only": True,
            "runner_effect": "artifacts_only",
            "artifact_path": clean_text(paths.get("result")),
            "latest_status_path": clean_text(paths.get("latest_status")),
            "ledger_schema_path": clean_text(paths.get("ledger_schema")),
            "reconciliation_plan_path": clean_text(paths.get("reconciliation_plan")),
            "redaction_policy_path": clean_text(paths.get("redaction_policy")),
            "failure_ledger_schema_path": clean_text(paths.get("failure_ledger_schema")),
            "no_fake_execution_policy_path": clean_text(paths.get("no_fake_execution_policy")),
            "operator_markdown_path": clean_text(paths.get("operator_md")),
            "operator_summary": (
                "Live order ledger scaffold artifacts are schema-only and non-executable. Authenticated "
                "retrieval, account reads, wallet use, signing, and order behavior remain blocked."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_order_ledger_safety_flags())
        return value


@dataclass(frozen=True)
class LiveOrderLedgerScaffoldResult:
    market_symbol: str
    strategy_name: str
    ledger_schema: Mapping[str, Any]
    reconciliation_plan: Mapping[str, Any]
    redaction_policy: Mapping[str, Any]
    failure_ledger_schema: Mapping[str, Any]
    no_fake_execution_policy: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": LIVE_ORDER_LEDGER_SCAFFOLD_RESULT_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_SCHEMA_ONLY,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "review_only": True,
            "preflight_only": True,
            "schema_only": True,
            "scaffold_only": True,
            "dry_run": True,
            "market": clean_text(self.market_symbol).upper() or "BTC",
            "market_symbol": clean_text(self.market_symbol).upper() or "BTC",
            "strategy_name": clean_text(self.strategy_name) or "tiny-momentum",
            "ledger_schema": dict(self.ledger_schema),
            "reconciliation_plan": dict(self.reconciliation_plan),
            "redaction_policy": dict(self.redaction_policy),
            "failure_ledger_schema": dict(self.failure_ledger_schema),
            "no_fake_execution_policy": dict(self.no_fake_execution_policy),
            "latest_status": dict(self.latest_status),
            "ledger_record_count": 0,
            "failure_record_count": 0,
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": (
                "Live order ledger reconciliation scaffold generated schema-only artifacts. It did not submit, "
                "cancel, fetch authenticated data, read account runtime data, connect a wallet, sign, or invent "
                "execution records."
            ),
            "generated_at": self.generated_at,
        }
        value.update(live_order_ledger_safety_flags())
        value["validation"] = validate_live_order_ledger_scaffold(value, generated_at=self.generated_at)
        return value


def live_order_ledger_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "schema_only": True,
        "scaffold_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "authenticated_fetch_enabled": False,
        "live_order_ledger_executable": False,
        "allowed_for_live": False,
        "live_ready": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_available": False,
        "order_cancellation_attempted": False,
        "order_cancellation_available": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_connection_attempted": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "signed_payload_generation_enabled": False,
        "signed_payload_generated": False,
        "signed_payload_available": False,
        "signed_order_generation_enabled": False,
        "signed_order_payload_generated": False,
        "order_payload_generated": False,
        "real_order_submitted": False,
        "order_submitted": False,
        "real_order_cancelled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "balance_read_attempted": False,
        "balance_read_enabled": False,
        "position_read_attempted": False,
        "position_read_enabled": False,
        "fill_read_attempted": False,
        "fill_read_enabled": False,
        "pnl_read_attempted": False,
        "pnl_read_enabled": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "credentials_values_exposed": False,
        "raw_response_persisted": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def validate_live_order_ledger_scaffold(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != LIVE_ORDER_LEDGER_SCAFFOLD_RESULT_CONTRACT:
        errors.append(f"contract_version must be {LIVE_ORDER_LEDGER_SCAFFOLD_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("execution_mode") != EXECUTION_MODE:
        errors.append("execution_mode must be preflight")
        statuses.append("invalid_execution_mode")
    for field in ("review_only", "preflight_only", "schema_only", "scaffold_only", "non_executable"):
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
    ledger_schema = dict(value.get("ledger_schema", {}) or {})
    failure_schema = dict(value.get("failure_ledger_schema", {}) or {})
    plan = dict(value.get("reconciliation_plan", {}) or {})
    redaction = dict(value.get("redaction_policy", {}) or {})
    if ledger_schema.get("ledger_rows") != [] or ledger_schema.get("record_count") != 0:
        errors.append("ledger schema must contain zero rows")
        statuses.append("ledger_rows_present")
    if failure_schema.get("failure_rows") != [] or failure_schema.get("failure_row_count") != 0:
        errors.append("failure ledger schema must contain zero rows")
        statuses.append("failure_rows_present")
    if redaction.get("redaction_policy_exists") is not True:
        errors.append("redaction policy must exist")
        statuses.append("redaction_policy_missing")
    if plan.get("descriptive_only") is not True or plan.get("runtime_collection_steps") != []:
        errors.append("reconciliation plan must be descriptive only")
        statuses.append("reconciliation_plan_not_descriptive_only")
    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must remain 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in FORBIDDEN_ARTIFACT_KEYS:
            errors.append(f"{path}.{key} is forbidden in live order ledger scaffold artifacts")
            statuses.append("forbidden_artifact_field_detected")
    valid = not errors
    return {
        "contract_version": LIVE_ORDER_LEDGER_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses)
        or (["live_order_ledger_scaffold_valid"] if valid else ["live_order_ledger_scaffold_blocked"]),
        "errors": errors,
        "generated_at": generated_at,
        **live_order_ledger_safety_flags(),
    }


def _ledger_field_specs() -> list[dict[str, Any]]:
    return [
        _field_spec("ledger_row_reference", "internal scaffold reference; absent until separate approval"),
        _field_spec("operator_packet_reference", "link to a future supervised operator packet"),
        _field_spec("market_reference", "operator-provided market label or identifier reference"),
        _field_spec("strategy_reference", "operator-provided strategy label"),
        _field_spec("intent_reference", "local intent artifact reference"),
        _field_spec("redacted_response_reference", "redacted response artifact reference only"),
        _field_spec("status_label", "operator-reviewed status label"),
        _field_spec("failure_reference", "optional local failure schema row reference"),
        _field_spec("operator_review_note", "text note without runtime values"),
    ]


def _failure_field_specs() -> list[dict[str, Any]]:
    return [
        _field_spec("failure_row_reference", "internal scaffold reference; absent until separate approval"),
        _field_spec("failure_stage_label", "local stage label for a future failure review"),
        _field_spec("failure_reason_label", "operator-readable reason label without runtime values"),
        _field_spec("redacted_response_reference", "redacted response reference only"),
        _field_spec("operator_review_status_label", "manual review status label"),
        _field_spec("operator_review_note", "text note without runtime values"),
    ]


def _field_spec(name: str, description: str) -> dict[str, Any]:
    return {
        "field_name": clean_text(name),
        "description": clean_text(description),
        "required_in_this_task": False,
        "value_emitted_in_this_task": False,
        "runtime_value_allowed_in_this_task": False,
    }


def _plan_step(check_id: str, description: str) -> dict[str, Any]:
    return {
        "step_id": clean_text(check_id),
        "description": clean_text(description),
        "descriptive_only": True,
        "runtime_action_enabled": False,
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
