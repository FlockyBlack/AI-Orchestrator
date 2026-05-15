from __future__ import annotations

import importlib
import json
import socket
from pathlib import Path
from typing import Callable

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_mini_app_operator_panel import build_telegram_mini_app_panel_artifact_summary
from pm_bot.operator_runner.telegram_operator_control_bot import TelegramOperatorControlResponse

GENERATED_AT = "2026-05-11T00:00:00Z"
AUTHORIZED_USER_ID = "1001"
UNAUTHORIZED_USER_ID = "9999"
RAW_TOKEN = "123456:raw-telegram-token-value"
MINI_APP_URL = "https://example.invalid/pmbot-panel"

FORCED_FALSE_FLAGS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "would_submit_order",
)


class FakePollingRunner:
    def __init__(self, *, command: str = "/status", user_id: str = AUTHORIZED_USER_ID) -> None:
        self.command = command
        self.user_id = user_id
        self.started = False
        self.reply = None
        self.redacted_status = {}

    def run_polling(self, *, config, adapter, printer):  # type: ignore[no-untyped-def]
        self.started = True
        self.redacted_status = config.to_redacted_status()
        self.reply = adapter.handle_text(user_id=self.user_id, chat_id="chat-1", text=self.command)
        printer("fake polling invoked")


def _env(
    *,
    token: str = RAW_TOKEN,
    allowed_ids: str = AUTHORIZED_USER_ID,
    mini_app_url: str = "",
    artifact_dir: str = "",
) -> dict[str, str]:
    value = {
        runtime.TELEGRAM_BOT_TOKEN_ENV: token,
        runtime.ALLOWED_OPERATOR_IDS_ENV: allowed_ids,
    }
    if mini_app_url:
        value[runtime.TELEGRAM_MINI_APP_URL_ENV] = mini_app_url
    if artifact_dir:
        value[runtime.PMBOT_ARTIFACT_DIR_ENV] = artifact_dir
    return value


def _collecting_printer() -> tuple[list[str], Callable[[str], None]]:
    lines: list[str] = []
    return lines, lines.append


def _context() -> dict:
    return {
        "telegram_mini_app_operator_panel_summary": build_telegram_mini_app_panel_artifact_summary(
            latest_panel_html_path="telegram_mini_app_operator_panel_044.html",
            latest_panel_json_path="telegram_mini_app_operator_panel_044.json",
            panel_artifact_available=True,
            generated_at=GENERATED_AT,
        ),
        "tiny_live_canary_gonogo_gate_summary": {
            "status": "NO_GO_UNRESOLVED_BLOCKERS",
            "overall_decision": "NO_GO",
            "unresolved_blocker_count": 2,
            "resolved_blocker_count": 0,
            "allowed_for_live": False,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
            "order_submission_enabled": False,
        },
        "live_connector_blocker_matrix": {
            "unresolved_blocker_count": 2,
            "resolved_blocker_count": 0,
            "blockers": [
                {
                    "blocker_id": "B1",
                    "resolution_status": "unresolved",
                    "why_it_blocks_live_execution": "No live approval exists.",
                }
            ],
        },
    }


def _adapter(*, mini_app_url: str = "", artifact_dir: Path | None = None) -> runtime.TelegramOperatorRuntimeAdapter:
    config = runtime.TelegramRuntimeConfig(
        bot_token=RAW_TOKEN,
        allowed_operator_ids=(AUTHORIZED_USER_ID,),
        mini_app_url=mini_app_url,
        artifact_dir=artifact_dir,
        generated_at=GENERATED_AT,
    )
    return runtime.TelegramOperatorRuntimeAdapter(config=config, context=_context())


def test_missing_token_exits_safely_without_starting_polling() -> None:
    fake_runner = FakePollingRunner()
    lines, printer = _collecting_printer()

    status = runtime.main(
        env=_env(token="", allowed_ids=AUTHORIZED_USER_ID),
        printer=printer,
        polling_runner=fake_runner,
    )
    rendered = "\n".join(lines)

    assert status == 2
    assert fake_runner.started is False
    assert "Telegram token: missing" in rendered
    assert "Set Telegram bot token before starting long polling" in rendered
    assert RAW_TOKEN not in rendered


def test_token_presence_is_reported_only_as_configured_redacted() -> None:
    fake_runner = FakePollingRunner()
    lines, printer = _collecting_printer()

    status = runtime.main(env=_env(), printer=printer, polling_runner=fake_runner)
    rendered = "\n".join(lines)

    assert status == 0
    assert fake_runner.started is True
    assert "Telegram token: configured:redacted" in rendered
    assert "Allowed operator IDs: configured count:1" in rendered
    assert RAW_TOKEN not in rendered
    assert AUTHORIZED_USER_ID not in rendered
    assert fake_runner.redacted_status["telegram_token"] == "configured:redacted"


def test_missing_allowed_operator_ids_exits_safely() -> None:
    fake_runner = FakePollingRunner()
    lines, printer = _collecting_printer()

    status = runtime.main(env=_env(allowed_ids=""), printer=printer, polling_runner=fake_runner)
    rendered = "\n".join(lines)

    assert status == 2
    assert fake_runner.started is False
    assert "Allowed operator IDs: missing" in rendered
    assert "Set allowed Telegram operator user IDs before starting long polling" in rendered
    assert RAW_TOKEN not in rendered


def test_allowed_operator_ids_parse_correctly_without_raw_status_output() -> None:
    parsed = runtime.parse_allowed_operator_ids("1001, 1002;1001 0003")
    load_result = runtime.load_runtime_config(_env(allowed_ids="1001, 1002;1001 0003"))
    rendered = "\n".join(runtime.startup_status_lines(load_result))

    assert parsed == ("1001", "1002", "3")
    assert load_result.config.allowed_operator_ids == ("1001", "1002", "3")
    assert "Allowed operator IDs: configured count:3" in rendered
    assert "1002" not in rendered


def test_invalid_operator_ids_fail_safely_without_polling() -> None:
    fake_runner = FakePollingRunner()
    lines, printer = _collecting_printer()

    status = runtime.main(env=_env(allowed_ids="1001,not-a-user-id"), printer=printer, polling_runner=fake_runner)
    rendered = "\n".join(lines)

    assert status == 2
    assert fake_runner.started is False
    assert "Allowed operator IDs: invalid" in rendered
    assert "must be numeric IDs" in rendered
    assert "not-a-user-id" not in rendered
    assert RAW_TOKEN not in rendered


def test_runtime_does_not_start_polling_on_import() -> None:
    module = importlib.reload(runtime)

    assert module.TASK_ID == runtime.TASK_ID
    assert module.is_supported_runtime_command("/status") is True
    assert module.is_supported_runtime_command("/unknown") is False


def test_telegram_client_transport_is_injected_or_faked_without_network(monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    fake_runner = FakePollingRunner(command="/status")
    lines, printer = _collecting_printer()

    status = runtime.main(env=_env(), printer=printer, polling_runner=fake_runner)

    assert status == 0
    assert fake_runner.started is True
    assert "fake polling invoked" in lines
    assert fake_runner.reply.authorized is True
    assert "🤖 Статус бота" in fake_runner.reply.text
    assert "allowed_for_live=false" in fake_runner.reply.text


def test_command_routing_calls_existing_handlers() -> None:
    adapter = _adapter()

    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/risk")

    assert isinstance(reply.response, TelegramOperatorControlResponse)
    assert reply.command == "/risk"
    assert reply.authorized is True
    assert "⚙️ Лимиты" in reply.text
    assert "Лимиты показываются только как review/status." in reply.text
    assert reply.summary["review_only"] is True


def test_unauthorized_user_denied_safely() -> None:
    adapter = _adapter()

    reply = adapter.handle_text(user_id=UNAUTHORIZED_USER_ID, chat_id="chat-1", text="/status")
    rendered = json.dumps(reply.to_redacted_dict(), sort_keys=True)

    assert reply.authorized is False
    assert "Access denied" in reply.text
    assert UNAUTHORIZED_USER_ID not in rendered
    for flag in FORCED_FALSE_FLAGS:
        assert reply.summary[flag] is False


def test_authorized_status_works_through_runtime_adapter() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/status")

    assert reply.authorized is True
    assert "allowed_for_live=false" in reply.text
    assert "live trading disabled" in reply.text
    assert "order submission disabled" in reply.text
    assert reply.summary["network_used"] is False


def test_panel_with_optional_mini_app_url_uses_button_without_exposing_secrets() -> None:
    adapter = _adapter(mini_app_url=MINI_APP_URL)

    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    rendered = json.dumps(reply.to_redacted_dict(), sort_keys=True)

    assert reply.authorized is True
    assert "Telegram Mini App Operator Panel v1" in reply.text
    assert "Mini App настроен. Открой панель кнопкой ниже." in reply.text
    assert reply.panel_button_text == "Открыть PMBOT Mini App"
    assert reply.panel_button_url == MINI_APP_URL
    assert RAW_TOKEN not in rendered
    assert AUTHORIZED_USER_ID not in rendered


def test_panel_without_mini_app_url_returns_static_artifact_message() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")

    assert "Panel artifact доступен: true" in reply.text
    assert "Mini App URL пока не настроен" in reply.text
    assert reply.panel_button_url == ""


def test_pause_and_kill_remain_local_markers_only(tmp_path: Path) -> None:
    adapter = _adapter(artifact_dir=tmp_path)

    pause = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/pause")
    kill = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/kill")
    state_path = tmp_path / "telegram_operator_control_state_043.json"
    persisted = json.loads(state_path.read_text(encoding="utf-8"))

    assert "локальный маркер Telegram operator-control state" in pause.text
    assert "Отмена ордеров" in kill.text
    assert kill.state["operator_pause_requested"] is True
    assert kill.state["operator_kill_switch_requested"] is True
    assert persisted["operator_pause_requested"] is True
    assert persisted["operator_kill_switch_requested"] is True
    assert persisted["does_not_modify_trading_execution"] is True
    assert persisted["raw_operator_user_id_persisted"] is False
    assert AUTHORIZED_USER_ID not in json.dumps(persisted, sort_keys=True)


def test_no_live_flags_are_enabled_by_runtime_adapter() -> None:
    adapter = _adapter()

    for command in (
        "/start",
        "/help",
        "/status",
        "/btc",
        "/intent",
        "/risk",
        "/auth",
        "/order",
        "/gonogo",
        "/evidence",
        "/blockers",
        "/pause",
        "/kill",
        "/panel",
    ):
        reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text=command)
        redacted = reply.to_redacted_dict()
        for flag in FORCED_FALSE_FLAGS:
            assert reply.summary[flag] is False
            assert redacted[flag] is False
        assert reply.summary["live_approval"] is False
        assert reply.summary["execution_enabling"] is False
        assert redacted["network_used"] is False
        assert redacted["external_api_calls_performed"] is False
