from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.telegram_operator_i18n import normalize_operator_language
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, write_json
from pm_bot.trading_core.secret_boundary_policy import validate_secret_boundary_telegram_operator_control_state

TELEGRAM_OPERATOR_CONTROL_STATE_CONTRACT = "pmbot_telegram_operator_control_state.v1"
TELEGRAM_OPERATOR_CONTROL_STATE_SUMMARY_CONTRACT = "pmbot_telegram_operator_control_state_summary.v1"
TELEGRAM_OPERATOR_CONTROL_STATE_VALIDATION_CONTRACT = "pmbot_telegram_operator_control_state_validation.v1"

STATE_ARTIFACT_NAME = "telegram_operator_control_state_043.json"

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "would_submit_order",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "wallet_signing_enabled",
    "wallet_enabled",
)


@dataclass(frozen=True)
class TelegramOperatorControlState:
    state_id: str
    generated_at: str
    operator_pause_requested: bool = False
    operator_kill_switch_requested: bool = False
    operator_language: str = ""
    last_command_summary: Mapping[str, Any] | None = None
    last_operator_user_hash: str = ""
    state_source: str = "local_operator_state_artifact"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        language = normalize_operator_language(self.operator_language)
        value["contract_version"] = TELEGRAM_OPERATOR_CONTROL_STATE_CONTRACT
        value["schema_version"] = "043.v1"
        value["operator_language"] = language
        value["operator_language_selected"] = bool(language)
        value["operator_language_scope"] = "global_local_operator_state"
        value["last_command_summary"] = dict(self.last_command_summary or _empty_command_summary())
        value["review_only"] = True
        value["local_operator_state_only"] = True
        value["safe_local_pause_marker_only"] = True
        value["safe_local_kill_switch_marker_only"] = True
        value["does_not_modify_trading_execution"] = True
        value["raw_telegram_data_persisted"] = False
        value["raw_operator_user_id_persisted"] = False
        value["operator_user_hash_only"] = bool(self.last_operator_user_hash)
        value.update(_state_safety_flags())
        return value


def build_telegram_operator_control_state(
    *,
    operator_pause_requested: bool = False,
    operator_kill_switch_requested: bool = False,
    operator_language: str = "",
    last_command_summary: Mapping[str, Any] | None = None,
    last_operator_user_hash: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    command_summary = dict(last_command_summary or _empty_command_summary(generated_at=generated_at))
    state = TelegramOperatorControlState(
        state_id=_stable_id(
            "telegram-operator-control-state-043",
            {
                "generated_at": generated_at,
                "operator_pause_requested": operator_pause_requested,
                "operator_kill_switch_requested": operator_kill_switch_requested,
                "operator_language": normalize_operator_language(operator_language),
                "last_command_summary": command_summary,
                "last_operator_user_hash": clean_text(last_operator_user_hash),
            },
        ),
        generated_at=generated_at,
        operator_pause_requested=operator_pause_requested,
        operator_kill_switch_requested=operator_kill_switch_requested,
        operator_language=normalize_operator_language(operator_language),
        last_command_summary=command_summary,
        last_operator_user_hash=clean_text(last_operator_user_hash),
    ).to_dict()
    state["validation"] = validate_telegram_operator_control_state(state, generated_at=generated_at)
    return state


def record_telegram_operator_control_command(
    state: Mapping[str, Any] | None,
    *,
    command: str,
    operator_user_id: Any,
    authorized: bool,
    command_status: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    current = dict(state or {})
    command_summary = {
        "contract_version": "pmbot_telegram_operator_control_command_summary.v1",
        "generated_at": generated_at,
        "command": normalize_telegram_command(command),
        "authorized": authorized,
        "command_status": clean_text(command_status),
        "review_only": True,
        "execution_enabling": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "order_submission_enabled": False,
        "would_submit_order": False,
    }
    return build_telegram_operator_control_state(
        operator_pause_requested=current.get("operator_pause_requested") is True,
        operator_kill_switch_requested=current.get("operator_kill_switch_requested") is True,
        operator_language=clean_text(current.get("operator_language")),
        last_command_summary=command_summary,
        last_operator_user_hash=hash_operator_identifier(operator_user_id),
        generated_at=generated_at,
    )


def request_telegram_operator_pause(
    state: Mapping[str, Any] | None,
    *,
    operator_user_id: Any,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    current = dict(state or {})
    return build_telegram_operator_control_state(
        operator_pause_requested=True,
        operator_kill_switch_requested=current.get("operator_kill_switch_requested") is True,
        operator_language=clean_text(current.get("operator_language")),
        last_command_summary={
            "contract_version": "pmbot_telegram_operator_control_command_summary.v1",
            "generated_at": generated_at,
            "command": "/pause",
            "authorized": True,
            "command_status": "local_pause_marker_recorded",
            "review_only": True,
            "execution_enabling": False,
            "live_execution_approved": False,
            "canary_executable_now": False,
            "order_submission_enabled": False,
            "would_submit_order": False,
        },
        last_operator_user_hash=hash_operator_identifier(operator_user_id),
        generated_at=generated_at,
    )


def request_telegram_operator_kill_switch(
    state: Mapping[str, Any] | None,
    *,
    operator_user_id: Any,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    current = dict(state or {})
    return build_telegram_operator_control_state(
        operator_pause_requested=current.get("operator_pause_requested") is True,
        operator_kill_switch_requested=True,
        operator_language=clean_text(current.get("operator_language")),
        last_command_summary={
            "contract_version": "pmbot_telegram_operator_control_command_summary.v1",
            "generated_at": generated_at,
            "command": "/kill",
            "authorized": True,
            "command_status": "local_kill_switch_marker_recorded",
            "review_only": True,
            "execution_enabling": False,
            "live_execution_approved": False,
            "canary_executable_now": False,
            "order_submission_enabled": False,
            "would_submit_order": False,
        },
        last_operator_user_hash=hash_operator_identifier(operator_user_id),
        generated_at=generated_at,
    )


def set_telegram_operator_language(
    state: Mapping[str, Any] | None,
    *,
    operator_user_id: Any,
    language: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    current = dict(state or {})
    normalized_language = normalize_operator_language(language)
    return build_telegram_operator_control_state(
        operator_pause_requested=current.get("operator_pause_requested") is True,
        operator_kill_switch_requested=current.get("operator_kill_switch_requested") is True,
        operator_language=normalized_language,
        last_command_summary={
            "contract_version": "pmbot_telegram_operator_control_command_summary.v1",
            "generated_at": generated_at,
            "command": "/language",
            "authorized": True,
            "command_status": "operator_language_selected",
            "operator_language": normalized_language,
            "review_only": True,
            "execution_enabling": False,
            "live_execution_approved": False,
            "canary_executable_now": False,
            "order_submission_enabled": False,
            "would_submit_order": False,
        },
        last_operator_user_hash=hash_operator_identifier(operator_user_id),
        generated_at=generated_at,
    )


def summarize_telegram_operator_control_state(
    state: Mapping[str, Any] | None,
    *,
    latest_state_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    state_value = dict(state or build_telegram_operator_control_state(generated_at=generated_at))
    validation = validate_telegram_operator_control_state(state_value, generated_at=generated_at)
    return {
        "contract_version": TELEGRAM_OPERATOR_CONTROL_STATE_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "telegram-operator-control-state-summary-043",
            {
                "state_id": state_value.get("state_id"),
                "latest_state_path": clean_text(latest_state_path),
                "validation_status": validation.get("status"),
            },
        ),
        "generated_at": generated_at,
        "state_id": clean_text(state_value.get("state_id")),
        "operator_pause_requested": state_value.get("operator_pause_requested") is True,
        "operator_kill_switch_requested": state_value.get("operator_kill_switch_requested") is True,
        "operator_language": normalize_operator_language(state_value.get("operator_language")),
        "operator_language_selected": bool(normalize_operator_language(state_value.get("operator_language"))),
        "operator_language_scope": "global_local_operator_state",
        "latest_telegram_operator_control_state_path": clean_text(latest_state_path),
        "last_command_summary": dict(state_value.get("last_command_summary", {})),
        "validation_status": clean_text(validation.get("status")),
        "validation_error_count": len(validation.get("errors", [])),
        "review_only": True,
        "local_operator_state_only": True,
        "does_not_modify_trading_execution": True,
        "raw_telegram_data_persisted": False,
        "raw_operator_user_id_persisted": False,
        **_state_safety_flags(),
    }


def validate_telegram_operator_control_state(
    state: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    state_value = dict(state)
    if state_value.get("contract_version") != TELEGRAM_OPERATOR_CONTROL_STATE_CONTRACT:
        errors.append(f"contract_version must be {TELEGRAM_OPERATOR_CONTROL_STATE_CONTRACT}")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if state_value.get(field) is not False:
            errors.append(f"{field} must be false")
    if state_value.get("review_only") is not True:
        errors.append("review_only must be true")
    if state_value.get("local_operator_state_only") is not True:
        errors.append("local_operator_state_only must be true")
    if state_value.get("does_not_modify_trading_execution") is not True:
        errors.append("does_not_modify_trading_execution must be true")
    if clean_text(state_value.get("operator_language")) and not normalize_operator_language(
        state_value.get("operator_language")
    ):
        errors.append("operator_language must be empty, ru, or en")
    if state_value.get("raw_telegram_data_persisted") is not False:
        errors.append("raw_telegram_data_persisted must be false")
    if state_value.get("raw_operator_user_id_persisted") is not False:
        errors.append("raw_operator_user_id_persisted must be false")
    secret_validation = validate_secret_boundary_telegram_operator_control_state(
        state_value,
        generated_at=generated_at,
    )
    if secret_validation.get("valid") is not True:
        errors.append("telegram operator control state violates static secret boundary")
    valid = not errors
    return {
        "contract_version": TELEGRAM_OPERATOR_CONTROL_STATE_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "telegram-operator-control-state-validation-043",
            {"state_id": state_value.get("state_id"), "errors": errors},
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        "secret_boundary_validation": secret_validation,
        **_state_safety_flags(),
    }


def write_telegram_operator_control_state(path: str | Path, state: Mapping[str, Any]) -> None:
    write_json(path, state)


def load_telegram_operator_control_state(path: str | Path) -> dict[str, Any]:
    return load_json_object(path, label="telegram operator control state")


def hash_operator_identifier(operator_user_id: Any) -> str:
    text = clean_text(operator_user_id)
    if not text:
        return ""
    return "operator-user-sha256:" + hashlib.sha256(f"pmbot-telegram-operator:{text}".encode("utf-8")).hexdigest()


def normalize_telegram_command(value: Any) -> str:
    text = clean_text(value).split(maxsplit=1)[0].lower()
    if "@" in text:
        text = text.split("@", 1)[0]
    return text if text.startswith("/") else ""


def _empty_command_summary(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_operator_control_command_summary.v1",
        "generated_at": generated_at,
        "command": "",
        "authorized": False,
        "command_status": "no_command_recorded",
        "review_only": True,
        "execution_enabling": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "order_submission_enabled": False,
        "would_submit_order": False,
    }


def _state_safety_flags() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "execution_enabling": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "would_submit_order": False,
        "order_submission_enabled": False,
        "real_order_submitted": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "browser_automation_added": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
