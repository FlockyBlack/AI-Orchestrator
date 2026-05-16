from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text
from pm_bot.trading_core.selected_token_verification_models import (
    REQUIRED_FALSE_FLAGS as SELECTED_TOKEN_VERIFICATION_REQUIRED_FALSE_FLAGS,
    selected_token_verification_safety_flags,
)

TASK_ID = "ORCH-PMBOT-TRADING-MVP-076D-PAYLOAD-DRY-RUN-READINESS-CONSOLIDATION-NO-LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

MODE = "payload dry-run readiness consolidation / no-live / no-submit"
EXECUTION_MODE = "local_artifact_read_only_payload_dry_run_readiness_review"

PAYLOAD_DRY_RUN_READINESS_CONFIG_CONTRACT = "pmbot_payload_dry_run_readiness_076d_config.v1"
PAYLOAD_DRY_RUN_READINESS_RESULT_CONTRACT = "pmbot_payload_dry_run_readiness_076d_result.v1"
PAYLOAD_DRY_RUN_READINESS_LATEST_STATUS_CONTRACT = "pmbot_latest_payload_dry_run_readiness_076d_status.v1"
PAYLOAD_DRY_RUN_READINESS_BLOCKERS_CONTRACT = "pmbot_payload_dry_run_readiness_076d_blockers.v1"
PAYLOAD_DRY_RUN_READINESS_VALIDATION_CONTRACT = "pmbot_payload_dry_run_readiness_076d_validation.v1"

STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE = "blocked_missing_selected_candidate"
STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN = "blocked_unverified_selected_token"
STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK = "blocked_signer_diagnostic_not_ok"
STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY = "blocked_signed_payload_dry_run_not_ready"
STATUS_BLOCKED_RISK_ENGINE_REVIEW = "blocked_risk_engine_review"
STATUS_READY_FOR_OPERATOR_REVIEW = "payload_dry_run_ready_for_operator_review"

VALID_STATUSES = {
    STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE,
    STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY,
    STATUS_BLOCKED_RISK_ENGINE_REVIEW,
    STATUS_READY_FOR_OPERATOR_REVIEW,
}

REQUIRED_FALSE_FLAGS = tuple(
    dict.fromkeys(
        (
            *SELECTED_TOKEN_VERIFICATION_REQUIRED_FALSE_FLAGS,
            "payload_dry_run_review_executable",
            "payload_dry_run_approves_live",
            "payload_dry_run_authorizes_order",
            "payload_dry_run_authorizes_submit",
            "payload_dry_run_ready_for_submit",
            "submit_ready",
            "live_ready",
            "allowed_for_live",
            "order_submission_enabled",
            "order_submission_performed",
            "order_cancellation_enabled",
            "order_cancellation_performed",
            "signing_by_default",
            "signing_enabled",
            "signing_performed",
            "signer_instantiated",
            "signer_instantiated_by_default",
            "wallet_connected",
            "wallet_connection_enabled",
            "full_signed_payload_output",
            "full_signed_order_output",
            "raw_signed_payload_emitted",
            "raw_signed_order_emitted",
            "real_order_submitted",
            "real_order_cancelled",
            "live_trading_enabled",
            "background_worker_added",
            "scheduler_or_daemon_added",
            "autonomous_live_trading_added",
        )
    )
)

FORBIDDEN_RAW_FIELD_NAMES = frozenset(
    {
        "token_id",
        "selected_token_id",
        "outcome_token_id",
        "clob_token_id",
        "target_token_id",
        "operator_selected_token_id",
        "raw_token_id",
        "full_token_id",
        "private_key",
        "wallet_private_key",
        "seed_phrase",
        "mnemonic",
        "api_secret",
        "auth_token",
        "passphrase",
        "secret",
        "signature",
        "signed_payload",
        "signed_order",
        "order_id",
        "client_order_id",
        "tx_hash",
        "transaction_hash",
        "fill_id",
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
class PayloadDryRunReadinessConfig:
    market: str
    strategy: str
    dry_run: bool
    artifact_root: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PAYLOAD_DRY_RUN_READINESS_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = _market(self.market)
        value["market_symbol"] = _market(self.market)
        value["strategy"] = _strategy(self.strategy)
        value["strategy_name"] = _strategy(self.strategy)
        value["dry_run"] = self.dry_run is True
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value.update(payload_dry_run_readiness_safety_flags())
        return value


def payload_dry_run_readiness_safety_flags() -> dict[str, Any]:
    value = selected_token_verification_safety_flags()
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
            "payload_dry_run_review_executable": False,
            "payload_dry_run_approves_live": False,
            "payload_dry_run_authorizes_order": False,
            "payload_dry_run_authorizes_submit": False,
            "payload_dry_run_ready_for_submit": False,
            "submit_ready": False,
            "live_ready": False,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "order_submission_performed": False,
            "order_cancellation_enabled": False,
            "order_cancellation_performed": False,
            "signing_by_default": False,
            "signing_enabled": False,
            "signing_performed": False,
            "signer_instantiated": False,
            "signer_instantiated_by_default": False,
            "wallet_connected": False,
            "wallet_connection_enabled": False,
            "full_signed_payload_output": False,
            "full_signed_order_output": False,
            "raw_signed_payload_emitted": False,
            "raw_signed_order_emitted": False,
            "real_order_submitted": False,
            "real_order_cancelled": False,
            "live_trading_enabled": False,
            "background_worker_added": False,
            "scheduler_or_daemon_added": False,
            "autonomous_live_trading_added": False,
            "source_payloads_embedded": False,
            "raw_token_ids_embedded": False,
            "fake_token_id_generated": False,
            "fake_balances_emitted": False,
            "fake_orders_emitted": False,
            "fake_fills_emitted": False,
            "fake_pnl_emitted": False,
        }
    )
    return value


def validate_payload_dry_run_readiness_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(value.get("status"))

    if value.get("contract_version") != PAYLOAD_DRY_RUN_READINESS_RESULT_CONTRACT:
        errors.append(f"contract_version must be {PAYLOAD_DRY_RUN_READINESS_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if status not in VALID_STATUSES:
        errors.append("status must be one of the 076D payload dry-run readiness statuses")
        statuses.append("invalid_status")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")

    for field in (
        "allowed_for_live",
        "live_ready",
        "submit_ready",
        "payload_dry_run_ready_for_submit",
        "order_submission_enabled",
        "signing_by_default",
    ):
        if value.get(field) is not False:
            errors.append(f"{field} must be false for 076D")
            statuses.append(f"{field}_must_be_false")

    component_statuses = value.get("component_statuses")
    component_statuses = component_statuses if isinstance(component_statuses, Mapping) else {}
    if status == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE:
        selected_candidate = component_statuses.get("selected_candidate")
        if not isinstance(selected_candidate, Mapping) or selected_candidate.get("ready") is not False:
            errors.append("missing selected candidate status requires selected_candidate.ready=false")
            statuses.append("selected_candidate_status_mismatch")
    if status == STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN:
        verification = component_statuses.get("selected_token_verification")
        if not isinstance(verification, Mapping) or verification.get("verified") is not False:
            errors.append("unverified selected token status requires selected_token_verification.verified=false")
            statuses.append("selected_token_verification_status_mismatch")
    if status == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK:
        signer = component_statuses.get("signer_diagnostic_evidence")
        if not isinstance(signer, Mapping) or signer.get("diagnostic_ok") is not False:
            errors.append("signer diagnostic blocker requires signer_diagnostic_evidence.diagnostic_ok=false")
            statuses.append("signer_diagnostic_status_mismatch")
    if status == STATUS_READY_FOR_OPERATOR_REVIEW:
        required_true = (
            ("selected_candidate", "ready"),
            ("selected_token_verification", "verified"),
            ("signer_diagnostic_evidence", "diagnostic_ok"),
            ("payload_dry_run", "ready"),
            ("risk_engine", "ready"),
        )
        for section, field in required_true:
            payload = component_statuses.get(section)
            if not isinstance(payload, Mapping) or payload.get(field) is not True:
                errors.append(f"{section}.{field} must be true for ready operator review")
                statuses.append(f"{section}_{field}_not_true")

    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("resolved_blocker_detected")
        if key in FORBIDDEN_RAW_FIELD_NAMES:
            errors.append(f"{path}.{key} must not be emitted by 076D; use fingerprints or summaries")
            statuses.append("raw_or_sensitive_field_detected")

    valid = not errors
    return {
        "contract_version": PAYLOAD_DRY_RUN_READINESS_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (["payload_dry_run_readiness_076d_valid"] if valid else ["payload_dry_run_readiness_076d_blocked"]),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **payload_dry_run_readiness_safety_flags(),
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
