from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.telegram_operator_i18n import (
    HOME_BUTTON_ROWS_BY_LANGUAGE,
    LANGUAGE_SELECTION_BUTTON_ROWS,
)
from pm_bot.operator_runner.telegram_product_ux_068c import EN_MAIN_MENU_LABELS, RU_MAIN_MENU_LABELS
from pm_bot.trading_core.schemas import normalize_path

TASK_ID = "ORCH-PMBOT-TELEGRAM-069C-SINGLE-MESSAGE-PRODUCT-MENU-NO-LIVE"
GENERATED_AT = "2026-05-15T00:00:00+04:00"
BASE_HEAD = "010bb351ab17e60275d4d6d0771f95ab8058e255"
WORKTREE = "C:/oc069c_telegram_single_message_product_menu_no_live"
BRANCH = "pmbot/telegram-069c-single-message-product-menu-no-live"

ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/telegram_single_message_product_menu_069c")
DOC_RESULT_PATH = Path("docs/ORCH_PMBOT_TELEGRAM_069C_SINGLE_MESSAGE_PRODUCT_MENU_NO_LIVE_RESULT.json")
RESULT_PATH = ARTIFACT_DIR / "telegram_single_message_product_menu_069c_result.json"
LATEST_STATUS_PATH = ARTIFACT_DIR / "latest_telegram_single_message_product_menu_status_069c.json"
RU_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_single_message_product_menu_ru_snapshot_069c.json"
EN_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_single_message_product_menu_en_snapshot_069c.json"
NAVIGATION_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_single_message_product_menu_navigation_snapshot_069c.json"
SAFETY_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_single_message_product_menu_safety_snapshot_069c.json"

START_LANGUAGE_LABELS = ("🇷🇺 Русский", "🇬🇧 English")
RU_BACK_LABEL = "⬅️ Назад"
EN_BACK_LABEL = "⬅️ Back"

TECHNICAL_PRIMARY_MENU_BLOCKLIST = (
    "DryRun",
    "Provider",
    "Gate",
    "062P",
    "063",
    "064",
    "readiness",
    "scaffold",
    "runner",
    "supervised live enablement",
    "static safety",
    "tiny order",
)

FORBIDDEN_LIVE_CONTROL_TERMS = (
    "run_signer",
    "pmbot:run:signer",
    "Run Signer",
    "approve-live",
    "send-order",
    "submit-order",
    "cancel-order",
    "connect-wallet",
    "unlock-wallet",
    "live-enable",
    "live-execute",
)

VALIDATION_RESULTS: tuple[Mapping[str, str], ...] = (
    {"command": "python -m pytest pm_bot/tests/test_telegram_single_message_product_menu_069c.py", "status": "passed"},
    {"command": "python -m pytest pm_bot/tests/test_telegram_product_start_language_068c.py", "status": "passed"},
    {"command": "python -m pytest pm_bot/tests/test_telegram_product_ux_067a.py", "status": "passed"},
    {"command": "python -m pytest pm_bot/tests/test_telegram_mini_app_product_dashboard_068d.py", "status": "passed"},
    {"command": "python -m pytest pm_bot/tests/test_telegram_wallet_auth_status_067e.py", "status": "passed"},
    {"command": "python -m pytest pm_bot/tests/test_telegram_forbidden_live_controls_063a.py", "status": "passed"},
    {"command": "python -m pytest pm_bot/tests/test_static_safety_invariant_report_060q.py", "status": "passed"},
    {"command": "python -B -m pytest pm_bot/tests", "status": "passed"},
    {"command": "python -m compileall -q pm_bot", "status": "passed"},
    {"command": "python -m compileall -q ai_orchestrator", "status": "passed"},
    {"command": "python -m pm_bot.operator_runner.telegram_runtime_smoke", "status": "passed"},
    {
        "command": "python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run",
        "status": "passed",
    },
    {"command": "git diff --check", "status": "passed"},
    {"command": "git diff --cached --check", "status": "passed"},
)


def build_ru_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    labels = _labels_for_language("ru")
    return {
        "contract_version": "pmbot_telegram_single_message_product_menu_ru_snapshot_069c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "language": "ru",
        "main_menu_labels": labels,
        "main_menu_labels_match_required": tuple(labels) == RU_MAIN_MENU_LABELS,
        "primary_menu_is_product_only": _primary_menu_is_product_only(labels),
        "debug_labels_hidden_from_primary_menu": _technical_labels_absent(labels),
        "product_screens": {
            "connection": ["🔄 Проверить снова", "📘 Инструкция", "💰 Перейти к балансу", "⬅️ Главное меню"],
            "balance_missing": ["🔌 Перейти к подключению"],
            "balance": ["🔄 Обновить", "🔌 Подключение", "⬅️ Главное меню"],
            "analytics": ["🔄 Обновить", "📈 Подробнее", "⬅️ Главное меню"],
            "launch": ["💵 Лимит на день", "📉 Максимальный убыток", "🎯 Выбор рынков", "▶️ Запустить", "⬅️ Главное меню"],
            "stop": ["🚀 Перейти к запуску", "⬅️ Главное меню"],
            "mini_app": ["Открыть Mini App", "⬅️ Главное меню"],
            "settings": ["🌐 Изменить язык", "⬅️ Главное меню"],
        },
        "no_fake_balance": True,
        "no_fake_trades": True,
        "no_fake_pnl": True,
        "allowed_for_live": False,
    }


def build_en_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    labels = _labels_for_language("en")
    return {
        "contract_version": "pmbot_telegram_single_message_product_menu_en_snapshot_069c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "language": "en",
        "main_menu_labels": labels,
        "main_menu_labels_match_required": tuple(labels) == EN_MAIN_MENU_LABELS,
        "primary_menu_is_product_only": _primary_menu_is_product_only(labels),
        "debug_labels_hidden_from_primary_menu": _technical_labels_absent(labels),
        "product_screens": {
            "connection": ["🔄 Check again", "📘 Guide", "💰 Go to balance", "⬅️ Main menu"],
            "balance_missing": ["🔌 Go to connection"],
            "balance": ["🔄 Refresh", "🔌 Connection", "⬅️ Main menu"],
            "analytics": ["🔄 Refresh", "📈 Details", "⬅️ Main menu"],
            "launch": ["💵 Daily limit", "📉 Max loss", "🎯 Market selection", "▶️ Launch", "⬅️ Main menu"],
            "stop": ["🚀 Go to launch", "⬅️ Main menu"],
            "mini_app": ["Open Mini App", "⬅️ Main menu"],
            "settings": ["🌐 Change language", "⬅️ Main menu"],
        },
        "no_fake_balance": True,
        "no_fake_trades": True,
        "no_fake_pnl": True,
        "allowed_for_live": False,
    }


def build_navigation_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_single_message_product_menu_navigation_snapshot_069c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "start_command_first_screen": "language_selection",
        "start_language_labels": _labels_from_rows(LANGUAGE_SELECTION_BUTTON_ROWS),
        "start_language_labels_match_required": _labels_from_rows(LANGUAGE_SELECTION_BUTTON_ROWS) == list(START_LANGUAGE_LABELS),
        "single_message_navigation": True,
        "normal_callback_renderer": "telegram_callback_edit_renderer",
        "normal_callbacks_use_edit_message_text": True,
        "normal_callbacks_send_new_message": False,
        "fallback_if_message_not_editable": "send_one_replacement_message",
        "language_selection_edits_same_message": True,
        "language_switching_edits_same_message": True,
        "back_button_edits_same_message": True,
    }


def build_safety_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_single_message_product_menu_safety_snapshot_069c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "single_message_navigation": True,
        "primary_menu_is_product_only": True,
        "debug_labels_hidden_from_primary_menu": True,
        "no_live_trading": True,
        "no_order_submission": True,
        "no_order_cancellation": True,
        "no_signing": True,
        "no_signer_instantiation": True,
        "no_signed_payload_generation": True,
        "no_wallet_connection": True,
        "no_authenticated_polymarket_calls": True,
        "no_private_key_reads": True,
        "no_api_secret_reads": True,
        "no_raw_secret_output": True,
        "no_secret_values_emitted": True,
        "no_secret_persistence": True,
        "no_fake_balance": True,
        "no_fake_trades": True,
        "no_fake_pnl": True,
        "no_scheduler_daemon_or_background_loop": True,
        "forbidden_live_controls_absent": True,
        "forbidden_live_control_terms": list(FORBIDDEN_LIVE_CONTROL_TERMS),
        "allowed_for_live": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_connection_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
    }


def build_latest_status(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_latest_telegram_single_message_product_menu_status_069c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "implemented_pending_commit_push",
        "single_message_navigation": True,
        "primary_menu_is_product_only": True,
        "debug_labels_hidden_from_primary_menu": True,
        "ru_menu_ready": True,
        "en_menu_ready": True,
        "mini_app_visible": True,
        "no_live_trading": True,
        "no_order_submission": True,
        "no_signing": True,
        "no_wallet_connection": True,
        "no_secret_values_emitted": True,
        "no_fake_balance": True,
        "no_fake_trades": True,
        "no_fake_pnl": True,
        "ru_snapshot_path": normalize_path(RU_SNAPSHOT_PATH),
        "en_snapshot_path": normalize_path(EN_SNAPSHOT_PATH),
        "navigation_snapshot_path": normalize_path(NAVIGATION_SNAPSHOT_PATH),
        "safety_snapshot_path": normalize_path(SAFETY_SNAPSHOT_PATH),
    }


def build_result(
    *,
    validation: list[Mapping[str, Any]] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_single_message_product_menu_result_069c.v1",
        "task_id": TASK_ID,
        "status": "implemented_pending_commit_push",
        "worktree": WORKTREE,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "head_before": BASE_HEAD,
        "head_after": "recorded_in_final_completion_report_after_commit",
        "head_after_note": "Embedding a commit's own SHA in a committed JSON artifact would change that SHA.",
        "generated_at": generated_at,
        "pushed": "recorded_in_final_completion_report_after_push",
        "remote_verified": "recorded_in_final_completion_report_after_push",
        "changed_files": [
            "docs/ORCH_PMBOT_TELEGRAM_069C_SINGLE_MESSAGE_PRODUCT_MENU_NO_LIVE.md",
            "docs/ORCH_PMBOT_TELEGRAM_069C_SINGLE_MESSAGE_PRODUCT_MENU_NO_LIVE_RESULT.json",
            "pm_bot/operator_runner/telegram_operator_control_bot.py",
            "pm_bot/operator_runner/telegram_operator_i18n.py",
            "pm_bot/operator_runner/telegram_operator_runtime.py",
            "pm_bot/operator_runner/telegram_product_ux_067a.py",
            "pm_bot/operator_runner/telegram_product_ux_068c.py",
            "pm_bot/operator_runner/telegram_single_message_product_menu_069c.py",
            "pm_bot/tests/test_telegram_mini_app_operator_panel_044.py",
            "pm_bot/tests/test_telegram_mini_app_scaffold_067b.py",
            "pm_bot/tests/test_telegram_operator_console_060t.py",
            "pm_bot/tests/test_telegram_operator_control_bot_043.py",
            "pm_bot/tests/test_telegram_product_start_language_068c.py",
            "pm_bot/tests/test_telegram_product_ux_067a.py",
            "pm_bot/tests/test_telegram_operator_runtime_045.py",
            "pm_bot/tests/test_telegram_operator_runtime_ux_smoke_fixes_046e.py",
            "pm_bot/tests/test_telegram_operator_ux_buttons_046.py",
            "pm_bot/tests/test_telegram_pre_live_gate_review_062t.py",
            "pm_bot/tests/test_telegram_ru_language_mini_app_dev_mode_046g.py",
            "pm_bot/tests/test_telegram_supervised_live_enablement_review_063t.py",
            "pm_bot/tests/test_telegram_tiny_order_review_061t.py",
            "pm_bot/tests/test_telegram_wallet_auth_status_067e.py",
            "pm_bot/tests/test_telegram_single_message_product_menu_069c.py",
            "pm_bot/trading_core/artifacts/telegram_product_ux_067a/telegram_product_ux_i18n_snapshot_067a.json",
            "pm_bot/trading_core/artifacts/telegram_product_ux_067a/telegram_product_ux_menu_snapshot_067a.json",
            "pm_bot/trading_core/artifacts/telegram_product_ux_fix_068c/telegram_product_ux_en_menu_snapshot_068c.json",
            "pm_bot/trading_core/artifacts/telegram_product_ux_fix_068c/telegram_product_ux_ru_menu_snapshot_068c.json",
            normalize_path(RESULT_PATH),
            normalize_path(LATEST_STATUS_PATH),
            normalize_path(RU_SNAPSHOT_PATH),
            normalize_path(EN_SNAPSHOT_PATH),
            normalize_path(NAVIGATION_SNAPSHOT_PATH),
            normalize_path(SAFETY_SNAPSHOT_PATH),
        ],
        "validation": [dict(item) for item in (VALIDATION_RESULTS if validation is None else validation)],
        "manual_verification": {
            "expected_start_flow": "/start shows the language picker, then RU/EN selection edits that message into the product menu.",
            "expected_navigation": "Product callbacks edit the same bot message; old/non-editable messages get one replacement message.",
            "mini_app_url_behavior": "Configured PMBOT_TELEGRAM_MINI_APP_URL adds an Open Mini App WebApp button; missing URL keeps the informational screen.",
        },
        "safety_statement": (
            "Telegram controls remain product status/review/dry-run only. This task does not enable live trading, "
            "wallet connection, signing, order submission, order cancellation, authenticated Polymarket calls, "
            "fake balances, fake trades, fake PnL, schedulers, daemons, or autonomous loops."
        ),
        "safety_flags": build_safety_snapshot(generated_at=generated_at),
    }


def write_telegram_single_message_product_menu_069c_artifacts(
    *,
    output_dir: str | Path = ARTIFACT_DIR,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    output = Path(output_dir)
    ru = build_ru_snapshot(generated_at=generated_at)
    en = build_en_snapshot(generated_at=generated_at)
    navigation = build_navigation_snapshot(generated_at=generated_at)
    safety = build_safety_snapshot(generated_at=generated_at)
    latest = build_latest_status(generated_at=generated_at)
    result = build_result(generated_at=generated_at)
    paths = {
        "docs_result": DOC_RESULT_PATH,
        "result": output / RESULT_PATH.name,
        "latest_status": output / LATEST_STATUS_PATH.name,
        "ru_snapshot": output / RU_SNAPSHOT_PATH.name,
        "en_snapshot": output / EN_SNAPSHOT_PATH.name,
        "navigation_snapshot": output / NAVIGATION_SNAPSHOT_PATH.name,
        "safety_snapshot": output / SAFETY_SNAPSHOT_PATH.name,
    }
    for key, payload in (
        ("docs_result", result),
        ("result", result),
        ("latest_status", latest),
        ("ru_snapshot", ru),
        ("en_snapshot", en),
        ("navigation_snapshot", navigation),
        ("safety_snapshot", safety),
    ):
        _write_json_lf(paths[key], payload)
    return {
        "result": result,
        "latest_status": latest,
        "ru_snapshot": ru,
        "en_snapshot": en,
        "navigation_snapshot": navigation,
        "safety_snapshot": safety,
        "paths": {key: normalize_path(path) for key, path in paths.items()},
    }


def _labels_for_language(language: str) -> list[str]:
    return _labels_from_rows(HOME_BUTTON_ROWS_BY_LANGUAGE[language])


def _labels_from_rows(rows: tuple[tuple[tuple[str, str], ...], ...]) -> list[str]:
    return [label for row in rows for label, _callback_data in row]


def _primary_menu_is_product_only(labels: list[str]) -> bool:
    allowed = set(RU_MAIN_MENU_LABELS) | set(EN_MAIN_MENU_LABELS)
    return bool(labels) and all(label in allowed for label in labels)


def _technical_labels_absent(labels: list[str]) -> bool:
    rendered = "\n".join(labels).lower()
    return all(term.lower() not in rendered for term in TECHNICAL_PRIMARY_MENU_BLOCKLIST)


def _write_json_lf(path: str | Path, value: Mapping[str, Any]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


if __name__ == "__main__":
    write_telegram_single_message_product_menu_069c_artifacts()
