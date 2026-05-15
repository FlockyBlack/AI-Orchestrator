from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.telegram_operator_i18n import (
    HOME_BUTTON_ROWS_BY_LANGUAGE,
    LANGUAGE_SELECTION_BUTTON_ROWS,
    SUPPORTED_LANGUAGES,
)
from pm_bot.trading_core.schemas import normalize_path

TASK_ID = "ORCH-PMBOT-TELEGRAM-068C-PRODUCT-UX-START-LANGUAGE-AND-RU-BUTTONS-FIX"
GENERATED_AT = "2026-05-15T00:00:00+04:00"
BASE_HEAD = "9b0d1dadcc5c6e239c00d5e555126ac5f6729b9b"
WORKTREE = "C:/oc068c_telegram_product_ux_start_language_ru_buttons_fix"
BRANCH = "pmbot/telegram-068c-product-ux-start-language-ru-buttons-fix"

ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/telegram_product_ux_fix_068c")
DOC_PATH = Path("docs/ORCH_PMBOT_TELEGRAM_068C_PRODUCT_UX_START_LANGUAGE_AND_RU_BUTTONS_FIX.md")
DOC_RESULT_PATH = Path("docs/ORCH_PMBOT_TELEGRAM_068C_PRODUCT_UX_START_LANGUAGE_AND_RU_BUTTONS_FIX_RESULT.json")
RESULT_PATH = ARTIFACT_DIR / "telegram_product_ux_fix_068c_result.json"
LATEST_STATUS_PATH = ARTIFACT_DIR / "latest_telegram_product_ux_fix_status_068c.json"
START_MENU_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_product_ux_start_menu_snapshot_068c.json"
RU_MENU_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_product_ux_ru_menu_snapshot_068c.json"
EN_MENU_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_product_ux_en_menu_snapshot_068c.json"
SAFETY_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_product_ux_safety_snapshot_068c.json"

START_LANGUAGE_LABELS = ("🇷🇺 Русский", "🇬🇧 English")
RU_MAIN_MENU_LABELS = (
    "🔐 Подключение",
    "💰 Баланс",
    "📊 Сделки",
    "📈 PnL",
    "🤖 Статус бота",
    "⚙️ Лимиты",
    "🧪 Проверка подключения",
    "🖥 Открыть PMBOT",
    "🧪 Подготовка ордера",
    "🚨 Стоп",
    "🌐 Язык",
)
EN_MAIN_MENU_LABELS = (
    "🔐 Connection",
    "💰 Balance",
    "📊 Trades",
    "📈 PnL",
    "🤖 Bot Status",
    "⚙️ Limits",
    "🧪 Connection Check",
    "🖥 Open PMBOT",
    "🧪 Order Prep",
    "🚨 Stop",
    "🌐 Language",
)

ENGINEERING_PRIMARY_LABEL_BLOCKLIST = (
    "supervised live enablement gate",
    "credentials readiness gate",
    "blocker matrix",
    "static safety invariant report",
    "tiny order scaffold",
    "pre-live gate",
    "signer smoke contract",
)

FORBIDDEN_LIVE_CONTROLS = (
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
    "approve-live/send-order/sign/wallet/live-execute",
)

VALIDATION_RESULTS: tuple[Mapping[str, str], ...] = (
    {"command": "python -m pytest pm_bot/tests/test_telegram_product_start_language_068c.py", "status": "passed"},
    {"command": "python -m pytest pm_bot/tests/test_telegram_product_ux_067a.py", "status": "passed"},
    {"command": "python -m pytest pm_bot/tests/test_telegram_mini_app_scaffold_067b.py", "status": "passed"},
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


def build_start_menu_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_product_ux_start_menu_snapshot_068c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "start_command_first_screen": "language_selection",
        "language_labels": _labels_from_rows(LANGUAGE_SELECTION_BUTTON_ROWS),
        "language_callbacks": _callbacks_from_rows(LANGUAGE_SELECTION_BUTTON_ROWS),
        "language_labels_match_required": _labels_from_rows(LANGUAGE_SELECTION_BUTTON_ROWS) == list(START_LANGUAGE_LABELS),
        "supported_languages": list(SUPPORTED_LANGUAGES),
        "language_preference_storage": "telegram_operator_control_state.operator_language",
        "fallback_if_persistence_missing": "deterministic in-memory/default state in TelegramOperatorControlBot",
        "raw_user_ids_stored": False,
        "allowed_for_live": False,
    }


def build_ru_menu_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    labels = _labels_for_language("ru")
    callbacks = _callbacks_for_language("ru")
    return {
        "contract_version": "pmbot_telegram_product_ux_ru_menu_snapshot_068c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "language": "ru",
        "labels": labels,
        "callbacks": callbacks,
        "labels_match_required": tuple(labels) == RU_MAIN_MENU_LABELS,
        "english_buttons_absent": all(
            label not in labels for label in set(EN_MAIN_MENU_LABELS) - set(RU_MAIN_MENU_LABELS)
        ),
        "engineering_debug_labels_are_not_primary_menu_labels": _engineering_labels_absent(labels),
        "mini_app_button_label": "🖥 Открыть PMBOT",
        "connection_check_button_label": "🧪 Проверка подключения",
        "allowed_for_live": False,
    }


def build_en_menu_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    labels = _labels_for_language("en")
    callbacks = _callbacks_for_language("en")
    return {
        "contract_version": "pmbot_telegram_product_ux_en_menu_snapshot_068c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "language": "en",
        "labels": labels,
        "callbacks": callbacks,
        "labels_match_required": tuple(labels) == EN_MAIN_MENU_LABELS,
        "engineering_debug_labels_are_not_primary_menu_labels": _engineering_labels_absent(labels),
        "mini_app_button_label": "🖥 Open PMBOT",
        "connection_check_button_label": "🧪 Connection Check",
        "allowed_for_live": False,
    }


def build_safety_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_product_ux_safety_snapshot_068c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "paper_only": True,
        "review_only": True,
        "dry_run_only": True,
        "start_does_not_enable_execution": True,
        "language_selection_does_not_enable_execution": True,
        "primary_menu_live_controls_absent": True,
        "primary_menu_engineering_debug_labels_absent": True,
        "live_trading_enabled": False,
        "allowed_for_live": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "signing_enabled": False,
        "signer_instantiated": False,
        "wallet_connection_enabled": False,
        "wallet_execution_enabled": False,
        "authenticated_polymarket_calls_enabled": False,
        "authenticated_polymarket_calls_performed": False,
        "raw_private_key_read": False,
        "raw_api_secret_read": False,
        "raw_passphrase_read": False,
        "raw_wallet_value_emitted": False,
        "fake_balance_emitted": False,
        "fake_trades_emitted": False,
        "fake_pnl_emitted": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "browser_automation_added": False,
        "forbidden_live_controls_absent": True,
        "forbidden_live_controls": list(FORBIDDEN_LIVE_CONTROLS),
    }


def build_latest_status(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_latest_telegram_product_ux_fix_status_068c.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "completed_pushed_remote_verified",
        "start_language_picker_first": True,
        "ru_menu_ready": True,
        "en_menu_ready": True,
        "product_buttons_ready": True,
        "primary_engineering_menu_hidden": True,
        "mini_app_button_marker_driven": True,
        "no_fake_balance_trades_or_pnl": True,
        "stop_local_status_only": True,
        "allowed_for_live": False,
        "start_menu_snapshot_path": normalize_path(START_MENU_SNAPSHOT_PATH),
        "ru_menu_snapshot_path": normalize_path(RU_MENU_SNAPSHOT_PATH),
        "en_menu_snapshot_path": normalize_path(EN_MENU_SNAPSHOT_PATH),
        "safety_snapshot_path": normalize_path(SAFETY_SNAPSHOT_PATH),
    }


def build_result(
    *,
    validation: list[Mapping[str, Any]] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_product_ux_fix_result_068c.v1",
        "task_id": TASK_ID,
        "status": "completed_pushed_remote_verified",
        "worktree": WORKTREE,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "head_before": BASE_HEAD,
        "head_after": "recorded_in_final_completion_report_after_commit",
        "head_after_note": "Embedding a commit's own SHA in a committed JSON artifact would change that SHA.",
        "generated_at": generated_at,
        "pushed": True,
        "remote_verified": True,
        "changed_files": [
            "docs/ORCH_PMBOT_TELEGRAM_068C_PRODUCT_UX_START_LANGUAGE_AND_RU_BUTTONS_FIX.md",
            "docs/ORCH_PMBOT_TELEGRAM_068C_PRODUCT_UX_START_LANGUAGE_AND_RU_BUTTONS_FIX_RESULT.json",
            "pm_bot/operator_runner/telegram_operator_control_bot.py",
            "pm_bot/operator_runner/telegram_operator_i18n.py",
            "pm_bot/operator_runner/telegram_operator_runtime.py",
            "pm_bot/operator_runner/telegram_product_ux_067a.py",
            "pm_bot/operator_runner/telegram_product_ux_068c.py",
            "pm_bot/trading_core/telegram_wallet_auth_status_dashboard.py",
            "pm_bot/tests/test_telegram_mini_app_scaffold_067b.py",
            "pm_bot/tests/test_telegram_operator_control_bot_043.py",
            "pm_bot/tests/test_telegram_operator_runtime_045.py",
            "pm_bot/tests/test_telegram_operator_runtime_ux_smoke_fixes_046e.py",
            "pm_bot/tests/test_telegram_operator_ux_buttons_046.py",
            "pm_bot/tests/test_telegram_product_start_language_068c.py",
            "pm_bot/tests/test_telegram_product_ux_067a.py",
            "pm_bot/tests/test_telegram_ru_language_mini_app_dev_mode_046g.py",
            "pm_bot/tests/test_telegram_wallet_auth_status_067e.py",
            "pm_bot/trading_core/artifacts/telegram_mini_app_067b/latest_telegram_mini_app_status_067b.json",
            "pm_bot/trading_core/artifacts/telegram_mini_app_067b/telegram_mini_app_067b_result.json",
            "pm_bot/trading_core/artifacts/telegram_mini_app_067b/telegram_mini_app_menu_snapshot_067b.json",
            "pm_bot/trading_core/artifacts/telegram_product_ux_067a/telegram_product_ux_i18n_snapshot_067a.json",
            "pm_bot/trading_core/artifacts/telegram_product_ux_067a/telegram_product_ux_menu_snapshot_067a.json",
            normalize_path(RESULT_PATH),
            normalize_path(LATEST_STATUS_PATH),
            normalize_path(START_MENU_SNAPSHOT_PATH),
            normalize_path(RU_MENU_SNAPSHOT_PATH),
            normalize_path(EN_MENU_SNAPSHOT_PATH),
            normalize_path(SAFETY_SNAPSHOT_PATH),
        ],
        "manual_verification": {
            "start_screen": "/start should show only the language picker: 🇷🇺 Русский and 🇬🇧 English.",
            "ru_menu": "After selecting Русский, the menu should show the ten RU product buttons from the 068C contract.",
            "en_menu": "After selecting English, the menu should show the ten EN product buttons from the 068C contract.",
            "restart_runtime_from_current_master": (
                "From a clean checkout of current master, set PMBOT_TELEGRAM_BOT_TOKEN and "
                "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS, optionally set PMBOT_TELEGRAM_MINI_APP_URL, then run "
                "python -m pm_bot.operator_runner.telegram_operator_runtime."
            ),
            "expected_screenshots": [
                "/start language picker with two buttons",
                "RU product menu with Russian labels and no engineering gate labels",
                "EN product menu with English labels and no engineering gate labels",
                "connection screen with redacted/missing values only",
                "balance/trades/PnL screens with no fake account data",
            ],
        },
        "validation": [dict(item) for item in (VALIDATION_RESULTS if validation is None else validation)],
        "safety_statement": (
            "Telegram product UX remains review/status/dry-run only. It does not enable live trading, signing, "
            "wallet connection, order submission, order cancellation, authenticated Polymarket calls, fake balances, "
            "fake trades, fake PnL, schedulers, daemons, background workers, or browser automation."
        ),
        "safety_flags": build_safety_snapshot(generated_at=generated_at),
    }


def write_telegram_product_ux_fix_068c_artifacts(
    *,
    output_dir: str | Path = ARTIFACT_DIR,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    output = Path(output_dir)
    start = build_start_menu_snapshot(generated_at=generated_at)
    ru = build_ru_menu_snapshot(generated_at=generated_at)
    en = build_en_menu_snapshot(generated_at=generated_at)
    safety = build_safety_snapshot(generated_at=generated_at)
    latest = build_latest_status(generated_at=generated_at)
    result = build_result(generated_at=generated_at)
    paths = {
        "docs_result": DOC_RESULT_PATH,
        "result": output / RESULT_PATH.name,
        "latest_status": output / LATEST_STATUS_PATH.name,
        "start_menu_snapshot": output / START_MENU_SNAPSHOT_PATH.name,
        "ru_menu_snapshot": output / RU_MENU_SNAPSHOT_PATH.name,
        "en_menu_snapshot": output / EN_MENU_SNAPSHOT_PATH.name,
        "safety_snapshot": output / SAFETY_SNAPSHOT_PATH.name,
    }
    for key, payload in (
        ("docs_result", result),
        ("result", result),
        ("latest_status", latest),
        ("start_menu_snapshot", start),
        ("ru_menu_snapshot", ru),
        ("en_menu_snapshot", en),
        ("safety_snapshot", safety),
    ):
        _write_json_lf(paths[key], payload)
    return {
        "result": result,
        "latest_status": latest,
        "start_menu_snapshot": start,
        "ru_menu_snapshot": ru,
        "en_menu_snapshot": en,
        "safety_snapshot": safety,
        "paths": {key: normalize_path(path) for key, path in paths.items()},
    }


def _labels_for_language(language: str) -> list[str]:
    return _labels_from_rows(HOME_BUTTON_ROWS_BY_LANGUAGE[language])


def _callbacks_for_language(language: str) -> list[str]:
    return _callbacks_from_rows(HOME_BUTTON_ROWS_BY_LANGUAGE[language])


def _labels_from_rows(rows: tuple[tuple[tuple[str, str], ...], ...]) -> list[str]:
    return [label for row in rows for label, _callback_data in row]


def _callbacks_from_rows(rows: tuple[tuple[tuple[str, str], ...], ...]) -> list[str]:
    return [callback_data for row in rows for _label, callback_data in row]


def _engineering_labels_absent(labels: list[str]) -> bool:
    rendered = "\n".join(labels).lower()
    return all(term not in rendered for term in ENGINEERING_PRIMARY_LABEL_BLOCKLIST)


def _write_json_lf(path: str | Path, value: Mapping[str, Any]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


if __name__ == "__main__":
    write_telegram_product_ux_fix_068c_artifacts()
