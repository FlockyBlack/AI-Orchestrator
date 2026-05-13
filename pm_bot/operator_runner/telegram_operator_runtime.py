from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from urllib.parse import urlsplit

from pm_bot.operator_runner.telegram_mini_app_operator_panel import (
    build_telegram_mini_app_panel_artifact_summary,
    summarize_telegram_mini_app_panel_model,
)
from pm_bot.operator_runner.telegram_operator_control_bot import (
    SUPPORTED_COMMANDS,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
    TelegramOperatorControlResponse,
)
from pm_bot.operator_runner.telegram_operator_control_state import (
    STATE_ARTIFACT_NAME,
    build_telegram_operator_control_state,
    load_telegram_operator_control_state,
    normalize_telegram_command,
    write_telegram_operator_control_state,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, normalize_path

TASK_ID = "ORCH-PMBOT-TRADING-MVP-045-TELEGRAM-BOT-RUNTIME-WIRING-FOR-EXISTING-BOT"

TELEGRAM_BOT_TOKEN_ENV = "PMBOT_TELEGRAM_BOT_TOKEN"
ALLOWED_OPERATOR_IDS_ENV = "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS"
TELEGRAM_MINI_APP_URL_ENV = "PMBOT_TELEGRAM_MINI_APP_URL"
PMBOT_ARTIFACT_DIR_ENV = "PMBOT_ARTIFACT_DIR"

TELEGRAM_RUNTIME_DEPENDENCY_MISSING = "Telegram runtime dependency missing"
PANEL_BUTTON_TEXT = "Open PMBOT Mini App Panel"

_OPERATOR_ID_SPLIT_RE = re.compile(r"[,;\s]+")


@dataclass(frozen=True)
class TelegramRuntimeConfig:
    bot_token: str = field(default="", repr=False)
    allowed_operator_ids: tuple[str, ...] = field(default_factory=tuple, repr=False)
    mini_app_url: str = field(default="", repr=False)
    artifact_dir: Path | None = None
    generated_at: str = GENERATED_AT

    @property
    def token_status(self) -> str:
        return "configured:redacted" if self.bot_token else "missing"

    @property
    def allowed_operator_count(self) -> int:
        return len(self.allowed_operator_ids)

    @property
    def mini_app_url_status(self) -> str:
        if not self.mini_app_url:
            return "not_configured"
        return "configured" if safe_mini_app_url(self.mini_app_url) else "configured_invalid"

    def to_redacted_status(self) -> dict[str, Any]:
        return {
            "task_id": TASK_ID,
            "telegram_token": self.token_status,
            "allowed_operator_ids_configured": bool(self.allowed_operator_ids),
            "allowed_operator_id_count": self.allowed_operator_count,
            "allowed_operator_ids_redacted": True,
            "mini_app_url_status": self.mini_app_url_status,
            "artifact_dir_configured": self.artifact_dir is not None,
            "artifact_dir": normalize_path(self.artifact_dir) if self.artifact_dir is not None else "",
            "raw_telegram_bot_token_exposed": False,
            "raw_operator_user_ids_exposed": False,
            "raw_telegram_init_data_exposed": False,
            **runtime_safety_flags(),
        }


@dataclass(frozen=True)
class TelegramRuntimeConfigLoadResult:
    config: TelegramRuntimeConfig
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class TelegramRuntimeReply:
    command: str
    authorized: bool
    text: str
    response: TelegramOperatorControlResponse
    panel_button_text: str = ""
    panel_button_url: str = field(default="", repr=False)

    @property
    def state(self) -> Mapping[str, Any]:
        return self.response.state

    @property
    def summary(self) -> Mapping[str, Any]:
        return self.response.summary

    def to_redacted_dict(self) -> dict[str, Any]:
        return {
            "task_id": TASK_ID,
            "command": self.command,
            "authorized": self.authorized,
            "text": self.text,
            "panel_button_attached": bool(self.panel_button_url),
            "panel_button_text": self.panel_button_text if self.panel_button_url else "",
            "panel_button_url_status": "configured:redacted" if self.panel_button_url else "not_configured",
            "state": dict(self.state),
            "summary": dict(self.summary),
            "raw_telegram_bot_token_exposed": False,
            "raw_operator_user_ids_exposed": False,
            "raw_telegram_init_data_exposed": False,
            **runtime_safety_flags(),
        }


class TelegramPollingRunner(Protocol):
    def run_polling(
        self,
        *,
        config: TelegramRuntimeConfig,
        adapter: "TelegramOperatorRuntimeAdapter",
        printer: Callable[[str], None],
    ) -> None:
        ...


class TelegramRuntimeDependencyError(RuntimeError):
    pass


class PythonTelegramBotPollingRunner:
    def run_polling(
        self,
        *,
        config: TelegramRuntimeConfig,
        adapter: "TelegramOperatorRuntimeAdapter",
        printer: Callable[[str], None],
    ) -> None:
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
            from telegram.ext import Application, MessageHandler, filters
        except ImportError as exc:  # pragma: no cover - exercised through main() error handling.
            raise TelegramRuntimeDependencyError(TELEGRAM_RUNTIME_DEPENDENCY_MISSING) from exc

        application = Application.builder().token(config.bot_token).build()

        async def handle_text(update: Any, context: Any) -> None:  # noqa: ARG001
            message = getattr(update, "effective_message", None)
            user = getattr(update, "effective_user", None)
            if message is None or user is None:
                return
            text = clean_text(getattr(message, "text", ""))
            if not text:
                return
            reply = adapter.handle_text(
                user_id=getattr(user, "id", ""),
                chat_id=getattr(message, "chat_id", None),
                text=text,
            )
            reply_markup = None
            if reply.panel_button_url:
                reply_markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(reply.panel_button_text, url=reply.panel_button_url)]]
                )
            await message.reply_text(reply.text, reply_markup=reply_markup, disable_web_page_preview=True)

        application.add_handler(MessageHandler(filters.TEXT, handle_text))
        printer("Telegram long polling: starting")
        printer("Telegram runtime safety: review-only; no live trading; no order submission; no wallet/signing.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


class TelegramOperatorRuntimeAdapter:
    def __init__(
        self,
        *,
        config: TelegramRuntimeConfig,
        context: Mapping[str, Any] | None = None,
        state: Mapping[str, Any] | None = None,
        bot: TelegramOperatorControlBot | None = None,
    ) -> None:
        self.config = config
        self.context = dict(context or load_runtime_context(config.artifact_dir, generated_at=config.generated_at))
        self.bot = bot or TelegramOperatorControlBot(
            config=TelegramOperatorControlConfig(
                telegram_bot_configured=bool(config.bot_token),
                allowed_operator_user_ids=config.allowed_operator_ids,
                token_status="configured_redacted" if config.bot_token else "missing",
                generated_at=config.generated_at,
            ),
            context=self.context,
            state=state or load_runtime_state(config.artifact_dir, generated_at=config.generated_at),
            generated_at=config.generated_at,
        )

    def handle_text(self, *, user_id: Any, text: str, chat_id: Any | None = None) -> TelegramRuntimeReply:
        response = self.bot.handle_command(user_id=user_id, text=text, chat_id=chat_id)
        self._persist_state(response.state)
        reply_text, button_text, button_url = self._decorate_response(response)
        return TelegramRuntimeReply(
            command=response.command,
            authorized=response.authorized,
            text=reply_text,
            response=response,
            panel_button_text=button_text,
            panel_button_url=button_url,
        )

    def _decorate_response(self, response: TelegramOperatorControlResponse) -> tuple[str, str, str]:
        if response.command != "/panel" or not response.authorized:
            return response.text, "", ""
        url = safe_mini_app_url(self.config.mini_app_url)
        if url:
            return (
                response.text
                + "\nMini App URL: configured.\n"
                + f"Button: {PANEL_BUTTON_TEXT}",
                PANEL_BUTTON_TEXT,
                url,
            )
        if self.config.mini_app_url:
            return (
                response.text
                + "\nMini App URL: configured but rejected by runtime URL safety checks; no button attached.",
                "",
                "",
            )
        return response.text + "\nMini App URL: not configured; use the local/static artifact if available.", "", ""

    def _persist_state(self, state: Mapping[str, Any]) -> None:
        if self.config.artifact_dir is None:
            return
        write_telegram_operator_control_state(self.config.artifact_dir / STATE_ARTIFACT_NAME, state)


def load_runtime_config(env: Mapping[str, str] | None = None, *, generated_at: str = GENERATED_AT) -> TelegramRuntimeConfigLoadResult:
    source = os.environ if env is None else env
    token = clean_text(source.get(TELEGRAM_BOT_TOKEN_ENV))
    raw_operator_ids = clean_text(source.get(ALLOWED_OPERATOR_IDS_ENV))
    mini_app_url = clean_text(source.get(TELEGRAM_MINI_APP_URL_ENV))
    artifact_dir_raw = clean_text(source.get(PMBOT_ARTIFACT_DIR_ENV))
    errors: list[str] = []

    if not token:
        errors.append("missing_token")
    if not raw_operator_ids:
        operator_ids: tuple[str, ...] = ()
        errors.append("missing_allowed_operator_ids")
    else:
        try:
            operator_ids = parse_allowed_operator_ids(raw_operator_ids)
        except ValueError:
            operator_ids = ()
            errors.append("invalid_allowed_operator_ids")

    config = TelegramRuntimeConfig(
        bot_token=token,
        allowed_operator_ids=operator_ids,
        mini_app_url=mini_app_url,
        artifact_dir=Path(artifact_dir_raw) if artifact_dir_raw else None,
        generated_at=generated_at,
    )
    return TelegramRuntimeConfigLoadResult(config=config, errors=tuple(errors))


def parse_allowed_operator_ids(raw_value: str) -> tuple[str, ...]:
    values = [item for item in _OPERATOR_ID_SPLIT_RE.split(clean_text(raw_value)) if item]
    if not values:
        raise ValueError("missing allowed operator IDs")
    normalized: list[str] = []
    for item in values:
        if not item.isdecimal():
            raise ValueError("allowed operator IDs must be numeric")
        normalized_id = str(int(item))
        if normalized_id not in normalized:
            normalized.append(normalized_id)
    return tuple(normalized)


def startup_status_lines(load_result: TelegramRuntimeConfigLoadResult) -> list[str]:
    config = load_result.config
    if "missing_allowed_operator_ids" in load_result.errors:
        operator_line = "Allowed operator IDs: missing"
    elif "invalid_allowed_operator_ids" in load_result.errors:
        operator_line = "Allowed operator IDs: invalid"
    else:
        operator_line = f"Allowed operator IDs: configured count:{config.allowed_operator_count}"
    lines = [
        f"Telegram token: {config.token_status}",
        operator_line,
        f"Mini App URL: {config.mini_app_url_status}",
        "Runtime mode: explicit long polling only",
        "Runtime safety: review-only; live trading disabled; order submission disabled; wallet/signing disabled.",
    ]
    if config.artifact_dir is not None:
        lines.append(f"Artifact directory: {normalize_path(config.artifact_dir)}")
    else:
        lines.append("Artifact directory: not configured")
    return lines


def startup_instruction_lines(errors: tuple[str, ...]) -> list[str]:
    lines: list[str] = []
    if "missing_token" in errors:
        lines.extend(
            [
                "Set Telegram bot token before starting long polling.",
                f'[Environment]::SetEnvironmentVariable("{TELEGRAM_BOT_TOKEN_ENV}", "TOKEN_FROM_BOTFATHER", "User")',
            ]
        )
    if "missing_allowed_operator_ids" in errors:
        lines.extend(
            [
                "Set allowed Telegram operator user IDs before starting long polling.",
                f'[Environment]::SetEnvironmentVariable("{ALLOWED_OPERATOR_IDS_ENV}", "123456789", "User")',
            ]
        )
    if "invalid_allowed_operator_ids" in errors:
        lines.append("Allowed Telegram operator user IDs must be numeric IDs separated by commas, semicolons, or spaces.")
    if lines:
        lines.append("After updating Windows User environment variables, open a new terminal and rerun the module.")
    return lines


def load_runtime_context(artifact_dir: Path | None, *, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    if artifact_dir is None:
        return {}
    context: dict[str, Any] = {}
    dashboard_path = artifact_dir / "paper_daily_dashboard.json"
    if dashboard_path.exists():
        try:
            context.update(load_json_object(dashboard_path, label="paper daily dashboard"))
        except Exception:
            context["artifact_context_load_status"] = "paper_daily_dashboard_unavailable"
    panel_json_path = artifact_dir / "telegram_mini_app_operator_panel_044.json"
    panel_html_path = artifact_dir / "telegram_mini_app_operator_panel_044.html"
    if panel_json_path.exists():
        try:
            panel = load_json_object(panel_json_path, label="telegram mini app operator panel")
            context["telegram_mini_app_operator_panel_summary"] = summarize_telegram_mini_app_panel_model(panel)
        except Exception:
            context["telegram_mini_app_operator_panel_summary"] = build_telegram_mini_app_panel_artifact_summary(
                latest_panel_html_path=normalize_path(panel_html_path) if panel_html_path.exists() else "",
                latest_panel_json_path=normalize_path(panel_json_path),
                panel_artifact_available=True,
                generated_at=generated_at,
            )
    elif panel_html_path.exists():
        context["telegram_mini_app_operator_panel_summary"] = build_telegram_mini_app_panel_artifact_summary(
            latest_panel_html_path=normalize_path(panel_html_path),
            latest_panel_json_path="",
            panel_artifact_available=True,
            generated_at=generated_at,
        )
    return context


def load_runtime_state(artifact_dir: Path | None, *, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    if artifact_dir is None:
        return build_telegram_operator_control_state(generated_at=generated_at)
    state_path = artifact_dir / STATE_ARTIFACT_NAME
    if not state_path.exists():
        return build_telegram_operator_control_state(generated_at=generated_at)
    try:
        return load_telegram_operator_control_state(state_path)
    except Exception:
        return build_telegram_operator_control_state(generated_at=generated_at)


def safe_mini_app_url(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    parsed = urlsplit(text)
    if parsed.scheme not in {"https", "http"}:
        return ""
    if not parsed.netloc or parsed.username or parsed.password:
        return ""
    return text


def run_runtime(
    *,
    config: TelegramRuntimeConfig,
    polling_runner: TelegramPollingRunner | None = None,
    printer: Callable[[str], None] = print,
) -> int:
    adapter = TelegramOperatorRuntimeAdapter(config=config)
    runner = polling_runner or PythonTelegramBotPollingRunner()
    try:
        runner.run_polling(config=config, adapter=adapter, printer=printer)
    except KeyboardInterrupt:
        printer("Telegram runtime stopped by operator with Ctrl+C.")
        return 0
    except TelegramRuntimeDependencyError:
        printer(TELEGRAM_RUNTIME_DEPENDENCY_MISSING)
        printer("Install python-telegram-bot in the local operator environment, then rerun the module.")
        return 2
    return 0


def main(
    argv: list[str] | None = None,  # noqa: ARG001
    *,
    env: Mapping[str, str] | None = None,
    printer: Callable[[str], None] = print,
    polling_runner: TelegramPollingRunner | None = None,
) -> int:
    load_result = load_runtime_config(env)
    for line in startup_status_lines(load_result):
        printer(line)
    if not load_result.ok:
        for line in startup_instruction_lines(load_result.errors):
            printer(line)
        return 2
    return run_runtime(config=load_result.config, polling_runner=polling_runner, printer=printer)


def runtime_safety_flags() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "execution_enabling": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "network_used_in_tests": False,
        "external_api_calls_in_tests": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "would_submit_order": False,
        "order_submission_enabled": False,
        "real_order_submitted": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "browser_automation_added": False,
        "resolved_blocker_count": 0,
    }


def is_supported_runtime_command(text: str) -> bool:
    command = normalize_telegram_command(text)
    return command in SUPPORTED_COMMANDS


if __name__ == "__main__":
    raise SystemExit(main())
