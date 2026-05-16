from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.operator_token_selection_models import (
    REQUIRED_FALSE_FLAGS as OPERATOR_TOKEN_SELECTION_REQUIRED_FALSE_FLAGS,
    operator_token_selection_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-075D-SELECTED-CANDIDATE-ARTIFACT-CONTRACT-NO-LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

MODE = "selected candidate artifact / dry-run / review-only / no-live"
EXECUTION_MODE = "local_artifact_read_only_selection_record"

SELECTED_CANDIDATE_ARTIFACT_CONFIG_CONTRACT = "pmbot_selected_candidate_artifact_config_075d.v1"
SELECTED_CANDIDATE_ARTIFACT_CONTRACT = "pmbot_selected_candidate_artifact_075d.v1"
SELECTED_CANDIDATE_ARTIFACT_RESULT_CONTRACT = "pmbot_selected_candidate_artifact_075d_result.v1"
SELECTED_CANDIDATE_ARTIFACT_LATEST_STATUS_CONTRACT = "pmbot_latest_selected_candidate_artifact_075d.v1"
SELECTED_CANDIDATE_ARTIFACT_SAFETY_SNAPSHOT_CONTRACT = "pmbot_selected_candidate_artifact_safety_snapshot_075d.v1"
SELECTED_CANDIDATE_ARTIFACT_SOURCE_SNAPSHOT_CONTRACT = "pmbot_selected_candidate_artifact_source_snapshot_075d.v1"
SELECTED_CANDIDATE_ARTIFACT_VALIDATION_CONTRACT = "pmbot_selected_candidate_artifact_validation_075d.v1"

STATUS_OPERATOR_SELECTION_REQUIRED = "operator_selection_required"
STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED = "selected_candidate_artifact_recorded"
STATUS_BLOCKED_INVALID_CANDIDATE_INDEX = "blocked_invalid_candidate_index"
STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED = "blocked_candidate_not_source_backed"

VALID_STATUSES = {
    STATUS_OPERATOR_SELECTION_REQUIRED,
    STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED,
    STATUS_BLOCKED_INVALID_CANDIDATE_INDEX,
    STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED,
}

EXPLICIT_WARNINGS = (
    "not live approval",
    "not trading authorization",
    "not submit-ready",
)

REQUIRED_FALSE_FLAGS = tuple(
    dict.fromkeys(
        (
            *OPERATOR_TOKEN_SELECTION_REQUIRED_FALSE_FLAGS,
            "selected_candidate_executable_for_live",
            "selected_candidate_executable",
            "selected_candidate_submit_ready",
            "selected_candidate_approves_live",
            "selected_candidate_approves_trading",
            "selected_candidate_approves_submit",
            "selected_candidate_authorizes_order",
            "live_approval_recorded",
            "trading_authorization_recorded",
            "submit_authorization_recorded",
            "order_authorization_recorded",
            "order_payload_ready",
            "ready_for_submit",
            "submit_ready",
            "raw_token_id_exposed",
            "full_token_id_included",
            "raw_token_id_persisted",
            "full_token_id_persisted",
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
    }
)


@dataclass(frozen=True)
class SelectedCandidateArtifactConfig:
    market: str
    strategy: str
    dry_run: bool
    artifact_root: str
    operator_token_selection_packet_path: str
    candidate_index: str
    created_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SELECTED_CANDIDATE_ARTIFACT_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = _market(self.market)
        value["market_symbol"] = _market(self.market)
        value["strategy"] = _strategy(self.strategy)
        value["strategy_name"] = _strategy(self.strategy)
        value["dry_run"] = self.dry_run is True
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value["generated_at"] = self.created_at
        value.update(selected_candidate_artifact_safety_flags())
        return value


@dataclass(frozen=True)
class SelectedCandidateArtifact:
    market: str
    strategy: str
    candidate_index: int
    candidate_id: str
    market_title: str
    market_slug: str
    outcome_label: str
    outcome_index: int
    token_id_short: str
    token_id_hash: str
    source_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    created_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SELECTED_CANDIDATE_ARTIFACT_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = _market(self.market)
        value["market_symbol"] = _market(self.market)
        value["strategy"] = _strategy(self.strategy)
        value["strategy_name"] = _strategy(self.strategy)
        value["source_ids"] = [clean_text(item) for item in self.source_ids if clean_text(item)]
        value["source_paths"] = [clean_text(item) for item in self.source_paths if clean_text(item)]
        value["token_id_hash_algorithm"] = "sha256"
        value["token_id_redaction"] = "shortened_and_sha256_only"
        value["source_backed"] = True
        value["token_id_source_backed"] = True
        value["selected_by_operator"] = True
        value["operator_selection_recorded"] = True
        value["selected_candidate_artifact_written"] = True
        value["selected_candidate_artifact_recorded"] = True
        value["selected_candidate_executable_for_live"] = False
        value["selected_candidate_executable"] = False
        value["selected_candidate_submit_ready"] = False
        value["selected_candidate_approves_live"] = False
        value["selected_candidate_approves_trading"] = False
        value["selected_candidate_approves_submit"] = False
        value["selected_candidate_authorizes_order"] = False
        value["live_approval_recorded"] = False
        value["trading_authorization_recorded"] = False
        value["submit_authorization_recorded"] = False
        value["order_authorization_recorded"] = False
        value["order_payload_ready"] = False
        value["ready_for_submit"] = False
        value["submit_ready"] = False
        value["allowed_for_live"] = False
        value["explicit_warnings"] = list(EXPLICIT_WARNINGS)
        value["warnings"] = list(EXPLICIT_WARNINGS)
        value["raw_token_id_exposed"] = False
        value["full_token_id_included"] = False
        value["raw_token_id_persisted"] = False
        value["full_token_id_persisted"] = False
        value["generated_at"] = self.created_at
        value.update(selected_candidate_artifact_safety_flags())
        return value


def selected_candidate_artifact_safety_flags() -> dict[str, Any]:
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
            "allowed_for_live": False,
            "selected_candidate_executable_for_live": False,
            "selected_candidate_executable": False,
            "selected_candidate_submit_ready": False,
            "selected_candidate_approves_live": False,
            "selected_candidate_approves_trading": False,
            "selected_candidate_approves_submit": False,
            "selected_candidate_authorizes_order": False,
            "live_approval_recorded": False,
            "trading_authorization_recorded": False,
            "submit_authorization_recorded": False,
            "order_authorization_recorded": False,
            "order_payload_ready": False,
            "ready_for_submit": False,
            "submit_ready": False,
            "raw_token_id_exposed": False,
            "full_token_id_included": False,
            "raw_token_id_persisted": False,
            "full_token_id_persisted": False,
            "selection_is_live_trading": False,
            "selection_approves_trading": False,
            "selection_approves_live_execution": False,
            "selection_approves_submit": False,
        }
    )
    return value


def build_safety_snapshot(*, status: str, created_at: str = GENERATED_AT) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_CANDIDATE_ARTIFACT_SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "safety_statement": (
            "075D reads local 073B source-backed candidate artifacts only and records an operator-selected "
            "candidate as a review-only artifact. It never invents token IDs, emits full token IDs, creates "
            "orders, signs payloads, submits, cancels, connects a wallet, reads secrets, calls Polymarket, "
            "or approves live trading."
        ),
        "explicit_warnings": list(EXPLICIT_WARNINGS),
        "created_at": created_at,
        "generated_at": created_at,
    }
    value.update(selected_candidate_artifact_safety_flags())
    return value


def validate_selected_candidate_artifact_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    artifact = dict(value.get("selected_candidate_artifact", {}))
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(value.get("status"))

    if value.get("contract_version") != SELECTED_CANDIDATE_ARTIFACT_RESULT_CONTRACT:
        errors.append(f"contract_version must be {SELECTED_CANDIDATE_ARTIFACT_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if status not in VALID_STATUSES:
        errors.append("status must be one of the 075D selected candidate artifact statuses")
        statuses.append("invalid_status")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_detected")
    if value.get("selected_candidate_executable_for_live") is not False:
        errors.append("selected_candidate_executable_for_live must be false")
        statuses.append("selected_candidate_executable_detected")
    if status == STATUS_OPERATOR_SELECTION_REQUIRED and value.get("candidate_index_provided") is not False:
        errors.append("operator_selection_required requires no candidate index")
        statuses.append("operator_selection_required_index_present")
    if status == STATUS_BLOCKED_INVALID_CANDIDATE_INDEX and value.get("candidate_index_valid") is not False:
        errors.append("blocked_invalid_candidate_index requires candidate_index_valid=false")
        statuses.append("invalid_index_status_mismatch")
    if status == STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED and value.get("selected_candidate_source_backed") is not False:
        errors.append("blocked_candidate_not_source_backed requires selected_candidate_source_backed=false")
        statuses.append("source_backed_status_mismatch")
    if status == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED:
        if artifact.get("contract_version") != SELECTED_CANDIDATE_ARTIFACT_CONTRACT:
            errors.append(f"selected_candidate_artifact.contract_version must be {SELECTED_CANDIDATE_ARTIFACT_CONTRACT}")
            statuses.append("invalid_artifact_contract")
        if artifact.get("source_backed") is not True:
            errors.append("selected candidate artifact requires source_backed=true")
            statuses.append("artifact_not_source_backed")
        if artifact.get("selected_by_operator") is not True:
            errors.append("selected candidate artifact requires selected_by_operator=true")
            statuses.append("artifact_not_operator_selected")
        if not clean_text(artifact.get("token_id_short")):
            errors.append("selected candidate artifact requires token_id_short")
            statuses.append("artifact_missing_token_id_short")
        if len(clean_text(artifact.get("token_id_hash"))) != 64:
            errors.append("selected candidate artifact requires sha256 token_id_hash")
            statuses.append("artifact_missing_token_id_hash")
        if tuple(artifact.get("explicit_warnings", ())) != EXPLICIT_WARNINGS:
            errors.append("selected candidate artifact must include the explicit warning contract")
            statuses.append("artifact_warning_contract_mismatch")

    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("resolved_blocker_detected")
        if key in FORBIDDEN_RAW_TOKEN_FIELD_NAMES:
            errors.append(f"{path}.{key} must not be emitted by 075D; use token_id_short and token_id_hash")
            statuses.append("raw_token_field_detected")

    valid = not errors
    return {
        "contract_version": SELECTED_CANDIDATE_ARTIFACT_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["selected_candidate_artifact_valid"]
            if valid
            else ["selected_candidate_artifact_blocked"]
        ),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **selected_candidate_artifact_safety_flags(),
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
