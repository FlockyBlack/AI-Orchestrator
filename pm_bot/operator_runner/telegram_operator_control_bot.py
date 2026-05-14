from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from pm_bot.operator_runner.telegram_operator_i18n import (
    DEFAULT_OPERATOR_LANGUAGE,
    HOME_BUTTON_ROWS_BY_LANGUAGE,
    LANGUAGE_SELECTION_BUTTON_ROWS,
    PANEL_FALLBACK_BUTTON_ROWS_BY_LANGUAGE,
    all_button_rows,
    language_from_command_text,
    normalize_operator_language,
    operator_language_from_state,
    operator_language_is_selected,
    render_home,
    render_language_selected,
    render_language_selection_prompt,
)
from pm_bot.operator_runner.telegram_operator_control_state import (
    build_telegram_operator_control_state,
    normalize_telegram_command,
    record_telegram_operator_control_command,
    request_telegram_operator_kill_switch,
    request_telegram_operator_pause,
    set_telegram_operator_language,
    summarize_telegram_operator_control_state,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, mapping_rows
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_telegram_operator_control_config,
    validate_secret_boundary_telegram_operator_control_summary,
)

TELEGRAM_OPERATOR_CONTROL_BOT_CONTRACT = "pmbot_telegram_operator_control_bot.v1"
TELEGRAM_OPERATOR_CONTROL_CONFIG_CONTRACT = "pmbot_telegram_operator_control_config.v1"
TELEGRAM_OPERATOR_CONTROL_RESPONSE_CONTRACT = "pmbot_telegram_operator_control_response.v1"
TELEGRAM_OPERATOR_CONTROL_SUMMARY_CONTRACT = "pmbot_telegram_operator_control_summary.v1"
TELEGRAM_OPERATOR_BUTTON_CONTRACT = "pmbot_telegram_operator_button.v1"
TELEGRAM_OPERATOR_KEYBOARD_CONTRACT = "pmbot_telegram_operator_keyboard.v1"

TASK_ID = "ORCH-PMBOT-TRADING-MVP-043-TELEGRAM-OPERATOR-CONTROL-BOT-V1"

SUPPORTED_COMMANDS = (
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
    "/panel",
    "/language",
    "/pause",
    "/kill",
)

CALLBACK_COMMAND_MAP = {
    "pmbot:status": "/status",
    "pmbot:btc": "/btc",
    "pmbot:intent": "/intent",
    "pmbot:risk": "/risk",
    "pmbot:auth": "/auth",
    "pmbot:order": "/order",
    "pmbot:gonogo": "/gonogo",
    "pmbot:evidence": "/evidence",
    "pmbot:blockers": "/blockers",
    "pmbot:panel": "/panel",
    "pmbot:language": "/language",
    "pmbot:lang:ru": "/language",
    "pmbot:lang:en": "/language",
    "pmbot:pause": "/pause",
    "pmbot:kill": "/kill",
}

HOME_BUTTON_ROWS = HOME_BUTTON_ROWS_BY_LANGUAGE["en"]
RUSSIAN_HOME_BUTTON_ROWS = HOME_BUTTON_ROWS_BY_LANGUAGE["ru"]

PANEL_FALLBACK_BUTTON_ROWS = PANEL_FALLBACK_BUTTON_ROWS_BY_LANGUAGE["en"]
RUSSIAN_PANEL_FALLBACK_BUTTON_ROWS = PANEL_FALLBACK_BUTTON_ROWS_BY_LANGUAGE["ru"]

FORBIDDEN_BUTTON_LABEL_TERMS = ("BUY", "SELL", "TRADE", "EXECUTE", "APPROVE LIVE")

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "would_submit_order",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "wallet_signing_enabled",
    "wallet_enabled",
)

UNAUTHORIZED_DENIAL = (
    "Access denied. This PMBOT operator surface is review-only and only configured operator IDs may use it."
)


class TelegramTransport(Protocol):
    def send_message(self, chat_id: Any, text: str) -> None:
        ...


@dataclass(frozen=True)
class TelegramOperatorButton:
    label: str
    callback_data: str = ""
    command: str = ""
    url: str = field(default="", repr=False)
    web_app_url: str = field(default="", repr=False)

    def to_dict(self, *, redact_urls: bool = False) -> dict[str, Any]:
        value = {
            "contract_version": TELEGRAM_OPERATOR_BUTTON_CONTRACT,
            "label": self.label,
            "callback_data": self.callback_data,
            "command": self.command,
            "has_url": bool(self.url),
            "has_web_app_url": bool(self.web_app_url),
            "url": "configured:redacted" if redact_urls and self.url else self.url,
            "web_app_url": "configured:redacted" if redact_urls and self.web_app_url else self.web_app_url,
            "safe_label": is_safe_operator_button_label(self.label),
            "review_only": True,
            "execution_enabling": False,
        }
        value.update(_control_safety_flags())
        return value


@dataclass(frozen=True)
class TelegramOperatorKeyboard:
    rows: tuple[tuple[TelegramOperatorButton, ...], ...] = ()

    @property
    def has_buttons(self) -> bool:
        return any(self.rows)

    def buttons(self) -> tuple[TelegramOperatorButton, ...]:
        return tuple(button for row in self.rows for button in row)

    def with_prepended_row(self, buttons: Sequence[TelegramOperatorButton]) -> "TelegramOperatorKeyboard":
        row = tuple(buttons)
        if not row:
            return self
        return TelegramOperatorKeyboard(rows=(row, *self.rows))

    def to_dict(self, *, redact_urls: bool = False) -> dict[str, Any]:
        return {
            "contract_version": TELEGRAM_OPERATOR_KEYBOARD_CONTRACT,
            "rows": [
                [button.to_dict(redact_urls=redact_urls) for button in row]
                for row in self.rows
            ],
            "button_count": len(self.buttons()),
            "safe_button_labels": all(is_safe_operator_button_label(button.label) for button in self.buttons()),
            "review_only": True,
            "execution_enabling": False,
            **_control_safety_flags(),
        }


@dataclass(frozen=True)
class TelegramOperatorControlConfig:
    telegram_bot_configured: bool = False
    allowed_operator_user_ids: tuple[str, ...] = ()
    bot_name: str = "PMBOT Operator Control Bot v1"
    token_status: str = "missing"
    generated_at: str = GENERATED_AT

    def is_authorized(self, user_id: Any) -> bool:
        allowed = {clean_text(item) for item in self.allowed_operator_user_ids if clean_text(item)}
        return bool(allowed) and clean_text(user_id) in allowed

    def to_redacted_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": TELEGRAM_OPERATOR_CONTROL_CONFIG_CONTRACT,
            "generated_at": self.generated_at,
            "bot_name": self.bot_name,
            "telegram_bot_token_status": "configured_redacted" if self.telegram_bot_configured else "missing",
            "telegram_bot_configured": self.telegram_bot_configured,
            "allowed_operator_ids_configured": bool(self.allowed_operator_user_ids),
            "allowed_operator_id_count": len([item for item in self.allowed_operator_user_ids if clean_text(item)]),
            "allowed_operator_ids_redacted": True,
            "raw_telegram_bot_token_exposed": False,
            "raw_operator_user_ids_exposed": False,
            "environment_inspected": False,
            "environment_secrets_read": False,
            "secrets_read": False,
            "secrets_printed": False,
            "secrets_persisted": False,
            "review_only": True,
            "execution_enabling": False,
        }
        value.update(_control_safety_flags())
        value["validation"] = validate_secret_boundary_telegram_operator_control_config(value)
        return value


@dataclass(frozen=True)
class TelegramOperatorControlResponse:
    command: str
    authorized: bool
    text: str
    state: Mapping[str, Any]
    summary: Mapping[str, Any]
    keyboard: TelegramOperatorKeyboard = field(default_factory=TelegramOperatorKeyboard)

    def to_dict(self) -> dict[str, Any]:
        value = {
            "contract_version": TELEGRAM_OPERATOR_CONTROL_RESPONSE_CONTRACT,
            "command": self.command,
            "authorized": self.authorized,
            "text": self.text,
            "state": dict(self.state),
            "summary": dict(self.summary),
            "keyboard": self.keyboard.to_dict(redact_urls=True),
        }
        value.update(_control_safety_flags())
        return value


class FakeTelegramTransport:
    """In-memory transport for tests; stores text and hashed chat identifiers only."""

    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def send_message(self, chat_id: Any, text: str) -> None:
        self.messages.append({"chat_id_hash": _hash_identifier(chat_id), "text": text})


class TelegramOperatorControlBot:
    def __init__(
        self,
        *,
        config: TelegramOperatorControlConfig | Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        state: Mapping[str, Any] | None = None,
        transport: TelegramTransport | None = None,
        generated_at: str = GENERATED_AT,
    ) -> None:
        self.config = config if isinstance(config, TelegramOperatorControlConfig) else config_from_mapping(config)
        self.context = dict(context or {})
        self.state = dict(state or build_telegram_operator_control_state(generated_at=generated_at))
        self.transport = transport
        self.generated_at = generated_at

    def handle_command(self, *, user_id: Any, text: str, chat_id: Any | None = None) -> TelegramOperatorControlResponse:
        command = normalize_telegram_command(text) or "/help"
        if command not in SUPPORTED_COMMANDS:
            command = "/help"
        requested_language = language_from_command_text(text) if command == "/language" else ""
        authorized = self.config.is_authorized(user_id)
        if not authorized:
            self.state = record_telegram_operator_control_command(
                self.state,
                command=command,
                operator_user_id=user_id,
                authorized=False,
                command_status="unauthorized_denied",
                generated_at=self.generated_at,
            )
            response = self._response(command, authorized=False, text=UNAUTHORIZED_DENIAL)
        elif command == "/start" and not operator_language_is_selected(self.state):
            self.state = record_telegram_operator_control_command(
                self.state,
                command=command,
                operator_user_id=user_id,
                authorized=True,
                command_status="operator_language_selection_prompted",
                generated_at=self.generated_at,
            )
            response = self._response(
                command,
                authorized=True,
                text=render_language_selection_prompt(),
                keyboard=build_language_selection_keyboard(),
            )
        elif command == "/language" and requested_language:
            self.state = set_telegram_operator_language(
                self.state,
                operator_user_id=user_id,
                language=requested_language,
                generated_at=self.generated_at,
            )
            response = self._response(
                command,
                authorized=True,
                text=render_language_selected(requested_language),
                keyboard=self._keyboard_for_language(requested_language),
            )
        elif command == "/language":
            self.state = record_telegram_operator_control_command(
                self.state,
                command=command,
                operator_user_id=user_id,
                authorized=True,
                command_status="operator_language_selection_prompted",
                generated_at=self.generated_at,
            )
            response = self._response(
                command,
                authorized=True,
                text=render_language_selection_prompt(),
                keyboard=build_language_selection_keyboard(),
            )
        elif command == "/pause":
            self.state = request_telegram_operator_pause(
                self.state,
                operator_user_id=user_id,
                generated_at=self.generated_at,
            )
            response = self._response(
                command,
                authorized=True,
                text=self._render_pause(),
                keyboard=self._keyboard_for_command(command),
            )
        elif command == "/kill":
            self.state = request_telegram_operator_kill_switch(
                self.state,
                operator_user_id=user_id,
                generated_at=self.generated_at,
            )
            response = self._response(
                command,
                authorized=True,
                text=self._render_kill(),
                keyboard=self._keyboard_for_command(command),
            )
        else:
            self.state = record_telegram_operator_control_command(
                self.state,
                command=command,
                operator_user_id=user_id,
                authorized=True,
                command_status="rendered_review_only_response",
                generated_at=self.generated_at,
            )
            response = self._response(
                command,
                authorized=True,
                text=self._render_command(command),
                keyboard=self._keyboard_for_command(command),
            )
        if self.transport is not None:
            self.transport.send_message(chat_id if chat_id is not None else user_id, response.text)
        return response

    def _response(
        self,
        command: str,
        *,
        authorized: bool,
        text: str,
        keyboard: TelegramOperatorKeyboard | None = None,
    ) -> TelegramOperatorControlResponse:
        summary = build_telegram_operator_control_summary(
            config=self.config,
            state=self.state,
            context=self.context,
            generated_at=self.generated_at,
        )
        return TelegramOperatorControlResponse(
            command=command,
            authorized=authorized,
            text=text,
            state=self.state,
            summary=summary,
            keyboard=keyboard or TelegramOperatorKeyboard(),
        )

    def _render_command(self, command: str) -> str:
        renderers = {
            "/start": self._render_start,
            "/help": self._render_help,
            "/status": self._render_status,
            "/btc": self._render_btc,
            "/intent": self._render_intent,
            "/risk": self._render_risk,
            "/auth": self._render_auth,
            "/order": self._render_order,
            "/gonogo": self._render_gonogo,
            "/evidence": self._render_evidence,
            "/blockers": self._render_blockers,
            "/panel": self._render_panel,
            "/language": render_language_selection_prompt,
        }
        return renderers.get(command, self._render_help)()

    def _render_start(self) -> str:
        return render_home(self._language())

    def _render_help(self) -> str:
        commands = "\n".join(f"{command}" for command in SUPPORTED_COMMANDS)
        if self._language() == "ru":
            return (
                "PMBOT команды оператора:\n"
                f"{commands}\n"
                "Безопасные кнопки: Статус, Go/No-Go, Риски, Блокеры, Evidence, Mini App, Пауза, Kill-switch, Язык.\n"
                "Ограничения: только обзор, бумажный/dry-run режим, live-торговля выключена, ордера выключены, "
                "кошелёк/подпись выключены, authenticated endpoints выключены, фонового исполнения нет."
            )
        return (
            "PMBOT Operator Control commands:\n"
            f"{commands}\n"
            "Safe controls: Status, Go/No-Go, Risk, Blockers, Evidence, Panel, Pause, Kill, Language.\n"
            "Safety limits: review-only, paper/dry-run visibility only, no live trading, no order submission, "
            "no wallet access, no signing, no authenticated endpoint calls, no background execution."
        )

    def _render_status(self) -> str:
        summary = self._summary()
        gonogo = dict(summary.get("gonogo_summary", {}))
        paper_canary = dict(summary.get("paper_canary_drill_status_summary", {}))
        paper_loop = dict(summary.get("paper_trading_loop_status_summary", {}))
        public_market_loop = dict(summary.get("public_market_paper_loop_status_summary", {}))
        state = dict(summary.get("state_summary", {}))
        if self._language() == "ru":
            return "\n".join(
                [
                    "Статус PMBOT: только обзор / live-торговля выключена",
                    f"Paper canary: {clean_text(paper_canary.get('status') or 'not_available')}",
                    f"Paper canary market: {clean_text(paper_canary.get('market') or 'not_available')}",
                    f"Paper trading loop: {clean_text(paper_loop.get('status') or 'not_available')}",
                    f"Paper trading risk: {clean_text(paper_loop.get('risk_decision') or 'not_available')}",
                    f"Paper trading intent: {clean_text(paper_loop.get('paper_intent_status') or 'not_available')}",
                    f"Public market paper loop: {clean_text(public_market_loop.get('status') or 'not_available')}",
                    f"Public market source: {clean_text(public_market_loop.get('source') or 'not_available')}",
                    f"Public market evidence: {clean_text(public_market_loop.get('evidence_pack_path') or 'not_available')}",
                    f"Go/No-Go: {clean_text(gonogo.get('overall_decision') or gonogo.get('status') or 'NO_GO')}",
                    "allowed_for_live: false",
                    "canary_executable_now: false",
                    "live_execution_approved: false",
                    "real_execution_available: false",
                    "live_connector_enabled: false",
                    f"Пауза: {str(state.get('operator_pause_requested') is True).lower()}",
                    f"Kill-switch: {str(state.get('operator_kill_switch_requested') is True).lower()}",
                ]
            )
        return "\n".join(
            [
                "PMBOT status: review-only / live blocked",
                f"Paper canary: {clean_text(paper_canary.get('status') or 'not_available')}",
                f"Paper canary market: {clean_text(paper_canary.get('market') or 'not_available')}",
                f"Paper trading loop: {clean_text(paper_loop.get('status') or 'not_available')}",
                f"Paper trading risk: {clean_text(paper_loop.get('risk_decision') or 'not_available')}",
                f"Paper trading intent: {clean_text(paper_loop.get('paper_intent_status') or 'not_available')}",
                f"Public market paper loop: {clean_text(public_market_loop.get('status') or 'not_available')}",
                f"Public market source: {clean_text(public_market_loop.get('source') or 'not_available')}",
                f"Public market evidence: {clean_text(public_market_loop.get('evidence_pack_path') or 'not_available')}",
                f"Go/no-go: {clean_text(gonogo.get('overall_decision') or gonogo.get('status') or 'NO_GO')}",
                "allowed_for_live: false",
                "canary_executable_now: false",
                "live_execution_approved: false",
                "real_execution_available: false",
                "live_connector_enabled: false",
                f"operator_pause_requested: {str(state.get('operator_pause_requested') is True).lower()}",
                f"operator_kill_switch_requested: {str(state.get('operator_kill_switch_requested') is True).lower()}",
            ]
        )

    def _render_btc(self) -> str:
        btc = dict(self._summary().get("btc_market_summary", {}))
        if not any(clean_text(btc.get(key)) for key in ("market_id", "market_slug", "market_title")):
            return (
                "BTC market snapshot: no saved BTC market snapshot is available in this context. "
                "No live market values are invented."
            )
        return "\n".join(
            [
                "BTC market snapshot: saved read-only artifact/fixture",
                f"Market: {clean_text(btc.get('market_slug') or btc.get('market_id')) or 'not_available'}",
                f"Status: {clean_text(btc.get('market_status') or 'not_available')}",
                f"BTC related: {str(btc.get('is_btc_related') is True).lower()}",
                f"Stale: {str(btc.get('stale') is True).lower()}",
                f"Best bid: {_display_known_value(btc.get('best_bid'))}",
                f"Best ask: {_display_known_value(btc.get('best_ask'))}",
                f"Last price: {_display_known_value(btc.get('last_price'))}",
                "Read-only: true; no live market value is fetched by this bot.",
            ]
        )

    def _render_intent(self) -> str:
        intent = dict(self._summary().get("btc_analysis_order_intent_summary", {}))
        return "\n".join(
            [
                "BTC dry-run order intent: dry-run only",
                f"Analysis status: {clean_text(intent.get('btc_market_analysis_status') or 'not_available')}",
                f"Intent status: {clean_text(intent.get('dry_run_order_intent_status') or 'not_available')}",
                f"Market: {clean_text(intent.get('intent_market_slug') or intent.get('intent_market_id') or 'not_available')}",
                f"Notional USD: {_display_known_value(intent.get('intent_notional_usd'))}",
                f"Limit price: {_display_known_value(intent.get('intent_limit_price'))}",
                f"Risk decision: {clean_text(intent.get('risk_decision_status') or 'not_available')}",
                "order_intent_is_not_order_submission: true",
                "allowed_for_live: false",
            ]
        )

    def _render_risk(self) -> str:
        risk = dict(self._summary().get("risk_summary", {}))
        if self._language() == "ru":
            return "\n".join(
                [
                    "Риски: только обзор",
                    f"Макс. размер ордера USD: {_display_known_value(risk.get('max_order_notional_usd'))}",
                    f"Макс. дневной убыток USD: {_display_known_value(risk.get('max_daily_loss_usd'))}",
                    f"Макс. общий exposure USD: {_display_known_value(risk.get('max_total_exposure_usd'))}",
                    f"Макс. market exposure USD: {_display_known_value(risk.get('max_market_exposure_usd'))}",
                    f"Макс. активных рынков: {_display_known_value(risk.get('max_active_markets') or risk.get('max_market_count'))}",
                    f"Макс. сделок/день: {_display_known_value(risk.get('max_trades_per_day'))}",
                    "allowed_for_live: false",
                ]
            )
        return "\n".join(
            [
                "Risk limits summary: review visibility only",
                f"Max order notional USD: {_display_known_value(risk.get('max_order_notional_usd'))}",
                f"Max daily loss USD: {_display_known_value(risk.get('max_daily_loss_usd'))}",
                f"Max total exposure USD: {_display_known_value(risk.get('max_total_exposure_usd'))}",
                f"Max market exposure USD: {_display_known_value(risk.get('max_market_exposure_usd'))}",
                f"Max active markets: {_display_known_value(risk.get('max_active_markets') or risk.get('max_market_count'))}",
                f"Max trades/day: {_display_known_value(risk.get('max_trades_per_day'))}",
                "allowed_for_live: false",
            ]
        )

    def _render_auth(self) -> str:
        summary = self._summary()
        config = dict(summary.get("config", {}))
        auth = dict(summary.get("live_credentials_auth_boundary_summary", {}))
        return "\n".join(
            [
                "Auth boundary: redacted/missing states only",
                f"Telegram bot token: {clean_text(config.get('telegram_bot_token_status') or 'missing')}",
                f"Allowed operator IDs configured: {str(config.get('allowed_operator_ids_configured') is True).lower()}",
                f"Allowed operator ID count: {int(config.get('allowed_operator_id_count', 0) or 0)}",
                f"Live credentials configured: {str(auth.get('live_credentials_configured') is True).lower()}",
                f"Missing live credentials: {int(auth.get('missing_credentials_count', 0) or 0)}",
                "secrets_redacted: true",
                "actual_secret_values_exposed: false",
                "authenticated_endpoints_enabled: false",
                "signing_enabled: false",
                "wallet_signing_enabled: false",
                "order_submission_enabled: false",
            ]
        )

    def _render_order(self) -> str:
        order = dict(self._summary().get("live_order_submission_boundary_summary", {}))
        return "\n".join(
            [
                "Live order submission boundary: disabled",
                f"Boundary status: {clean_text(order.get('status') or 'not_available')}",
                "order_submission_enabled: false",
                "would_submit_order: false",
                "authenticated_endpoint_enabled: false",
                "signing_enabled: false",
                "wallet_enabled: false",
                "allowed_for_live: false",
                "receipt_is_not_order_submission: true",
            ]
        )

    def _render_gonogo(self) -> str:
        gonogo = dict(self._summary().get("gonogo_summary", {}))
        reasons = _clean_list(gonogo.get("top_no_go_reasons"))[:5]
        if self._language() == "ru":
            lines = [
                "Go/No-Go: только обзор, решение NO-GO",
                f"Статус: {clean_text(gonogo.get('status') or 'NO_GO_UNRESOLVED_BLOCKERS')}",
                f"Итог: {clean_text(gonogo.get('overall_decision') or 'NO_GO')}",
                f"Нерешённые блокеры: {int(gonogo.get('unresolved_blocker_count', 0) or 0)}",
                f"Решённые блокеры: {int(gonogo.get('resolved_blocker_count', 0) or 0)}",
                "canary_executable_now: false",
                "live_execution_approved: false",
            ]
        else:
            lines = [
                "Final go/no-go: review-only NO-GO",
                f"Status: {clean_text(gonogo.get('status') or 'NO_GO_UNRESOLVED_BLOCKERS')}",
                f"Overall decision: {clean_text(gonogo.get('overall_decision') or 'NO_GO')}",
                f"Unresolved blockers: {int(gonogo.get('unresolved_blocker_count', 0) or 0)}",
                f"Resolved blockers: {int(gonogo.get('resolved_blocker_count', 0) or 0)}",
                "canary_executable_now: false",
                "live_execution_approved: false",
            ]
        if reasons:
            lines.append("Причины NO-GO:" if self._language() == "ru" else "No-go reasons:")
            lines.extend(bullet_lines(reasons))
        return "\n".join(lines)

    def _render_evidence(self) -> str:
        evidence = dict(self._summary().get("evidence_summary", {}))
        missing = _clean_list(evidence.get("missing_required_evidence"))[:5]
        if self._language() == "ru":
            lines = [
                "Evidence: только обзор",
                f"Статус: {clean_text(evidence.get('readiness_evidence_bundle_status') or evidence.get('status') or 'not_available')}",
                f"Evidence items: {int(evidence.get('evidence_item_count', 0) or 0)}",
                f"Недостающие evidence: {int(evidence.get('missing_required_evidence_count', 0) or 0)}",
                "readiness_evidence_bundle_is_not_live_approval: true",
                "execution_enabling: false",
            ]
        else:
            lines = [
                "Readiness evidence bundle: review-only",
                f"Status: {clean_text(evidence.get('readiness_evidence_bundle_status') or evidence.get('status') or 'not_available')}",
                f"Evidence items: {int(evidence.get('evidence_item_count', 0) or 0)}",
                f"Missing required evidence: {int(evidence.get('missing_required_evidence_count', 0) or 0)}",
                "readiness_evidence_bundle_is_not_live_approval: true",
                "execution_enabling: false",
            ]
        if missing:
            lines.append("Недостающие evidence:" if self._language() == "ru" else "Missing evidence:")
            lines.extend(bullet_lines(missing))
        return "\n".join(lines)

    def _render_blockers(self) -> str:
        blockers = dict(self._summary().get("blocker_summary", {}))
        reasons = _top_blocker_reasons(blockers)[:5]
        if self._language() == "ru":
            lines = [
                "Блокеры live-режима: не решены",
                f"Нерешённые блокеры: {int(blockers.get('unresolved_blockers', blockers.get('unresolved_blocker_count', 0)) or 0)}",
                f"Решённые блокеры: {int(blockers.get('resolved_blockers', blockers.get('resolved_blocker_count', 0)) or 0)}",
                "resolved_blocker_count остаётся 0 для live-блокеров.",
                "canary_executable_now: false",
            ]
        else:
            lines = [
                "Live blockers: unresolved",
                f"Unresolved blocker count: {int(blockers.get('unresolved_blockers', blockers.get('unresolved_blocker_count', 0)) or 0)}",
                f"Resolved blocker count: {int(blockers.get('resolved_blockers', blockers.get('resolved_blocker_count', 0)) or 0)}",
                "resolved_blocker_count remains 0 for live blockers.",
                "canary_executable_now: false",
            ]
        if reasons:
            lines.append("Главные причины блокировки:" if self._language() == "ru" else "Top blocker reasons:")
            lines.extend(bullet_lines(reasons))
        return "\n".join(lines)

    def _render_panel(self) -> str:
        panel = dict(self._summary().get("telegram_mini_app_operator_panel_summary", {}))
        if self._language() == "ru":
            return "\n".join(
                [
                    "Telegram Mini App Operator Panel v1: только обзор / live-режим выключен",
                    f"Panel artifact доступен: {str(panel.get('panel_artifact_available') is True).lower()}",
                    f"HTML artifact: {clean_text(panel.get('latest_telegram_mini_app_operator_panel_html_path') or 'not_available')}",
                    f"JSON artifact: {clean_text(panel.get('latest_telegram_mini_app_operator_panel_json_path') or 'not_available')}",
                    f"Mini App URL status: {clean_text(panel.get('mini_app_url_status') or 'not_configured_review_placeholder')}",
                    f"Telegram init data status: {clean_text(panel.get('telegram_init_data_status') or 'not_configured_redacted')}",
                    "review_only: true",
                    "live_actions_available: false",
                    "raw_telegram_bot_token_exposed: false",
                    "raw_telegram_init_data_exposed: false",
                    "raw_operator_user_ids_exposed: false",
                    "Live-ордера из бота или Mini App недоступны.",
                ]
            )
        return "\n".join(
            [
                "Telegram Mini App Operator Panel v1: review-only / live blocked",
                f"Panel artifact available: {str(panel.get('panel_artifact_available') is True).lower()}",
                f"HTML artifact: {clean_text(panel.get('latest_telegram_mini_app_operator_panel_html_path') or 'not_available')}",
                f"JSON artifact: {clean_text(panel.get('latest_telegram_mini_app_operator_panel_json_path') or 'not_available')}",
                f"Mini App URL status: {clean_text(panel.get('mini_app_url_status') or 'not_configured_review_placeholder')}",
                f"Telegram init data status: {clean_text(panel.get('telegram_init_data_status') or 'not_configured_redacted')}",
                "review_only: true",
                "live_actions_available: false",
                "raw_telegram_bot_token_exposed: false",
                "raw_telegram_init_data_exposed: false",
                "raw_operator_user_ids_exposed: false",
                "No live order action is available from this bot or panel.",
            ]
        )

    def _render_pause(self) -> str:
        if self._language() == "ru":
            return (
                "Пауза записана только как локальный маркер Telegram operator-control state. "
                "Live-исполнения здесь нет, торговое исполнение не изменялось."
            )
        return (
            "Pause marker recorded in local Telegram operator-control state only. "
            "No live execution path exists here and no trading execution was modified."
        )

    def _render_kill(self) -> str:
        if self._language() == "ru":
            return (
                "Kill-switch записан только как локальный маркер Telegram operator-control state. "
                "Отмена ордеров, действия с кошельком, подпись, authenticated call и live-исполнение не выполнялись."
            )
        return (
            "Kill-switch marker recorded in local Telegram operator-control state only. "
            "No order cancellation, wallet action, signing, authenticated call, or live execution was performed."
        )

    def _summary(self) -> dict[str, Any]:
        return build_telegram_operator_control_summary(
            config=self.config,
            state=self.state,
            context=self.context,
            generated_at=self.generated_at,
        )

    def _keyboard_for_command(self, command: str) -> TelegramOperatorKeyboard:
        if command == "/panel":
            return build_panel_fallback_keyboard(self._language())
        if command == "/language":
            return build_language_selection_keyboard()
        if command in SUPPORTED_COMMANDS:
            return build_operator_home_keyboard(self._language())
        return TelegramOperatorKeyboard()

    def _keyboard_for_language(self, language: str) -> TelegramOperatorKeyboard:
        return build_operator_home_keyboard(language)

    def _language(self) -> str:
        return operator_language_from_state(self.state, fallback=DEFAULT_OPERATOR_LANGUAGE)


def build_operator_home_keyboard(language: str = DEFAULT_OPERATOR_LANGUAGE) -> TelegramOperatorKeyboard:
    return _keyboard_from_rows(HOME_BUTTON_ROWS_BY_LANGUAGE[normalize_operator_language(language, fallback="en")])


def build_panel_fallback_keyboard(language: str = DEFAULT_OPERATOR_LANGUAGE) -> TelegramOperatorKeyboard:
    return _keyboard_from_rows(PANEL_FALLBACK_BUTTON_ROWS_BY_LANGUAGE[normalize_operator_language(language, fallback="en")])


def build_language_selection_keyboard() -> TelegramOperatorKeyboard:
    return _keyboard_from_rows(LANGUAGE_SELECTION_BUTTON_ROWS)


def telegram_callback_to_command(callback_data: str) -> str:
    return CALLBACK_COMMAND_MAP.get(clean_text(callback_data), "")


def telegram_button_label_to_command(label: str) -> str:
    normalized = clean_text(label).lower()
    for row in all_button_rows():
        for button_label, callback_data in row:
            if clean_text(button_label).lower() == normalized:
                return telegram_callback_to_command(callback_data)
    return ""


def is_safe_operator_button_label(label: str) -> bool:
    normalized = clean_text(label).upper()
    return bool(normalized) and not any(term in normalized for term in FORBIDDEN_BUTTON_LABEL_TERMS)


def _keyboard_from_rows(rows: Sequence[Sequence[tuple[str, str]]]) -> TelegramOperatorKeyboard:
    keyboard_rows: list[tuple[TelegramOperatorButton, ...]] = []
    for row in rows:
        keyboard_row: list[TelegramOperatorButton] = []
        for label, callback_data in row:
            if not is_safe_operator_button_label(label):
                raise ValueError(f"unsafe Telegram operator button label: {label}")
            command = telegram_callback_to_command(callback_data)
            keyboard_row.append(
                TelegramOperatorButton(
                    label=label,
                    callback_data=callback_data,
                    command=command,
                )
            )
        keyboard_rows.append(tuple(keyboard_row))
    return TelegramOperatorKeyboard(rows=tuple(keyboard_rows))


def config_from_mapping(value: Mapping[str, Any] | None = None) -> TelegramOperatorControlConfig:
    data = dict(value or {})
    allowed = data.get("allowed_operator_user_ids", ())
    if isinstance(allowed, str):
        allowed_values = tuple(item.strip() for item in allowed.split(",") if item.strip())
    elif isinstance(allowed, Sequence):
        allowed_values = tuple(clean_text(item) for item in allowed if clean_text(item))
    else:
        allowed_values = ()
    return TelegramOperatorControlConfig(
        telegram_bot_configured=(
            data.get("telegram_bot_configured") is True
            or clean_text(data.get("telegram_bot_token_status")) == "configured_redacted"
            or data.get("token_present") is True
        ),
        allowed_operator_user_ids=allowed_values,
        bot_name=clean_text(data.get("bot_name")) or "PMBOT Operator Control Bot v1",
        token_status=clean_text(data.get("telegram_bot_token_status") or data.get("token_status") or "missing"),
        generated_at=clean_text(data.get("generated_at")) or GENERATED_AT,
    )


def build_telegram_operator_control_config(
    *,
    telegram_bot_configured: bool = False,
    allowed_operator_user_ids: Sequence[Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    config = TelegramOperatorControlConfig(
        telegram_bot_configured=telegram_bot_configured,
        allowed_operator_user_ids=tuple(clean_text(item) for item in (allowed_operator_user_ids or ()) if clean_text(item)),
        generated_at=generated_at,
    )
    return config.to_redacted_dict()


def build_telegram_operator_control_summary(
    *,
    config: TelegramOperatorControlConfig | Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    context: Mapping[str, Any] | None = None,
    latest_state_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    config_mapping = dict(config or {}) if isinstance(config, Mapping) else {}
    config_obj = config if isinstance(config, TelegramOperatorControlConfig) else config_from_mapping(config_mapping)
    context_value = dict(context or {})
    state_value = dict(state or context_value.get("telegram_operator_control_state") or {})
    if not state_value:
        state_value = build_telegram_operator_control_state(generated_at=generated_at)
    if config_mapping.get("contract_version") == TELEGRAM_OPERATOR_CONTROL_CONFIG_CONTRACT:
        config_summary = dict(config_mapping)
        config_summary["validation"] = validate_secret_boundary_telegram_operator_control_config(
            config_summary,
            generated_at=generated_at,
        )
    else:
        config_summary = config_obj.to_redacted_dict()
    state_summary = summarize_telegram_operator_control_state(
        state_value,
        latest_state_path=latest_state_path
        or clean_text(context_value.get("latest_telegram_operator_control_state_path")),
        generated_at=generated_at,
    )
    btc = _first_mapping(
        context_value.get("btc_market_summary"),
        context_value.get("btc_market_snapshot_summary"),
        context_value.get("btc_read_only_connector_summary"),
        context_value.get("btc_market_section_feed"),
    )
    intent = _first_mapping(
        context_value.get("btc_analysis_order_intent_summary"),
        context_value.get("btc_order_intent_dry_run_summary"),
        context_value.get("btc_analysis_order_intent_section_feed"),
    )
    risk = _first_mapping(
        context_value.get("risk_control_plane_summary"),
        context_value.get("default_risk_limit_policy_summary"),
        context_value.get("risk_limit_policy"),
        context_value.get("risk_limit_panel_feed"),
    )
    auth = _first_mapping(
        context_value.get("live_credentials_auth_boundary_summary"),
        context_value.get("live_credentials_auth_boundary_section_feed"),
    )
    order = _first_mapping(
        context_value.get("live_order_submission_boundary_summary"),
        context_value.get("live_order_submission_boundary_section_feed"),
    )
    gonogo = _first_mapping(
        context_value.get("tiny_live_canary_gonogo_gate_summary"),
        context_value.get("tiny_live_canary_gonogo_gate"),
    )
    evidence = _first_mapping(
        context_value.get("readiness_evidence_bundle_summary"),
        context_value.get("evidence_summary"),
        context_value.get("readiness_evidence_bundle"),
    )
    paper_canary = _first_mapping(
        context_value.get("paper_canary_drill_status_summary"),
        context_value.get("paper_canary_drill_status"),
        context_value.get("latest_paper_canary_status"),
    )
    paper_loop = _first_mapping(
        context_value.get("paper_trading_loop_status_summary"),
        context_value.get("paper_trading_loop_status"),
        context_value.get("latest_paper_trading_status"),
    )
    public_market_loop = _first_mapping(
        context_value.get("public_market_paper_loop_status_summary"),
        context_value.get("public_market_paper_loop_status"),
        context_value.get("latest_public_market_paper_status"),
    )
    mini_panel = _first_mapping(
        context_value.get("telegram_mini_app_operator_panel_summary"),
        context_value.get("telegram_mini_app_operator_panel"),
    )
    blockers = _first_mapping(
        context_value.get("blocker_summary"),
        context_value.get("live_connector_blocker_matrix"),
        context_value.get("live_canary_readiness_summary"),
    )
    summary = {
        "contract_version": TELEGRAM_OPERATOR_CONTROL_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "telegram-operator-control-summary-043",
            {
                "config": config_summary,
                "state_id": state_value.get("state_id"),
                "gonogo": gonogo,
                "evidence": evidence,
                "blockers": blockers,
                "public_market_loop": public_market_loop,
            },
        ),
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "bot_name": config_summary.get("bot_name"),
        "configured": config_summary.get("telegram_bot_configured") is True,
        "allowed_operator_ids_configured": config_summary.get("allowed_operator_ids_configured") is True,
        "allowed_operator_id_count": int(config_summary.get("allowed_operator_id_count", 0) or 0),
        "config": config_summary,
        "state_summary": state_summary,
        "operator_pause_requested": state_summary.get("operator_pause_requested") is True,
        "operator_kill_switch_requested": state_summary.get("operator_kill_switch_requested") is True,
        "operator_language": clean_text(state_summary.get("operator_language")),
        "operator_language_selected": state_summary.get("operator_language_selected") is True,
        "operator_language_scope": "global_local_operator_state",
        "btc_market_summary": btc,
        "btc_analysis_order_intent_summary": intent,
        "risk_summary": risk,
        "live_credentials_auth_boundary_summary": auth,
        "live_order_submission_boundary_summary": order,
        "gonogo_summary": gonogo,
        "evidence_summary": evidence,
        "paper_canary_drill_status_summary": _normalize_paper_canary_summary(paper_canary),
        "paper_trading_loop_status_summary": _normalize_paper_trading_loop_summary(paper_loop),
        "public_market_paper_loop_status_summary": _normalize_public_market_paper_loop_summary(public_market_loop),
        "telegram_mini_app_operator_panel_summary": mini_panel,
        "blocker_summary": _normalize_blocker_summary(blockers),
        "review_only": True,
        "telegram_operator_control_bot_section_ready": True,
        "execution_enabling": False,
        "live_approval": False,
        "no_executable_live_action": True,
        "raw_telegram_bot_token_exposed": False,
        "raw_operator_user_ids_exposed": False,
    }
    summary.update(_control_safety_flags())
    summary["validation"] = validate_telegram_operator_control_summary(summary, generated_at=generated_at)
    return summary


def validate_telegram_operator_control_summary(
    summary: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    value = dict(summary)
    if value.get("contract_version") != TELEGRAM_OPERATOR_CONTROL_SUMMARY_CONTRACT:
        errors.append(f"contract_version must be {TELEGRAM_OPERATOR_CONTROL_SUMMARY_CONTRACT}")
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
    if value.get("execution_enabling") is not False:
        errors.append("execution_enabling must be false")
    if value.get("live_approval") is not False:
        errors.append("live_approval must be false")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
    secret_validation = validate_secret_boundary_telegram_operator_control_summary(value, generated_at=generated_at)
    if secret_validation.get("valid") is not True:
        errors.append("telegram operator control summary violates static secret boundary")
    valid = not errors
    return {
        "contract_version": "pmbot_telegram_operator_control_summary_validation.v1",
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        "secret_boundary_validation": secret_validation,
        **_control_safety_flags(),
    }


def _normalize_blocker_summary(blockers: Mapping[str, Any]) -> dict[str, Any]:
    rows = [dict(row) for row in mapping_rows(blockers.get("blockers"))]
    unresolved = [row for row in rows if clean_text(row.get("resolution_status")) != "resolved"]
    resolved = [row for row in rows if clean_text(row.get("resolution_status")) == "resolved"]
    unresolved_count = _int_first(
        blockers.get("unresolved_blockers"),
        blockers.get("unresolved_blocker_count"),
        blockers.get("unresolved_live_connector_blocker_count"),
        len(unresolved),
    )
    resolved_count = _int_first(
        blockers.get("resolved_blockers"),
        blockers.get("resolved_blocker_count"),
        blockers.get("resolved_live_connector_blocker_count"),
        len(resolved),
    )
    return dict(blockers) | {
        "unresolved_blockers": unresolved_count,
        "resolved_blockers": resolved_count,
        "unresolved_blocker_count": unresolved_count,
        "resolved_blocker_count": resolved_count,
        "top_blocker_reasons": _top_blocker_reasons(blockers),
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def _normalize_paper_canary_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or "not_available"),
        "mode": clean_text(value.get("mode") or "paper / review-only"),
        "live_execution": clean_text(value.get("live_execution") or "blocked"),
        "overall_decision": clean_text(value.get("overall_decision") or "NO_GO"),
        "artifact": clean_text(value.get("artifact")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "review_only": True,
        "execution_enabling": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _normalize_paper_trading_loop_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or value.get("market_symbol") or "not_available"),
        "strategy_name": clean_text(value.get("strategy_name") or "not_available"),
        "mode": clean_text(value.get("mode") or "paper / review-only"),
        "live_execution": clean_text(value.get("live_execution") or "blocked"),
        "live_execution_blocked": True,
        "signal_status": clean_text(value.get("signal_status") or "not_available"),
        "risk_decision": clean_text(value.get("risk_decision") or "not_available"),
        "paper_intent_status": clean_text(value.get("paper_intent_status") or "no_paper_intent"),
        "paper_intent_summary": clean_text(value.get("paper_intent_summary")),
        "artifact": clean_text(value.get("artifact_path") or value.get("artifact")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "review_only": True,
        "execution_enabling": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _normalize_public_market_paper_loop_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or value.get("market_symbol") or "not_available"),
        "strategy_name": clean_text(value.get("strategy_name") or "not_available"),
        "source": clean_text(value.get("source") or "not_available"),
        "source_type": clean_text(value.get("source_type") or "not_available"),
        "mode": clean_text(value.get("mode") or "paper / review-only"),
        "live_execution": clean_text(value.get("live_execution") or "blocked"),
        "live_execution_blocked": True,
        "evidence_pack_path": clean_text(value.get("evidence_pack_path")),
        "risk_decision": clean_text(value.get("risk_decision") or "not_available"),
        "paper_intent_status": clean_text(value.get("paper_intent_status") or "no_paper_intent"),
        "paper_intent_summary": clean_text(value.get("paper_intent_summary")),
        "artifact": clean_text(value.get("artifact_path") or value.get("artifact")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "review_only": True,
        "execution_enabling": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "auth_used": False,
        "credentials_used": False,
        "wallet_used": False,
        "signing_used": False,
        "order_endpoint_used": False,
    }


def _top_blocker_reasons(blockers: Mapping[str, Any]) -> list[str]:
    direct = _clean_list(blockers.get("top_blocker_reasons") or blockers.get("why_live_execution_is_blocked"))
    if direct:
        return direct
    rows = [dict(row) for row in mapping_rows(blockers.get("top_blockers") or blockers.get("blockers"))]
    return _clean_list(
        row.get("reason") or row.get("why_it_blocks_live_execution") or row.get("blocker_name") or row.get("message")
        for row in rows
    )


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


def _display_known_value(value: Any) -> str:
    if value is None or value == "":
        return "not_available"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return clean_text(value)


def _int_first(*values: Any) -> int:
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _control_safety_flags() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "execution_enabling": False,
        "network_used": False,
        "external_api_calls_performed": False,
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
        "autonomous_live_trading_added": False,
        "browser_automation_added": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _hash_identifier(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    return "telegram-chat-sha256:" + hashlib.sha256(f"pmbot-telegram-chat:{text}".encode("utf-8")).hexdigest()


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
