from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_operator_i18n import HOME_BUTTON_ROWS_BY_LANGUAGE, all_button_rows
from pm_bot.operator_runner.telegram_product_ux_068c import EN_MAIN_MENU_LABELS, RU_MAIN_MENU_LABELS
from pm_bot.operator_runner.telegram_status_registry import (
    STATUS_SOURCES,
    TELEGRAM_BALANCE_READONLY_STATUS_077F_FLOW_ID,
    build_telegram_console_context,
)
from pm_bot.trading_core.telegram_balance_readonly_status_077f import (
    ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME,
    SAFE_ACCOUNT_PROBE_COMMAND,
    build_telegram_balance_readonly_status,
)
from pm_bot.trading_core.live_account_readonly_state_models import (
    EXPECTED_SDK_INSTALL_COMMAND,
    EXPECTED_SDK_MODULE,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_API_SECRET = "raw-api-secret-077f-never-output"
RAW_PASSPHRASE = "raw-passphrase-077f-never-output"
RAW_WALLET = "0x3006000000000000000000000000000000000770"
RAW_FUNDER = "0x1111000000000000000000000000000000000770"

FORBIDDEN_CONTROL_TERMS = (
    "submit",
    "cancel",
    "sign",
    "wallet",
    "connect-wallet",
    "wallet-connect",
    "send-order",
    "submit-order",
    "cancel-order",
)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _env_row(name: str, present: bool) -> dict[str, Any]:
    return {
        "env_var_name": name,
        "present": present,
        "redaction_status": "present_redacted" if present else "missing",
        "raw_value_emitted": False,
    }


def _write_credential_visibility(
    root: Path,
    *,
    l2_visible: bool,
    wallet_visible: bool = True,
    signature_visible: bool = True,
    funder_visible: bool = True,
) -> None:
    requested_rows = [
        _env_row("POLYMARKET_API_KEY", l2_visible),
        _env_row("POLYMARKET_API_SECRET", l2_visible),
        _env_row("POLYMARKET_API_PASSPHRASE", l2_visible),
        _env_row("POLYMARKET_PRIVATE_KEY", True),
        _env_row("POLYMARKET_WALLET_ADDRESS", wallet_visible),
        _env_row("POLYMARKET_SIGNATURE_TYPE", signature_visible),
        _env_row("POLYMARKET_FUNDER_ADDRESS", funder_visible),
        _env_row("TELEGRAM_BOT_TOKEN", True),
        _env_row("TELEGRAM_ALLOWED_OPERATOR_IDS", True),
    ]
    missing_l2 = [row["env_var_name"] for row in requested_rows[:3] if row["present"] is not True]
    missing_wallet = [
        row["env_var_name"]
        for row in requested_rows
        if row["env_var_name"]
        in {"POLYMARKET_WALLET_ADDRESS", "POLYMARKET_SIGNATURE_TYPE", "POLYMARKET_FUNDER_ADDRESS"}
        and row["present"] is not True
    ]
    group_summary = {
        "polymarket_l2_visible": not missing_l2,
        "polymarket_l2_missing_env_vars": missing_l2,
        "private_key_visible": True,
        "wallet_context_visible": not missing_wallet,
        "wallet_context_missing_env_vars": missing_wallet,
        "telegram_credentials_visible": True,
    }
    latest = {
        "contract_version": "pmbot_latest_runtime_credential_visibility_077c_status.v1",
        "status": "runtime_credentials_visible" if not missing_l2 and not missing_wallet else "blocked",
        "polymarket_l2_visible": not missing_l2,
        "wallet_context_visible": not missing_wallet,
        "telegram_credentials_visible": True,
        "raw_values_emitted": False,
        "allowed_for_live": False,
    }
    result = {
        "contract_version": "pmbot_runtime_credential_visibility_077c_result.v1",
        "status": latest["status"],
        "requested_env_var_statuses": requested_rows,
        "group_summary": group_summary,
        "raw_values_emitted": False,
        "allowed_for_live": False,
        "trading_requested": False,
    }
    artifact_dir = root / "runtime_credential_visibility_077c"
    _write_json(artifact_dir / "latest_runtime_credential_visibility_077c_status.json", latest)
    _write_json(artifact_dir / "runtime_credential_visibility_077c_result.json", result)


def _write_account_artifact(
    root: Path,
    *,
    include_values: bool = True,
    performed: bool = True,
    status: str | None = None,
    sdk_status: str = "available",
) -> None:
    latest: dict[str, Any] = {
        "contract_version": "pmbot_latest_live_account_readonly_state_status_070c.v1",
        "status": status or ("account_state_probe_succeeded_live_blocked" if performed else "blocked_account_state_probe_failed"),
        "sdk_status": sdk_status,
        "expected_sdk_module": EXPECTED_SDK_MODULE,
        "expected_install_command": EXPECTED_SDK_INSTALL_COMMAND,
        "python_executable": "C:/safe/python.exe",
        "wallet_address_redacted": RAW_WALLET,
        "account_state_probe_performed": performed,
        "generated_at": GENERATED_AT,
        "allowed_for_live": False,
        "order_submission_enabled": False,
        "wallet_connection_attempted": False,
        "signing_enabled": False,
        "raw_values_emitted": False,
    }
    if include_values:
        latest.update(
            {
                "usdc_balance": "42.50",
                "open_position_count": 2,
                "open_order_count": 3,
            }
        )
    _write_json(root / "live_account_readonly_state_probe_070c" / "latest_live_account_readonly_state_status_070c.json", latest)


def _adapter(context: Mapping[str, Any]) -> runtime.TelegramOperatorRuntimeAdapter:
    bot = TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=context,
        generated_at=GENERATED_AT,
    )
    return runtime.TelegramOperatorRuntimeAdapter(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=context,
        bot=bot,
    )


def _ru_balance_reply(root: Path) -> runtime.TelegramRuntimeReply:
    context = build_telegram_console_context(artifact_root=root, generated_at=GENERATED_AT)
    adapter = _adapter(context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    return adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:balance")


def _labels(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def _callbacks(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.callback_data for row in reply.keyboard.rows for button in row if button.callback_data)


def _tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def test_missing_credentials_routes_to_connection(tmp_path: Path) -> None:
    _write_credential_visibility(tmp_path, l2_visible=False)

    reply = _ru_balance_reply(tmp_path)

    assert "Баланс недоступен: сначала завершите подключение." in reply.text
    assert _labels(reply) == ("🔌 Перейти к подключению",)
    assert _callbacks(reply) == ("pmbot:connection",)


def test_missing_funder_address_is_explained(tmp_path: Path) -> None:
    _write_credential_visibility(tmp_path, l2_visible=True, funder_visible=False)

    reply = _ru_balance_reply(tmp_path)

    assert "Баланс может быть недоступен: не указан Funder Address." in reply.text
    assert "Проверьте раздел Подключение." in reply.text
    assert _labels(reply) == ("🔌 Подключение",)
    assert _callbacks(reply) == ("pmbot:connection",)


def test_missing_account_artifact_shows_safe_command_and_refresh_controls(tmp_path: Path) -> None:
    _write_credential_visibility(tmp_path, l2_visible=True)

    reply = _ru_balance_reply(tmp_path)

    assert "Ключи видны, но проверка аккаунта ещё не выполнена." in reply.text
    assert SAFE_ACCOUNT_PROBE_COMMAND in reply.text
    assert _labels(reply) == ("🔄 Обновить", "🔌 Подключение", "⬅️ Главное меню")
    assert _callbacks(reply) == ("pmbot:balance", "pmbot:connection", "pmbot:home")


def test_blocked_sdk_unavailable_is_distinct_from_missing_account_artifact(tmp_path: Path) -> None:
    _write_credential_visibility(tmp_path, l2_visible=True)
    _write_account_artifact(
        tmp_path,
        include_values=False,
        performed=False,
        status="blocked_sdk_unavailable",
        sdk_status="blocked_sdk_unavailable",
    )

    status = build_telegram_balance_readonly_status(artifact_root=tmp_path, generated_at=GENERATED_AT)
    reply = _ru_balance_reply(tmp_path)

    assert status["screen_variant"] == "account_probe_blocked_sdk_unavailable"
    assert status["account_probe_blocked_sdk_unavailable"] is True
    assert status["account_expected_sdk_module"] == EXPECTED_SDK_MODULE
    assert status["account_expected_install_command"] == EXPECTED_SDK_INSTALL_COMMAND
    assert status["account_python_executable"] == "C:/safe/python.exe"
    assert "Проверка аккаунта заблокирована: официальный Polymarket CLOB SDK недоступен" in reply.text
    assert "Баланс не прочитан; фейковые значения не показываются." in reply.text
    assert f"Ожидаемый SDK: {EXPECTED_SDK_MODULE}" in reply.text
    assert f"Безопасная команда установки: {EXPECTED_SDK_INSTALL_COMMAND}" in reply.text
    assert "Python: C:/safe/python.exe" in reply.text
    assert "Ключи видны, но проверка аккаунта ещё не выполнена." not in reply.text
    assert SAFE_ACCOUNT_PROBE_COMMAND in reply.text


def test_present_artifact_shows_only_real_available_fields(tmp_path: Path) -> None:
    _write_credential_visibility(tmp_path, l2_visible=True)
    _write_account_artifact(tmp_path, include_values=True)

    reply = _ru_balance_reply(tmp_path)
    rendered = reply.text + "\n" + json.dumps(reply.to_redacted_dict(), ensure_ascii=False, sort_keys=True)

    assert "Кошелёк: 0x3006...0770" in reply.text
    assert "USDC: 42.50" in reply.text
    assert "Открытые позиции: 2" in reply.text
    assert "Открытые ордера: 3" in reply.text
    assert "Проверка аккаунта: выполнена" in reply.text
    assert f"Последняя проверка: {GENERATED_AT}" in reply.text
    assert "Статус проверки: account_state_probe_succeeded_live_blocked" in reply.text
    for raw in (RAW_API_SECRET, RAW_PASSPHRASE, RAW_WALLET, RAW_FUNDER):
        assert raw not in rendered
    for fake_value in ("$0", "0.00", "fake balance", "fake pnl", "order_id", "tx_hash", "profit:", "loss:"):
        assert fake_value not in rendered.lower()


def test_present_artifact_without_fields_does_not_invent_values(tmp_path: Path) -> None:
    _write_credential_visibility(tmp_path, l2_visible=True)
    _write_account_artifact(tmp_path, include_values=False, performed=False)

    status = build_telegram_balance_readonly_status(artifact_root=tmp_path, generated_at=GENERATED_AT)
    reply = _ru_balance_reply(tmp_path)

    assert status["account_readonly_artifact_available"] is True
    assert status["usdc_balance_display"] == ""
    assert status["open_positions_count_display"] == ""
    assert status["open_orders_count_display"] == ""
    assert "USDC: не найдено в последней проверке" in reply.text
    assert "Открытые позиции: не найдено в последней проверке" in reply.text
    assert "Открытые ордера: не найдено в последней проверке" in reply.text
    assert "Проверка аккаунта: не выполнена" in reply.text


def test_balance_status_source_and_refresh_button_are_registered() -> None:
    source = next(item for item in STATUS_SOURCES if item.flow_id == TELEGRAM_BALANCE_READONLY_STATUS_077F_FLOW_ID)

    assert source.artifact_dir_name == ARTIFACT_DIR_NAME
    assert source.latest_status_filename == LATEST_STATUS_FILENAME
    assert source.context_key == "telegram_balance_readonly_status_077f_status_summary"
    assert ("🔄 Обновить", "pmbot:balance") in [button for row in all_button_rows() for button in row]


def test_primary_menu_remains_clean_and_balance_controls_are_not_live_controls() -> None:
    ru_labels = tuple(label for row in HOME_BUTTON_ROWS_BY_LANGUAGE["ru"] for label, _callback in row)
    en_labels = tuple(label for row in HOME_BUTTON_ROWS_BY_LANGUAGE["en"] for label, _callback in row)

    assert ru_labels == RU_MAIN_MENU_LABELS
    assert en_labels == EN_MAIN_MENU_LABELS

    balance_controls = [
        f"{label} {callback_data}"
        for row in all_button_rows()
        for label, callback_data in row
        if callback_data in {"pmbot:balance", "pmbot:connection", "pmbot:home"}
    ]
    violations = []
    for control in balance_controls:
        tokens = _tokenize(control)
        if any(term in control.lower() for term in FORBIDDEN_CONTROL_TERMS) or tokens.intersection({"submit", "cancel", "sign", "wallet"}):
            violations.append(control)
    assert violations == []
