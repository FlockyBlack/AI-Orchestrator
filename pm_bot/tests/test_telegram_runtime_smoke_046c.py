from __future__ import annotations

import io
import json
import socket
from pathlib import Path
from urllib.error import HTTPError

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner import telegram_runtime_smoke as smoke

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
)


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


def test_no_network_smoke_reports_token_configured_redacted_only() -> None:
    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(),
        dependency_checker=lambda: _dependency(True),
        generated_at=GENERATED_AT,
    )
    rendered = "\n".join(smoke.render_smoke_report_lines(report))

    assert report["env_status"]["telegram_token"] == "configured:redacted"
    assert "Telegram token: configured:redacted" in rendered
    assert RAW_TOKEN not in json.dumps(report, sort_keys=True)
    assert RAW_TOKEN not in rendered
    assert report["network_check"]["error_category"] == "not_requested"


def test_no_network_smoke_reports_missing_token_safely() -> None:
    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(token=""),
        dependency_checker=lambda: _dependency(True),
        generated_at=GENERATED_AT,
    )
    rendered = "\n".join(smoke.render_smoke_report_lines(report))

    assert report["env_status"]["telegram_token"] == "missing"
    assert "missing_token" in report["config_errors"]
    assert "Telegram token: missing" in rendered
    assert RAW_TOKEN not in rendered


def test_operator_ids_are_reported_by_count_only() -> None:
    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(allowed_ids=f"{AUTHORIZED_USER_ID}, {SECOND_OPERATOR_ID}"),
        dependency_checker=lambda: _dependency(True),
        generated_at=GENERATED_AT,
    )
    rendered = json.dumps(report, sort_keys=True)

    assert report["env_status"]["allowed_operator_id_count"] == 2
    assert report["env_status"]["allowed_operator_ids_redacted"] is True
    assert AUTHORIZED_USER_ID not in rendered
    assert SECOND_OPERATOR_ID not in rendered


def test_dependency_installed_and_missing_are_handled_safely() -> None:
    installed = smoke.build_telegram_runtime_smoke_report(
        env=_env(),
        dependency_checker=lambda: _dependency(True),
        generated_at=GENERATED_AT,
    )
    missing = smoke.build_telegram_runtime_smoke_report(
        env=_env(),
        dependency_checker=lambda: _dependency(False),
        generated_at=GENERATED_AT,
    )

    assert installed["dependency_check"]["status"] == "installed"
    assert installed["ready_to_start_runtime"] is True
    assert missing["dependency_check"]["status"] == "missing"
    assert missing["ready_to_start_runtime"] is False
    assert RAW_TOKEN not in json.dumps(missing, sort_keys=True)


def test_runtime_module_import_check_works() -> None:
    result = smoke.check_runtime_module_import()

    assert result["ok"] is True
    assert result["module"] == "pm_bot.operator_runner.telegram_operator_runtime"
    assert result["runtime_command"] == "python -m pm_bot.operator_runner.telegram_operator_runtime"


def test_mini_app_url_configured_and_missing_are_represented_safely() -> None:
    configured = smoke.build_telegram_runtime_smoke_report(
        env=_env(mini_app_url=MINI_APP_URL),
        dependency_checker=lambda: _dependency(True),
        generated_at=GENERATED_AT,
    )
    missing = smoke.build_telegram_runtime_smoke_report(
        env=_env(),
        dependency_checker=lambda: _dependency(True),
        generated_at=GENERATED_AT,
    )

    assert configured["env_status"]["mini_app_url_status"] == "configured"
    assert configured["env_status"]["mini_app_url_redacted"] is True
    assert missing["env_status"]["mini_app_url_status"] == "missing"
    assert MINI_APP_URL not in json.dumps(configured, sort_keys=True)


def test_no_network_smoke_does_not_call_external_network(monkeypatch) -> None:
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

    assert report["no_network_by_default"] is True
    assert report["network_check"]["requested"] is False


def test_optional_network_check_path_can_be_faked() -> None:
    def fake_get_me(token: str) -> dict[str, object]:
        assert token == RAW_TOKEN
        return {
            "requested": True,
            "telegram_api_reachable": True,
            "get_me_ok": True,
            "bot_username": "fuzzer_test_bot",
            "error_category": "",
        }

    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(),
        network_check=True,
        dependency_checker=lambda: _dependency(True),
        telegram_get_me_checker=fake_get_me,
        generated_at=GENERATED_AT,
    )

    assert report["network_check"]["requested"] is True
    assert report["network_check"]["telegram_api_reachable"] is True
    assert report["network_check"]["get_me_ok"] is True
    assert report["network_check"]["bot_username"] == "fuzzer_test_bot"
    assert RAW_TOKEN not in json.dumps(report, sort_keys=True)


def test_401_unauthorized_is_categorized_safely_without_printing_token() -> None:
    def unauthorized(_request, timeout):  # type: ignore[no-untyped-def]
        raise HTTPError(
            f"https://api.telegram.org/bot{RAW_TOKEN}/getMe",
            401,
            "Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b""),
        )

    result = smoke.telegram_get_me(RAW_TOKEN, opener=unauthorized)
    rendered = json.dumps(result, sort_keys=True)

    assert result["telegram_api_reachable"] is True
    assert result["get_me_ok"] is False
    assert result["error_category"] == "unauthorized"
    assert RAW_TOKEN not in rendered


def test_timeout_is_categorized_safely() -> None:
    def timeout(_request, timeout):  # type: ignore[no-untyped-def]
        raise TimeoutError("timed out")

    result = smoke.telegram_get_me(RAW_TOKEN, opener=timeout)
    rendered = json.dumps(result, sort_keys=True)

    assert result["telegram_api_reachable"] is False
    assert result["get_me_ok"] is False
    assert result["error_category"] == "timeout"
    assert RAW_TOKEN not in rendered


def test_docs_mention_ctrl_c_stop_and_no_live_trading() -> None:
    doc = Path("docs/ORCH_PMBOT_TRADING_MVP_046C_TELEGRAM_RUNTIME_SMOKE_AND_OPERATOR_HANDOFF.md").read_text(
        encoding="utf-8"
    )

    assert "Ctrl+C" in doc
    assert "no trading is enabled" in doc.lower()
    assert "python -m pm_bot.operator_runner.telegram_runtime_smoke" in doc
    assert "python -m pm_bot.operator_runner.telegram_operator_runtime" in doc


def test_live_flags_remain_false_in_smoke_report() -> None:
    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(),
        dependency_checker=lambda: _dependency(True),
        generated_at=GENERATED_AT,
    )
    flags = report["review_only_safety_flags_expected_false"]

    for flag in FORCED_FALSE_FLAGS:
        assert flags[flag] is False
    assert report["review_only_safety_flags_ok"] is True
    assert report["review_only_blocker_expectations"]["resolved_blocker_count"] == 0
    assert report["live_trading_enabled"] is False
    assert report["real_orders_submitted"] is False
    assert report["wallet_integration_added"] is False
    assert report["authenticated_polymarket_endpoint_calls_added"] is False
