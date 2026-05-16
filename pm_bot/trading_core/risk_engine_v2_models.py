from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-RISK-074D-RISK-ENGINE-V2-SCAFFOLD-NO-LIVE"
REQUIRED_BASE_HEAD = "21dede35d750311e81d31051eff60fb9902dd17c"

EXECUTION_MODE = "risk_engine_v2_review"
MODE = "risk engine v2 supervised readiness review / dry-run / no-live"

DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

STATUS_BLOCKED = "blocked_risk_engine_v2_review"
STATUS_PASSED_REVIEW_CHECK = "passed_review_check_no_live"
STATUS_UNKNOWN = "unknown_evidence"
STATUS_MISSING = "missing_evidence"
STATUS_REVIEW_REQUIRED = "review_required"

RISK_ENGINE_V2_BLOCKER_CONTRACT = "pmbot_risk_engine_v2_blocker_074d.v1"
RISK_ENGINE_V2_GATE_EVALUATION_CONTRACT = "pmbot_risk_engine_v2_gate_evaluation_074d.v1"
RISK_ENGINE_V2_BLOCKERS_CONTRACT = "pmbot_risk_engine_v2_blockers_074d.v1"
RISK_ENGINE_V2_LATEST_STATUS_CONTRACT = "pmbot_latest_risk_engine_v2_review_074d.v1"
RISK_ENGINE_V2_SAFETY_SNAPSHOT_CONTRACT = "pmbot_risk_engine_v2_safety_snapshot_074d.v1"
RISK_ENGINE_V2_RESULT_CONTRACT = "pmbot_risk_engine_v2_review_074d.v1"
RISK_ENGINE_V2_VALIDATION_CONTRACT = "pmbot_risk_engine_v2_validation_074d.v1"

RISK_ENGINE_V2_GATE_DEFINITIONS: tuple[dict[str, str], ...] = (
    {
        "gate_id": "stale_data",
        "blocker_id": "risk_v2_stale_data_or_freshness_unknown",
        "category": "data_freshness",
        "label": "stale data",
    },
    {
        "gate_id": "liquidity_evidence",
        "blocker_id": "risk_v2_liquidity_evidence_missing_or_weak",
        "category": "liquidity",
        "label": "missing or weak liquidity evidence",
    },
    {
        "gate_id": "source_backed_token_candidate",
        "blocker_id": "risk_v2_source_backed_token_candidate_missing",
        "category": "token_candidate",
        "label": "missing source-backed token candidate",
    },
    {
        "gate_id": "account_readonly_evidence",
        "blocker_id": "risk_v2_account_readonly_evidence_missing",
        "category": "account_readonly",
        "label": "missing account read-only evidence",
    },
    {
        "gate_id": "signer_diagnostic_evidence",
        "blocker_id": "risk_v2_signer_diagnostic_evidence_missing",
        "category": "signer_diagnostic",
        "label": "missing signer diagnostic evidence",
    },
    {
        "gate_id": "selected_token_payload_readiness",
        "blocker_id": "risk_v2_selected_token_payload_readiness_missing",
        "category": "selected_token_payload",
        "label": "missing selected-token payload readiness",
    },
    {
        "gate_id": "exposure_cap",
        "blocker_id": "risk_v2_total_exposure_cap_unknown_or_exceeded",
        "category": "exposure_caps",
        "label": "exposure caps",
    },
    {
        "gate_id": "per_market_cap",
        "blocker_id": "risk_v2_per_market_cap_unknown_or_exceeded",
        "category": "per_market_cap",
        "label": "per-market cap",
    },
    {
        "gate_id": "daily_loss_cap",
        "blocker_id": "risk_v2_daily_loss_cap_unknown_or_exceeded",
        "category": "daily_loss_cap",
        "label": "daily loss cap",
    },
    {
        "gate_id": "duplicate_attempt_guard",
        "blocker_id": "risk_v2_duplicate_attempt_guard_unknown_or_triggered",
        "category": "duplicate_attempt_guard",
        "label": "duplicate attempt guard",
    },
    {
        "gate_id": "halt_states",
        "blocker_id": "risk_v2_halt_state_unknown_or_active",
        "category": "halt_states",
        "label": "halt states",
    },
    {
        "gate_id": "unknown_means_block",
        "blocker_id": "risk_v2_unknown_evidence_blocks",
        "category": "unknown_means_block",
        "label": "unknown means block",
    },
    {
        "gate_id": "operator_approval_required",
        "blocker_id": "risk_v2_operator_approval_required",
        "category": "operator_approval",
        "label": "operator approval required",
    },
    {
        "gate_id": "explicit_live_authorization_missing",
        "blocker_id": "risk_v2_explicit_live_authorization_missing",
        "category": "live_authorization",
        "label": "explicit live authorization missing",
    },
)

REQUIRED_GATE_IDS = tuple(row["gate_id"] for row in RISK_ENGINE_V2_GATE_DEFINITIONS)
REQUIRED_BLOCKER_IDS = tuple(row["blocker_id"] for row in RISK_ENGINE_V2_GATE_DEFINITIONS)

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "risk_engine_v2_executable_for_live",
    "live_execution_authorized",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "canary_executable_now",
    "operator_approved",
    "operator_approval_recorded",
    "approval_consumed",
    "first_live_order_authorized",
    "first_live_order_attempted",
    "order_generation_enabled",
    "order_generation_attempted",
    "order_payload_generated",
    "order_payload_executable",
    "order_payload_signing_enabled",
    "order_payload_signing_attempted",
    "order_payload_signed",
    "signed_payload_generation_enabled",
    "signed_payload_generation_attempted",
    "signed_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signed_order_generated",
    "signed_order_payload_generated",
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
    "authenticated_trading_enabled",
    "authenticated_trading_call_performed",
    "network_trading_call_performed",
    "trading_write_call_performed",
    "network_write_call_performed",
    "network_write_performed",
    "network_post_performed",
    "network_put_performed",
    "network_patch_performed",
    "network_delete_performed",
    "private_key_read",
    "seed_phrase_read",
    "mnemonic_read",
    "api_secret_read",
    "auth_token_read",
    "passphrase_read",
    "credential_value_read",
    "credential_values_read",
    "credential_values_printed",
    "credential_values_stored",
    "credential_values_serialized",
    "environment_values_read",
    "secret_files_read",
    "secrets_read",
    "secrets_printed",
    "secrets_persisted",
    "raw_values_emitted",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
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

BLOCKING_EVIDENCE_STATUSES = frozenset(
    {
        STATUS_UNKNOWN,
        STATUS_MISSING,
        "stale",
        "weak",
        "blocked",
        "cap_exceeded",
        "duplicate_detected",
        "halt_active",
        "review_required",
        "authorization_missing",
        "unsafe_source_flag",
    }
)


@dataclass(frozen=True)
class RiskEngineV2Blocker:
    blocker_id: str
    gate_id: str
    category: str
    reason: str
    evidence_status: str
    source_keys: tuple[str, ...] = ()
    severity: str = "critical"
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = RISK_ENGINE_V2_BLOCKER_CONTRACT
        value["task_id"] = TASK_ID
        value["blocker_id"] = clean_text(self.blocker_id)
        value["gate_id"] = clean_text(self.gate_id)
        value["gate_label"] = risk_engine_v2_gate_label(self.gate_id)
        value["category"] = clean_text(self.category)
        value["reason"] = clean_text(self.reason)
        value["evidence_status"] = clean_text(self.evidence_status) or STATUS_UNKNOWN
        value["source_keys"] = [clean_text(item) for item in self.source_keys if clean_text(item)]
        value["severity"] = clean_text(self.severity) or "critical"
        value["resolution_status"] = "unresolved"
        value["resolved"] = False
        value["blocks_first_supervised_tiny_order"] = True
        value["blocks_live_execution"] = True
        value.update(risk_engine_v2_safety_flags())
        return value


@dataclass(frozen=True)
class RiskEngineV2SafetySnapshot:
    market_symbol: str
    strategy_name: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": RISK_ENGINE_V2_SAFETY_SNAPSHOT_CONTRACT,
            "task_id": TASK_ID,
            "status": STATUS_BLOCKED,
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "review_artifact_only": True,
            "unknown_means_block": True,
            "default_mode_reads_private_material": False,
            "default_mode_instantiates_signer": False,
            "default_mode_prepares_executable_payload": False,
            "default_mode_calls_network": False,
            "generated_at": self.generated_at,
        }
        value.update(risk_engine_v2_safety_flags())
        return value


@dataclass(frozen=True)
class RiskEngineV2ReviewResult:
    market_symbol: str
    strategy_name: str
    gate_evaluations: tuple[Mapping[str, Any], ...]
    blockers: tuple[Mapping[str, Any], ...]
    safety_snapshot: Mapping[str, Any]
    latest_status: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        blockers = [dict(row) for row in self.blockers]
        gates = [dict(row) for row in self.gate_evaluations]
        blocker_ids = [clean_text(row.get("blocker_id")) for row in blockers if clean_text(row.get("blocker_id"))]
        unknown_blockers = [
            clean_text(row.get("blocker_id"))
            for row in blockers
            if clean_text(row.get("evidence_status")) in {STATUS_UNKNOWN, STATUS_MISSING}
        ]
        value = {
            "contract_version": RISK_ENGINE_V2_RESULT_CONTRACT,
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
            "no_live": True,
            "local_artifact_only": True,
            "unknown_means_block": True,
            "risk_engine_v2_executable_for_live": False,
            "allowed_for_live": False,
            "first_supervised_tiny_order_blocked": True,
            "gate_evaluations": gates,
            "gate_count": len(gates),
            "required_gate_ids": list(REQUIRED_GATE_IDS),
            "blockers": blockers,
            "blocker_ids": blocker_ids,
            "blocker_count": len(blockers),
            "remaining_blocker_count": len(blockers),
            "unknown_blocker_ids": unknown_blockers,
            "unknown_blocker_count": len(unknown_blockers),
            "resolved_blocker_count": 0,
            "safety_snapshot": dict(self.safety_snapshot),
            "latest_status": dict(self.latest_status),
            "artifact_paths": dict(self.artifact_paths),
            "operator_summary": (
                "Risk Engine v2 review remains no-live and blocks the first supervised tiny order until all "
                "review evidence, caps, duplicate guard, halt state, operator approval, and explicit live "
                "authorization are satisfied in separate approved tasks."
            ),
            "generated_at": self.generated_at,
        }
        value.update(risk_engine_v2_safety_flags())
        value["validation"] = validate_risk_engine_v2_review_result(value, generated_at=self.generated_at)
        return value


def risk_engine_v2_gate_label(gate_id: str) -> str:
    gate = clean_text(gate_id)
    for row in RISK_ENGINE_V2_GATE_DEFINITIONS:
        if row["gate_id"] == gate:
            return row["label"]
    return gate


def risk_engine_v2_blocker_id_for_gate(gate_id: str) -> str:
    gate = clean_text(gate_id)
    for row in RISK_ENGINE_V2_GATE_DEFINITIONS:
        if row["gate_id"] == gate:
            return row["blocker_id"]
    return f"risk_v2_{gate or 'unknown'}_blocked"


def risk_engine_v2_category_for_gate(gate_id: str) -> str:
    gate = clean_text(gate_id)
    for row in RISK_ENGINE_V2_GATE_DEFINITIONS:
        if row["gate_id"] == gate:
            return row["category"]
    return gate or "unknown"


def risk_engine_v2_safety_flags() -> dict[str, Any]:
    value: dict[str, Any] = {
        "execution_mode": EXECUTION_MODE,
        "mode": MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "no_live": True,
        "local_artifact_only": True,
        "local_artifact_read_only": True,
        "network_used": False,
        "external_api_calls_performed": False,
        "polymarket_api_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "risk_engine_v2_executable_for_live": False,
        "allowed_for_live": False,
        "first_supervised_tiny_order_blocked": True,
        "unknown_means_block": True,
        "operator_approval_required_before_live": True,
        "explicit_live_authorization_required": True,
        "no_submit": True,
        "no_cancel": True,
        "no_signing": True,
        "no_wallet": True,
        "no_private_material_reads": True,
        "resolved_blocker_count": 0,
    }
    value.update({field: False for field in FORCED_FALSE_EXECUTION_FIELDS})
    return value


def validate_risk_engine_v2_review_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []

    if value.get("contract_version") != RISK_ENGINE_V2_RESULT_CONTRACT:
        errors.append(f"contract_version must be {RISK_ENGINE_V2_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")
        statuses.append("task_id_mismatch")
    if value.get("status") != STATUS_BLOCKED:
        errors.append(f"status must remain {STATUS_BLOCKED}")
        statuses.append("status_not_blocked")
    for field in ("review_only", "dry_run_only", "non_executable", "unknown_means_block"):
        if value.get(field) is not True:
            errors.append(f"{field} must be true")
            statuses.append(f"{field}_missing")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_not_false")
    if value.get("risk_engine_v2_executable_for_live") is not False:
        errors.append("risk_engine_v2_executable_for_live must be false")
        statuses.append("risk_engine_v2_executable_for_live_not_false")
    if value.get("first_supervised_tiny_order_blocked") is not True:
        errors.append("first_supervised_tiny_order_blocked must be true")
        statuses.append("first_supervised_tiny_order_not_blocked")
    if int(value.get("remaining_blocker_count", 0) or 0) <= 0:
        errors.append("remaining_blocker_count must be positive")
        statuses.append("remaining_blockers_missing")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")

    gate_ids = {
        clean_text(row.get("gate_id"))
        for row in value.get("gate_evaluations", [])
        if isinstance(row, Mapping)
    }
    for gate_id in REQUIRED_GATE_IDS:
        if gate_id not in gate_ids:
            errors.append(f"required gate missing: {gate_id}")
            statuses.append("required_gate_missing")

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
        if key in FORBIDDEN_VALUE_FIELD_NAMES and _value_present(nested):
            errors.append(f"{path}.{key} must not be emitted")
            statuses.append("forbidden_runtime_value_field_detected")

    valid = not errors
    return {
        "contract_version": RISK_ENGINE_V2_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else STATUS_BLOCKED,
        "statuses": _dedupe(statuses) or (["risk_engine_v2_review_valid"] if valid else ["risk_engine_v2_blocked"]),
        "errors": _dedupe(errors),
        "generated_at": generated_at,
        **risk_engine_v2_safety_flags(),
    }


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


def _value_present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(clean_text(value)) and clean_text(value).lower() not in {"blocked", "missing", "redacted"}
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
