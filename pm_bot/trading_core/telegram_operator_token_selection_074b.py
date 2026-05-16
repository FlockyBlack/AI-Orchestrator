from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, normalize_path, write_json

TASK_ID = "ORCH-PMBOT-TELEGRAM-074B-OPERATOR-TOKEN-SELECTION-UX-NO-TRADING"

STATUS_CONTRACT = "pmbot_telegram_operator_token_selection_074b.v1"
RESULT_CONTRACT = "pmbot_telegram_operator_token_selection_074b_result.v1"
MENU_SNAPSHOT_CONTRACT = "pmbot_telegram_operator_token_selection_074b_menu_snapshot.v1"
SAFETY_SNAPSHOT_CONTRACT = "pmbot_telegram_operator_token_selection_074b_safety_snapshot.v1"

ARTIFACT_DIR_NAME = "telegram_operator_token_selection_074b"
RESULT_FILENAME = "telegram_operator_token_selection_074b_result.json"
LATEST_STATUS_FILENAME = "latest_telegram_operator_token_selection_074b.json"
MENU_SNAPSHOT_FILENAME = "telegram_operator_token_selection_menu_snapshot_074b.json"
SAFETY_SNAPSHOT_FILENAME = "telegram_operator_token_selection_safety_snapshot_074b.json"

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME

SOURCE_073B_ARTIFACT_DIR_NAMES = ("operator_token_selection_packet_073b",)
SOURCE_073B_FILENAMES = (
    "operator_token_selection_candidates_073b.json",
    "operator_token_selection_packet_073b.json",
    "operator_token_selection_packet_073b_result.json",
    "latest_operator_token_selection_status_073b.json",
)
FALLBACK_SOURCE_DIR_NAMES = (
    "order_prep_packet_072a",
    "discovery_to_token_resolver_bridge_071d",
    "public_market_token_discovery_071a",
)
FALLBACK_SOURCE_FILENAMES = (
    "order_prep_packet_operator_review_072a.json",
    "latest_order_prep_packet_072a.json",
    "latest_order_prep_packet_status_072a.json",
    "discovery_to_token_resolver_bridge_071d_result.json",
    "discovery_to_token_operator_selection_required_071d.json",
    "public_market_token_discovery_071a_result.json",
    "public_outcome_token_candidates_071a.json",
)

CONTROL_BUTTON_ROWS_RU = (
    (("Обновить", "pmbot:token_selection"),),
    (("Кандидат 1", "pmbot:token_selection:candidate:0"), ("Кандидат 2", "pmbot:token_selection:candidate:1")),
    (("Назад", "pmbot:home"),),
)
CONTROL_BUTTON_ROWS_EN = (
    (("Refresh", "pmbot:token_selection"),),
    (("Candidate 1", "pmbot:token_selection:candidate:0"), ("Candidate 2", "pmbot:token_selection:candidate:1")),
    (("Back", "pmbot:home"),),
)

_CANDIDATE_LIST_KEYS = (
    "source_backed_candidates",
    "source_backed_token_candidates",
    "valid_source_backed_candidates",
    "outcome_token_candidates",
)
_ABSENT_TEXT = {
    "",
    "0",
    "false",
    "missing",
    "none",
    "not_available",
    "not available",
    "not_found",
    "not found",
    "unknown",
    "unavailable",
    "null",
}


def telegram_operator_token_selection_artifact_paths(
    output_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(output_dir) if output_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / RESULT_FILENAME,
        "latest_status": root / LATEST_STATUS_FILENAME,
        "menu_snapshot": root / MENU_SNAPSHOT_FILENAME,
        "safety_snapshot": root / SAFETY_SNAPSHOT_FILENAME,
    }


def build_telegram_operator_token_selection_status(
    *,
    artifact_root: str | Path | None = None,
    selected_candidate_index: int | str | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    source_payloads = _load_candidate_source_payloads(root)
    source_candidates = _collect_source_backed_candidates(source_payloads, generated_at=generated_at)
    selected_index = _parse_candidate_index(selected_candidate_index)
    selected_candidate = _candidate_by_index(source_candidates, selected_index)
    cli_instruction = build_candidate_cli_instruction(selected_index) if selected_index is not None else ""
    status = "candidates_ready_selection_required" if source_candidates else "no_source_backed_candidates_found"
    status_value: dict[str, Any] = {
        "contract_version": STATUS_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": status,
        "mode": "telegram token selection review / local artifacts / no-trading",
        "execution_mode": "local_artifact_read_only",
        "telegram_screen_title_ru": "🎯 Выбор рынка / Token ID",
        "telegram_screen_title_en": "Market / Token ID",
        "artifact_root": normalize_path(root),
        "source_073b_artifact_available": any(row["source_family"] == "073b" for row in source_payloads),
        "source_artifact_count": len(source_payloads),
        "source_artifacts": [_source_payload_summary(row) for row in source_payloads],
        "source_backed_candidate_count": len(source_candidates),
        "candidate_index_base": 0,
        "candidate_display_limit": 2,
        "candidate_list": source_candidates[:2],
        "additional_candidate_count": max(0, len(source_candidates) - 2),
        "operator_selection_required": True,
        "explicit_operator_selection_required": True,
        "requires_explicit_operator_selection": True,
        "selected_candidate_index": selected_index,
        "selected_candidate_available": bool(selected_candidate),
        "selected_candidate_preview": selected_candidate,
        "selection_artifact_write_supported": False,
        "selection_artifact_write_performed": False,
        "telegram_button_selection_writes_local_artifacts": False,
        "cli_instruction_required": True,
        "candidate_cli_instruction": cli_instruction,
        "button_selection_behavior_ru": (
            "Кнопка кандидата показывает локальную CLI-команду; Telegram не меняет selection artifacts."
        ),
        "button_selection_behavior_en": (
            "Candidate buttons show the local CLI command; Telegram does not change selection artifacts."
        ),
        "screen_buttons": [
            {"label_ru": label, "callback_data": callback_data}
            for row in CONTROL_BUTTON_ROWS_RU
            for label, callback_data in row
        ],
        "raw_token_id_exposed": False,
        "token_ids_redacted_or_shortened": True,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **telegram_operator_token_selection_safety_flags(),
    }
    status_value["status_text_ru"] = render_telegram_operator_token_selection_text(status_value, language="ru")
    status_value["status_text_en"] = render_telegram_operator_token_selection_text(status_value, language="en")
    return status_value


def write_telegram_operator_token_selection_074b_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    selected_candidate_index: int | str | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    status = build_telegram_operator_token_selection_status(
        artifact_root=artifact_root,
        selected_candidate_index=selected_candidate_index,
        generated_at=generated_at,
    )
    paths = telegram_operator_token_selection_artifact_paths(output_dir)
    menu = build_telegram_operator_token_selection_menu_snapshot(generated_at=generated_at)
    safety = build_telegram_operator_token_selection_safety_snapshot(generated_at=generated_at)
    result = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "completed_review_only",
        "latest_status_path": normalize_path(paths["latest_status"]),
        "menu_snapshot_path": normalize_path(paths["menu_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "telegram_operator_token_selection_074b": status,
        "menu_snapshot": menu,
        "safety_snapshot": safety,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **telegram_operator_token_selection_safety_flags(),
    }
    write_json(paths["latest_status"], status)
    write_json(paths["menu_snapshot"], menu)
    write_json(paths["safety_snapshot"], safety)
    write_json(paths["result"], result)
    return {
        "result_path": normalize_path(paths["result"]),
        "latest_status_path": normalize_path(paths["latest_status"]),
        "menu_snapshot_path": normalize_path(paths["menu_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "result": result,
        "latest_status": status,
        "menu_snapshot": menu,
        "safety_snapshot": safety,
    }


def build_telegram_operator_token_selection_menu_snapshot(
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    buttons = [
        *_button_rows("ru", CONTROL_BUTTON_ROWS_RU),
        *_button_rows("en", CONTROL_BUTTON_ROWS_EN),
    ]
    return {
        "contract_version": MENU_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "title_ru": "🎯 Выбор рынка / Token ID",
        "title_en": "Market / Token ID",
        "buttons": buttons,
        "button_count": len(buttons),
        "allowed_callbacks": [
            "pmbot:token_selection",
            "pmbot:token_selection:candidate:0",
            "pmbot:token_selection:candidate:1",
            "pmbot:home",
        ],
        "candidate_buttons_create_artifacts": False,
        "candidate_buttons_show_cli_instruction": True,
        "forbidden_live_controls_added": False,
        "submit_cancel_controls_added": False,
        "signing_controls_added": False,
        "wallet_controls_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_operator_token_selection_safety_flags(),
    }


def build_telegram_operator_token_selection_safety_snapshot(
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "safe_local_token_selection_review_only",
        "allowed_inputs": [
            "local 073B operator token selection artifacts when present",
            "local 072A/071D/071A source-backed token candidate artifacts for fallback display only",
        ],
        "telegram_behavior": [
            "refresh re-renders local artifact summaries",
            "candidate buttons render CLI instructions only",
            "Telegram does not create or update selection artifacts",
        ],
        "local_artifact_read_only": True,
        "candidate_buttons_create_artifacts": False,
        "raw_token_id_exposed": False,
        "token_ids_redacted_or_shortened": True,
        "no_live_controls": True,
        **telegram_operator_token_selection_safety_flags(),
    }


def render_telegram_operator_token_selection_text(
    status: Mapping[str, Any],
    *,
    language: str = "ru",
) -> str:
    value = dict(status or {})
    candidates = [dict(row) for row in value.get("candidate_list", []) if isinstance(row, Mapping)]
    selected_index = value.get("selected_candidate_index")
    selected_available = value.get("selected_candidate_available") is True
    cli_instruction = clean_text(value.get("candidate_cli_instruction"))
    if clean_text(language).lower() == "en":
        lines = [
            "Market / Token ID",
            f"Candidates: {int(value.get('source_backed_candidate_count', 0) or 0)}",
            "Explicit operator selection required: yes",
        ]
        lines.extend(_candidate_lines_en(candidates))
        if int(value.get("additional_candidate_count", 0) or 0) > 0:
            lines.append(f"Additional candidates: {int(value.get('additional_candidate_count', 0) or 0)}")
        if selected_index is not None:
            lines.append(f"Candidate button: {int(selected_index) + 1}")
            lines.append("Local artifact write: no")
            lines.append(
                "Instruction: " + (cli_instruction if selected_available else "candidate index is not available")
            )
        return "\n".join(lines)

    lines = [
        "🎯 Выбор рынка / Token ID",
        f"Кандидаты: {int(value.get('source_backed_candidate_count', 0) or 0)}",
        "Требуется явный выбор оператора: да",
    ]
    lines.extend(_candidate_lines_ru(candidates))
    if int(value.get("additional_candidate_count", 0) or 0) > 0:
        lines.append(f"Дополнительные кандидаты: {int(value.get('additional_candidate_count', 0) or 0)}")
    if selected_index is not None:
        lines.append(f"Кнопка кандидата: {int(selected_index) + 1}")
        lines.append("Запись local selection artifacts: нет")
        lines.append("Инструкция: " + (cli_instruction if selected_available else "кандидат недоступен"))
    return "\n".join(lines)


def normalize_telegram_operator_token_selection_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    candidates = [dict(row) for row in value.get("candidate_list", []) if isinstance(row, Mapping)]
    return {
        "contract_version": clean_text(value.get("contract_version")),
        "screen_available": clean_text(value.get("contract_version")) == STATUS_CONTRACT,
        "status": clean_text(value.get("status") or "token_selection_missing"),
        "mode": clean_text(value.get("mode") or "telegram token selection review / local artifacts / no-trading"),
        "execution_mode": clean_text(value.get("execution_mode") or "local_artifact_read_only"),
        "telegram_screen_title_ru": clean_text(value.get("telegram_screen_title_ru") or "🎯 Выбор рынка / Token ID"),
        "telegram_screen_title_en": clean_text(value.get("telegram_screen_title_en") or "Market / Token ID"),
        "market": clean_text(value.get("market") or value.get("market_symbol")),
        "artifact_root": clean_text(value.get("artifact_root")),
        "source_073b_artifact_available": value.get("source_073b_artifact_available") is True,
        "source_artifact_count": _int_or_zero(value.get("source_artifact_count")),
        "source_backed_candidate_count": _int_or_zero(value.get("source_backed_candidate_count")),
        "candidate_index_base": _int_or_zero(value.get("candidate_index_base")),
        "candidate_display_limit": _int_or_zero(value.get("candidate_display_limit"), 2),
        "candidate_list": candidates,
        "additional_candidate_count": _int_or_zero(value.get("additional_candidate_count")),
        "operator_selection_required": True,
        "explicit_operator_selection_required": True,
        "requires_explicit_operator_selection": True,
        "selected_candidate_index": value.get("selected_candidate_index"),
        "selected_candidate_available": value.get("selected_candidate_available") is True,
        "selection_artifact_write_supported": False,
        "selection_artifact_write_performed": False,
        "telegram_button_selection_writes_local_artifacts": False,
        "cli_instruction_required": True,
        "candidate_cli_instruction": clean_text(value.get("candidate_cli_instruction")),
        "status_text_ru": clean_text(value.get("status_text_ru")),
        "status_text_en": clean_text(value.get("status_text_en")),
        "raw_token_id_exposed": False,
        "token_ids_redacted_or_shortened": True,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **telegram_operator_token_selection_safety_flags(),
    }


def build_candidate_cli_instruction(candidate_index: int | None) -> str:
    if candidate_index is None:
        return ""
    return (
        "python -m pm_bot.operator_runner.operator_token_selection_packet "
        "--market BTC --strategy tiny-momentum --dry-run "
        f"--candidate-index {candidate_index}"
    )


def telegram_operator_token_selection_safety_flags() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "dry_run_only": True,
        "preflight_only": True,
        "local_artifact_read_only": True,
        "local_artifact_only": True,
        "read_only": True,
        "network_used": False,
        "external_api_calls_performed": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "telegram_authenticated_call_performed": False,
        "polymarket_api_calls_performed": 0,
        "wallet_connection_attempted": False,
        "wallet_connection_enabled": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "credential_values_read": False,
        "credentials_values_read": False,
        "credential_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "environment_values_read": False,
        "environment_values_serialized": False,
        "environment_values_printed": False,
        "environment_values_stored": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "credentials_values_exposed": False,
        "raw_token_id_exposed": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_available": False,
        "signed_payload_generation_enabled": False,
        "signed_payload_generated": False,
        "signed_order_generation_enabled": False,
        "signed_order_payload_generated": False,
        "order_generation_enabled": False,
        "order_generation_attempted": False,
        "order_payload_generated": False,
        "order_submission_available": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "order_cancel_enabled": False,
        "real_order_submitted": False,
        "real_order_cancelled": False,
        "balance_read_attempted": False,
        "balance_values_emitted": False,
        "allowance_values_emitted": False,
        "position_read_attempted": False,
        "fill_read_attempted": False,
        "pnl_read_attempted": False,
        "fake_balance_added": False,
        "fake_pnl_added": False,
        "fake_trades_added": False,
        "live_trading_enabled": False,
        "live_execution_allowed": False,
        "live_execution_approved": False,
        "live_execution_performed": False,
        "allowed_for_live": False,
        "operator_approved": False,
        "operator_approved_for_live": False,
        "candidate_is_executable": False,
        "token_selection_executable": False,
        "token_selection_executed": False,
        "auto_selected_for_live": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "telegram_live_order_controls_added": False,
        "telegram_signing_controls_added": False,
        "telegram_wallet_controls_added": False,
        "selection_artifact_write_supported": False,
        "selection_artifact_write_performed": False,
        "telegram_button_selection_writes_local_artifacts": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def _load_candidate_source_payloads(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _source_073b_paths(root):
        payload = _load_optional_json(path, "074B source 073B artifact")
        if payload:
            rows.append(
                {
                    "source_family": "073b",
                    "path": path,
                    "payload": payload,
                }
            )
    for path in _fallback_source_paths(root):
        payload = _load_optional_json(path, "074B fallback source artifact")
        if payload:
            rows.append(
                {
                    "source_family": "fallback",
                    "path": path,
                    "payload": payload,
                }
            )
    return rows


def _source_073b_paths(root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for dirname in SOURCE_073B_ARTIFACT_DIR_NAMES:
        for filename in SOURCE_073B_FILENAMES:
            paths.append(root / dirname / filename)
    for filename in SOURCE_073B_FILENAMES:
        paths.append(root / filename)
    if root.name in SOURCE_073B_ARTIFACT_DIR_NAMES:
        for filename in SOURCE_073B_FILENAMES:
            paths.append(root / filename)
    return _dedupe_paths(paths)


def _fallback_source_paths(root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for dirname in FALLBACK_SOURCE_DIR_NAMES:
        for filename in FALLBACK_SOURCE_FILENAMES:
            paths.append(root / dirname / filename)
    return _dedupe_paths(paths)


def _collect_source_backed_candidates(
    source_payloads: Sequence[Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in source_payloads:
        source_path = source.get("path")
        source_id = clean_text(source.get("source_family"))
        for raw in _candidate_rows_from_payload(source.get("payload")):
            candidate = _normalize_candidate(raw, source_path=source_path, source_id=source_id, generated_at=generated_at)
            if candidate:
                rows.append(candidate)
    return _dedupe_candidates(rows)


def _candidate_rows_from_payload(payload: Any) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for key in _CANDIDATE_LIST_KEYS:
                nested = value.get(key)
                if isinstance(nested, list):
                    rows.extend(row for row in nested if isinstance(row, Mapping))
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(payload)
    return rows


def _normalize_candidate(
    raw: Mapping[str, Any],
    *,
    source_path: Any,
    source_id: str,
    generated_at: str,
) -> dict[str, Any]:
    value = dict(raw or {})
    token_id = clean_text(
        value.get("token_id")
        or value.get("selected_token_id")
        or value.get("target_token_id")
        or value.get("outcome_token_id")
        or value.get("clob_token_id")
    )
    source_backed = (
        value.get("source_backed") is True
        or value.get("token_id_source_backed") is True
        or value.get("token_id_is_source_backed") is True
    )
    if not token_id or source_backed is not True:
        return {}
    market_title = clean_text(
        value.get("question")
        or value.get("market_title")
        or value.get("title")
        or value.get("market_slug")
        or value.get("market_id")
        or "market title unavailable"
    )
    outcome_label = clean_text(
        value.get("outcome_name")
        or value.get("outcome_label")
        or value.get("outcome")
        or value.get("label")
        or "outcome unavailable"
    )
    candidate_index = _candidate_index(value.get("candidate_index"), fallback=None)
    source_ids = _clean_list(value.get("source_ids"))
    if source_id and source_id not in source_ids:
        source_ids.append(source_id)
    source_paths = _clean_list(value.get("source_paths"))
    path_text = normalize_path(source_path) if isinstance(source_path, Path) else clean_text(source_path)
    if path_text and path_text not in source_paths:
        source_paths.append(path_text)
    return {
        "contract_version": "pmbot_telegram_operator_token_selection_candidate_074b.v1",
        "task_id": TASK_ID,
        "candidate_index": candidate_index,
        "display_index": (candidate_index + 1) if candidate_index is not None else 0,
        "candidate_id": clean_text(
            value.get("candidate_id")
            or value.get("bridge_candidate_id")
            or value.get("source_token_candidate_id")
            or value.get("token_candidate_id")
        ),
        "market_title": market_title,
        "market_slug": clean_text(value.get("market_slug")),
        "condition_id_present": bool(clean_text(value.get("condition_id") or value.get("market_id"))),
        "outcome_label": outcome_label,
        "outcome_index": _int_or_zero(value.get("outcome_index")),
        "token_id_short": shorten_token_id(token_id),
        "token_id_redacted": True,
        "raw_token_id_exposed": False,
        "source_backed": True,
        "token_id_source_backed": True,
        "source_ids": source_ids,
        "source_path_count": len(source_paths),
        "source_paths": source_paths[:4],
        "operator_selectable": value.get("operator_selectable") is not False,
        "requires_explicit_operator_selection": True,
        "generated_at": generated_at,
        **telegram_operator_token_selection_safety_flags(),
    }


def _dedupe_candidates(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for row in candidates:
        value = dict(row)
        key = (
            clean_text(value.get("token_id_short")),
            clean_text(value.get("market_slug") or value.get("market_title")),
            clean_text(value.get("outcome_label")),
        )
        if key in seen:
            continue
        seen.add(key)
        assigned = dict(value)
        assigned["candidate_index"] = len(result)
        assigned["display_index"] = len(result) + 1
        result.append(assigned)
    return result


def _candidate_by_index(candidates: Sequence[Mapping[str, Any]], selected_index: int | None) -> dict[str, Any]:
    if selected_index is None:
        return {}
    for row in candidates:
        value = dict(row)
        if _candidate_index(value.get("candidate_index"), fallback=-1) == selected_index:
            return value
    return {}


def shorten_token_id(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "missing"
    if len(text) <= 12:
        return text[:2] + "..." + text[-2:]
    return text[:6] + "..." + text[-4:]


def _candidate_lines_ru(candidates: Sequence[Mapping[str, Any]]) -> list[str]:
    if not candidates:
        return ["Кандидаты из локальных artifacts не найдены."]
    lines: list[str] = []
    for row in candidates:
        value = dict(row)
        lines.extend(
            [
                f"Кандидат {int(value.get('display_index', 0) or 0)}:",
                f"Рынок: {clean_text(value.get('market_title') or 'не найден')}",
                f"Исход: {clean_text(value.get('outcome_label') or 'не найден')}",
                f"Token ID: {clean_text(value.get('token_id_short') or 'redacted')}",
                f"source-backed: {'да' if value.get('source_backed') is True else 'нет'}",
            ]
        )
    return lines


def _candidate_lines_en(candidates: Sequence[Mapping[str, Any]]) -> list[str]:
    if not candidates:
        return ["No candidates found in local artifacts."]
    lines: list[str] = []
    for row in candidates:
        value = dict(row)
        lines.extend(
            [
                f"Candidate {int(value.get('display_index', 0) or 0)}:",
                f"Market: {clean_text(value.get('market_title') or 'not found')}",
                f"Outcome: {clean_text(value.get('outcome_label') or 'not found')}",
                f"Token ID: {clean_text(value.get('token_id_short') or 'redacted')}",
                f"source-backed: {'yes' if value.get('source_backed') is True else 'no'}",
            ]
        )
    return lines


def _source_payload_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(row.get("payload", {}))
    path = row.get("path")
    return {
        "source_family": clean_text(row.get("source_family")),
        "available": bool(payload),
        "path": normalize_path(path) if isinstance(path, Path) else clean_text(path),
        "status": clean_text(payload.get("status") or dict(payload.get("latest_status", {})).get("status")),
        "contract_version": clean_text(
            payload.get("contract_version") or dict(payload.get("latest_status", {})).get("contract_version")
        ),
    }


def _load_optional_json(path: Path | None, label: str) -> dict[str, Any]:
    if path is None or not path.exists() or not path.is_file():
        return {}
    try:
        return load_json_object(path, label=label)
    except Exception:
        return {}


def _dedupe_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(path)
    return tuple(unique)


def _parse_candidate_index(value: int | str | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _candidate_index(value: Any, *, fallback: int | None) -> int | None:
    parsed = _parse_candidate_index(value)
    return fallback if parsed is None else parsed


def _clean_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        text = clean_text(values)
        return [text] if text else []
    try:
        return [clean_text(item) for item in values if clean_text(item)]
    except TypeError:
        return []


def _int_or_zero(*values: Any) -> int:
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _button_rows(language: str, rows: Sequence[Sequence[tuple[str, str]]]) -> list[dict[str, str]]:
    return [
        {
            "language": language,
            "label": label,
            "callback_data": callback_data,
        }
        for row in rows
        for label, callback_data in row
    ]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the 074B Telegram token selection review screen artifacts.")
    parser.add_argument("--artifact-root", default="", help="Root directory containing local source artifacts.")
    parser.add_argument("--output-dir", default="", help="Directory for 074B output artifacts.")
    parser.add_argument("--candidate-index", default=None, help="Optional zero-based candidate index to show CLI for.")
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--json", action="store_true", help="Print the generated result JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generated = write_telegram_operator_token_selection_074b_artifacts(
        artifact_root=args.artifact_root or None,
        output_dir=args.output_dir or None,
        selected_candidate_index=args.candidate_index,
        generated_at=args.generated_at,
    )
    if args.json:
        import json

        print(json.dumps(generated["result"], indent=2, sort_keys=True, ensure_ascii=False))
    else:
        status = generated["latest_status"]
        _safe_print(status["status_text_ru"])
        _safe_print(f"result_path: {generated['result_path']}")
    return 0


def _safe_print(value: str) -> None:
    text = str(value)
    try:
        print(text)
    except UnicodeEncodeError:
        import sys

        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


if __name__ == "__main__":
    raise SystemExit(main())
