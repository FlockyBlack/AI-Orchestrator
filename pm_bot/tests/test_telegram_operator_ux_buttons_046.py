from __future__ import annotations

import asyncio
import json
import socket
from pathlib import Path
from typing import Any

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_mini_app_operator_panel import build_telegram_mini_app_panel_artifact_summary
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    FORBIDDEN_BUTTON_LABEL_TERMS,
)

GENERATED_AT = "2026-05-13T00:00:00Z"
AUTHORIZED_USER_ID = "1001"
UNAUTHORIZED_USER_ID = "9999"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_INIT_DATA = "query_id=abc&user={raw-operator}&auth_date=1&hash=raw-init-data-secret"
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

HOME_LABEL_ROWS = (
    ("Status", "Go/No-Go"),
    ("Risk", "Blockers"),
    ("Evidence", "Panel"),
    ("Pause", "Kill"),
    ("Language",),
)


class FakeMenuBot:
    def __init__(self) -> None:
        self.commands: tuple[Any, ...] = ()

    async def set_my_commands(self, commands: tuple[Any, ...]) -> None:
        self.commands = commands


def _context() -> dict[str, Any]:
    return {
        "raw_telegram_bot_token": RAW_TOKEN,
        "telegram_init_data": RAW_INIT_DATA,
        "telegram_mini_app_operator_panel_summary": build_telegram_mini_app_panel_artifact_summary(
            latest_panel_html_path="telegram_mini_app_operator_panel_044.html",
            latest_panel_json_path="telegram_mini_app_operator_panel_044.json",
            panel_artifact_available=True,
            generated_at=GENERATED_AT,
        ),
        "tiny_live_canary_gonogo_gate_summary": {
            "status": "NO_GO_UNRESOLVED_BLOCKERS",
            "overall_decision": "NO_GO",
            "top_no_go_reasons": ["live approval missing", "order submission disabled"],
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
        "risk_control_plane_summary": {
            "max_order_notional_usd": 1,
            "max_daily_loss_usd": 5,
            "max_total_exposure_usd": 25,
            "max_market_exposure_usd": 2,
            "max_active_markets": 3,
            "max_trades_per_day": 2,
            "allowed_for_live": False,
        },
        "live_credentials_auth_boundary_summary": {
            "live_credentials_configured": False,
            "missing_credentials_count": 3,
            "authenticated_endpoints_enabled": False,
            "signing_enabled": False,
            "wallet_signing_enabled": False,
            "order_submission_enabled": False,
            "allowed_for_live": False,
        },
        "live_order_submission_boundary_summary": {
            "status": "dry_run_submission_boundary_review_ready",
            "would_submit_order": False,
            "order_submission_enabled": False,
            "authenticated_endpoint_enabled": False,
            "signing_enabled": False,
            "wallet_enabled": False,
            "allowed_for_live": False,
        },
        "readiness_evidence_bundle_summary": {
            "readiness_evidence_bundle_status": "readiness_evidence_bundle_review_ready",
            "evidence_item_count": 22,
            "missing_required_evidence_count": 0,
            "missing_required_evidence": [],
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
        },
    }


def _adapter(
    *,
    mini_app_url: str = "",
    artifact_dir: Path | None = None,
) -> runtime.TelegramOperatorRuntimeAdapter:
    return runtime.TelegramOperatorRuntimeAdapter(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            mini_app_url=mini_app_url,
            artifact_dir=artifact_dir,
            generated_at=GENERATED_AT,
        ),
        context=_context(),
    )


def _label_rows(reply: runtime.TelegramRuntimeReply) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(button.label for button in row) for row in reply.keyboard.rows)


def _button_labels(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def test_start_prompts_for_language_when_language_is_not_selected() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")

    assert "Choose operator language" in reply.text
    assert _label_rows(reply) == (("🇷🇺 Русский", "🇬🇧 English"),)
    assert reply.keyboard.to_dict()["safe_button_labels"] is True


def test_help_includes_command_overview_and_safe_controls() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/help")

    assert "PMBOT Operator Control commands" in reply.text
    assert "/status" in reply.text
    assert "/panel" in reply.text
    assert "/gonogo" in reply.text
    assert "Safe controls: Status, Go/No-Go, Risk, Blockers, Evidence, Panel, Pause, Kill, Language." in reply.text
    assert _label_rows(reply) == HOME_LABEL_ROWS


def test_callbacks_route_to_same_safe_command_handlers() -> None:
    adapter = _adapter()

    for callback_data, command in CALLBACK_COMMAND_MAP.items():
        reply = adapter.handle_callback(
            user_id=AUTHORIZED_USER_ID,
            chat_id="chat-1",
            callback_data=callback_data,
        )

        assert reply.command == command
        assert reply.authorized is True
        assert reply.summary["review_only"] is True
        assert reply.summary["execution_enabling"] is False


def test_unauthorized_callback_is_denied_safely_without_raw_identifier() -> None:
    reply = _adapter().handle_callback(
        user_id=UNAUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:status",
    )
    rendered = json.dumps(reply.to_redacted_dict(), sort_keys=True)

    assert reply.authorized is False
    assert "Access denied" in reply.text
    assert UNAUTHORIZED_USER_ID not in rendered
    assert RAW_TOKEN not in rendered
    for flag in FORCED_FALSE_FLAGS:
        assert reply.summary[flag] is False


def test_panel_includes_mini_app_url_button_when_configured_without_exposing_url_in_redacted_payload() -> None:
    reply = _adapter(mini_app_url=MINI_APP_URL).handle_text(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        text="/panel",
    )
    first_button = reply.keyboard.rows[0][0]
    redacted = json.dumps(reply.to_redacted_dict(), sort_keys=True)

    assert "Telegram Mini App Operator Panel v1" in reply.text
    assert "Mini App URL: configured." in reply.text
    assert reply.panel_button_text == runtime.PANEL_BUTTON_TEXT
    assert reply.panel_button_url == MINI_APP_URL
    assert first_button.label == "Открыть PMBOT"
    assert first_button.web_app_url == MINI_APP_URL
    assert MINI_APP_URL not in redacted


def test_panel_output_does_not_expose_token_init_data_or_raw_operator_ids() -> None:
    reply = _adapter(mini_app_url=MINI_APP_URL).handle_text(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        text="/panel",
    )
    rendered = json.dumps(reply.to_redacted_dict(), sort_keys=True)

    assert RAW_TOKEN not in reply.text
    assert RAW_INIT_DATA not in reply.text
    assert AUTHORIZED_USER_ID not in reply.text
    assert RAW_TOKEN not in rendered
    assert RAW_INIT_DATA not in rendered
    assert AUTHORIZED_USER_ID not in rendered
    assert "raw_telegram_bot_token_exposed: false" in reply.text
    assert "raw_telegram_init_data_exposed: false" in reply.text


def test_panel_fallback_when_mini_app_url_is_missing() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")

    assert "Mini App URL не настроен" in reply.text
    assert "Panel artifact available: true" in reply.text
    assert reply.panel_button_url == ""
    assert _label_rows(reply) == (("Status", "Go/No-Go"), ("Blockers",), ("Language",))


def test_no_button_label_includes_forbidden_execution_terms() -> None:
    replies = [
        _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start"),
        _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel"),
        _adapter(mini_app_url=MINI_APP_URL).handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel"),
    ]

    for reply in replies:
        for label in _button_labels(reply):
            upper_label = label.upper()
            assert not any(term in upper_label for term in FORBIDDEN_BUTTON_LABEL_TERMS)


def test_pause_and_kill_buttons_remain_local_markers_only(tmp_path: Path) -> None:
    adapter = _adapter(artifact_dir=tmp_path)

    pause = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:pause")
    kill = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:kill")
    persisted = json.loads((tmp_path / "telegram_operator_control_state_043.json").read_text(encoding="utf-8"))

    assert "local Telegram operator-control state only" in pause.text
    assert "No order cancellation" in kill.text
    assert persisted["operator_pause_requested"] is True
    assert persisted["operator_kill_switch_requested"] is True
    assert persisted["does_not_modify_trading_execution"] is True
    assert persisted["order_submission_enabled"] is False
    assert persisted["live_execution_approved"] is False
    assert AUTHORIZED_USER_ID not in json.dumps(persisted, sort_keys=True)


def test_runtime_can_set_command_menu_through_fake_telegram_client() -> None:
    fake_bot = FakeMenuBot()

    configured = asyncio.run(runtime.configure_telegram_command_menu(fake_bot))

    assert configured is True
    assert fake_bot.commands == runtime.telegram_command_menu_items()
    assert fake_bot.commands[0] == ("start", "Open operator home")
    assert fake_bot.commands[-1] == ("help", "Help")


def test_no_external_network_calls_for_buttons_callbacks_and_command_menu(monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    adapter = _adapter(mini_app_url=MINI_APP_URL)

    assert adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start").authorized is True
    assert adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:blockers").authorized is True


def test_live_flags_remain_false_and_resolved_blockers_remain_zero_for_all_button_callbacks() -> None:
    adapter = _adapter(mini_app_url=MINI_APP_URL)

    for callback_data in CALLBACK_COMMAND_MAP:
        reply = adapter.handle_callback(
            user_id=AUTHORIZED_USER_ID,
            chat_id="chat-1",
            callback_data=callback_data,
        )
        redacted = reply.to_redacted_dict()
        blockers = dict(reply.summary.get("blocker_summary", {}))

        assert blockers["resolved_blocker_count"] == 0
        assert redacted["resolved_blocker_count"] == 0
        for flag in FORCED_FALSE_FLAGS:
            assert reply.summary[flag] is False
            assert redacted[flag] is False
        assert reply.summary["live_approval"] is False
        assert reply.summary["execution_enabling"] is False
        assert redacted["network_used"] is False
        assert redacted["external_api_calls_performed"] is False
