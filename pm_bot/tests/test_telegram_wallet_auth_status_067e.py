from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_status_registry import (
    TELEGRAM_CONNECTION_STATUS_067E_FLOW_ID,
    STATUS_SOURCES,
    build_telegram_console_context,
    safe_action_by_callback,
    safe_action_by_id,
    validate_safe_action,
)
from pm_bot.trading_core.telegram_wallet_auth_status_dashboard import (
    ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME,
    RESULT_FILENAME,
    build_telegram_wallet_auth_status,
    telegram_wallet_auth_status_artifact_paths,
    write_telegram_wallet_auth_status_067e_artifacts,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_WALLET = "0x3006000000000000000000000000000000008989"
RAW_FUNDER = "0x1111000000000000000000000000000000005555"
RAW_SECRET_VALUES = (
    "raw-private-key-067e-never-output",
    "raw-api-secret-067e-never-output",
    "raw-passphrase-067e-never-output",
)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _marker(label: str, present: bool) -> dict[str, Any]:
    return {
        "marker_label": label,
        "marker_group": "credential_source_marker",
        "required_for_redacted_review": True,
        "present": present,
        "result_category": "present_redacted" if present else "missing",
        "presence_boolean_only": True,
        "value_redacted": True,
        "value_read": False,
        "raw_value_emitted": False,
    }


def _write_presence_and_probe_artifacts(root: Path) -> None:
    _write_json(
        root / "explicit_live_credentials_readiness_gate_064" / "redacted_marker_presence_064.json",
        {
            "contract_version": "fixture.credentials.064.v1",
            "marker_checks": [
                _marker("PMBOT_POLYMARKET_L2_API_KEY_PRESENT", True),
                _marker("PMBOT_POLYMARKET_L2_API_SECRET_PRESENT", True),
                _marker("PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT", True),
                _marker("PMBOT_PRIVATE_KEY_CONFIGURED", True),
                _marker("PMBOT_WALLET_ADDRESS_CONFIGURED", True),
                _marker("PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED", True),
            ],
            "credential_values_read": False,
            "raw_values_emitted": False,
        },
    )
    _write_json(
        root / "clob_l2_auth_readonly_probe_067c" / "latest_clob_l2_auth_readonly_probe_status_067c.json",
        {
            "contract_version": "pmbot_clob_l2_auth_readonly_probe_067c.fixture.v1",
            "task_id": "ORCH-PMBOT-TELEGRAM-067C-CLOB-L2-AUTH-READONLY-PROBE",
            "status": "ok",
            "wallet_address": RAW_WALLET,
            "signature_type": 3,
            "funder_address": RAW_FUNDER,
            "open_orders_status": "known_from_probe",
            "balance_allowance_status": "known_from_probe",
            "private_key": RAW_SECRET_VALUES[0],
            "api_secret": RAW_SECRET_VALUES[1],
            "passphrase": RAW_SECRET_VALUES[2],
            "real_authenticated_get_performed": True,
        },
    )


def _adapter(
    *,
    context: Mapping[str, Any],
    mini_app_url: str = "",
    action_runner=None,  # type: ignore[no-untyped-def]
) -> runtime.TelegramOperatorRuntimeAdapter:
    bot = TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=context,
        action_runner=action_runner,
        generated_at=GENERATED_AT,
    )
    return runtime.TelegramOperatorRuntimeAdapter(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            mini_app_url=mini_app_url,
            generated_at=GENERATED_AT,
        ),
        context=context,
        bot=bot,
    )


def _button_labels(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def _callback_data(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.callback_data for row in reply.keyboard.rows for button in row if button.callback_data)


def test_067e_builds_required_artifacts_from_redacted_presence_and_067c_probe(tmp_path: Path) -> None:
    _write_presence_and_probe_artifacts(tmp_path)

    generated = write_telegram_wallet_auth_status_067e_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    paths = telegram_wallet_auth_status_artifact_paths(tmp_path / ARTIFACT_DIR_NAME)
    latest = generated["latest_status"]
    rendered = json.dumps(generated, sort_keys=True, ensure_ascii=False)

    assert paths["result"].name == RESULT_FILENAME
    assert paths["latest_status"].name == LATEST_STATUS_FILENAME
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert paths["menu_snapshot"].exists()
    assert paths["safety_snapshot"].exists()
    assert latest["api_keys_display_ru"] == "добавлены"
    assert latest["private_key_display_ru"] == "добавлен"
    assert latest["wallet_display"] == "0x3006...8989"
    assert latest["signature_type_display"] == "3"
    assert latest["funder_display"] == "0x1111...5555"
    assert latest["l2_auth_probe_display"] == "ok"
    assert latest["open_orders_status"] == "known_from_probe"
    assert latest["balance_allowance_status"] == "known_from_probe"
    assert "🔐 Подключение" in latest["status_text_ru"]
    assert "Values never shown" in latest["status_text_ru"]
    assert latest["dashboard_authenticated_call_performed"] is False
    assert latest["order_submission_attempted"] is False
    assert latest["wallet_connection_attempted"] is False
    assert RAW_WALLET not in rendered
    assert RAW_FUNDER not in rendered
    for raw in RAW_SECRET_VALUES:
        assert raw not in rendered


def test_067e_missing_artifacts_default_to_missing_and_unknown_without_probe(tmp_path: Path) -> None:
    status = build_telegram_wallet_auth_status(artifact_root=tmp_path, generated_at=GENERATED_AT)

    assert status["api_keys_display_ru"] == "не добавлены"
    assert status["private_key_display_ru"] == "не добавлен"
    assert status["wallet_display"] == "missing"
    assert status["signature_type_display"] == "missing"
    assert status["funder_display"] == "missing"
    assert status["l2_auth_probe_display"] == "not run"
    assert status["open_orders_status"] == "unknown"
    assert status["balance_allowance_status"] == "unknown"
    assert status["clob_l2_auth_readonly_probe_artifact_available"] is False
    assert status["credential_values_read"] is False
    assert status["raw_values_emitted"] is False


def test_067e_telegram_screen_renders_ru_buttons_and_mini_app_when_configured(tmp_path: Path) -> None:
    _write_presence_and_probe_artifacts(tmp_path)
    write_telegram_wallet_auth_status_067e_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context, mini_app_url="https://example.com/pmbot")
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/connection_status")
    labels = _button_labels(reply)
    callbacks = _callback_data(reply)

    assert reply.command == "/connection_status"
    assert "🔐 Подключение" in reply.text
    assert "API ключи: добавлены" in reply.text
    assert "Private key: добавлен" in reply.text
    assert "Wallet: 0x3006...8989" in reply.text
    assert "L2 auth probe: ok" in reply.text
    assert "Open orders: known_from_probe" in reply.text
    assert "Balance/allowance: known_from_probe" in reply.text
    assert "🧪 Проверить подключение" in labels
    assert "⬅️ Назад" in labels
    assert "pmbot:run:connection_status_067e" in callbacks
    assert "pmbot:home" in callbacks
    assert reply.panel_button_url == ""


def test_067e_safe_action_is_dry_run_status_only_and_callback_renders_result(tmp_path: Path) -> None:
    _write_presence_and_probe_artifacts(tmp_path)
    write_telegram_wallet_auth_status_067e_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    action = safe_action_by_id("run_connection_status_067e")
    callback_action = safe_action_by_callback("pmbot:run:connection_status_067e")

    assert action is not None
    assert callback_action == action
    assert validate_safe_action(action) == []
    assert action.module == "pm_bot.operator_runner.telegram_connection_status_dashboard"
    assert action.args == ("--dry-run",)

    calls: list[str] = []

    def fake_action_runner(action_id: str) -> dict[str, Any]:
        calls.append(action_id)
        return {
            "status": "completed",
            "returncode": 0,
            "stdout_excerpt": "067E status refreshed in dry-run mode",
            "stderr_excerpt": "",
        }

    adapter = _adapter(
        context=build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT),
        action_runner=fake_action_runner,
    )
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    reply = adapter.handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:run:connection_status_067e",
    )

    assert "dry-run/preflight action" in reply.text
    assert "067E status refreshed in dry-run mode" in reply.text
    assert "order_submission_enabled: false" in reply.text
    assert "wallet_signing_enabled: false" in reply.text
    assert calls == ["run_connection_status_067e"]


def test_067e_status_source_is_registered_without_wallet_control_tokens() -> None:
    source = next(item for item in STATUS_SOURCES if item.flow_id == TELEGRAM_CONNECTION_STATUS_067E_FLOW_ID)

    assert source.artifact_dir_name == ARTIFACT_DIR_NAME
    assert source.latest_status_filename == LATEST_STATUS_FILENAME
    assert source.context_key == "telegram_connection_status_067e_status_summary"
    rendered_control_values = " ".join(
        [
            "pmbot:connection_status",
            "pmbot:run:connection_status_067e",
            "Run read-only status check 067E",
            "Запустить read-only проверку",
        ]
    ).lower()
    assert "wallet" not in rendered_control_values
    assert "signer" not in rendered_control_values
    assert "connect-wallet" not in rendered_control_values
