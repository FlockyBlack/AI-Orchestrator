from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.operator_token_selection_models import (
    REQUIRED_FALSE_FLAGS as OPERATOR_TOKEN_SELECTION_REQUIRED_FALSE_FLAGS,
    operator_token_selection_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-075A-SELECTED-CANDIDATE-OPERATOR-INSTRUCTION-PACKET-NO-LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

MODE = "selected candidate instruction packet / dry-run / review-only / no-live"
EXECUTION_MODE = "local_artifact_read_only_instruction_packet"

SELECTED_CANDIDATE_INSTRUCTION_CONFIG_CONTRACT = "pmbot_selected_candidate_instruction_config_075a.v1"
SELECTED_CANDIDATE_INSTRUCTION_CANDIDATE_CONTRACT = "pmbot_selected_candidate_instruction_candidate_075a.v1"
SELECTED_CANDIDATE_INSTRUCTION_CANDIDATES_CONTRACT = "pmbot_selected_candidate_instruction_candidates_075a.v1"
SELECTED_CANDIDATE_INSTRUCTION_PACKET_CONTRACT = "pmbot_selected_candidate_instruction_packet_075a.v1"
SELECTED_CANDIDATE_INSTRUCTION_RESULT_CONTRACT = "pmbot_selected_candidate_instruction_packet_075a_result.v1"
SELECTED_CANDIDATE_INSTRUCTION_LATEST_STATUS_CONTRACT = (
    "pmbot_latest_selected_candidate_instruction_packet_075a.v1"
)
SELECTED_CANDIDATE_INSTRUCTION_SAFETY_SNAPSHOT_CONTRACT = (
    "pmbot_selected_candidate_instruction_safety_snapshot_075a.v1"
)
SELECTED_CANDIDATE_INSTRUCTION_VALIDATION_CONTRACT = "pmbot_selected_candidate_instruction_validation_075a.v1"

STATUS_OPERATOR_SELECTION_REQUIRED = "operator_selection_required"
STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES = "blocked_missing_source_backed_candidates"

VALID_STATUSES = {
    STATUS_OPERATOR_SELECTION_REQUIRED,
    STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES,
}

REQUIRED_FALSE_FLAGS = tuple(
    dict.fromkeys(
        (
            *OPERATOR_TOKEN_SELECTION_REQUIRED_FALSE_FLAGS,
            "instruction_packet_executable_for_live",
            "instruction_packet_generated_selected_token",
            "selection_artifact_write_supported",
            "selection_artifact_write_performed",
            "selected_candidate_artifact_written",
            "selected_token_artifact_written",
            "selected_token_id_present",
            "selected_token_source_backed",
            "operator_selection_recorded",
            "operator_selection_applied",
            "operator_selection_mutation_performed",
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
class SelectedCandidateInstructionConfig:
    market: str
    strategy: str
    dry_run: bool
    artifact_root: str
    operator_token_selection_packet_path: str
    candidate_index: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SELECTED_CANDIDATE_INSTRUCTION_CONFIG_CONTRACT
        value["task_id"] = TASK_ID
        value["market"] = _market(self.market)
        value["market_symbol"] = _market(self.market)
        value["strategy"] = _strategy(self.strategy)
        value["strategy_name"] = _strategy(self.strategy)
        value["dry_run"] = self.dry_run is True
        value["mode"] = MODE
        value["execution_mode"] = EXECUTION_MODE
        value.update(selected_candidate_instruction_safety_flags())
        return value


@dataclass(frozen=True)
class SelectedCandidateInstructionCandidate:
    candidate_index: int
    display_index: int
    candidate_id: str
    market_title: str
    market_slug: str
    outcome_label: str
    outcome_index: int
    token_id_short: str
    source_ids: tuple[str, ...]
    source_paths: tuple[str, ...]
    evidence_summary: tuple[str, ...]
    safe_cli_command: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = SELECTED_CANDIDATE_INSTRUCTION_CANDIDATE_CONTRACT
        value["task_id"] = TASK_ID
        value["source_ids"] = [clean_text(item) for item in self.source_ids if clean_text(item)]
        value["source_paths"] = [clean_text(item) for item in self.source_paths if clean_text(item)]
        value["evidence_summary"] = [
            clean_text(item) for item in self.evidence_summary if clean_text(item)
        ]
        value["source_backed"] = True
        value["token_id_source_backed"] = True
        value["token_id_present_in_source"] = clean_text(self.token_id_short) != "missing"
        value["token_id_shortened"] = True
        value["raw_token_id_exposed"] = False
        value["full_token_id_included"] = False
        value["operator_selectable"] = True
        value["requires_manual_operator_selection"] = True
        value["selection_command_writes_075a_artifacts"] = False
        value["selection_command_reuses_073b_contract"] = True
        value.update(selected_candidate_instruction_safety_flags())
        return value


def selected_candidate_instruction_safety_flags() -> dict[str, Any]:
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
            "instruction_packet_executable_for_live": False,
            "instruction_packet_generated_selected_token": False,
            "selection_artifact_write_supported": False,
            "selection_artifact_write_performed": False,
            "selected_candidate_artifact_written": False,
            "selected_token_artifact_written": False,
            "selected_token_id_present": False,
            "selected_token_source_backed": False,
            "operator_selection_recorded": False,
            "operator_selection_applied": False,
            "operator_selection_mutation_performed": False,
            "raw_token_id_exposed": False,
            "full_token_id_included": False,
            "selection_is_live_trading": False,
            "selection_approves_trading": False,
            "selection_approves_live_execution": False,
        }
    )
    return value


def build_safety_snapshot(*, status: str, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_CANDIDATE_INSTRUCTION_SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "safety_statement": (
            "075A reads local 073B source-backed candidate artifacts only and emits a review-only "
            "operator instruction packet. It does not select a token, mutate selection state, invent "
            "token IDs, create orders, sign payloads, submit, cancel, read secrets, call Polymarket, "
            "or approve live trading."
        ),
        "generated_at": generated_at,
    }
    value.update(selected_candidate_instruction_safety_flags())
    return value


def validate_selected_candidate_instruction_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    packet = dict(value.get("packet", {}))
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(value.get("status"))
    candidate_count = _safe_int(value.get("source_backed_candidate_count"))

    if value.get("contract_version") != SELECTED_CANDIDATE_INSTRUCTION_RESULT_CONTRACT:
        errors.append(f"contract_version must be {SELECTED_CANDIDATE_INSTRUCTION_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if packet.get("contract_version") != SELECTED_CANDIDATE_INSTRUCTION_PACKET_CONTRACT:
        errors.append(f"packet.contract_version must be {SELECTED_CANDIDATE_INSTRUCTION_PACKET_CONTRACT}")
        statuses.append("invalid_packet_contract")
    if status not in VALID_STATUSES:
        errors.append("status must be one of the 075A selected candidate instruction statuses")
        statuses.append("invalid_status")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must be false")
        statuses.append("allowed_for_live_detected")
    if value.get("instruction_packet_executable_for_live") is not False:
        errors.append("instruction_packet_executable_for_live must be false")
        statuses.append("instruction_packet_executable_detected")
    if value.get("selected_candidate_artifact_written") is not False:
        errors.append("selected_candidate_artifact_written must be false")
        statuses.append("selected_candidate_artifact_written_detected")
    if value.get("selected_token_artifact_written") is not False:
        errors.append("selected_token_artifact_written must be false")
        statuses.append("selected_token_artifact_written_detected")
    if status == STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES and candidate_count != 0:
        errors.append("blocked_missing_source_backed_candidates requires zero source-backed candidates")
        statuses.append("missing_candidates_count_mismatch")
    if status == STATUS_OPERATOR_SELECTION_REQUIRED and candidate_count <= 0:
        errors.append("operator_selection_required requires at least one source-backed candidate")
        statuses.append("operator_selection_required_missing_candidates")

    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_false_flag_detected")
        if key in FORBIDDEN_RAW_TOKEN_FIELD_NAMES:
            errors.append(f"{path}.{key} must not be emitted by 075A; use token_id_short only")
            statuses.append("raw_token_field_detected")

    for index, candidate in enumerate(_rows(value.get("source_backed_candidates"))):
        if candidate.get("source_backed") is not True:
            errors.append(f"source_backed_candidates[{index}].source_backed must be true")
            statuses.append("candidate_not_source_backed")
        if clean_text(candidate.get("token_id_short")) == "missing":
            errors.append(f"source_backed_candidates[{index}].token_id_short must be present")
            statuses.append("candidate_missing_short_token_id")
        if candidate.get("raw_token_id_exposed") is not False:
            errors.append(f"source_backed_candidates[{index}].raw_token_id_exposed must be false")
            statuses.append("candidate_raw_token_exposed")
        if "--candidate-index" not in clean_text(candidate.get("safe_cli_command")):
            errors.append(f"source_backed_candidates[{index}].safe_cli_command must include --candidate-index")
            statuses.append("candidate_cli_missing_index")

    valid = not errors
    return {
        "contract_version": SELECTED_CANDIDATE_INSTRUCTION_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["selected_candidate_instruction_packet_valid"]
            if valid
            else ["selected_candidate_instruction_packet_blocked"]
        ),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **selected_candidate_instruction_safety_flags(),
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


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
