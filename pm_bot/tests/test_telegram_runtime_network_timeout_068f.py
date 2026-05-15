from __future__ import annotations

import json
from typing import Any, Callable

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner import telegram_runtime_smoke as smoke
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    SAFE_ACTION_COMMANDS,
    SUPPORTED_COMMANDS,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
RAW_TOKEN = "123456:raw-telegram-token-value-068f"
AUTHORIZED_USER_ID = "1001"


def _env(**overrides: str) -> dict[str, str]:
    value = {
        runtime.TELEGRAM_BOT_TOKEN_ENV: RAW_TOKEN,
        runtime.ALLOWED_OPERATOR_IDS_ENV: AUTHORIZED_USER_ID,
    }
    value.update(overrides)
    return value


def _dependency(installed: bool = True) -> dict[str, object]:
    return {
        "dependency": "python-telegram-bot",
        "installed": installed,
        "status": "installed" if installed else "missing",
        "error_category": "" if installed else "not_importable",
    }


def test_default_timeout_settings_are_loaded_and_printed() -> None:
    load_result = runtime.load_runtime_config(_env(), generated_at=GENERATED_AT)
    network = load_result.config.network
    rendered = "\n".join(runtime.startup_status_lines(load_result))

    assert load_result.ok is True
    assert load_result.warnings == ()
    assert network.connect_timeout == 30.0
    assert network.read_timeout == 30.0
    assert network.write_timeout == 30.0
    assert network.pool_timeout == 30.0
    assert network.bootstrap_retries == 3
    assert "Telegram network: connect=30s read=30s write=30s pool=30s bootstrap_retries=3" in rendered
    assert RAW_TOKEN not in rendered


def test_env_overrides_are_parsed_for_timeouts_and_retries() -> None:
    load_result = runtime.load_runtime_config(
        _env(
            **{
                runtime.TELEGRAM_CONNECT_TIMEOUT_ENV: "45",
                runtime.TELEGRAM_READ_TIMEOUT_ENV: "46.5",
                runtime.TELEGRAM_WRITE_TIMEOUT_ENV: "47",
                runtime.TELEGRAM_POOL_TIMEOUT_ENV: "48",
                runtime.TELEGRAM_BOOTSTRAP_RETRIES_ENV: "5",
            }
        ),
        generated_at=GENERATED_AT,
    )
    network = load_result.config.network

    assert network.connect_timeout == 45.0
    assert network.read_timeout == 46.5
    assert network.write_timeout == 47.0
    assert network.pool_timeout == 48.0
    assert network.bootstrap_retries == 5
    assert load_result.warnings == ()


def test_invalid_env_values_fall_back_safely_with_clear_warnings() -> None:
    load_result = runtime.load_runtime_config(
        _env(
            **{
                runtime.TELEGRAM_CONNECT_TIMEOUT_ENV: "-1",
                runtime.TELEGRAM_READ_TIMEOUT_ENV: "not-a-number",
                runtime.TELEGRAM_WRITE_TIMEOUT_ENV: "nan",
                runtime.TELEGRAM_POOL_TIMEOUT_ENV: "0",
                runtime.TELEGRAM_BOOTSTRAP_RETRIES_ENV: "-2",
            }
        ),
        generated_at=GENERATED_AT,
    )
    rendered = "\n".join(runtime.startup_status_lines(load_result))
    network = load_result.config.network

    assert load_result.ok is True
    assert network.connect_timeout == 30.0
    assert network.read_timeout == 30.0
    assert network.write_timeout == 30.0
    assert network.pool_timeout == 30.0
    assert network.bootstrap_retries == 3
    assert "Telegram network config warnings:" in rendered
    assert "invalid_pmbot_telegram_connect_timeout_seconds_using_default" in rendered
    assert "invalid_pmbot_telegram_bootstrap_retries_using_default" in rendered
    assert RAW_TOKEN not in rendered


def test_token_remains_redacted_in_runtime_and_smoke_outputs() -> None:
    load_result = runtime.load_runtime_config(_env(), generated_at=GENERATED_AT)
    status_json = json.dumps(load_result.config.to_redacted_status(), sort_keys=True)
    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(),
        dependency_checker=lambda: _dependency(True),
        generated_at=GENERATED_AT,
    )
    rendered = "\n".join(smoke.render_smoke_report_lines(report))

    assert "configured:redacted" in status_json
    assert report["env_status"]["telegram_token"] == "configured:redacted"
    assert RAW_TOKEN not in status_json
    assert RAW_TOKEN not in json.dumps(report, sort_keys=True)
    assert RAW_TOKEN not in rendered


def test_runtime_smoke_includes_timeout_retry_settings_without_network_by_default() -> None:
    report = smoke.build_telegram_runtime_smoke_report(
        env=_env(
            **{
                runtime.TELEGRAM_CONNECT_TIMEOUT_ENV: "41",
                runtime.TELEGRAM_BOOTSTRAP_RETRIES_ENV: "4",
            }
        ),
        network_check=False,
        dependency_checker=lambda: _dependency(True),
        telegram_get_me_checker=lambda _token: (_ for _ in ()).throw(
            AssertionError("getMe should not be called by default")
        ),
        generated_at=GENERATED_AT,
    )
    rendered = "\n".join(smoke.render_smoke_report_lines(report))

    assert report["no_network_by_default"] is True
    assert report["network_check"]["requested"] is False
    assert report["telegram_network_settings"]["connect_timeout_seconds"] == 41.0
    assert report["telegram_network_settings"]["bootstrap_retries"] == 4
    assert "Telegram network: connect=41s read=30s write=30s pool=30s bootstrap_retries=4" in rendered


def test_application_builder_request_config_receives_timeout_values() -> None:
    requests: list[dict[str, float]] = []

    class FakeBuilder:
        def __init__(self) -> None:
            self.request_value: dict[str, float] | None = None
            self.get_updates_request_value: dict[str, float] | None = None

        def request(self, value: dict[str, float]) -> "FakeBuilder":
            self.request_value = value
            return self

        def get_updates_request(self, value: dict[str, float]) -> "FakeBuilder":
            self.get_updates_request_value = value
            return self

    def request_factory(**kwargs: float) -> dict[str, float]:
        requests.append(dict(kwargs))
        return dict(kwargs)

    network = runtime.TelegramRuntimeNetworkConfig(
        connect_timeout=11,
        read_timeout=12,
        write_timeout=13,
        pool_timeout=14,
        bootstrap_retries=6,
    )
    builder = FakeBuilder()

    configured = runtime.configure_telegram_application_builder_network(
        builder,
        network,
        request_factory=request_factory,
    )
    kwargs = runtime.build_telegram_run_polling_kwargs(
        _fake_run_polling_with_network_kwargs,
        allowed_updates=("message",),
        network=network,
    )

    assert configured is builder
    assert requests == [
        {"connect_timeout": 11, "read_timeout": 12, "write_timeout": 13, "pool_timeout": 14},
        {"connect_timeout": 11, "read_timeout": 12, "write_timeout": 13, "pool_timeout": 14},
    ]
    assert builder.request_value == requests[0]
    assert builder.get_updates_request_value == requests[1]
    assert kwargs["bootstrap_retries"] == 6
    assert kwargs["connect_timeout"] == 11
    assert kwargs["read_timeout"] == 12
    assert kwargs["write_timeout"] == 13
    assert kwargs["pool_timeout"] == 14


def test_timeout_diagnostic_text_is_clear_and_redacted() -> None:
    class TimedOut(Exception):
        pass

    class TimeoutPollingRunner:
        def run_polling(self, *, config, adapter, printer):  # type: ignore[no-untyped-def]
            raise TimedOut("connect timed out")

    lines: list[str] = []
    config = runtime.TelegramRuntimeConfig(
        bot_token=RAW_TOKEN,
        allowed_operator_ids=(AUTHORIZED_USER_ID,),
        generated_at=GENERATED_AT,
    )

    status = runtime.run_runtime(config=config, polling_runner=TimeoutPollingRunner(), printer=lines.append)
    rendered = "\n".join(lines)

    assert status == 2
    assert runtime.TELEGRAM_BOOTSTRAP_TIMEOUT_DIAGNOSTIC in rendered
    assert "VPN/firewall/proxy/api.telegram.org" in rendered
    assert "PMBOT_TELEGRAM_* timeout env vars" in rendered
    assert RAW_TOKEN not in rendered


def test_no_live_sign_wallet_or_order_controls_are_added() -> None:
    records = [
        *SUPPORTED_COMMANDS,
        *SAFE_ACTION_COMMANDS,
        *CALLBACK_COMMAND_MAP.keys(),
        *CALLBACK_COMMAND_MAP.values(),
        *(command for command, _description in runtime.telegram_command_menu_items()),
    ]
    rendered = "\n".join(records).lower()
    flags = runtime.runtime_safety_flags()

    for forbidden in (
        "approve-live",
        "send-order",
        "submit-order",
        "cancel-order",
        "connect-wallet",
        "unlock-wallet",
        "run_signer",
        "pmbot:run:signer",
    ):
        assert forbidden not in rendered
    assert flags["live_execution_performed"] is False
    assert flags["real_order_submitted"] is False
    assert flags["wallet_signing_performed"] is False
    assert flags["authenticated_endpoint_call_performed"] is False


def _fake_run_polling_with_network_kwargs(
    *,
    allowed_updates: Any,
    bootstrap_retries: int,
    connect_timeout: float,
    read_timeout: float,
    write_timeout: float,
    pool_timeout: float,
) -> None:
    del allowed_updates, bootstrap_retries, connect_timeout, read_timeout, write_timeout, pool_timeout
