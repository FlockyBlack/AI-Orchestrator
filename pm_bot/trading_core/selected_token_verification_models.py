from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.operator_token_selection_models import (
    REQUIRED_FALSE_FLAGS as OPERATOR_TOKEN_SELECTION_REQUIRED_FALSE_FLAGS,
    operator_token_selection_safety_flags,
)
from pm_bot.trading_core.selected_candidate_artifact_models import (
    REQUIRED_FALSE_FLAGS as SELECTED_CANDIDATE_REQUIRED_FALSE_FLAGS,
)
from pm_bot.trading_core.selected_token_payload_readiness_models import (
    REQUIRED_FALSE_FLAGS as PAYLOAD_READINESS_REQUIRED_FALSE_FLAGS,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-076A-SELECTED-TOKEN-VERIFICATION-BRIDGE-NO-LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

MODE = "selected token verification bridge / dry-run / no-live / no-submit"
EXECUTION_MODE = "local_artifact_read_only_verification_bridge"

SELECTED_TOKEN_VERIFICATION_CONFIG_CONTRACT = "pmbot_selected_token_verification_bridge_076a_config.v1"
SELECTED_TOKEN_VERIFICATION_RESULT_CONTRACT = "pmbot_selected_token_verification_bridge_076a_result.v1"
SELECTED_TOKEN_VERIFICATION_LATEST_STATUS_CONTRACT = (
    "pmbot_latest_selected_token_verification_bridge_076a_status.v1"
)
SELECTED_TOKEN_VERIFICATION_EVIDENCE_CONTRACT = "pmbot_selected_token_verification_bridge_076a_evidence.v1"
SELECTED_TOKEN_VERIFICATION_VALIDATION_CONTRACT = "pmbot_selected_token_verification_bridge_076a_validation.v1"

STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE_ARTIFACT = "blocked_missing_selected_candidate_artifact"
STATUS_BLOCKED_SELECTED_TOKEN_NOT_SOURCE_VERIFIED = "blocked_selected_token_not_source_verified"
STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN = "selected_token_verified_for_payload_dry_run"

VALID_STATUSES = {
    STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE_ARTIFACT,
    STATUS_BLOCKED_SELECTED_TOKEN_NOT_SOURCE_VERIFIED,
    STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN,
}

REQUIRED_FALSE_FLAGS = tuple(
    dict.fromkeys(
        (
            *OPERATOR_TOKEN_SELECTION_REQUIRED_FALSE_FLAGS,
            *SELECTED_CANDIDATE_REQUIRED_FALSE_FLAGS,
            *PAYLOAD_READINESS_REQUIRED_FALSE_FLAGS,
            "selected_token_verification_executable",
            "selected_token_verification_approves_live",
            "selected_token_verification_approves_submit",
            "selected_token_verification_authorizes_order",
            "selected_token_payload_ready_for_submit",
            "ready_for_submit",
            "submit_ready",
            "allowed_for_live",
            "live_ready",
            "live_execution_ready",
            "signing_ready",
            "signer_instantiated",
            "wallet_connected",
            "payload_written_for_submit",
        )
    )
)

FORBIDDEN_RAW_TOKEN_FIELD_NAMES = frozenset(
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
class SelectedTokenVerificationConfig:
    market: str
    strategy: str
    dry_run: bool
    artifact_root: str
    selected_candidate_artifact_path: str
    operator_token_selection_packet_path: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SELECTED_TOKEN_VERIFICATION_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = _market(self.market)
        value["market_symbol"] = _market(self.market)
        value["strategy"] = _strategy(self.strategy)
        value["strategy_name"] = _strategy(self.strategy)
        value["dry_run"] = self.dry_run is True
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value.update(selected_token_verification_safety_flags())
        return value


def selected_token_verification_safety_flags() -> dict[str, Any]:
    value = operator_token_selection_safety_flags()
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
            "public_data_only": True,
            "safe_summary_only": True,
            "non_executable": True,
            "selected_token_verification_executable": False,
            "selected_token_verification_approves_live": False,
            "selected_token_verification_approves_submit": False,
            "selected_token_verification_authorizes_order": False,
            "selected_token_payload_ready_for_submit": False,
            "ready_for_submit": False,
            "submit_ready": False,
            "allowed_for_live": False,
            "live_ready": False,
            "live_execution_ready": False,
            "signing_ready": False,
            "signer_instantiated": False,
            "wallet_connected": False,
            "payload_written_for_submit": False,
            "raw_token_id_exposed": False,
            "full_token_id_included": False,
            "raw_token_id_persisted": False,
            "full_token_id_persisted": False,
            "source_payloads_embedded": False,
            "raw_token_ids_embedded": False,
        }
    )
    return value


def validate_selected_token_verification_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(value.get("status"))

    if value.get("contract_version") != SELECTED_TOKEN_VERIFICATION_RESULT_CONTRACT:
        errors.append(f"contract_version must be {SELECTED_TOKEN_VERIFICATION_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if status not in VALID_STATUSES:
        errors.append("status must be one of the 076A selected token verification bridge statuses")
        statuses.append("invalid_status")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_detected")
    if value.get("selected_token_payload_ready_for_submit") is not False:
        errors.append("selected_token_payload_ready_for_submit must be false")
        statuses.append("submit_readiness_detected")

    if status == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE_ARTIFACT:
        if value.get("selected_candidate_artifact_present") is not False:
            errors.append("missing selected candidate artifact status requires selected_candidate_artifact_present=false")
            statuses.append("missing_artifact_status_mismatch")
    if status == STATUS_BLOCKED_SELECTED_TOKEN_NOT_SOURCE_VERIFIED:
        if value.get("selected_token_verified_for_payload_dry_run") is not False:
            errors.append("blocked verification status requires selected_token_verified_for_payload_dry_run=false")
            statuses.append("blocked_verification_status_mismatch")
    if status == STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN:
        required_true = (
            "selected_candidate_artifact_present",
            "candidate_index_exists",
            "selected_by_operator",
            "source_backed",
            "token_hash_match",
            "candidate_index_match",
            "market_match",
            "strategy_match",
            "market_title_match",
            "outcome_label_match",
            "selected_candidate_in_known_candidate_set",
            "selected_token_verified_for_payload_dry_run",
        )
        for field in required_true:
            if value.get(field) is not True:
                errors.append(f"{field} must be true for verified payload dry-run status")
                statuses.append(f"{field}_not_true")

    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("resolved_blocker_detected")
        if key in FORBIDDEN_RAW_TOKEN_FIELD_NAMES:
            errors.append(f"{path}.{key} must not be emitted by 076A; use token_id_short and token_id_hash")
            statuses.append("raw_or_sensitive_field_detected")

    valid = not errors
    return {
        "contract_version": SELECTED_TOKEN_VERIFICATION_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["selected_token_verification_bridge_valid"]
            if valid
            else ["selected_token_verification_bridge_blocked"]
        ),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **selected_token_verification_safety_flags(),
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
