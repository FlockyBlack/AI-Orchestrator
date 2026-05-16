from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.guarded_signer_diagnostic_models import (
    REQUIRED_FALSE_FLAGS as GUARDED_SIGNER_REQUIRED_FALSE_FLAGS,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text
from pm_bot.trading_core.selected_token_payload_readiness_models import (
    REQUIRED_FALSE_FLAGS as PAYLOAD_READINESS_REQUIRED_FALSE_FLAGS,
    selected_token_payload_readiness_safety_flags,
)

TASK_ID = "ORCH-PMBOT-TRADING-MVP-076C-SIGNER-DIAGNOSTIC-EVIDENCE-BRIDGE-NO-LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

MODE = "signer diagnostic evidence bridge / local artifact read-only / no-live"
EXECUTION_MODE = "local_artifact_read_only_evidence_bridge"

SIGNER_DIAGNOSTIC_EVIDENCE_RESULT_CONTRACT = "pmbot_signer_diagnostic_evidence_bridge_076c_result.v1"
SIGNER_DIAGNOSTIC_EVIDENCE_LATEST_STATUS_CONTRACT = (
    "pmbot_latest_signer_diagnostic_evidence_bridge_076c_status.v1"
)
SIGNER_DIAGNOSTIC_EVIDENCE_VALIDATION_CONTRACT = (
    "pmbot_signer_diagnostic_evidence_bridge_076c_validation.v1"
)
SIGNER_DIAGNOSTIC_EVIDENCE_SAFETY_SNAPSHOT_CONTRACT = (
    "pmbot_signer_diagnostic_evidence_bridge_076c_safety_snapshot.v1"
)

STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE = "blocked_missing_signer_diagnostic_evidence"
STATUS_BLOCKED_SIGNER_DIAGNOSTIC_FAILED = "blocked_signer_diagnostic_failed"
STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN = (
    "signer_diagnostic_evidence_ok_for_payload_dry_run"
)

VALID_STATUSES = {
    STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_FAILED,
    STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN,
}

REQUIRED_FALSE_FLAGS = tuple(
    dict.fromkeys(
        (
            *GUARDED_SIGNER_REQUIRED_FALSE_FLAGS,
            *PAYLOAD_READINESS_REQUIRED_FALSE_FLAGS,
            "signer_ready_for_live",
            "signer_instantiated",
            "signer_instantiation_attempted",
            "signer_diagnostic_executed_by_bridge",
            "order_submit_ready",
            "full_signed_payload_output",
            "signing_by_default",
            "live",
        )
    )
)

FORBIDDEN_VALUE_FIELD_NAMES = frozenset(
    {
        "private_key",
        "wallet_private_key",
        "seed_phrase",
        "mnemonic",
        "api_secret",
        "auth_token",
        "passphrase",
        "secret",
        "raw_value",
        "masked_value",
        "signature",
        "signed_payload",
        "signed_order",
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill_id",
        "fill",
        "fills",
        "fill_price",
        "filled_size",
        "balance",
        "balances",
        "position",
        "positions",
        "pnl",
        "realized_pnl",
        "unrealized_pnl",
    }
)


@dataclass(frozen=True)
class SignerDiagnosticEvidenceSafetySnapshot:
    market_symbol: str = DEFAULT_MARKET
    strategy_name: str = DEFAULT_STRATEGY
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": SIGNER_DIAGNOSTIC_EVIDENCE_SAFETY_SNAPSHOT_CONTRACT,
            "task_id": TASK_ID,
            "status": "active_signer_diagnostic_evidence_bridge_safety_snapshot",
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "market": _market(self.market_symbol),
            "market_symbol": _market(self.market_symbol),
            "strategy_name": _strategy(self.strategy_name),
            "local_artifact_read_only": True,
            "bridge_executes_signer_diagnostic": False,
            "bridge_reads_private_key": False,
            "bridge_instantiates_signer": False,
            "bridge_generates_signed_payload": False,
            "full_signed_payload_output_allowed": False,
            "raw_private_key_output_allowed": False,
            "api_secret_output_allowed": False,
            "order_submit_ready": False,
            "signer_ready_for_live": False,
            "generated_at": self.generated_at,
        }
        value.update(signer_diagnostic_evidence_safety_flags())
        return value


def signer_diagnostic_evidence_safety_flags() -> dict[str, Any]:
    value = selected_token_payload_readiness_safety_flags()
    value.update(
        {
            "mode": MODE,
            "execution_mode": EXECUTION_MODE,
            "paper_only": True,
            "review_only": True,
            "preflight_only": True,
            "dry_run_only": True,
            "local_artifact_only": True,
            "local_artifact_read_only": True,
            "read_only": True,
            "safe_summary_only": True,
            "non_executable": True,
            "signer_diagnostic_executed_by_bridge": False,
            "signer_instantiated": False,
            "signer_instantiation_attempted": False,
            "signer_ready_for_live": False,
            "order_submit_ready": False,
            "full_signed_payload_output": False,
            "signing_by_default": False,
            "live": False,
            "source_payload_embedded": False,
            "source_payloads_embedded": False,
            "raw_secret_values_embedded": False,
            "full_signed_payload_embedded": False,
        }
    )
    return value


def validate_signer_diagnostic_evidence_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(value.get("status"))

    if value.get("contract_version") != SIGNER_DIAGNOSTIC_EVIDENCE_RESULT_CONTRACT:
        errors.append(f"contract_version must be {SIGNER_DIAGNOSTIC_EVIDENCE_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")
        statuses.append("task_id_mismatch")
    if status not in VALID_STATUSES:
        errors.append("status must be a recognized 076C signer diagnostic evidence status")
        statuses.append("invalid_status")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_detected")
    if value.get("signer_ready_for_live") is not False:
        errors.append("signer_ready_for_live must be false")
        statuses.append("signer_ready_for_live_detected")
    if value.get("order_submit_ready") is not False:
        errors.append("order_submit_ready must be false")
        statuses.append("order_submit_ready_detected")
    if value.get("full_signed_payload_output") is not False:
        errors.append("full_signed_payload_output must be false")
        statuses.append("full_signed_payload_output_detected")

    if status == STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN:
        if value.get("signer_diagnostic_evidence_ok_for_payload_dry_run") is not True:
            errors.append("OK status requires signer_diagnostic_evidence_ok_for_payload_dry_run=true")
            statuses.append("ok_status_without_ok_flag")
    else:
        if value.get("signer_diagnostic_evidence_ok_for_payload_dry_run") is not False:
            errors.append("blocked status requires signer_diagnostic_evidence_ok_for_payload_dry_run=false")
            statuses.append("blocked_status_with_ok_flag")

    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("resolved_blocker_detected")
        if key in FORBIDDEN_VALUE_FIELD_NAMES and nested:
            errors.append(f"{path}.{key} must not be emitted")
            statuses.append("forbidden_value_emitted")

    valid = not errors
    return {
        "contract_version": SIGNER_DIAGNOSTIC_EVIDENCE_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["signer_diagnostic_evidence_bridge_valid"]
            if valid
            else ["signer_diagnostic_evidence_bridge_blocked"]
        ),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **signer_diagnostic_evidence_safety_flags(),
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


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
