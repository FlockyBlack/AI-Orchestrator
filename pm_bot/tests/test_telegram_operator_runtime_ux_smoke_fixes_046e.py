from __future__ import annotations

import io
import json
import socket
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner import telegram_runtime_smoke as smoke
from pm_bot.operator_runner.telegram_mini_app_operator_panel import build_telegram_mini_app_panel_artifact_summary
from pm_bot.operator_runner.telegram_operator_control_bot import FORBIDDEN_BUTTON_LABEL_TERMS

GENERATED_AT = "2026-05-13T00:00:00Z"
RAW_TOKEN = "123456:raw-telegram-token-value"
AUTHORIZED_USER_ID = "1001"
SECOND_OPERATOR_ID = "1002"
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


class FakePollingRunnerError:
    def __init__(self, exc: BaseException) -> None:
        self.exc = exc

    def run_polling(self, *, config, adapter, printer) -> None:  # type: ignore[no-untyped-def]
        raise self.exc


def _env(
    *,
    token: str = RAW_TOKEN,
    allowed_ids: str = AUTHORIZED_USER_ID,
    mini_app_url: str = "",
) -> dict[str, str]:
    value = {
        runtime.TELEGRAM_BOT_TOKEN_ENV: token,
        runtime.ALLOWED_OPERATOR_IDS_ENV: allowed_ids,
    }
    if mini_app_url:
        value[runtime.TELEGRAM_MINI_APP_URL_ENV] = mini_app_url
    return value


def _dependency(installed: bool = True) -> dict[str, object]:
    return {
        "dependency": "python-telegram-bot",
        "installed": installed,
        "status": "installed" if installed else "missing",
        "error_category": "" if installed else "not_importable",
    }


def _context() -> dict[str, Any]:
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


def _collecting_printer() -> tuple[list[str], Callable[[str], None]]:
    lines: list[str] = []
    return lines, lines.append


def _button_labels(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def test_no_network_smoke_remains_no_network_and_has_sections(monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    def blocked_get_me(token: str):  # type: ignore[no-untyped-def]
        raise AssertionError("getMe should not be called without --network-check")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(),
        network_check=False,
        dependency_checker=lambda: _dependency(True),
        telegram_get_me_checker=blocked_get_me,
        generated_at=GENERATED_AT,
    )
    rendered = "\n".join(smoke.render_smoke_report_lines(report))

    assert report["network_check"]["requested"] is False
    assert report["network_check"]["error_category"] == smoke.NETWORK_NOT_REQUESTED
    for section in ("Environment", "Dependency", "Runtime module", "Mini App", "Safety", "Next run command"):
        assert section in rendered


def test_smoke_redacts_token_and_reports_operator_ids_by_count_only() -> None:
    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(allowed_ids=f"{AUTHORIZED_USER_ID}, {SECOND_OPERATOR_ID}"),
        dependency_checker=lambda: _dependency(True),
        generated_at=GENERATED_AT,
    )
    rendered = "\n".join(smoke.render_smoke_report_lines(report))
    payload = json.dumps(report, sort_keys=True)

    assert "Telegram token: configured:redacted" in rendered
    assert "Allowed operator IDs: configured count:2" in rendered
    assert report["env_status"]["allowed_operator_id_count"] == 2
    assert RAW_TOKEN not in rendered
    assert RAW_TOKEN not in payload
    assert AUTHORIZED_USER_ID not in rendered
    assert SECOND_OPERATOR_ID not in payload


def test_network_check_401_timeout_unreachable_and_conflict_are_safe() -> None:
    def unauthorized(_request, timeout):  # type: ignore[no-untyped-def]
        raise HTTPError(
            f"https://api.telegram.org/bot{RAW_TOKEN}/getMe",
            401,
            "Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b""),
        )

    def timeout(_request, timeout):  # type: ignore[no-untyped-def]
        raise TimeoutError("timed out")

    def unreachable(_request, timeout):  # type: ignore[no-untyped-def]
        raise URLError(OSError("DNS name resolution failed"))

    invalid = smoke.telegram_get_me(RAW_TOKEN, opener=unauthorized)
    timed_out = smoke.telegram_get_me(RAW_TOKEN, opener=timeout)
    blocked = smoke.telegram_get_me(RAW_TOKEN, opener=unreachable)
    conflict = smoke.sanitize_network_check_result(
        {
            "telegram_api_reachable": True,
            "get_me_ok": False,
            "bot_username": RAW_TOKEN,
            "error_category": "conflict",
        },
        bot_token=RAW_TOKEN,
    )
    rendered = json.dumps([invalid, timed_out, blocked, conflict], sort_keys=True)

    assert invalid["error_category"] == smoke.NETWORK_INVALID_OR_REVOKED_TOKEN
    assert timed_out["error_category"] == smoke.NETWORK_TELEGRAM_API_TIMEOUT
    assert blocked["error_category"] == smoke.NETWORK_UNREACHABLE
    assert conflict["error_category"] == smoke.NETWORK_POLLING_CONFLICT
    assert RAW_TOKEN not in rendered


def test_dependency_missing_message_is_actionable() -> None:
    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(),
        dependency_checker=lambda: _dependency(False),
        generated_at=GENERATED_AT,
    )
    rendered = "\n".join(smoke.render_smoke_report_lines(report))

    assert "python-telegram-bot: missing" in rendered
    assert "Install python-telegram-bot" in rendered
    assert report["ready_to_start_runtime"] is False
    assert RAW_TOKEN not in rendered


def test_runtime_expected_startup_errors_do_not_expose_token() -> None:
    lines, printer = _collecting_printer()
    status = runtime.run_runtime(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        polling_runner=FakePollingRunnerError(RuntimeError(f"Unauthorized token {RAW_TOKEN}")),
        printer=printer,
    )
    rendered = "\n".join(lines)

    assert status == 2
    assert "invalid or revoked bot token" in rendered
    assert "Token was not printed" in rendered
    assert "Traceback" not in rendered
    assert RAW_TOKEN not in rendered


def test_start_wording_is_concise_and_includes_keyboard() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")

    assert reply.text.splitlines()[:4] == [
        "PMBOT Operator Control",
        "Review-only",
        "Live trading disabled",
        "Use buttons below",
    ]
    assert reply.keyboard.has_buttons is True
    assert "No orders, wallets, signing, or authenticated Polymarket calls." in reply.text


def test_panel_missing_mini_app_url_fallback_is_clear() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")

    assert "Mini App URL is not configured yet" in reply.text
    assert "Use the fallback buttons below" in reply.text
    assert reply.panel_button_url == ""
    assert tuple(tuple(button.label for button in row) for row in reply.keyboard.rows) == (
        ("Status", "Go/No-Go"),
        ("Blockers",),
    )


def test_panel_configured_mini_app_url_includes_safe_button_link() -> None:
    reply = _adapter(mini_app_url=MINI_APP_URL).handle_text(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        text="/panel",
    )
    first_button = reply.keyboard.rows[0][0]
    redacted = json.dumps(reply.to_redacted_dict(), sort_keys=True)

    assert reply.panel_button_text == runtime.PANEL_BUTTON_TEXT
    assert reply.panel_button_url == MINI_APP_URL
    assert first_button.label == runtime.PANEL_BUTTON_TEXT
    assert first_button.web_app_url == MINI_APP_URL
    assert "review-only" in reply.text
    assert RAW_TOKEN not in redacted
    assert MINI_APP_URL not in redacted


def test_no_forbidden_execution_button_labels() -> None:
    replies = [
        _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start"),
        _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel"),
        _adapter(mini_app_url=MINI_APP_URL).handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel"),
    ]

    for reply in replies:
        for label in _button_labels(reply):
            upper = label.upper()
            assert not any(term in upper for term in FORBIDDEN_BUTTON_LABEL_TERMS)


def test_pause_kill_local_markers_and_live_flags_remain_false(tmp_path: Path) -> None:
    adapter = _adapter(artifact_dir=tmp_path)

    pause = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/pause")
    kill = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/kill")
    persisted = json.loads((tmp_path / "telegram_operator_control_state_043.json").read_text(encoding="utf-8"))

    assert "local Telegram operator-control state only" in pause.text
    assert "No order cancellation" in kill.text
    assert persisted["operator_pause_requested"] is True
    assert persisted["operator_kill_switch_requested"] is True
    assert persisted["does_not_modify_trading_execution"] is True
    for flag in FORCED_FALSE_FLAGS:
        assert kill.summary[flag] is False
        assert kill.to_redacted_dict()[flag] is False
    assert kill.to_redacted_dict()["resolved_blocker_count"] == 0


def test_no_external_network_calls_in_runtime_ux_tests(monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    adapter = _adapter(mini_app_url=MINI_APP_URL)
    assert adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start").authorized is True
    assert adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel").authorized is True
