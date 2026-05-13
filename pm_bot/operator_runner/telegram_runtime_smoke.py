from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import socket
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    HOME_BUTTON_ROWS,
    PANEL_FALLBACK_BUTTON_ROWS,
    SUPPORTED_COMMANDS,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

TASK_ID = "ORCH-PMBOT-TRADING-MVP-046E-TELEGRAM-OPERATOR-RUNTIME-UX-SMOKE-FIXES"
CONTRACT_VERSION = "pmbot_telegram_runtime_smoke_046e.v1"
RUNTIME_MODULE = "pm_bot.operator_runner.telegram_operator_runtime"
RUNTIME_COMMAND = "python -m pm_bot.operator_runner.telegram_operator_runtime"
SMOKE_COMMAND = "python -m pm_bot.operator_runner.telegram_runtime_smoke"
HANDOFF_CHECKLIST_PATH = (
    "docs/ORCH_PMBOT_TRADING_MVP_046E_TELEGRAM_OPERATOR_RUNTIME_UX_SMOKE_FIXES.md"
)
TELEGRAM_GET_ME_URL_REDACTED = "https://api.telegram.org/bot<redacted>/getMe"

NETWORK_NOT_REQUESTED = "NOT_REQUESTED"
NETWORK_MISSING_TOKEN = "MISSING_TOKEN"
NETWORK_INVALID_OR_REVOKED_TOKEN = "INVALID_OR_REVOKED_TOKEN"
NETWORK_TELEGRAM_API_TIMEOUT = "TELEGRAM_API_TIMEOUT"
NETWORK_UNREACHABLE = "NETWORK_UNREACHABLE"
NETWORK_POLLING_CONFLICT = "POLLING_CONFLICT"
NETWORK_RATE_LIMITED = "TELEGRAM_RATE_LIMITED"
NETWORK_TELEGRAM_SERVER_ERROR = "TELEGRAM_SERVER_ERROR"
NETWORK_TELEGRAM_HTTP_ERROR = "TELEGRAM_HTTP_ERROR"
NETWORK_TELEGRAM_API_ERROR = "TELEGRAM_API_ERROR"

EXPECTED_FALSE_FLAGS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "would_submit_order",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
    "authenticated_endpoint_call_performed",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_performed",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "cryptographic_signing_performed",
    "real_order_placement_added",
    "real_order_placement_performed",
    "real_order_submitted",
    "live_execution_allowed",
    "live_execution_performed",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "browser_automation_added",
)


def build_telegram_runtime_smoke_report(
    *,
    env: Mapping[str, str] | None = None,
    network_check: bool = False,
    dependency_checker: Callable[[], Mapping[str, Any]] | None = None,
    runtime_import_checker: Callable[[], Mapping[str, Any]] | None = None,
    telegram_get_me_checker: Callable[[str], Mapping[str, Any]] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    source = os.environ if env is None else env
    load_result = runtime.load_runtime_config(source, generated_at=generated_at)
    dependency = _normalize_dependency_check(
        dependency_checker() if dependency_checker is not None else check_python_telegram_bot_dependency()
    )
    runtime_import = _normalize_runtime_import_check(
        runtime_import_checker() if runtime_import_checker is not None else check_runtime_module_import()
    )
    safety_flags = review_only_safety_flags_expected_false()
    network_result = (
        run_explicit_network_check(
            load_result.config.bot_token,
            telegram_get_me_checker=telegram_get_me_checker,
        )
        if network_check
        else {
            "requested": False,
            "telegram_api_reachable": None,
            "get_me_ok": None,
            "bot_username": "",
            "error_category": NETWORK_NOT_REQUESTED,
            "api_url": TELEGRAM_GET_ME_URL_REDACTED,
        }
    )

    config_errors = tuple(clean_text(item) for item in load_result.errors if clean_text(item))
    report = {
        "contract_version": CONTRACT_VERSION,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "smoke_command": SMOKE_COMMAND,
        "runtime_command": RUNTIME_COMMAND,
        "handoff_checklist_path": HANDOFF_CHECKLIST_PATH,
        "network_check_requested": network_check,
        "no_network_by_default": not network_check,
        "env_status": {
            "telegram_bot_token_env": runtime.TELEGRAM_BOT_TOKEN_ENV,
            "telegram_token": load_result.config.token_status,
            "allowed_operator_ids_env": runtime.ALLOWED_OPERATOR_IDS_ENV,
            "allowed_operator_ids_configured": bool(load_result.config.allowed_operator_ids),
            "allowed_operator_id_count": load_result.config.allowed_operator_count,
            "allowed_operator_ids_redacted": True,
            "mini_app_url_env": runtime.TELEGRAM_MINI_APP_URL_ENV,
            "mini_app_url_status": mini_app_url_status(load_result.config.mini_app_url),
            "mini_app_url_redacted": bool(load_result.config.mini_app_url),
            "artifact_dir_env": runtime.PMBOT_ARTIFACT_DIR_ENV,
            "artifact_dir_configured": load_result.config.artifact_dir is not None,
        },
        "config_errors": list(config_errors),
        "dependency_check": dependency,
        "runtime_module_import": runtime_import,
        "safe_commands": list(SUPPORTED_COMMANDS),
        "expected_telegram_command_menu": [
            {"command": f"/{command}", "description": description}
            for command, description in runtime.telegram_command_menu_items()
        ],
        "expected_telegram_buttons": {
            "home_rows": _button_rows(HOME_BUTTON_ROWS),
            "panel_fallback_rows": _button_rows(PANEL_FALLBACK_BUTTON_ROWS),
            "mini_app_launch_button": runtime.PANEL_BUTTON_TEXT,
        },
        "review_only_safety_flags_expected_false": safety_flags,
        "review_only_safety_flags_ok": all(value is False for value in safety_flags.values()),
        "review_only_blocker_expectations": {"resolved_blocker_count": 0},
        "ready_to_start_runtime": (
            load_result.ok
            and dependency.get("installed") is True
            and runtime_import.get("ok") is True
        ),
        "network_check": network_result,
        "raw_telegram_bot_token_exposed": False,
        "raw_operator_user_ids_exposed": False,
        "raw_telegram_init_data_exposed": False,
        "live_trading_enabled": False,
        "real_orders_submitted": False,
        "wallet_integration_added": False,
        "cryptographic_signing_added": False,
        "authenticated_polymarket_endpoint_calls_added": False,
        "autonomous_execution_added": False,
    }
    return report


def check_python_telegram_bot_dependency() -> dict[str, Any]:
    try:
        telegram_spec = importlib.util.find_spec("telegram")
        telegram_ext_spec = importlib.util.find_spec("telegram.ext")
    except Exception:
        return {
            "dependency": "python-telegram-bot",
            "installed": False,
            "status": "missing",
            "error_category": "dependency_probe_failed",
        }
    installed = telegram_spec is not None and telegram_ext_spec is not None
    return {
        "dependency": "python-telegram-bot",
        "installed": installed,
        "status": "installed" if installed else "missing",
        "error_category": "" if installed else "not_importable",
    }


def check_runtime_module_import(
    *,
    importer: Callable[[str], Any] = importlib.import_module,
) -> dict[str, Any]:
    try:
        module = importer(RUNTIME_MODULE)
    except Exception:
        return {
            "module": RUNTIME_MODULE,
            "ok": False,
            "status": "failed",
            "error_category": "import_failed",
        }
    return {
        "module": RUNTIME_MODULE,
        "ok": hasattr(module, "main"),
        "status": "ok" if hasattr(module, "main") else "missing_main",
        "runtime_command": RUNTIME_COMMAND,
    }


def run_explicit_network_check(
    bot_token: str,
    *,
    telegram_get_me_checker: Callable[[str], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if not clean_text(bot_token):
        return {
            "requested": True,
            "telegram_api_reachable": False,
            "get_me_ok": False,
            "bot_username": "",
            "error_category": NETWORK_MISSING_TOKEN,
            "api_url": TELEGRAM_GET_ME_URL_REDACTED,
        }
    checker = telegram_get_me_checker or telegram_get_me
    return sanitize_network_check_result(checker(bot_token), bot_token=bot_token)


def telegram_get_me(
    bot_token: str,
    *,
    timeout_seconds: float = 10.0,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    request = Request(
        f"https://api.telegram.org/bot{bot_token}/getMe",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with opener(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return {
            "requested": True,
            "telegram_api_reachable": True,
            "get_me_ok": False,
            "bot_username": "",
            "error_category": categorize_telegram_get_me_http_error(exc),
            "api_url": TELEGRAM_GET_ME_URL_REDACTED,
        }
    except (TimeoutError, socket.timeout):
        return _network_error_result(NETWORK_TELEGRAM_API_TIMEOUT)
    except URLError as exc:
        return _network_error_result(categorize_telegram_network_exception(exc))
    except OSError as exc:
        return _network_error_result(categorize_telegram_network_exception(exc))
    except Exception as exc:
        return _network_error_result(categorize_telegram_network_exception(exc))

    result = payload.get("result") if isinstance(payload, Mapping) else {}
    username = clean_text(result.get("username")) if isinstance(result, Mapping) else ""
    ok = isinstance(payload, Mapping) and payload.get("ok") is True
    return {
        "requested": True,
        "telegram_api_reachable": True,
        "get_me_ok": ok,
        "bot_username": username if ok else "",
        "error_category": "" if ok else NETWORK_TELEGRAM_API_ERROR,
        "api_url": TELEGRAM_GET_ME_URL_REDACTED,
    }


def categorize_telegram_get_me_http_error(exc: HTTPError) -> str:
    if exc.code == 401:
        return NETWORK_INVALID_OR_REVOKED_TOKEN
    if exc.code == 409 or _looks_like_polling_conflict(exc):
        return NETWORK_POLLING_CONFLICT
    if exc.code == 429:
        return NETWORK_RATE_LIMITED
    if 500 <= exc.code <= 599:
        return NETWORK_TELEGRAM_SERVER_ERROR
    return NETWORK_TELEGRAM_HTTP_ERROR


def categorize_telegram_network_exception(exc: BaseException) -> str:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return NETWORK_TELEGRAM_API_TIMEOUT
    reason = getattr(exc, "reason", None)
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return NETWORK_TELEGRAM_API_TIMEOUT
    reason_text = clean_text(reason)
    text = f"{exc.__class__.__name__} {clean_text(exc)} {reason_text}".lower()
    if "conflict" in text or "terminated by other getupdates request" in text or "409" in text:
        return NETWORK_POLLING_CONFLICT
    if "timed out" in text or "timeout" in text:
        return NETWORK_TELEGRAM_API_TIMEOUT
    if (
        "dns" in text
        or "name resolution" in text
        or "network is unreachable" in text
        or "connection refused" in text
        or "connection reset" in text
        or "connect" in text
        or "unreachable" in text
        or "gaierror" in text
    ):
        return NETWORK_UNREACHABLE
    return NETWORK_UNREACHABLE


def mini_app_url_status(value: str) -> str:
    if not clean_text(value):
        return "missing"
    if runtime.safe_mini_app_url(value):
        return "configured"
    return "configured_invalid"


def review_only_safety_flags_expected_false() -> dict[str, bool]:
    flags = runtime.runtime_safety_flags()
    return {key: flags.get(key) for key in EXPECTED_FALSE_FLAGS}


def render_smoke_report_lines(report: Mapping[str, Any]) -> list[str]:
    env_status = dict(report.get("env_status", {}))
    dependency = dict(report.get("dependency_check", {}))
    runtime_import = dict(report.get("runtime_module_import", {}))
    network = dict(report.get("network_check", {}))
    safety = dict(report.get("review_only_safety_flags_expected_false", {}))
    operator_ids_line = (
        f"configured count:{int(env_status.get('allowed_operator_id_count', 0) or 0)}"
        if env_status.get("allowed_operator_ids_configured") is True
        else "missing"
    )
    config_errors = [clean_text(item) for item in report.get("config_errors", []) if clean_text(item)]
    lines = [
        "PMBOT Telegram runtime smoke",
        f"Task: {clean_text(report.get('task_id'))}",
        "",
        "Environment",
        f"Telegram token: {clean_text(env_status.get('telegram_token')) or 'missing'}",
        f"Allowed operator IDs: {operator_ids_line}",
        f"Artifact directory: {'configured' if env_status.get('artifact_dir_configured') is True else 'not configured'}",
        "",
        "Dependency",
        f"python-telegram-bot: {clean_text(dependency.get('status')) or 'missing'}",
        f"Dependency fix: {dependency_action(dependency)}",
        "",
        "Runtime module",
        f"Runtime module import: {clean_text(runtime_import.get('status')) or 'failed'}",
        f"Runtime command: {clean_text(report.get('runtime_command'))}",
        "",
        "Mini App",
        f"Mini App URL: {clean_text(env_status.get('mini_app_url_status')) or 'missing'}",
        "Panel fallback: safe review-only buttons are available when the Mini App URL is missing.",
        "",
        "Safety",
        "Safety flags expected false: "
        + ("ok" if all(value is False for value in safety.values()) else "blocked"),
        "Live trading enabled: false",
        "Real orders submitted: false",
        "Wallet/signing enabled: false",
        "Resolved blocker count: 0",
        "",
        "Network check",
        f"Network check requested: {str(report.get('network_check_requested') is True).lower()}",
    ]
    if network.get("requested") is True:
        lines.extend(
            [
                f"Telegram API reachable: {str(network.get('telegram_api_reachable') is True).lower()}",
                f"getMe ok: {str(network.get('get_me_ok') is True).lower()}",
                f"Bot username: {clean_text(network.get('bot_username')) or 'not_available'}",
                f"Network error category: {clean_text(network.get('error_category')) or 'none'}",
                f"Network fix: {network_action(network)}",
            ]
        )
    else:
        lines.append("Network check: not requested")
    if config_errors:
        lines.append("Config errors: " + ", ".join(config_errors))
    lines.extend(
        [
            "",
            "Next run command",
            f"No-network smoke: {clean_text(report.get('smoke_command'))}",
            f"Optional network check: {clean_text(report.get('smoke_command'))} --network-check",
            f"Runtime: {clean_text(report.get('runtime_command'))}",
            f"Handoff checklist: {clean_text(report.get('handoff_checklist_path'))}",
            f"Ready to start runtime: {str(report.get('ready_to_start_runtime') is True).lower()}",
        ]
    )
    return lines


def dependency_action(dependency: Mapping[str, Any]) -> str:
    if dependency.get("installed") is True:
        return "none"
    return "Install python-telegram-bot in the same Python environment, then rerun the smoke."


def network_action(network: Mapping[str, Any]) -> str:
    category = normalize_network_error_category(clean_text(network.get("error_category")))
    if category in {"", "none"} and network.get("get_me_ok") is True:
        return "none"
    actions = {
        NETWORK_INVALID_OR_REVOKED_TOKEN: "Replace PMBOT_TELEGRAM_BOT_TOKEN from BotFather and open a new terminal.",
        NETWORK_TELEGRAM_API_TIMEOUT: "Check connectivity and Telegram availability, then retry.",
        NETWORK_UNREACHABLE: "Check DNS, proxy, firewall, or local network access.",
        NETWORK_POLLING_CONFLICT: "Stop the other polling runtime that is using this bot token, wait briefly, then rerun.",
        NETWORK_MISSING_TOKEN: "Set PMBOT_TELEGRAM_BOT_TOKEN locally without printing it.",
        NETWORK_RATE_LIMITED: "Wait for Telegram rate limiting to clear, then retry.",
        NETWORK_TELEGRAM_SERVER_ERROR: "Telegram returned a server error; retry later.",
    }
    return actions.get(category, "Inspect the safe error category and rerun the no-network smoke.")


def main(
    argv: list[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    printer: Callable[[str], None] = print,
) -> int:
    parser = argparse.ArgumentParser(description="PMBOT Telegram runtime smoke diagnostics.")
    parser.add_argument(
        "--network-check",
        action="store_true",
        help="Explicitly call Telegram getMe with the configured bot token.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the redacted smoke report as JSON.",
    )
    args = parser.parse_args(argv)
    report = build_telegram_runtime_smoke_report(env=env, network_check=args.network_check)
    if args.json:
        printer(json.dumps(report, indent=2, sort_keys=True))
    else:
        for line in render_smoke_report_lines(report):
            printer(line)
    return 0


def _normalize_dependency_check(value: Mapping[str, Any]) -> dict[str, Any]:
    installed = value.get("installed") is True
    return {
        "dependency": "python-telegram-bot",
        "installed": installed,
        "status": "installed" if installed else "missing",
        "error_category": "" if installed else clean_text(value.get("error_category")) or "not_importable",
    }


def _normalize_runtime_import_check(value: Mapping[str, Any]) -> dict[str, Any]:
    ok = value.get("ok") is True
    return {
        "module": RUNTIME_MODULE,
        "ok": ok,
        "status": "ok" if ok else clean_text(value.get("status")) or "failed",
        "runtime_command": RUNTIME_COMMAND,
        "error_category": "" if ok else clean_text(value.get("error_category")) or "import_failed",
    }


def sanitize_network_check_result(value: Mapping[str, Any], *, bot_token: str) -> dict[str, Any]:
    username = _redact_sensitive_text(clean_text(value.get("bot_username")), bot_token)
    category = normalize_network_error_category(
        clean_text(value.get("error_category")) or ("none" if value.get("get_me_ok") is True else NETWORK_UNREACHABLE)
    )
    return {
        "requested": True,
        "telegram_api_reachable": value.get("telegram_api_reachable") is True,
        "get_me_ok": value.get("get_me_ok") is True,
        "bot_username": username if value.get("get_me_ok") is True else "",
        "error_category": _redact_sensitive_text(category, bot_token),
        "api_url": TELEGRAM_GET_ME_URL_REDACTED,
    }


def _network_error_result(category: str) -> dict[str, Any]:
    return {
        "requested": True,
        "telegram_api_reachable": False,
        "get_me_ok": False,
        "bot_username": "",
        "error_category": normalize_network_error_category(category),
        "api_url": TELEGRAM_GET_ME_URL_REDACTED,
    }


def normalize_network_error_category(category: str) -> str:
    text = clean_text(category)
    if not text:
        return ""
    normalized = text.upper()
    legacy = {
        "NOT_REQUESTED": NETWORK_NOT_REQUESTED,
        "MISSING_TOKEN": NETWORK_MISSING_TOKEN,
        "UNAUTHORIZED": NETWORK_INVALID_OR_REVOKED_TOKEN,
        "INVALID_TOKEN": NETWORK_INVALID_OR_REVOKED_TOKEN,
        "INVALID_OR_REVOKED_TOKEN": NETWORK_INVALID_OR_REVOKED_TOKEN,
        "TIMEOUT": NETWORK_TELEGRAM_API_TIMEOUT,
        "TIMED_OUT": NETWORK_TELEGRAM_API_TIMEOUT,
        "TELEGRAM_API_TIMEOUT": NETWORK_TELEGRAM_API_TIMEOUT,
        "NETWORK_ERROR": NETWORK_UNREACHABLE,
        "CONNECT_ERROR": NETWORK_UNREACHABLE,
        "DNS_ERROR": NETWORK_UNREACHABLE,
        "NETWORK_UNREACHABLE": NETWORK_UNREACHABLE,
        "CONFLICT": NETWORK_POLLING_CONFLICT,
        "POLLING_CONFLICT": NETWORK_POLLING_CONFLICT,
        "RATE_LIMITED": NETWORK_RATE_LIMITED,
        "TELEGRAM_RATE_LIMITED": NETWORK_RATE_LIMITED,
        "TELEGRAM_SERVER_ERROR": NETWORK_TELEGRAM_SERVER_ERROR,
        "TELEGRAM_HTTP_ERROR": NETWORK_TELEGRAM_HTTP_ERROR,
        "TELEGRAM_ERROR": NETWORK_TELEGRAM_API_ERROR,
        "TELEGRAM_API_ERROR": NETWORK_TELEGRAM_API_ERROR,
        "NONE": "none",
    }
    return legacy.get(normalized, normalized)


def _button_rows(rows: tuple[tuple[tuple[str, str], ...], ...]) -> list[list[str]]:
    return [[label for label, _callback_data in row] for row in rows]


def _redact_sensitive_text(value: str, bot_token: str) -> str:
    token = clean_text(bot_token)
    if token and token in value:
        return value.replace(token, "<redacted>")
    return value


def _looks_like_polling_conflict(exc: HTTPError) -> bool:
    text = f"{clean_text(exc)} {clean_text(getattr(exc, 'reason', ''))}".lower()
    return "conflict" in text or "terminated by other getupdates request" in text


if __name__ == "__main__":
    raise SystemExit(main())
