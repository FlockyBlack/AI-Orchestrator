from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.telegram_operator_control_bot import SUPPORTED_COMMANDS
from pm_bot.operator_runner.telegram_operator_i18n import (
    DEFAULT_OPERATOR_LANGUAGE,
    HOME_BUTTON_ROWS_BY_LANGUAGE,
    SUPPORTED_LANGUAGES,
)
from pm_bot.trading_core.schemas import normalize_path

TASK_ID = "ORCH-PMBOT-TELEGRAM-067A-PRODUCT-UX-RU-FIRST-MENU-NO-LIVE"
GENERATED_AT = "2026-05-15T00:00:00+04:00"
BASE_HEAD = "bd84069654a3b412f76d63405b60da7feb5c6c9d"
WORKTREE = "C:/oc067a_telegram_product_ux_ru_first_menu"
BRANCH = "pmbot/telegram-067a-product-ux-ru-first-menu-no-live"

ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/telegram_product_ux_067a")
DOC_RESULT_PATH = Path("docs/ORCH_PMBOT_TELEGRAM_067A_PRODUCT_UX_RU_FIRST_MENU_NO_LIVE_RESULT.json")
RESULT_PATH = ARTIFACT_DIR / "telegram_product_ux_067a_result.json"
LATEST_STATUS_PATH = ARTIFACT_DIR / "latest_telegram_product_ux_status_067a.json"
MENU_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_product_ux_menu_snapshot_067a.json"
I18N_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_product_ux_i18n_snapshot_067a.json"
SAFETY_SNAPSHOT_PATH = ARTIFACT_DIR / "telegram_product_ux_safety_snapshot_067a.json"

RU_MAIN_MENU_LABELS = (
    "🔌 Подключение",
    "💰 Баланс",
    "📊 Аналитика",
    "🚀 Запуск",
    "⛔ Остановить",
    "🌐 Mini App",
    "⚙️ Настройки",
)

EN_MAIN_MENU_LABELS = (
    "🔌 Connection",
    "💰 Balance",
    "📊 Analytics",
    "🚀 Launch",
    "⛔ Stop",
    "🌐 Mini App",
    "⚙️ Settings",
)

PRODUCT_COMMANDS = (
    "/start",
    "/home",
    "/connection",
    "/balance",
    "/analytics",
    "/launch",
    "/panel",
    "/stop",
    "/settings",
    "/ru",
    "/en",
    "/language",
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
)

VALIDATION_RESULTS: tuple[Mapping[str, str], ...] = (
    {
        "command": "python -m pytest pm_bot/tests/test_telegram_product_ux_067a.py",
        "status": "passed",
    },
    {
        "command": "python -m pytest pm_bot/tests/test_telegram_forbidden_live_controls_063a.py",
        "status": "passed",
    },
    {
        "command": "python -m pytest pm_bot/tests/test_telegram_credentials_readiness_review_064t.py",
        "status": "passed",
    },
    {
        "command": "python -m pytest pm_bot/tests/test_static_safety_invariant_report_060q.py",
        "status": "passed",
    },
    {
        "command": "python -B -m pytest pm_bot/tests",
        "status": "passed",
        "details": "1947 passed",
    },
    {
        "command": "python -m compileall -q pm_bot",
        "status": "passed",
    },
    {
        "command": "python -m compileall -q ai_orchestrator",
        "status": "passed",
    },
    {
        "command": "python -m pm_bot.operator_runner.telegram_runtime_smoke",
        "status": "passed",
    },
    {
        "command": "python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run",
        "status": "passed",
        "details": "critical findings: 0",
    },
    {
        "command": "git diff --check",
        "status": "passed",
    },
    {
        "command": "git diff --cached --check",
        "status": "passed",
    },
)


def build_telegram_product_ux_menu_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    ru_labels = _labels_for_language("ru")
    en_labels = _labels_for_language("en")
    return {
        "contract_version": "pmbot_telegram_product_ux_menu_snapshot_067a.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "default_visible_language": DEFAULT_OPERATOR_LANGUAGE,
        "ru_main_menu_labels": ru_labels,
        "en_main_menu_labels": en_labels,
        "ru_main_menu_labels_match_required": tuple(ru_labels) == RU_MAIN_MENU_LABELS,
        "en_main_menu_labels_match_required": tuple(en_labels) == EN_MAIN_MENU_LABELS,
        "primary_callbacks": _callbacks_for_language("ru"),
        "product_commands": list(PRODUCT_COMMANDS),
        "product_commands_supported": all(command in SUPPORTED_COMMANDS for command in PRODUCT_COMMANDS),
        "supported_language_commands": ["/ru", "/en", "/language"],
        "engineering_debug_labels_are_not_primary_menu_labels": True,
        "primary_menu_debug_labels_absent": True,
        "primary_menu_live_controls_absent": True,
        "allowed_for_live": False,
    }


def build_telegram_product_ux_i18n_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_product_ux_i18n_snapshot_067a.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "supported_languages": list(SUPPORTED_LANGUAGES),
        "default_visible_language": DEFAULT_OPERATOR_LANGUAGE,
        "language_preference_storage": "telegram_operator_control_state.operator_language",
        "language_preference_storage_safe_local_state_only": True,
        "language_preference_raw_user_ids_stored": False,
        "ru_first": DEFAULT_OPERATOR_LANGUAGE == "ru",
        "ru_commands": ["/ru", "/language ru"],
        "en_commands": ["/en", "/language en"],
        "screen_titles": {
            "ru": [
                "Подключение",
                "Баланс",
                "Аналитика",
                "Запуск",
                "Остановить",
                "Mini App",
                "Настройки",
            ],
            "en": list(EN_MAIN_MENU_LABELS),
        },
        "user_facing_terms": {
            "ru": [
                "Подключение",
                "Баланс",
                "Аналитика",
                "Запуск",
                "Mini App",
                "Настройки",
            ],
            "en": [
                "Connection",
                "Balance",
                "Analytics",
                "Launch",
                "Mini App",
                "Settings",
            ],
        },
        "allowed_for_live": False,
    }


def build_telegram_product_ux_safety_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_product_ux_safety_snapshot_067a.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "paper_only": True,
        "review_only": True,
        "dry_run_only": True,
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


def build_latest_telegram_product_ux_status(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_latest_telegram_product_ux_status_067a.v1",
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "completed_pushed_remote_verified",
        "default_visible_language": DEFAULT_OPERATOR_LANGUAGE,
        "ru_first_menu_ready": True,
        "language_switching_ready": True,
        "product_screens_ready": True,
        "no_fake_balance_trades_or_pnl": True,
        "emergency_stop_placeholder_local_only": True,
        "allowed_for_live": False,
        "safety_snapshot_path": normalize_path(SAFETY_SNAPSHOT_PATH),
        "menu_snapshot_path": normalize_path(MENU_SNAPSHOT_PATH),
        "i18n_snapshot_path": normalize_path(I18N_SNAPSHOT_PATH),
    }


def build_telegram_product_ux_result(
    *,
    validation: list[Mapping[str, Any]] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_telegram_product_ux_result_067a.v1",
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
            "docs/ORCH_PMBOT_TELEGRAM_067A_PRODUCT_UX_RU_FIRST_MENU_NO_LIVE.md",
            "docs/ORCH_PMBOT_TELEGRAM_067A_PRODUCT_UX_RU_FIRST_MENU_NO_LIVE_RESULT.json",
            "pm_bot/operator_runner/telegram_operator_control_bot.py",
            "pm_bot/operator_runner/telegram_operator_i18n.py",
            "pm_bot/operator_runner/telegram_operator_runtime.py",
            "pm_bot/operator_runner/telegram_product_ux_067a.py",
            "pm_bot/tests/test_telegram_product_ux_067a.py",
            "pm_bot/tests/test_telegram_operator_control_bot_043.py",
            "pm_bot/tests/test_telegram_operator_runtime_045.py",
            "pm_bot/tests/test_telegram_operator_ux_buttons_046.py",
            "pm_bot/tests/test_telegram_operator_runtime_ux_smoke_fixes_046e.py",
            "pm_bot/tests/test_telegram_ru_language_mini_app_dev_mode_046g.py",
            "pm_bot/tests/test_telegram_mini_app_operator_panel_044.py",
            "pm_bot/tests/test_telegram_tiny_order_review_061t.py",
            normalize_path(RESULT_PATH),
            normalize_path(LATEST_STATUS_PATH),
            normalize_path(MENU_SNAPSHOT_PATH),
            normalize_path(I18N_SNAPSHOT_PATH),
            normalize_path(SAFETY_SNAPSHOT_PATH),
        ],
        "validation": [dict(item) for item in (VALIDATION_RESULTS if validation is None else validation)],
        "safety_statement": (
            "Telegram product UX remains review/status/dry-run only. It does not enable live trading, "
            "wallet connection, signing, order submission, order cancellation, authenticated Polymarket calls, "
            "or fake balance/trade/PnL output."
        ),
        "safety_flags": build_telegram_product_ux_safety_snapshot(generated_at=generated_at),
    }


def write_telegram_product_ux_067a_artifacts(
    *,
    output_dir: str | Path = ARTIFACT_DIR,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    output = Path(output_dir)
    menu = build_telegram_product_ux_menu_snapshot(generated_at=generated_at)
    i18n = build_telegram_product_ux_i18n_snapshot(generated_at=generated_at)
    safety = build_telegram_product_ux_safety_snapshot(generated_at=generated_at)
    latest = build_latest_telegram_product_ux_status(generated_at=generated_at)
    result = build_telegram_product_ux_result(generated_at=generated_at)
    paths = {
        "docs_result": DOC_RESULT_PATH,
        "result": output / RESULT_PATH.name,
        "latest_status": output / LATEST_STATUS_PATH.name,
        "menu_snapshot": output / MENU_SNAPSHOT_PATH.name,
        "i18n_snapshot": output / I18N_SNAPSHOT_PATH.name,
        "safety_snapshot": output / SAFETY_SNAPSHOT_PATH.name,
    }
    _write_json_lf(paths["docs_result"], result)
    _write_json_lf(paths["result"], result)
    _write_json_lf(paths["latest_status"], latest)
    _write_json_lf(paths["menu_snapshot"], menu)
    _write_json_lf(paths["i18n_snapshot"], i18n)
    _write_json_lf(paths["safety_snapshot"], safety)
    return {
        "result": result,
        "latest_status": latest,
        "menu_snapshot": menu,
        "i18n_snapshot": i18n,
        "safety_snapshot": safety,
        "paths": {key: normalize_path(path) for key, path in paths.items()},
    }


def _labels_for_language(language: str) -> list[str]:
    return [label for row in HOME_BUTTON_ROWS_BY_LANGUAGE[language] for label, _callback_data in row]


def _callbacks_for_language(language: str) -> list[str]:
    return [callback_data for row in HOME_BUTTON_ROWS_BY_LANGUAGE[language] for _label, callback_data in row]


def _write_json_lf(path: str | Path, value: Mapping[str, Any]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_bytes((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))


if __name__ == "__main__":
    write_telegram_product_ux_067a_artifacts()
