from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.artifact_resolution import (
    DEFAULT_ARTIFACT_ROOT,
    resolve_artifact_root,
    resolve_artifact_subdir,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, normalize_path, write_json
from pm_bot.trading_core.live_account_readonly_state_models import (
    EXPECTED_SDK_INSTALL_COMMAND,
    EXPECTED_SDK_MODULE,
)

TASK_ID = "ORCH-PMBOT-TELEGRAM-077F-BALANCE-READONLY-ACCOUNT-INTEGRATION-NO-LIVE"

STATUS_CONTRACT = "pmbot_telegram_balance_readonly_status_077f.v1"
RESULT_CONTRACT = "pmbot_telegram_balance_readonly_status_077f_result.v1"
MENU_SNAPSHOT_CONTRACT = "pmbot_telegram_balance_readonly_menu_snapshot_077f.v1"
SAFETY_SNAPSHOT_CONTRACT = "pmbot_telegram_balance_readonly_safety_snapshot_077f.v1"

ARTIFACT_DIR_NAME = "telegram_balance_readonly_status_077f"
RESULT_FILENAME = "telegram_balance_readonly_status_077f_result.json"
LATEST_STATUS_FILENAME = "latest_telegram_balance_readonly_status_077f.json"
MENU_SNAPSHOT_FILENAME = "telegram_balance_readonly_menu_snapshot_077f.json"
SAFETY_SNAPSHOT_FILENAME = "telegram_balance_readonly_safety_snapshot_077f.json"

DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME

RUNTIME_077C_DIR_NAMES = ("runtime_credential_visibility_077c",)
RUNTIME_077C_LATEST_FILENAMES = ("latest_runtime_credential_visibility_077c_status.json",)
RUNTIME_077C_RESULT_FILENAMES = ("runtime_credential_visibility_077c_result.json",)

ACCOUNT_070C_DIR_NAMES = ("live_account_readonly_state_probe_070c",)
ACCOUNT_070C_FILENAMES = (
    "latest_live_account_readonly_state_status_070c.json",
    "live_account_readonly_state_probe_070c_result.json",
)

SAFE_ACCOUNT_PROBE_COMMAND = (
    "python -m pm_bot.operator_runner.live_account_readonly_state_probe "
    "--market BTC --strategy tiny-momentum --dry-run"
)

L2_ENV_VARS = (
    "POLYMARKET_API_KEY",
    "POLYMARKET_API_SECRET",
    "POLYMARKET_API_PASSPHRASE",
)
WALLET_CONTEXT_ENV_VARS = (
    "POLYMARKET_WALLET_ADDRESS",
    "POLYMARKET_SIGNATURE_TYPE",
    "POLYMARKET_FUNDER_ADDRESS",
)

_ABSENT_TEXT = {
    "",
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


def telegram_balance_readonly_artifact_paths(output_dir: str | Path | None = None) -> dict[str, Path]:
    root = resolve_artifact_subdir(ARTIFACT_DIR_NAME, artifact_dir=output_dir)
    return {
        "root": root,
        "result": root / RESULT_FILENAME,
        "latest_status": root / LATEST_STATUS_FILENAME,
        "menu_snapshot": root / MENU_SNAPSHOT_FILENAME,
        "safety_snapshot": root / SAFETY_SNAPSHOT_FILENAME,
    }


def build_telegram_balance_readonly_status(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = resolve_artifact_root(artifact_root)
    credential_latest_path = _first_existing_path(
        _candidate_paths(root, RUNTIME_077C_DIR_NAMES, RUNTIME_077C_LATEST_FILENAMES)
    )
    credential_result_path = _first_existing_path(
        _candidate_paths(root, RUNTIME_077C_DIR_NAMES, RUNTIME_077C_RESULT_FILENAMES)
    )
    account_path = _first_existing_path(_candidate_paths(root, ACCOUNT_070C_DIR_NAMES, ACCOUNT_070C_FILENAMES))

    credential_latest = _load_optional_json(credential_latest_path, "077F runtime credential latest status")
    credential_result = _load_optional_json(credential_result_path, "077F runtime credential result")
    account = _load_optional_json(account_path, "077F live account read-only artifact")
    credential = _credential_visibility_summary(credential_latest, credential_result)
    account_summary = _account_artifact_summary(account, account_path)

    credentials_visible = credential["polymarket_l2_visible"] is True
    funder_present = credential["funder_address_present"] is True
    account_available = bool(account)
    sdk_unavailable = _account_probe_blocked_sdk_unavailable(account_summary)
    if not credentials_visible:
        status = "balance_unavailable_missing_credentials"
        screen_variant = "missing_credentials"
    elif not funder_present:
        status = "balance_maybe_unavailable_missing_funder"
        screen_variant = "missing_funder"
    elif not account_available:
        status = "balance_readonly_account_probe_missing"
        screen_variant = "missing_account_artifact"
    elif sdk_unavailable:
        status = "balance_readonly_account_probe_blocked_sdk_unavailable"
        screen_variant = "account_probe_blocked_sdk_unavailable"
    else:
        status = "balance_readonly_account_artifact_available"
        screen_variant = "account_artifact_available"

    latest_status: dict[str, Any] = {
        "contract_version": STATUS_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": status,
        "screen_variant": screen_variant,
        "mode": "telegram balance read-only account artifact display",
        "execution_mode": "local_artifact_read_only_display",
        "artifact_root": normalize_path(root),
        "credential_visibility_artifact_available": bool(credential_latest or credential_result),
        "credential_visibility_latest_path": normalize_path(credential_latest_path) if credential_latest_path else "",
        "credential_visibility_result_path": normalize_path(credential_result_path) if credential_result_path else "",
        "credentials_visible": credentials_visible,
        "polymarket_l2_visible": credentials_visible,
        "missing_l2_env_vars": list(credential["missing_l2_env_vars"]),
        "wallet_context_complete": credential["wallet_context_complete"] is True,
        "missing_wallet_context_env_vars": list(credential["missing_wallet_context_env_vars"]),
        "wallet_address_present": credential["wallet_address_present"] is True,
        "signature_type_present": credential["signature_type_present"] is True,
        "funder_address_present": funder_present,
        "account_readonly_artifact_available": account_available,
        "account_readonly_artifact_path": normalize_path(account_path) if account_path else "",
        "account_probe_run": account_available,
        "account_probe_blocked_sdk_unavailable": sdk_unavailable,
        "account_probe_status": account_summary["account_probe_status"],
        "account_sdk_status": account_summary["account_sdk_status"],
        "account_expected_sdk_module": account_summary["account_expected_sdk_module"],
        "account_expected_install_command": account_summary["account_expected_install_command"],
        "account_python_executable": account_summary["account_python_executable"],
        "account_sdk_import_reports": list(account_summary["account_sdk_import_reports"]),
        "account_pip_package_visibility": list(account_summary["account_pip_package_visibility"]),
        "account_state_probe_performed": account_summary["account_state_probe_performed"] is True,
        "safe_account_probe_command": SAFE_ACCOUNT_PROBE_COMMAND,
        "wallet_short_address": account_summary["wallet_short_address"],
        "usdc_balance_display": account_summary["usdc_balance_display"],
        "open_positions_count_display": account_summary["open_positions_count_display"],
        "open_orders_count_display": account_summary["open_orders_count_display"],
        "last_check_timestamp": account_summary["last_check_timestamp"],
        "last_check_status": account_summary["last_check_status"],
        "source_artifacts": {
            "runtime_credential_visibility_077c_latest": _artifact_summary(credential_latest_path, credential_latest),
            "runtime_credential_visibility_077c_result": _artifact_summary(credential_result_path, credential_result),
            "live_account_readonly_state_probe_070c": _artifact_summary(account_path, account),
        },
        "display_only": True,
        "local_artifact_read_only": True,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_balance_readonly_safety_flags(),
    }
    latest_status["status_text_ru"] = render_telegram_balance_readonly_status_text(latest_status, language="ru")
    latest_status["status_text_en"] = render_telegram_balance_readonly_status_text(latest_status, language="en")
    return latest_status


def write_telegram_balance_readonly_status_077f_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    status = build_telegram_balance_readonly_status(artifact_root=artifact_root, generated_at=generated_at)
    paths = telegram_balance_readonly_artifact_paths(output_dir)
    menu = build_telegram_balance_readonly_menu_snapshot(generated_at=generated_at)
    safety = build_telegram_balance_readonly_safety_snapshot(generated_at=generated_at)
    result = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "completed_display_only",
        "latest_status_path": normalize_path(paths["latest_status"]),
        "menu_snapshot_path": normalize_path(paths["menu_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "telegram_balance_readonly_status_077f": status,
        "menu_snapshot": menu,
        "safety_snapshot": safety,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "display_only": True,
        "execution_enabling": False,
        **telegram_balance_readonly_safety_flags(),
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


def build_telegram_balance_readonly_menu_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    buttons = [
        {"language": "ru", "label": "🔄 Обновить", "callback_data": "pmbot:balance"},
        {"language": "ru", "label": "🔌 Подключение", "callback_data": "pmbot:connection"},
        {"language": "ru", "label": "⬅️ Главное меню", "callback_data": "pmbot:home"},
        {"language": "en", "label": "🔄 Refresh", "callback_data": "pmbot:balance"},
        {"language": "en", "label": "🔌 Connection", "callback_data": "pmbot:connection"},
        {"language": "en", "label": "⬅️ Main menu", "callback_data": "pmbot:home"},
    ]
    return {
        "contract_version": MENU_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "title_ru": "💰 Баланс",
        "title_en": "Balance",
        "buttons": buttons,
        "button_count": len(buttons),
        "refresh_callback_data": "pmbot:balance",
        "connection_callback_data": "pmbot:connection",
        "safe_account_probe_command": SAFE_ACCOUNT_PROBE_COMMAND,
        "safe_command_display_only": True,
        "safe_command_button_added": False,
        "forbidden_live_controls_added": False,
        "submit_cancel_controls_added": False,
        "signing_controls_added": False,
        "wallet_controls_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_balance_readonly_safety_flags(),
    }


def build_telegram_balance_readonly_safety_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "safe_local_readonly_balance_display",
        "allowed_inputs": [
            "local 077C runtime credential visibility artifacts",
            "local 070C live account read-only probe artifacts",
        ],
        "forbidden_actions": [
            "live trading",
            "order submission",
            "order cancellation",
            "wallet connection",
            "signing",
            "secret display",
            "authenticated calls from Telegram balance rendering",
            "fake balances, positions, orders, fills, or PnL",
        ],
        "display_does_not_run_probe": True,
        "safe_probe_command_is_text_only": True,
        "no_fake_balance_pnl_orders": True,
        **telegram_balance_readonly_safety_flags(),
    }


def render_telegram_balance_readonly_status_text(status: Mapping[str, Any], *, language: str = "ru") -> str:
    value = normalize_telegram_balance_readonly_status_summary(status)
    if clean_text(language).lower() == "ru":
        if value["screen_variant"] == "missing_credentials":
            return "\n".join(
                [
                    "💰 Баланс",
                    "Баланс недоступен: сначала завершите подключение.",
                ]
            )
        if value["screen_variant"] == "missing_funder":
            return "\n".join(
                [
                    "💰 Баланс",
                    "Баланс может быть недоступен: не указан Funder Address.",
                    "Проверьте раздел Подключение.",
                ]
            )
        if value["screen_variant"] == "missing_account_artifact":
            return "\n".join(
                [
                    "💰 Баланс",
                    "Ключи видны, но проверка аккаунта ещё не выполнена.",
                    "Безопасная команда:",
                    value["safe_account_probe_command"],
                ]
            )
        if value["screen_variant"] == "account_probe_blocked_sdk_unavailable":
            return "\n".join(
                [
                    "💰 Баланс",
                    "Проверка баланса недоступна: не найден Polymarket CLOB SDK в текущем Python.",
                    "Баланс не прочитан; фейковые значения не показываются.",
                    f"Ожидаемый SDK: {value['account_expected_sdk_module'] or EXPECTED_SDK_MODULE}",
                    "Безопасные команды:",
                    value["account_expected_install_command"] or EXPECTED_SDK_INSTALL_COMMAND,
                    value["safe_account_probe_command"],
                    f"Python: {value['account_python_executable'] or 'нет данных'}",
                    f"Статус проверки: {value['account_probe_status'] or 'blocked_sdk_unavailable'}",
                ]
            )
        return "\n".join(
            [
                "💰 Баланс",
                f"Кошелёк: {value['wallet_short_address'] or 'нет данных'}",
                f"USDC: {value['usdc_balance_display'] or 'не найдено в последней проверке'}",
                f"Открытые позиции: {value['open_positions_count_display'] or 'не найдено в последней проверке'}",
                f"Открытые ордера: {value['open_orders_count_display'] or 'не найдено в последней проверке'}",
                f"Проверка аккаунта: {'выполнена' if value['account_state_probe_performed'] else 'не выполнена'}",
                f"Последняя проверка: {value['last_check_timestamp'] or 'нет данных'}",
                f"Статус проверки: {value['last_check_status'] or 'нет данных'}",
            ]
        )

    if value["screen_variant"] == "missing_credentials":
        return "\n".join(
            [
                "💰 Balance",
                "Balance is unavailable: finish connection first.",
            ]
        )
    if value["screen_variant"] == "missing_funder":
        return "\n".join(
            [
                "💰 Balance",
                "Balance may be unavailable: Funder Address is not set.",
                "Check the Connection section.",
            ]
        )
    if value["screen_variant"] == "missing_account_artifact":
        return "\n".join(
            [
                "💰 Balance",
                "Keys are visible, but the account check has not been run yet.",
                "Safe command:",
                value["safe_account_probe_command"],
            ]
        )
    if value["screen_variant"] == "account_probe_blocked_sdk_unavailable":
        return "\n".join(
            [
                "💰 Balance",
                "Balance check is unavailable: Polymarket CLOB SDK was not found in the current Python.",
                "Balance was not read; fake values are not shown.",
                f"Expected SDK: {value['account_expected_sdk_module'] or EXPECTED_SDK_MODULE}",
                "Safe commands:",
                value["account_expected_install_command"] or EXPECTED_SDK_INSTALL_COMMAND,
                value["safe_account_probe_command"],
                f"Python: {value['account_python_executable'] or 'no data'}",
                f"Check status: {value['account_probe_status'] or 'blocked_sdk_unavailable'}",
            ]
        )
    return "\n".join(
        [
            "💰 Balance",
            f"Wallet: {value['wallet_short_address'] or 'no data'}",
            f"USDC: {value['usdc_balance_display'] or 'not found in the latest check'}",
            f"Open positions: {value['open_positions_count_display'] or 'not found in the latest check'}",
            f"Open orders: {value['open_orders_count_display'] or 'not found in the latest check'}",
            f"Account check: {'performed' if value['account_state_probe_performed'] else 'not performed'}",
            f"Last check: {value['last_check_timestamp'] or 'no data'}",
            f"Check status: {value['last_check_status'] or 'no data'}",
        ]
    )


def normalize_telegram_balance_readonly_status_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    screen_variant = clean_text(value.get("screen_variant"))
    if screen_variant not in {
        "missing_credentials",
        "missing_funder",
        "missing_account_artifact",
        "account_probe_blocked_sdk_unavailable",
        "account_artifact_available",
    }:
        if value.get("credentials_visible") is not True:
            screen_variant = "missing_credentials"
        elif value.get("funder_address_present") is not True:
            screen_variant = "missing_funder"
        elif value.get("account_readonly_artifact_available") is not True:
            screen_variant = "missing_account_artifact"
        elif value.get("account_probe_blocked_sdk_unavailable") is True:
            screen_variant = "account_probe_blocked_sdk_unavailable"
        else:
            screen_variant = "account_artifact_available"
    return {
        "contract_version": clean_text(value.get("contract_version")),
        "screen_available": (
            clean_text(value.get("contract_version")) == STATUS_CONTRACT
            or value.get("screen_available") is True
        ),
        "status": clean_text(value.get("status") or "balance_unavailable_missing_credentials"),
        "screen_variant": screen_variant,
        "mode": clean_text(value.get("mode") or "telegram balance read-only account artifact display"),
        "execution_mode": clean_text(value.get("execution_mode") or "local_artifact_read_only_display"),
        "credentials_visible": value.get("credentials_visible") is True
        or value.get("polymarket_l2_visible") is True,
        "polymarket_l2_visible": value.get("polymarket_l2_visible") is True
        or value.get("credentials_visible") is True,
        "missing_l2_env_vars": _clean_list(value.get("missing_l2_env_vars")),
        "wallet_context_complete": value.get("wallet_context_complete") is True,
        "missing_wallet_context_env_vars": _clean_list(value.get("missing_wallet_context_env_vars")),
        "wallet_address_present": value.get("wallet_address_present") is True,
        "signature_type_present": value.get("signature_type_present") is True,
        "funder_address_present": value.get("funder_address_present") is True,
        "account_readonly_artifact_available": value.get("account_readonly_artifact_available") is True,
        "account_readonly_artifact_path": clean_text(value.get("account_readonly_artifact_path")),
        "account_probe_run": value.get("account_probe_run") is True,
        "account_probe_blocked_sdk_unavailable": value.get("account_probe_blocked_sdk_unavailable") is True,
        "account_probe_status": clean_text(value.get("account_probe_status")),
        "account_sdk_status": clean_text(value.get("account_sdk_status")),
        "account_expected_sdk_module": clean_text(value.get("account_expected_sdk_module")) or EXPECTED_SDK_MODULE,
        "account_expected_install_command": (
            clean_text(value.get("account_expected_install_command")) or EXPECTED_SDK_INSTALL_COMMAND
        ),
        "account_python_executable": clean_text(value.get("account_python_executable")),
        "account_sdk_import_reports": [
            dict(row) for row in value.get("account_sdk_import_reports", []) if isinstance(row, Mapping)
        ],
        "account_pip_package_visibility": [
            dict(row) for row in value.get("account_pip_package_visibility", []) if isinstance(row, Mapping)
        ],
        "account_state_probe_performed": value.get("account_state_probe_performed") is True,
        "safe_account_probe_command": clean_text(value.get("safe_account_probe_command")) or SAFE_ACCOUNT_PROBE_COMMAND,
        "wallet_short_address": _safe_short_address(value.get("wallet_short_address")),
        "usdc_balance_display": _optional_display(value.get("usdc_balance_display")),
        "open_positions_count_display": _optional_display(value.get("open_positions_count_display")),
        "open_orders_count_display": _optional_display(value.get("open_orders_count_display")),
        "last_check_timestamp": _optional_display(value.get("last_check_timestamp")),
        "last_check_status": _optional_display(value.get("last_check_status")),
        "display_only": True,
        "local_artifact_read_only": True,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_balance_readonly_safety_flags(),
    }


def telegram_balance_readonly_safety_flags() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "display_only": True,
        "network_used": False,
        "external_api_calls_performed": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "telegram_authenticated_call_performed": False,
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
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "credentials_values_exposed": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "order_submission_available": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "order_cancel_enabled": False,
        "real_order_submitted": False,
        "real_order_cancelled": False,
        "balance_read_attempted": False,
        "position_read_attempted": False,
        "fill_read_attempted": False,
        "pnl_read_attempted": False,
        "fake_balance_added": False,
        "fake_balances_emitted": False,
        "fake_orders_emitted": False,
        "fake_positions_emitted": False,
        "fake_fills_emitted": False,
        "fake_pnl_added": False,
        "fake_pnl_emitted": False,
        "live_trading_enabled": False,
        "allowed_for_live": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "live_execution_approved": False,
        "live_execution_performed": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "live_connector_enabled": False,
        "telegram_live_order_controls_added": False,
        "telegram_signing_controls_added": False,
        "telegram_wallet_controls_added": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def _credential_visibility_summary(
    latest: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    payloads = (dict(result or {}), dict(latest or {}))
    group = _first_mapping(*(payload.get("group_summary") for payload in payloads))
    missing_l2 = _missing_env_vars(payloads, group, "polymarket_l2_missing_env_vars", L2_ENV_VARS)
    missing_wallet = _missing_env_vars(payloads, group, "wallet_context_missing_env_vars", WALLET_CONTEXT_ENV_VARS)
    l2_visible = _visible_flag(payloads, group, "polymarket_l2_visible", L2_ENV_VARS, missing_l2)
    wallet_context_complete = _visible_flag(
        payloads,
        group,
        "wallet_context_visible",
        WALLET_CONTEXT_ENV_VARS,
        missing_wallet,
    )
    return {
        "polymarket_l2_visible": l2_visible,
        "missing_l2_env_vars": tuple(missing_l2),
        "wallet_context_complete": wallet_context_complete,
        "missing_wallet_context_env_vars": tuple(missing_wallet),
        "wallet_address_present": "POLYMARKET_WALLET_ADDRESS" not in missing_wallet
        and (_row_present(payloads, "POLYMARKET_WALLET_ADDRESS") or wallet_context_complete),
        "signature_type_present": "POLYMARKET_SIGNATURE_TYPE" not in missing_wallet
        and (_row_present(payloads, "POLYMARKET_SIGNATURE_TYPE") or wallet_context_complete),
        "funder_address_present": "POLYMARKET_FUNDER_ADDRESS" not in missing_wallet
        and (_row_present(payloads, "POLYMARKET_FUNDER_ADDRESS") or wallet_context_complete),
    }


def _account_artifact_summary(account: Mapping[str, Any], path: Path | None) -> dict[str, Any]:
    value = dict(account or {})
    latest = _first_mapping(value.get("latest_status"), value)
    account_status = _first_mapping(value.get("account_status"), latest.get("account_status"))
    sdk_status = _first_mapping(value.get("sdk_status"))
    search_payloads = (latest, value, account_status)
    sdk_payloads = (latest, sdk_status, value)
    account_probe_status = _first_optional_text(search_payloads, ("status", "account_status"))
    account_sdk_status = _first_optional_text(sdk_payloads, ("sdk_status", "status"))
    return {
        "available": bool(value),
        "path": normalize_path(path) if path else "",
        "wallet_short_address": _first_short_address(search_payloads),
        "usdc_balance_display": _first_usdc_balance(search_payloads),
        "open_positions_count_display": _first_count_display(
            search_payloads,
            ("open_position_count", "open_positions_count", "position_count", "positions_count"),
            ("open_positions", "positions"),
        ),
        "open_orders_count_display": _first_count_display(
            search_payloads,
            ("open_order_count", "open_orders_count", "order_count", "orders_count"),
            ("open_orders", "orders"),
        ),
        "last_check_timestamp": _first_optional_text(search_payloads, ("last_check_timestamp", "generated_at")),
        "last_check_status": account_probe_status,
        "account_probe_status": account_probe_status,
        "account_sdk_status": account_sdk_status,
        "account_expected_sdk_module": _first_optional_text(sdk_payloads, ("expected_sdk_module",))
        or EXPECTED_SDK_MODULE,
        "account_expected_install_command": _first_optional_text(sdk_payloads, ("expected_install_command",))
        or EXPECTED_SDK_INSTALL_COMMAND,
        "account_python_executable": _first_optional_text(sdk_payloads, ("python_executable",)),
        "account_sdk_import_reports": tuple(_first_list(sdk_payloads, "sdk_import_reports")),
        "account_pip_package_visibility": tuple(_first_list(sdk_payloads, "pip_package_visibility")),
        "account_state_probe_performed": any(payload.get("account_state_probe_performed") is True for payload in search_payloads),
    }


def _account_probe_blocked_sdk_unavailable(account_summary: Mapping[str, Any]) -> bool:
    return "blocked_sdk_unavailable" in {
        clean_text(account_summary.get("account_probe_status")),
        clean_text(account_summary.get("account_sdk_status")),
        clean_text(account_summary.get("last_check_status")),
    }


def _missing_env_vars(
    payloads: Sequence[Mapping[str, Any]],
    group: Mapping[str, Any],
    missing_key: str,
    env_vars: Sequence[str],
) -> list[str]:
    flag_key = {
        "polymarket_l2_missing_env_vars": "polymarket_l2_visible",
        "wallet_context_missing_env_vars": "wallet_context_visible",
    }.get(missing_key, "")
    if flag_key and group.get(flag_key) is True:
        return []
    if flag_key and any(payload.get(flag_key) is True for payload in payloads):
        return []
    direct = _clean_list(group.get(missing_key))
    if direct:
        return [item for item in env_vars if item in direct]
    rows = _env_rows(payloads)
    if rows:
        missing = [name for name in env_vars if dict(rows.get(name, {})).get("present") is not True]
        return missing
    for payload in payloads:
        if payload.get(missing_key):
            return [item for item in env_vars if item in _clean_list(payload.get(missing_key))]
    return list(env_vars)


def _visible_flag(
    payloads: Sequence[Mapping[str, Any]],
    group: Mapping[str, Any],
    flag_key: str,
    env_vars: Sequence[str],
    missing_env_vars: Sequence[str],
) -> bool:
    if flag_key in group:
        return group.get(flag_key) is True
    for payload in payloads:
        if flag_key in payload:
            return payload.get(flag_key) is True
    rows = _env_rows(payloads)
    if rows:
        return all(dict(rows.get(name, {})).get("present") is True for name in env_vars)
    return not missing_env_vars


def _env_rows(payloads: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    rows: dict[str, Mapping[str, Any]] = {}
    for payload in payloads:
        for key in ("requested_env_var_statuses", "runtime_alias_env_var_statuses"):
            for row in payload.get(key, []) or []:
                if isinstance(row, Mapping) and clean_text(row.get("env_var_name")):
                    rows[clean_text(row.get("env_var_name"))] = row
    return rows


def _row_present(payloads: Sequence[Mapping[str, Any]], env_var_name: str) -> bool:
    row = dict(_env_rows(payloads).get(env_var_name, {}))
    return row.get("present") is True


def _first_short_address(payloads: Sequence[Mapping[str, Any]]) -> str:
    for key in (
        "wallet_short_address",
        "wallet_address_redacted",
        "wallet_address",
        "wallet",
        "account_address_redacted",
        "account_address",
    ):
        for payload in payloads:
            text = _safe_short_address(payload.get(key))
            if text:
                return text
    return ""


def _first_usdc_balance(payloads: Sequence[Mapping[str, Any]]) -> str:
    for key in (
        "usdc_balance_display",
        "usdc_balance",
        "usdc_available_balance",
        "available_usdc",
        "cash_usdc",
    ):
        text = _first_optional_text(payloads, (key,))
        if text:
            return text
    for payload in payloads:
        balance = _balance_from_collection(payload.get("balances"))
        if balance:
            return balance
        balance = _balance_from_collection(payload.get("account_balances"))
        if balance:
            return balance
    return ""


def _balance_from_collection(value: Any) -> str:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if clean_text(key).upper() == "USDC":
                return _optional_display(nested)
        return ""
    if isinstance(value, list):
        for row in value:
            if not isinstance(row, Mapping):
                continue
            asset = clean_text(row.get("asset") or row.get("asset_code") or row.get("currency")).upper()
            if asset != "USDC":
                continue
            return _first_optional_text((row,), ("balance", "amount", "value", "available"))
    return ""


def _first_count_display(
    payloads: Sequence[Mapping[str, Any]],
    count_keys: Sequence[str],
    list_keys: Sequence[str],
) -> str:
    for key in count_keys:
        for payload in payloads:
            value = payload.get(key)
            if value is None or isinstance(value, bool):
                continue
            try:
                return str(int(value))
            except (TypeError, ValueError):
                text = _optional_display(value)
                if text:
                    return text
    for key in list_keys:
        for payload in payloads:
            value = payload.get(key)
            if isinstance(value, list):
                return str(len(value))
    return ""


def _first_optional_text(payloads: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> str:
    for key in keys:
        for payload in payloads:
            text = _optional_display(payload.get(key))
            if text:
                return text
    return ""


def _first_list(payloads: Sequence[Mapping[str, Any]], key: str) -> list[Any]:
    for payload in payloads:
        value = payload.get(key)
        if isinstance(value, list):
            return list(value)
        if isinstance(value, tuple):
            return list(value)
    return []


def _optional_display(value: Any) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, (dict, list, tuple)):
        return ""
    text = clean_text(value)
    if text.lower() in _ABSENT_TEXT:
        return ""
    return text


def _safe_short_address(value: Any) -> str:
    text = clean_text(value)
    lowered = text.lower()
    if lowered in _ABSENT_TEXT or lowered in {"present", "present_redacted", "redacted"}:
        return ""
    if text.startswith("0x") and "..." in text and len(text) <= 32:
        return text
    if text.startswith("0x") and len(text) == 42:
        return f"{text[:6]}...{text[-4:]}"
    return ""


def _artifact_summary(path: Path | None, payload: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(payload or {})
    return {
        "available": bool(value),
        "path": normalize_path(path) if path else "",
        "status": clean_text(value.get("status") or "not_available") if value else "missing",
        "contract_version": clean_text(value.get("contract_version")) if value else "",
    }


def _candidate_paths(root: Path, dir_names: Sequence[str], filenames: Sequence[str]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for dirname in dir_names:
        for filename in filenames:
            paths.append(root / dirname / filename)
    for filename in filenames:
        paths.append(root / filename)
    return _dedupe_paths(paths)


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


def _first_existing_path(paths: Sequence[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def _load_optional_json(path: Path | None, label: str) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return load_json_object(path, label=label)
    except Exception:
        return {}


def _first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping) and value:
            return dict(value)
    return {}


def _clean_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values] if clean_text(values) else []
    try:
        return [clean_text(item) for item in values if clean_text(item)]
    except TypeError:
        return []


if __name__ == "__main__":
    write_telegram_balance_readonly_status_077f_artifacts()
