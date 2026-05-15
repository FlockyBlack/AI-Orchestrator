from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol, Sequence

from pm_bot.operator_runner.telegram_operator_i18n import (
    DEFAULT_OPERATOR_LANGUAGE,
    HOME_BUTTON_ROWS_BY_LANGUAGE,
    LANGUAGE_SELECTION_BUTTON_ROWS,
    PANEL_FALLBACK_BUTTON_ROWS_BY_LANGUAGE,
    all_button_rows,
    connection_status_button_rows,
    credentials_readiness_review_label,
    language_from_command_text,
    normalize_operator_language,
    operator_console_button_rows,
    operator_language_from_state,
    operator_language_is_selected,
    pre_live_gate_review_label,
    render_home,
    render_language_selected,
    render_language_selection_prompt,
    supervised_live_enablement_review_label,
    tiny_order_review_label,
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
from pm_bot.operator_runner.telegram_status_registry import (
    SAFE_ACTIONS,
    execute_safe_telegram_operator_action,
    safe_action_by_id,
    safe_action_command_for_callback,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, mapping_rows
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_telegram_operator_control_config,
    validate_secret_boundary_telegram_operator_control_summary,
)
from pm_bot.trading_core.telegram_wallet_auth_status_dashboard import render_telegram_wallet_auth_status_text

TELEGRAM_OPERATOR_CONTROL_BOT_CONTRACT = "pmbot_telegram_operator_control_bot.v1"
TELEGRAM_OPERATOR_CONTROL_CONFIG_CONTRACT = "pmbot_telegram_operator_control_config.v1"
TELEGRAM_OPERATOR_CONTROL_RESPONSE_CONTRACT = "pmbot_telegram_operator_control_response.v1"
TELEGRAM_OPERATOR_CONTROL_SUMMARY_CONTRACT = "pmbot_telegram_operator_control_summary.v1"
TELEGRAM_OPERATOR_BUTTON_CONTRACT = "pmbot_telegram_operator_button.v1"
TELEGRAM_OPERATOR_KEYBOARD_CONTRACT = "pmbot_telegram_operator_keyboard.v1"

TASK_ID = "ORCH-PMBOT-TRADING-MVP-043-TELEGRAM-OPERATOR-CONTROL-BOT-V1"
TASK_ID_060T = "ORCH-PMBOT-TELEGRAM-060T-OPERATOR-CONSOLE-FOR-PMBOT-STATUS-AND-DRY-RUNS"
TASK_ID_061T = "ORCH-PMBOT-TELEGRAM-061T-TINY-ORDER-SCAFFOLD-REVIEW-PANEL"
TASK_ID_062T = "ORCH-PMBOT-TELEGRAM-062T-PRE-LIVE-TINY-ORDER-GATE-REVIEW-PANEL"
TASK_ID_063T = "ORCH-PMBOT-TELEGRAM-063T-SUPERVISED-LIVE-ENABLEMENT-REVIEW-PANEL"
TASK_ID_064T = "ORCH-PMBOT-TELEGRAM-064T-CREDENTIALS-READINESS-REVIEW-PANEL"
TASK_ID_067E = "ORCH-PMBOT-TELEGRAM-067E-WALLET-AUTH-STATUS-DASHBOARD-NO-LIVE"

SAFE_ACTION_COMMANDS = tuple(f"/{action.action_id}" for action in SAFE_ACTIONS)

SUPPORTED_COMMANDS = (
    "/start",
    "/help",
    "/status",
    "/connection_status",
    "/btc",
    "/intent",
    "/risk",
    "/auth",
    "/order",
    "/gonogo",
    "/evidence",
    "/blockers",
    "/panel",
    "/readiness",
    "/tiny_order_review",
    "/pre_live_gate_review",
    "/supervised_live_review",
    "/credentials_readiness_review",
    "/language",
    "/pause",
    "/kill",
    *SAFE_ACTION_COMMANDS,
)

CALLBACK_COMMAND_MAP = {
    "pmbot:status": "/status",
    "pmbot:connection_status": "/connection_status",
    "pmbot:home": "/start",
    "pmbot:btc": "/btc",
    "pmbot:intent": "/intent",
    "pmbot:risk": "/risk",
    "pmbot:auth": "/auth",
    "pmbot:order": "/order",
    "pmbot:gonogo": "/gonogo",
    "pmbot:evidence": "/evidence",
    "pmbot:blockers": "/blockers",
    "pmbot:panel": "/panel",
    "pmbot:readiness": "/readiness",
    "pmbot:pre_live_gate_review": "/pre_live_gate_review",
    "pmbot:supervised_live_review": "/supervised_live_review",
    "pmbot:credentials_readiness_review": "/credentials_readiness_review",
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
    "operator_approved",
    "candidate_is_executable",
    "signing_available",
    "signed_payload_available",
    "order_submission_available",
    "wallet_available",
    "ready_for_future_live_enablement",
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "order_cancel_enabled",
    "would_submit_order",
    "authenticated_polymarket_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
    "credential_values_read",
    "credentials_values_read",
    "raw_values_emitted",
    "broad_environment_scan_performed",
    "environment_values_read",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "wallet_signing_enabled",
    "wallet_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
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
        action_runner: Callable[[str], Mapping[str, Any]] | None = None,
        generated_at: str = GENERATED_AT,
    ) -> None:
        self.config = config if isinstance(config, TelegramOperatorControlConfig) else config_from_mapping(config)
        self.context = dict(context or {})
        self.state = dict(state or build_telegram_operator_control_state(generated_at=generated_at))
        self.transport = transport
        self.action_runner = action_runner or (
            lambda action_id: execute_safe_telegram_operator_action(action_id, generated_at=generated_at)
        )
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
        if command in SAFE_ACTION_COMMANDS:
            return self._render_safe_action(command)
        renderers = {
            "/start": self._render_start,
            "/help": self._render_help,
            "/status": self._render_status,
            "/connection_status": self._render_connection_status,
            "/btc": self._render_btc,
            "/intent": self._render_intent,
            "/risk": self._render_risk,
            "/auth": self._render_auth,
            "/order": self._render_order,
            "/gonogo": self._render_gonogo,
            "/evidence": self._render_evidence,
            "/blockers": self._render_blockers,
            "/panel": self._render_panel,
            "/readiness": self._render_readiness,
            "/tiny_order_review": self._render_tiny_order_review,
            "/pre_live_gate_review": self._render_pre_live_gate_review,
            "/supervised_live_review": self._render_supervised_live_review,
            "/credentials_readiness_review": self._render_credentials_readiness_review,
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
        decision_ledger = dict(summary.get("paper_decision_ledger_status_summary", {}))
        live_preflight = dict(summary.get("live_connector_preflight_status_summary", {}))
        authenticated_clob = dict(summary.get("authenticated_clob_preflight_status_summary", {}))
        clob_l2_marker = dict(summary.get("clob_l2_marker_preflight_status_summary", {}))
        no_order_auth_get = dict(summary.get("no_order_auth_get_preflight_status_summary", {}))
        signer_boundary = dict(summary.get("signer_boundary_preflight_status_summary", {}))
        tiny_scaffold = dict(summary.get("tiny_order_scaffold_status_summary", {}))
        pre_live_gate = dict(summary.get("pre_live_tiny_order_gate_status_summary", {}))
        supervised_gate = dict(summary.get("supervised_tiny_live_enablement_gate_status_summary", {}))
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
                    f"Paper decision ledger outcome: {clean_text(decision_ledger.get('last_outcome') or 'not_available')}",
                    f"Paper decision ledger entries: {clean_text(decision_ledger.get('ledger_entry_count') or '0')}",
                    f"Paper decision ledger evidence: {clean_text(decision_ledger.get('evidence_pack_path') or 'not_available')}",
                    f"Live connector preflight: {clean_text(live_preflight.get('status') or 'not_available')}",
                    f"Live preflight public network: {clean_text(live_preflight.get('public_network_status') or 'not_available')}",
                    f"Live preflight auth boundary: {clean_text(live_preflight.get('auth_boundary_status') or 'not_available')}",
                    f"Authenticated CLOB preflight: {clean_text(authenticated_clob.get('status') or 'not_available')}",
                    f"Authenticated CLOB auth presence: {clean_text(authenticated_clob.get('auth_presence_status') or 'not_available')}",
                    f"Authenticated CLOB base URL: {clean_text(authenticated_clob.get('clob_base_url_status') or 'not_available')}",
                    f"CLOB/L2 marker preflight: {clean_text(clob_l2_marker.get('status') or 'not_available')}",
                    f"L2 marker complete: {str(clob_l2_marker.get('l2_marker_set_complete') is True).lower()}",
                    f"Unsafe L2 marker detected: {str(clob_l2_marker.get('unsafe_raw_value_detected') is True).lower()}",
                    f"No-order auth GET 059: {clean_text(no_order_auth_get.get('no_order_auth_get_status') or 'not_available')}",
                    f"No-order auth GET blockers: {int(no_order_auth_get.get('blocker_count', 0) or 0)}",
                    f"Signer boundary 060: {clean_text(signer_boundary.get('status') or 'not_available')}",
                    f"Live candidate intent: {clean_text(signer_boundary.get('live_candidate_intent_status') or 'not_available')}",
                    f"Unsigned plan: {clean_text(signer_boundary.get('unsigned_plan_status') or 'not_available')}",
                    f"Tiny order scaffold 061: {clean_text(tiny_scaffold.get('status') or 'not_available')}",
                    f"Tiny candidate: {clean_text(tiny_scaffold.get('tiny_candidate') or 'not_available')}",
                    f"Approval packet: {clean_text(tiny_scaffold.get('manual_tiny_order_approval_packet_path') or 'not_available')}",
                    f"Предлайв-гейт tiny order: {clean_text(pre_live_gate.get('status') or 'not_available')}",
                    f"Предлайв чеклист: {clean_text(pre_live_gate.get('checklist_path') or 'not_available')}",
                    f"Предлайв блокеры: {int(pre_live_gate.get('blocker_count', 0) or 0)}",
                    f"Предлайв readiness: {clean_text(pre_live_gate.get('readiness_status') or 'blocked')}",
                    f"Обзор supervised readiness 063: {clean_text(supervised_gate.get('status') or 'not_available')}",
                    f"063 чеклист: {clean_text(supervised_gate.get('operator_checklist_path') or 'not_available')}",
                    f"063 блокеры: {int(supervised_gate.get('blocker_count', 0) or 0)}",
                    f"063 env readiness: {clean_text(supervised_gate.get('env_readiness_path') or 'not_available')}",
                    f"063 manual approval packet: {clean_text(supervised_gate.get('manual_approval_packet_path') or 'not_available')}",
                    "Малый ордер",
                    "Пакет ручного подтверждения: "
                    + clean_text(tiny_scaffold.get("approval_packet_path") or "not_available"),
                    "Лимиты: " + _render_hard_limits_inline(tiny_scaffold),
                    "Оператор подтвердил: нет",
                    "Кандидат не исполняемый",
                    "Подписание заблокировано",
                    "Отправка ордера заблокирована",
                    "Live-торговля заблокирована",
                    "Operator approved: false",
                    "Signer blocked: true",
                    "Signed payload unavailable: true",
                    "Order submission blocked: true",
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
                f"Paper decision ledger outcome: {clean_text(decision_ledger.get('last_outcome') or 'not_available')}",
                f"Paper decision ledger entries: {clean_text(decision_ledger.get('ledger_entry_count') or '0')}",
                f"Paper decision ledger evidence: {clean_text(decision_ledger.get('evidence_pack_path') or 'not_available')}",
                f"Live connector preflight: {clean_text(live_preflight.get('status') or 'not_available')}",
                f"Live preflight public network: {clean_text(live_preflight.get('public_network_status') or 'not_available')}",
                f"Live preflight auth boundary: {clean_text(live_preflight.get('auth_boundary_status') or 'not_available')}",
                f"Authenticated CLOB preflight: {clean_text(authenticated_clob.get('status') or 'not_available')}",
                f"Authenticated CLOB auth presence: {clean_text(authenticated_clob.get('auth_presence_status') or 'not_available')}",
                f"Authenticated CLOB base URL: {clean_text(authenticated_clob.get('clob_base_url_status') or 'not_available')}",
                f"CLOB/L2 marker preflight: {clean_text(clob_l2_marker.get('status') or 'not_available')}",
                f"L2 marker complete: {str(clob_l2_marker.get('l2_marker_set_complete') is True).lower()}",
                f"Unsafe L2 marker detected: {str(clob_l2_marker.get('unsafe_raw_value_detected') is True).lower()}",
                f"No-order auth GET 059: {clean_text(no_order_auth_get.get('no_order_auth_get_status') or 'not_available')}",
                f"No-order auth GET blockers: {int(no_order_auth_get.get('blocker_count', 0) or 0)}",
                f"Signer boundary 060: {clean_text(signer_boundary.get('status') or 'not_available')}",
                f"Live candidate intent: {clean_text(signer_boundary.get('live_candidate_intent_status') or 'not_available')}",
                f"Unsigned plan: {clean_text(signer_boundary.get('unsigned_plan_status') or 'not_available')}",
                f"Tiny order scaffold 061: {clean_text(tiny_scaffold.get('status') or 'not_available')}",
                f"Tiny candidate: {clean_text(tiny_scaffold.get('tiny_candidate') or 'not_available')}",
                f"Approval packet: {clean_text(tiny_scaffold.get('manual_tiny_order_approval_packet_path') or 'not_available')}",
                f"Pre-live tiny order gate: {clean_text(pre_live_gate.get('status') or 'not_available')}",
                f"Pre-live checklist: {clean_text(pre_live_gate.get('checklist_path') or 'not_available')}",
                f"Pre-live blockers: {int(pre_live_gate.get('blocker_count', 0) or 0)}",
                f"Pre-live readiness: {clean_text(pre_live_gate.get('readiness_status') or 'blocked')}",
                f"Supervised readiness review 063: {clean_text(supervised_gate.get('status') or 'not_available')}",
                f"063 checklist: {clean_text(supervised_gate.get('operator_checklist_path') or 'not_available')}",
                f"063 blockers: {int(supervised_gate.get('blocker_count', 0) or 0)}",
                f"063 env readiness: {clean_text(supervised_gate.get('env_readiness_path') or 'not_available')}",
                f"063 manual approval packet: {clean_text(supervised_gate.get('manual_approval_packet_path') or 'not_available')}",
                f"Hard limits: {_render_hard_limits_inline(tiny_scaffold)}",
                "Candidate is executable: false",
                "Signing blocked",
                "Live execution blocked",
                "Operator approved: false",
                "Signer blocked: true",
                "Signed payload unavailable: true",
                "Order submission blocked: true",
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
        live_preflight = dict(summary.get("live_connector_preflight_status_summary", {}))
        authenticated_clob = dict(summary.get("authenticated_clob_preflight_status_summary", {}))
        clob_l2_marker = dict(summary.get("clob_l2_marker_preflight_status_summary", {}))
        no_order_auth_get = dict(summary.get("no_order_auth_get_preflight_status_summary", {}))
        signer_boundary = dict(summary.get("signer_boundary_preflight_status_summary", {}))
        return "\n".join(
            [
                "Auth boundary: redacted/missing states only",
                f"Telegram bot token: {clean_text(config.get('telegram_bot_token_status') or 'missing')}",
                f"Allowed operator IDs configured: {str(config.get('allowed_operator_ids_configured') is True).lower()}",
                f"Allowed operator ID count: {int(config.get('allowed_operator_id_count', 0) or 0)}",
                f"Live credentials configured: {str(auth.get('live_credentials_configured') is True).lower()}",
                f"Missing live credentials: {int(auth.get('missing_credentials_count', 0) or 0)}",
                f"Live preflight auth boundary: {clean_text(live_preflight.get('auth_boundary_status') or 'not_available')}",
                f"Authenticated CLOB auth presence: {clean_text(authenticated_clob.get('auth_presence_status') or 'not_available')}",
                f"Authenticated CLOB base URL: {clean_text(authenticated_clob.get('clob_base_url_status') or 'not_available')}",
                f"Authenticated CLOB blockers: {int(authenticated_clob.get('blocker_count', 0) or 0)}",
                f"CLOB/L2 marker preflight: {clean_text(clob_l2_marker.get('status') or 'not_available')}",
                f"L2 markers complete: {str(clob_l2_marker.get('l2_marker_set_complete') is True).lower()}",
                f"Unsafe L2 marker detected: {str(clob_l2_marker.get('unsafe_raw_value_detected') is True).lower()}",
                f"No-order auth GET 059: {clean_text(no_order_auth_get.get('no_order_auth_get_status') or 'not_available')}",
                f"No-order auth GET blockers: {int(no_order_auth_get.get('blocker_count', 0) or 0)}",
                f"Signer boundary 060: {clean_text(signer_boundary.get('status') or 'not_available')}",
                f"Signer status: {clean_text(signer_boundary.get('signer_status') or 'blocked')}",
                f"Signed payload status: {clean_text(signer_boundary.get('signed_payload_status') or 'unavailable')}",
                "secrets_redacted: true",
                "actual_secret_values_exposed: false",
                "authenticated_endpoints_enabled: false",
                "signing_enabled: false",
                "wallet_signing_enabled: false",
                "order_submission_enabled: false",
            ]
        )

    def _render_connection_status(self) -> str:
        status = dict(self._summary().get("telegram_connection_status_067e_status_summary", {}))
        if not status:
            status = {
                "api_keys_display_ru": "не добавлены",
                "api_keys_display_en": "not added",
                "private_key_display_ru": "не добавлен",
                "private_key_display_en": "not added",
                "wallet_display": "missing",
                "signature_type_display": "missing",
                "funder_display": "missing",
                "l2_auth_probe_display": "not run",
                "open_orders_status": "unknown",
                "balance_allowance_status": "unknown",
            }
        return render_telegram_wallet_auth_status_text(status, language=self._language())

    def _render_order(self) -> str:
        order = dict(self._summary().get("live_order_submission_boundary_summary", {}))
        live_preflight = dict(self._summary().get("live_connector_preflight_status_summary", {}))
        authenticated_clob = dict(self._summary().get("authenticated_clob_preflight_status_summary", {}))
        signer_boundary = dict(self._summary().get("signer_boundary_preflight_status_summary", {}))
        tiny_scaffold = dict(self._summary().get("tiny_order_scaffold_status_summary", {}))
        return "\n".join(
            [
                "Live order submission boundary: disabled",
                f"Boundary status: {clean_text(order.get('status') or 'not_available')}",
                f"Preflight status: {clean_text(live_preflight.get('status') or 'not_available')}",
                f"Authenticated CLOB preflight: {clean_text(authenticated_clob.get('status') or 'not_available')}",
                f"Signer boundary 060: {clean_text(signer_boundary.get('status') or 'not_available')}",
                f"Unsigned plan: {clean_text(signer_boundary.get('unsigned_plan_status') or 'not_available')}",
                f"Tiny order scaffold 061: {clean_text(tiny_scaffold.get('status') or 'not_available')}",
                f"Approval packet: {clean_text(tiny_scaffold.get('manual_tiny_order_approval_packet_path') or 'not_available')}",
                "operator_approved: false",
                "candidate_is_executable: false",
                "order_submission_enabled: false",
                "order_submission_blocked: true",
                "order_cancellation_blocked: true",
                "would_submit_order: false",
                "authenticated_endpoint_enabled: false",
                "signing_enabled: false",
                "signing_blocked: true",
                "wallet_enabled: false",
                "balance_read_blocked: true",
                "position_read_blocked: true",
                "live_execution_blocked: true",
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
        live_preflight = dict(self._summary().get("live_connector_preflight_status_summary", {}))
        authenticated_clob = dict(self._summary().get("authenticated_clob_preflight_status_summary", {}))
        clob_l2_marker = dict(self._summary().get("clob_l2_marker_preflight_status_summary", {}))
        no_order_auth_get = dict(self._summary().get("no_order_auth_get_preflight_status_summary", {}))
        signer_boundary = dict(self._summary().get("signer_boundary_preflight_status_summary", {}))
        pre_live_gate = dict(self._summary().get("pre_live_tiny_order_gate_status_summary", {}))
        supervised_gate = dict(self._summary().get("supervised_tiny_live_enablement_gate_status_summary", {}))
        credentials_gate = dict(self._summary().get("explicit_live_credentials_readiness_gate_status_summary", {}))
        reasons = _top_blocker_reasons(blockers)[:5]
        preflight_reasons = _clean_list(live_preflight.get("top_blocker_reasons"))[:5]
        authenticated_clob_reasons = _clean_list(authenticated_clob.get("top_blocker_reasons"))[:5]
        clob_l2_marker_reasons = _clean_list(clob_l2_marker.get("top_blocker_reasons"))[:5]
        no_order_auth_get_reasons = _clean_list(no_order_auth_get.get("top_blocker_reasons"))[:5]
        signer_boundary_reasons = _clean_list(signer_boundary.get("top_blocker_reasons"))[:5]
        pre_live_gate_reasons = _clean_list(pre_live_gate.get("top_blocker_reasons"))[:5]
        supervised_gate_reasons = _clean_list(supervised_gate.get("top_blocker_reasons"))[:5]
        credentials_gate_reasons = _clean_list(credentials_gate.get("top_blocker_reasons"))[:5]
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
        if preflight_reasons:
            lines.append("Live preflight blockers:" if self._language() != "ru" else "Блокеры live preflight:")
            lines.extend(bullet_lines(preflight_reasons))
        if authenticated_clob_reasons:
            lines.append(
                "Authenticated CLOB preflight blockers:"
                if self._language() != "ru"
                else "Блокеры authenticated CLOB preflight:"
            )
            lines.extend(bullet_lines(authenticated_clob_reasons))
        if clob_l2_marker_reasons:
            lines.append(
                "CLOB/L2 marker preflight blockers:"
                if self._language() != "ru"
                else "Блокеры CLOB/L2 marker preflight:"
            )
            lines.extend(bullet_lines(clob_l2_marker_reasons))
        if no_order_auth_get_reasons:
            lines.append(
                "No-order auth GET 059 blockers:"
                if self._language() != "ru"
                else "Блокеры no-order auth GET 059:"
            )
            lines.extend(bullet_lines(no_order_auth_get_reasons))
        if signer_boundary_reasons:
            lines.append(
                "Signer boundary 060 blockers:"
                if self._language() != "ru"
                else "Блокеры signer boundary 060:"
            )
            lines.extend(bullet_lines(signer_boundary_reasons))
        if pre_live_gate_reasons:
            lines.append(
                "Pre-live tiny order gate blockers:"
                if self._language() != "ru"
                else "Блокеры предлайв-гейта tiny order:"
            )
            lines.extend(bullet_lines(pre_live_gate_reasons))
        if supervised_gate_reasons:
            lines.append(
                "Supervised readiness blockers:"
                if self._language() != "ru"
                else "Блокеры supervised readiness:"
            )
            lines.extend(bullet_lines(supervised_gate_reasons))
        if credentials_gate_reasons:
            lines.append(
                "Credentials readiness blockers:"
                if self._language() != "ru"
                else "Блокеры credentials readiness:"
            )
            lines.extend(bullet_lines(credentials_gate_reasons))
        if reasons:
            lines.append("Главные причины блокировки:" if self._language() == "ru" else "Top blocker reasons:")
            lines.extend(bullet_lines(reasons))
        return "\n".join(lines)

    def _render_panel(self) -> str:
        summary = self._summary()
        panel = dict(summary.get("telegram_mini_app_operator_panel_summary", {}))
        readiness = dict(summary.get("telegram_operator_console_readiness_summary", {}))
        latest = dict(summary.get("telegram_operator_console_latest_artifacts", {}))
        tiny_scaffold = dict(summary.get("tiny_order_scaffold_status_summary", {}))
        pre_live_gate = dict(summary.get("pre_live_tiny_order_gate_status_summary", {}))
        supervised_gate = dict(summary.get("supervised_tiny_live_enablement_gate_status_summary", {}))
        credentials_gate = dict(summary.get("explicit_live_credentials_readiness_gate_status_summary", {}))
        available = sum(1 for value in latest.values() if isinstance(value, Mapping) and value.get("available") is True)
        missing = sum(1 for value in latest.values() if isinstance(value, Mapping) and value.get("available") is not True)
        if self._language() == "ru":
            return "\n".join(
                [
                    "Telegram Mini App Operator Panel v1 / PMBOT Operator Console 060T: только обзор / live-режим выключен",
                    "Главное меню",
                    "PMBOT Status",
                    "Paper Runs / Бумажный прогон",
                    "Public Market Evidence / Публичный рынок",
                    "Decision Ledger / Журнал решений",
                    "Live Readiness / Live-проверка",
                    "Tiny Order Review / Малый ордер",
                    "Pre-live tiny order gate / Предлайв-гейт tiny order",
                    "Supervised readiness review 063 / Обзор supervised readiness 063",
                    "Credentials readiness review / Проверка готовности credentials",
                    "Tiny Candidate: " + clean_text(tiny_scaffold.get("tiny_candidate") or "not_available"),
                    "Пакет ручного подтверждения: "
                    + clean_text(tiny_scaffold.get("approval_packet_path") or "not_available"),
                    "Лимиты: " + _render_hard_limits_inline(tiny_scaffold),
                    "Submission Status: " + clean_text(dict(tiny_scaffold.get("submission_status", {})).get("status") or "blocked"),
                    "Run Tiny Scaffold Dry-Run",
                    "062P status: " + clean_text(pre_live_gate.get("status") or "not_available"),
                    "Чеклист: " + clean_text(pre_live_gate.get("checklist_path") or "not_available"),
                    "Блокеры: " + str(int(pre_live_gate.get("blocker_count", 0) or 0)),
                    "Readiness summary: " + clean_text(pre_live_gate.get("readiness_summary_path") or "not_available"),
                    "Dry-run предлайв-гейта 062P",
                    "063 status: " + clean_text(supervised_gate.get("status") or "not_available"),
                    "Чеклист оператора: "
                    + clean_text(supervised_gate.get("operator_checklist_path") or "not_available"),
                    "Матрица блокеров: " + str(int(supervised_gate.get("blocker_count", 0) or 0)),
                    "Лимиты риска: " + _render_risk_limits_inline(supervised_gate),
                    "Kill switch план: " + _render_plan_inline(supervised_gate, "kill_switch_plan_summary"),
                    "Cancel plan: " + _render_plan_inline(supervised_gate, "cancel_plan_summary"),
                    "Failure plan: " + _render_plan_inline(supervised_gate, "failure_plan_summary"),
                    "Готовность окружения: " + _render_env_readiness_inline(supervised_gate),
                    "Пакет ручного подтверждения: "
                    + clean_text(supervised_gate.get("manual_approval_packet_path") or "not_available"),
                    "Dry-run supervised gate 063",
                    "Credentials readiness status: "
                    + clean_text(credentials_gate.get("status") or "not_available"),
                    "Только наличие маркеров",
                    "Значения не показываются",
                    "Live не включён",
                    "Только dry-run",
                    "Missing credential markers: "
                    + str(int(credentials_gate.get("missing_required_marker_count", 0) or 0)),
                    "Credential marker blockers: "
                    + str(int(credentials_gate.get("blocker_count", 0) or 0)),
                    "Dry-run credentials readiness 064",
                    "Оператор подтвердил: нет",
                    "Кандидат не исполняемый",
                    "Подписание заблокировано",
                    "Отправка ордера заблокирована",
                    "Blockers / Блокеры",
                    "Latest Artifacts",
                    "Safety State",
                    f"Готовность review-only: {int(readiness.get('readiness_percent', 0) or 0)}%",
                    f"Latest artifacts available/missing: {available}/{missing}",
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
                    "Только review-only",
                    "Live-ордера из бота или Mini App недоступны.",
                    "Live-торговля заблокирована",
                ]
            )
        return "\n".join(
            [
                "Telegram Mini App Operator Panel v1 / PMBOT Operator Console 060T: review-only / live blocked",
                "Main PMBOT menu",
                "PMBOT Status",
                "Paper Runs",
                    "Public Market Evidence",
                    "Decision Ledger",
                    "Live Readiness",
                    "Tiny Order Review",
                    "Pre-live tiny order gate",
                    "Supervised readiness review 063",
                    "Credentials readiness review",
                    "Tiny Candidate: " + clean_text(tiny_scaffold.get("tiny_candidate") or "not_available"),
                    "Approval Packet: " + clean_text(tiny_scaffold.get("approval_packet_path") or "not_available"),
                    "Hard Limits: " + _render_hard_limits_inline(tiny_scaffold),
                    "Submission Status: " + clean_text(dict(tiny_scaffold.get("submission_status", {})).get("status") or "blocked"),
                    "Run Tiny Scaffold Dry-Run",
                    "062P status: " + clean_text(pre_live_gate.get("status") or "not_available"),
                    "Checklist: " + clean_text(pre_live_gate.get("checklist_path") or "not_available"),
                    "Blockers: " + str(int(pre_live_gate.get("blocker_count", 0) or 0)),
                    "Readiness summary: " + clean_text(pre_live_gate.get("readiness_summary_path") or "not_available"),
                    "Run Pre-live Gate 062P Dry-Run",
                    "063 status: " + clean_text(supervised_gate.get("status") or "not_available"),
                    "Operator checklist: "
                    + clean_text(supervised_gate.get("operator_checklist_path") or "not_available"),
                    "Blocker matrix: " + str(int(supervised_gate.get("blocker_count", 0) or 0)),
                    "Risk limits: " + _render_risk_limits_inline(supervised_gate),
                    "Kill switch plan: " + _render_plan_inline(supervised_gate, "kill_switch_plan_summary"),
                    "Cancel plan: " + _render_plan_inline(supervised_gate, "cancel_plan_summary"),
                    "Failure plan: " + _render_plan_inline(supervised_gate, "failure_plan_summary"),
                    "Env readiness: " + _render_env_readiness_inline(supervised_gate),
                    "Manual approval packet: "
                    + clean_text(supervised_gate.get("manual_approval_packet_path") or "not_available"),
                    "Local 063 dry-run command",
                    "Credentials readiness status: "
                    + clean_text(credentials_gate.get("status") or "not_available"),
                    "Presence-only",
                    "Values never shown",
                    "Not live-enabled",
                    "Dry-run only",
                    "Missing credential markers: "
                    + str(int(credentials_gate.get("missing_required_marker_count", 0) or 0)),
                    "Credential marker blockers: "
                    + str(int(credentials_gate.get("blocker_count", 0) or 0)),
                    "Dry-run credentials readiness 064",
                    "Blockers",
                    "Latest Artifacts",
                "Safety State",
                f"Review readiness: {int(readiness.get('readiness_percent', 0) or 0)}%",
                f"Latest artifacts available/missing: {available}/{missing}",
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
                "Review-only actions: dry-run and preflight only.",
                "No live order action is available from this bot or panel.",
            ]
        )

    def _render_tiny_order_review(self) -> str:
        tiny_scaffold = dict(self._summary().get("tiny_order_scaffold_status_summary", {}))
        command = "python -m pm_bot.operator_runner.tiny_order_scaffold --market BTC --strategy tiny-momentum --dry-run"
        language = self._language()
        lines = [
            tiny_order_review_label("section", language),
            f"061 status: {clean_text(tiny_scaffold.get('status') or 'not_available')}",
            f"{tiny_order_review_label('tiny_candidate', language)}: "
            f"{clean_text(tiny_scaffold.get('tiny_candidate') or 'not_available')}",
            f"{tiny_order_review_label('approval_packet', language)}: "
            f"{clean_text(tiny_scaffold.get('approval_packet_path') or tiny_scaffold.get('manual_tiny_order_approval_packet_path') or 'not_available')}",
            f"{tiny_order_review_label('hard_limits', language)}: {_render_hard_limits_inline(tiny_scaffold)}",
            f"{tiny_order_review_label('submission_status', language)}: "
            f"{clean_text(dict(tiny_scaffold.get('submission_status', {})).get('status') or 'blocked')}",
            tiny_order_review_label("operator_approved_false", language),
            tiny_order_review_label("candidate_not_executable", language),
            tiny_order_review_label("signing_blocked", language),
            tiny_order_review_label("order_submission_blocked", language),
            tiny_order_review_label("wallet_blocked", language),
            tiny_order_review_label("live_blocked", language),
            f"{tiny_order_review_label('run_dry_run', language)}: {command}",
            "review_only: true",
            "execution_enabling: false",
            "order_submission_enabled: false",
            "signing_enabled: false",
            "wallet_signing_enabled: false",
            "live_execution_approved: false",
        ]
        return "\n".join(line for line in lines if clean_text(line))

    def _render_pre_live_gate_review(self) -> str:
        pre_live_gate = dict(self._summary().get("pre_live_tiny_order_gate_status_summary", {}))
        command = (
            "python -m pm_bot.operator_runner.pre_live_tiny_order_gate "
            "--market BTC --strategy tiny-momentum --dry-run"
        )
        language = self._language()
        lines = [
            pre_live_gate_review_label("section", language),
            f"{pre_live_gate_review_label('status', language)}: "
            f"{clean_text(pre_live_gate.get('status') or 'not_available')}",
            f"{pre_live_gate_review_label('checklist', language)}: "
            f"{clean_text(pre_live_gate.get('checklist_path') or 'not_available')}",
            f"{pre_live_gate_review_label('blockers', language)}: "
            f"{int(pre_live_gate.get('blocker_count', 0) or 0)}",
            f"{pre_live_gate_review_label('readiness', language)}: "
            f"{clean_text(pre_live_gate.get('readiness_summary_path') or 'not_available')}",
            f"{pre_live_gate_review_label('operator_md', language)}: "
            f"{clean_text(pre_live_gate.get('operator_markdown_path') or 'not_available')}",
            f"{pre_live_gate_review_label('run_dry_run', language)}: {command}",
            pre_live_gate_review_label("review_only", language),
            pre_live_gate_review_label("dry_run_only", language),
            pre_live_gate_review_label("operator_approved_false", language),
            pre_live_gate_review_label("candidate_not_executable", language),
            pre_live_gate_review_label("signing_unavailable", language),
            pre_live_gate_review_label("order_submission_unavailable", language),
            pre_live_gate_review_label("wallet_unavailable", language),
            pre_live_gate_review_label("live_blocked", language),
            pre_live_gate_review_label("ready_future_false", language),
            pre_live_gate_review_label("allowed_live_false", language),
            pre_live_gate_review_label("resolved_zero", language),
            "operator_approved: false",
            "candidate_is_executable: false",
            "signing_available: false",
            "signed_payload_available: false",
            "order_submission_available: false",
            "wallet_available: false",
            "live_execution_approved: false",
            "ready_for_future_live_enablement: false",
            "allowed_for_live: false",
            "review_only: true",
            "dry_run_only: true",
            "execution_enabling: false",
        ]
        return "\n".join(line for line in lines if clean_text(line))

    def _render_supervised_live_review(self) -> str:
        supervised_gate = dict(self._summary().get("supervised_tiny_live_enablement_gate_status_summary", {}))
        command = (
            "python -m pm_bot.operator_runner.supervised_tiny_live_enablement_gate "
            "--market BTC --strategy tiny-momentum --dry-run"
        )
        language = self._language()
        lines = [
            supervised_live_enablement_review_label("section", language),
            f"{supervised_live_enablement_review_label('status', language)}: "
            f"{clean_text(supervised_gate.get('status') or 'not_available')}",
            f"{supervised_live_enablement_review_label('checklist', language)}: "
            f"{clean_text(supervised_gate.get('operator_checklist_path') or 'not_available')}",
            f"{supervised_live_enablement_review_label('blockers', language)}: "
            f"{int(supervised_gate.get('blocker_count', 0) or 0)}",
            f"{supervised_live_enablement_review_label('risk_limits', language)}: "
            f"{_render_risk_limits_inline(supervised_gate)}",
            f"{supervised_live_enablement_review_label('kill_switch', language)}: "
            f"{_render_plan_inline(supervised_gate, 'kill_switch_plan_summary')}",
            f"{supervised_live_enablement_review_label('cancel_plan', language)}: "
            f"{_render_plan_inline(supervised_gate, 'cancel_plan_summary')}",
            f"{supervised_live_enablement_review_label('failure_plan', language)}: "
            f"{_render_plan_inline(supervised_gate, 'failure_plan_summary')}",
            f"{supervised_live_enablement_review_label('env_readiness', language)}: "
            f"{_render_env_readiness_inline(supervised_gate)}",
            f"{supervised_live_enablement_review_label('manual_approval_packet', language)}: "
            f"{clean_text(supervised_gate.get('manual_approval_packet_path') or 'not_available')}",
            f"{supervised_live_enablement_review_label('run_dry_run', language)}: {command}",
            supervised_live_enablement_review_label("review_only", language),
            supervised_live_enablement_review_label("dry_run_only", language),
            supervised_live_enablement_review_label("not_executable", language),
            supervised_live_enablement_review_label("operator_approval_required", language),
            supervised_live_enablement_review_label("operator_approved_false", language),
            supervised_live_enablement_review_label("candidate_not_executable", language),
            supervised_live_enablement_review_label("env_presence_only", language),
            supervised_live_enablement_review_label("resolved_zero", language),
            supervised_live_enablement_review_label("allowed_live_false", language),
            "operator_approved: false",
            "candidate_is_executable: false",
            "live_execution_approved: false",
            "canary_executable_now: false",
            "real_execution_available: false",
            "order_submission_enabled: false",
            "order_cancel_enabled: false",
            "wallet_signing_enabled: false",
            "signing_enabled: false",
            "signed_payload_generation_enabled: false",
            "signed_order_generation_enabled: false",
            "authenticated_polymarket_enabled: false",
            "live_connector_enabled: false",
            "allowed_for_live: false",
            "review_only: true",
            "dry_run_only: true",
            "execution_enabling: false",
        ]
        return "\n".join(line for line in lines if clean_text(line))

    def _render_credentials_readiness_review(self) -> str:
        credentials_gate = dict(self._summary().get("explicit_live_credentials_readiness_gate_status_summary", {}))
        command = (
            "python -m pm_bot.operator_runner.explicit_live_credentials_readiness_gate "
            "--market BTC --strategy tiny-momentum --dry-run"
        )
        language = self._language()
        marker_rows = [
            dict(row)
            for row in credentials_gate.get("required_marker_presence", [])
            if isinstance(row, Mapping)
        ]
        missing_markers = _clean_list(credentials_gate.get("missing_required_markers"))[:10]
        missing_blockers = [
            clean_text(row.get("blocker_id"))
            for row in credentials_gate.get("missing_marker_blockers", [])
            if isinstance(row, Mapping) and clean_text(row.get("blocker_id"))
        ][:10]
        marker_lines = [
            (
                f"{clean_text(row.get('marker_label'))}: "
                f"{'present' if row.get('present') is True else 'absent'}; "
                f"{clean_text(row.get('result_category') or 'missing')}; "
                "value_redacted=true; raw_value_emitted=false"
            )
            for row in marker_rows
            if clean_text(row.get("marker_label"))
        ]
        lines = [
            credentials_readiness_review_label("section", language),
            f"{credentials_readiness_review_label('status', language)}: "
            f"{clean_text(credentials_gate.get('status') or 'not_available')}",
            f"{credentials_readiness_review_label('readiness', language)}: "
            f"{clean_text(credentials_gate.get('readiness_status') or 'blocked')}",
            credentials_readiness_review_label("warning", language),
            credentials_readiness_review_label("presence_only", language),
            credentials_readiness_review_label("values_never_shown", language),
            credentials_readiness_review_label("not_live_enabled", language),
            credentials_readiness_review_label("dry_run_only", language),
            f"{credentials_readiness_review_label('markers', language)}: "
            f"required={int(credentials_gate.get('required_marker_count', 0) or 0)}; "
            f"missing={int(credentials_gate.get('missing_required_marker_count', 0) or 0)}; "
            f"execution_flags_present={int(credentials_gate.get('present_execution_flag_count', 0) or 0)}",
            f"{credentials_readiness_review_label('blockers', language)}: "
            f"{int(credentials_gate.get('blocker_count', 0) or 0)}",
            f"{credentials_readiness_review_label('operator_boundary', language)}: "
            f"{clean_text(credentials_gate.get('operator_approval_boundary_path') or 'not_available')}",
            f"{credentials_readiness_review_label('safety_policy', language)}: "
            f"{clean_text(credentials_gate.get('safety_policy_validation_path') or 'not_available')}",
            f"{credentials_readiness_review_label('run_dry_run', language)}: {command}",
            credentials_readiness_review_label("resolved_zero", language),
            credentials_readiness_review_label("allowed_live_false", language),
            "presence_only: true",
            "values_never_shown: true",
            "redacted_labels_only: true",
            "credential_values_read: false",
            "raw_values_emitted: false",
            "broad_environment_scan_performed: false",
            "allowed_for_live: false",
            "resolved_blocker_count: 0",
            "operator_approved: false",
            "candidate_is_executable: false",
            "review_only: true",
            "dry_run_only: true",
            "execution_enabling: false",
        ]
        if marker_lines:
            lines.append(credentials_readiness_review_label("markers", language))
            lines.extend(marker_lines)
        if missing_markers:
            lines.append(credentials_readiness_review_label("missing_markers", language))
            lines.extend(bullet_lines(missing_markers))
        if missing_blockers:
            lines.append(credentials_readiness_review_label("blockers", language))
            lines.extend(bullet_lines(missing_blockers))
        return "\n".join(line for line in lines if clean_text(line))

    def _render_readiness(self) -> str:
        readiness = dict(self._summary().get("telegram_operator_console_readiness_summary", {}))
        items = dict(readiness.get("items", {}))
        if self._language() == "ru":
            return "\n".join(
                [
                    "PMBOT Readiness: только review-only",
                    f"Готовность: {int(readiness.get('readiness_percent', 0) or 0)}%",
                    f"Paper system: {clean_text(items.get('paper_system') or 'blocked')}",
                    f"Public market data: {clean_text(items.get('public_market_data') or 'blocked')}",
                    f"Decision ledger: {clean_text(items.get('decision_ledger') or 'blocked')}",
                    f"Live connector preflight: {clean_text(items.get('live_connector_preflight') or 'blocked')}",
                    f"Auth boundary: {clean_text(items.get('auth_boundary') or 'blocked')}",
                    f"Signer boundary: {clean_text(items.get('signer_boundary') or 'not implemented yet')}",
                    f"Tiny order scaffold: {clean_text(items.get('tiny_order_scaffold') or 'not implemented yet')}",
                    f"Pre-live tiny order gate: {clean_text(items.get('pre_live_tiny_order_gate') or 'not implemented yet')}",
                    f"Supervised readiness review 063: {clean_text(items.get('supervised_tiny_live_enablement_gate') or 'not implemented yet')}",
                    f"Credentials readiness review: {clean_text(items.get('explicit_live_credentials_readiness_gate') or 'not implemented yet')}",
                    f"Order submission: {clean_text(items.get('order_submission') or 'blocked')}",
                    f"Live execution: {clean_text(items.get('live_execution') or 'blocked')}",
                    "Labels: paper_demo_ready, pre_live_boundary_ready, signer_boundary_missing, tiny_order_scaffold_missing, pre_live_tiny_order_gate_missing, supervised_tiny_live_enablement_gate_missing, credentials_readiness_review_missing, live_execution_blocked",
                    "Live-торговля заблокирована",
                ]
            )
        return "\n".join(
            [
                "PMBOT Readiness: review-only",
                f"Readiness: {int(readiness.get('readiness_percent', 0) or 0)}%",
                f"Paper system: {clean_text(items.get('paper_system') or 'blocked')}",
                f"Public market data: {clean_text(items.get('public_market_data') or 'blocked')}",
                f"Decision ledger: {clean_text(items.get('decision_ledger') or 'blocked')}",
                f"Live connector preflight: {clean_text(items.get('live_connector_preflight') or 'blocked')}",
                f"Auth boundary: {clean_text(items.get('auth_boundary') or 'blocked')}",
                f"Signer boundary: {clean_text(items.get('signer_boundary') or 'not implemented yet')}",
                f"Tiny order scaffold: {clean_text(items.get('tiny_order_scaffold') or 'not implemented yet')}",
                f"Pre-live tiny order gate: {clean_text(items.get('pre_live_tiny_order_gate') or 'not implemented yet')}",
                f"Supervised readiness review 063: {clean_text(items.get('supervised_tiny_live_enablement_gate') or 'not implemented yet')}",
                f"Credentials readiness review: {clean_text(items.get('explicit_live_credentials_readiness_gate') or 'not implemented yet')}",
                f"Order submission: {clean_text(items.get('order_submission') or 'blocked')}",
                f"Live execution: {clean_text(items.get('live_execution') or 'blocked')}",
                "Labels: paper_demo_ready, pre_live_boundary_ready, signer_boundary_missing, tiny_order_scaffold_missing, pre_live_tiny_order_gate_missing, supervised_tiny_live_enablement_gate_missing, credentials_readiness_review_missing, live_execution_blocked",
            ]
        )

    def _render_safe_action(self, command: str) -> str:
        action_id = command.lstrip("/")
        action = safe_action_by_id(action_id)
        if action is None:
            return "Unknown PMBOT safe action. No execution was performed."
        result = dict(self.action_runner(action.action_id))
        stdout = clean_text(result.get("stdout_excerpt"))
        stderr = clean_text(result.get("stderr_excerpt"))
        label = action.label_ru if self._language() == "ru" else action.label_en
        if self._language() == "ru":
            lines = [
                f"{label}: dry-run/preflight action",
                f"Статус: {clean_text(result.get('status') or 'blocked')}",
                f"Код возврата: {int(result.get('returncode', 0) or 0)}",
                "Только review-only; live-торговля заблокирована.",
                "order_submission_enabled: false",
                "signing_enabled: false",
                "wallet_signing_enabled: false",
                "candidate_is_executable: false",
                "live_execution_blocked: true",
            ]
            if stdout:
                lines.append(f"Вывод: {stdout}")
            if stderr:
                lines.append(f"Ошибка: {stderr}")
            return "\n".join(lines)
        lines = [
            f"{label}: dry-run/preflight action",
            f"Status: {clean_text(result.get('status') or 'blocked')}",
            f"Return code: {int(result.get('returncode', 0) or 0)}",
            "Review-only; live trading remains blocked.",
            "order_submission_enabled: false",
            "signing_enabled: false",
            "wallet_signing_enabled: false",
            "candidate_is_executable: false",
            "live_execution_blocked: true",
        ]
        if stdout:
            lines.append(f"Output: {stdout}")
        if stderr:
            lines.append(f"Error: {stderr}")
        return "\n".join(lines)

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
            if operator_language_is_selected(self.state):
                return build_operator_console_keyboard(self._language())
            return build_panel_fallback_keyboard(self._language())
        if command == "/connection_status":
            return build_connection_status_keyboard(self._language())
        if command == "/language":
            return build_language_selection_keyboard()
        if command in {
            "/readiness",
            "/tiny_order_review",
            "/pre_live_gate_review",
            "/supervised_live_review",
            "/credentials_readiness_review",
        } or command in SAFE_ACTION_COMMANDS:
            if operator_language_is_selected(self.state):
                return build_operator_console_keyboard(self._language())
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


def build_operator_console_keyboard(language: str = DEFAULT_OPERATOR_LANGUAGE) -> TelegramOperatorKeyboard:
    return _keyboard_from_rows(operator_console_button_rows(normalize_operator_language(language, fallback="en")))


def build_connection_status_keyboard(language: str = DEFAULT_OPERATOR_LANGUAGE) -> TelegramOperatorKeyboard:
    return _keyboard_from_rows(connection_status_button_rows(normalize_operator_language(language, fallback="en")))


def build_language_selection_keyboard() -> TelegramOperatorKeyboard:
    return _keyboard_from_rows(LANGUAGE_SELECTION_BUTTON_ROWS)


def telegram_callback_to_command(callback_data: str) -> str:
    return CALLBACK_COMMAND_MAP.get(clean_text(callback_data), "") or safe_action_command_for_callback(callback_data)


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
    paper_decision_ledger = _first_mapping(
        context_value.get("paper_decision_ledger_status_summary"),
        context_value.get("paper_decision_ledger_status"),
        context_value.get("latest_paper_decision_ledger_status"),
    )
    live_connector_preflight = _first_mapping(
        context_value.get("live_connector_preflight_status_summary"),
        context_value.get("live_connector_preflight_status"),
        context_value.get("latest_live_connector_preflight_status"),
    )
    authenticated_clob_preflight = _first_mapping(
        context_value.get("authenticated_clob_preflight_status_summary"),
        context_value.get("authenticated_clob_preflight_status"),
        context_value.get("latest_authenticated_clob_preflight_status"),
    )
    clob_l2_marker_preflight = _first_mapping(
        context_value.get("clob_l2_marker_preflight_status_summary"),
        context_value.get("clob_l2_marker_preflight_status"),
        context_value.get("latest_clob_l2_marker_preflight_status"),
        authenticated_clob_preflight.get("clob_l2_marker_preflight_status_summary"),
    )
    no_order_auth_get_preflight = _first_mapping(
        context_value.get("no_order_auth_get_preflight_status_summary"),
        context_value.get("no_order_auth_get_preflight_status"),
        context_value.get("latest_no_order_auth_get_preflight_status"),
        authenticated_clob_preflight.get("no_order_auth_get_preflight_status_summary"),
    )
    signer_boundary_preflight = _first_mapping(
        context_value.get("signer_boundary_preflight_status_summary"),
        context_value.get("signer_boundary_preflight_status"),
        context_value.get("latest_signer_boundary_preflight_status"),
    )
    tiny_order_scaffold = _first_mapping(
        context_value.get("tiny_order_scaffold_status_summary"),
        context_value.get("tiny_order_scaffold_status"),
        context_value.get("latest_tiny_order_scaffold_status"),
    )
    pre_live_tiny_order_gate = _first_mapping(
        context_value.get("pre_live_tiny_order_gate_status_summary"),
        context_value.get("pre_live_tiny_order_gate_status"),
        context_value.get("latest_pre_live_tiny_order_gate_status"),
    )
    supervised_tiny_live_enablement_gate = _first_mapping(
        context_value.get("supervised_tiny_live_enablement_gate_status_summary"),
        context_value.get("supervised_tiny_live_enablement_gate_status"),
        context_value.get("latest_supervised_tiny_live_enablement_status"),
        context_value.get("telegram_supervised_live_enablement_review_063t_status"),
    )
    explicit_live_credentials_readiness_gate = _first_mapping(
        context_value.get("explicit_live_credentials_readiness_gate_status_summary"),
        context_value.get("explicit_live_credentials_readiness_gate_status"),
        context_value.get("latest_explicit_live_credentials_readiness_gate_status"),
        context_value.get("telegram_credentials_readiness_review_064t_status"),
    )
    telegram_connection_status_067e = _first_mapping(
        context_value.get("telegram_connection_status_067e_status_summary"),
        context_value.get("telegram_connection_status_067e_status"),
        context_value.get("latest_telegram_wallet_auth_status_067e"),
    )
    mini_panel = _first_mapping(
        context_value.get("telegram_mini_app_operator_panel_summary"),
        context_value.get("telegram_mini_app_operator_panel"),
    )
    telegram_operator_console = _first_mapping(
        context_value.get("telegram_operator_console_060t_status_registry"),
        context_value.get("telegram_operator_console_status_registry_snapshot"),
    )
    telegram_operator_console_readiness = _first_mapping(
        context_value.get("telegram_operator_console_readiness_summary"),
        telegram_operator_console.get("readiness_summary"),
    )
    telegram_operator_console_latest_artifacts = _first_mapping(
        context_value.get("telegram_operator_console_latest_artifacts"),
        telegram_operator_console.get("latest_artifacts"),
    )
    telegram_operator_console_safety_state = _first_mapping(
        context_value.get("telegram_operator_console_safety_state"),
        telegram_operator_console.get("safety_state"),
    )
    blockers = _first_mapping(
        context_value.get("blocker_summary"),
        context_value.get("telegram_operator_console_blockers_summary"),
        telegram_operator_console.get("blockers_summary"),
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
                "paper_decision_ledger": paper_decision_ledger,
                "live_connector_preflight": live_connector_preflight,
                "authenticated_clob_preflight": authenticated_clob_preflight,
                "clob_l2_marker_preflight": clob_l2_marker_preflight,
                "no_order_auth_get_preflight": no_order_auth_get_preflight,
                "signer_boundary_preflight": signer_boundary_preflight,
                "tiny_order_scaffold": tiny_order_scaffold,
                "pre_live_tiny_order_gate": pre_live_tiny_order_gate,
                "supervised_tiny_live_enablement_gate": supervised_tiny_live_enablement_gate,
                "explicit_live_credentials_readiness_gate": explicit_live_credentials_readiness_gate,
                "telegram_connection_status_067e": telegram_connection_status_067e,
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
        "paper_decision_ledger_status_summary": _normalize_paper_decision_ledger_summary(paper_decision_ledger),
        "live_connector_preflight_status_summary": _normalize_live_connector_preflight_summary(
            live_connector_preflight
        ),
        "authenticated_clob_preflight_status_summary": _normalize_authenticated_clob_preflight_summary(
            authenticated_clob_preflight
        ),
        "clob_l2_marker_preflight_status_summary": _normalize_clob_l2_marker_preflight_summary(
            clob_l2_marker_preflight
        ),
        "no_order_auth_get_preflight_status_summary": _normalize_no_order_auth_get_preflight_summary(
            no_order_auth_get_preflight
        ),
        "signer_boundary_preflight_status_summary": _normalize_signer_boundary_preflight_summary(
            signer_boundary_preflight
        ),
        "tiny_order_scaffold_status_summary": _normalize_tiny_order_scaffold_summary(tiny_order_scaffold),
        "pre_live_tiny_order_gate_status_summary": _normalize_pre_live_tiny_order_gate_summary(
            pre_live_tiny_order_gate
        ),
        "supervised_tiny_live_enablement_gate_status_summary": _normalize_supervised_tiny_live_enablement_summary(
            supervised_tiny_live_enablement_gate
        ),
        "explicit_live_credentials_readiness_gate_status_summary": _normalize_credentials_readiness_summary(
            explicit_live_credentials_readiness_gate
        ),
        "telegram_connection_status_067e_status_summary": _normalize_connection_status_067e_summary(
            telegram_connection_status_067e
        ),
        "telegram_mini_app_operator_panel_summary": mini_panel,
        "telegram_operator_console_060t_status_registry": telegram_operator_console,
        "telegram_operator_console_readiness_summary": _normalize_telegram_console_readiness_summary(
            telegram_operator_console_readiness
        ),
        "telegram_operator_console_latest_artifacts": telegram_operator_console_latest_artifacts,
        "telegram_operator_console_safety_state": telegram_operator_console_safety_state,
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


def _normalize_telegram_console_readiness_summary(readiness: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(readiness or {})
    items = value.get("items") if isinstance(value.get("items"), Mapping) else {}
    normalized_items = {
        "paper_system": clean_text(dict(items).get("paper_system") or "blocked"),
        "public_market_data": clean_text(dict(items).get("public_market_data") or "blocked"),
        "decision_ledger": clean_text(dict(items).get("decision_ledger") or "blocked"),
        "live_connector_preflight": clean_text(dict(items).get("live_connector_preflight") or "blocked"),
        "auth_boundary": clean_text(dict(items).get("auth_boundary") or "blocked"),
        "signer_boundary": clean_text(dict(items).get("signer_boundary") or "not implemented yet"),
        "tiny_order_scaffold": clean_text(dict(items).get("tiny_order_scaffold") or "not implemented yet"),
        "pre_live_tiny_order_gate": clean_text(
            dict(items).get("pre_live_tiny_order_gate") or "not implemented yet"
        ),
        "supervised_tiny_live_enablement_gate": clean_text(
            dict(items).get("supervised_tiny_live_enablement_gate") or "not implemented yet"
        ),
        "explicit_live_credentials_readiness_gate": clean_text(
            dict(items).get("explicit_live_credentials_readiness_gate") or "not implemented yet"
        ),
        "order_submission": clean_text(dict(items).get("order_submission") or "blocked"),
        "live_execution": clean_text(dict(items).get("live_execution") or "blocked"),
    }
    return {
        "status": "telegram_operator_console_readiness_review_only",
        "readiness_percent": _int_first(value.get("readiness_percent")),
        "readiness_scope": clean_text(value.get("readiness_scope") or "telegram_review_only_dry_run_and_preflight_console"),
        "items": normalized_items,
        "labels": _clean_list(
            value.get("labels")
            or (
                "paper_demo_ready",
                "pre_live_boundary_ready",
                "signer_boundary_missing",
                "tiny_order_scaffold_missing",
                "pre_live_tiny_order_gate_missing",
                "supervised_tiny_live_enablement_gate_missing",
                "credentials_readiness_review_missing",
                "live_execution_blocked",
            )
        ),
        "paper_demo_ready": value.get("paper_demo_ready") is True,
        "pre_live_boundary_ready": value.get("pre_live_boundary_ready") is True,
        "signer_boundary_missing": True,
        "tiny_order_scaffold_missing": True,
        "pre_live_tiny_order_gate_missing": True,
        "supervised_tiny_live_enablement_gate_missing": True,
        "credentials_readiness_review_missing": True,
        "live_execution_blocked": True,
        "review_only": True,
        "execution_enabling": False,
        "live_execution_approved": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
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


def _normalize_paper_decision_ledger_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    counts = value.get("count_by_outcome") if isinstance(value.get("count_by_outcome"), Mapping) else {}
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or value.get("market_symbol") or "not_available"),
        "strategy_name": clean_text(value.get("strategy_name") or "not_available"),
        "source_type": clean_text(value.get("source_type") or "not_available"),
        "latest_run_source": clean_text(value.get("latest_run_source") or "not_available"),
        "last_outcome": clean_text(value.get("last_outcome") or "not_available"),
        "ledger_entry_count": _int_first(value.get("ledger_entry_count"), 0),
        "count_by_outcome": dict(counts),
        "evidence_pack_path": clean_text(value.get("evidence_pack_path")),
        "latest_ledger_path": clean_text(value.get("latest_ledger_path")),
        "summary_path": clean_text(value.get("summary_path")),
        "trace_path": clean_text(value.get("trace_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "mode": clean_text(value.get("mode") or "paper / review-only"),
        "live_execution": clean_text(value.get("live_execution") or "blocked"),
        "live_execution_blocked": True,
        "next_operator_action": clean_text(
            value.get("next_operator_action") or "review only; no live action available"
        ),
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


def _normalize_live_connector_preflight_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:8]
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or "not_available"),
        "mode": clean_text(value.get("mode") or "preflight / review-only"),
        "execution_mode": clean_text(value.get("execution_mode") or "paper_or_preflight"),
        "public_network_status": clean_text(
            value.get("public_network_status") or value.get("public_network") or "not_available"
        ),
        "auth_boundary_status": clean_text(
            value.get("auth_boundary_status") or value.get("auth_boundary") or "not_available"
        ),
        "blocker_count": _int_first(value.get("blocker_count"), len(blockers)),
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "artifact_path": clean_text(value.get("artifact_path")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "review_only": True,
        "preflight_only": True,
        "order_submission_blocked": True,
        "signing_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "next_operator_action": clean_text(
            value.get("next_operator_action") or "review preflight only, no live order available"
        ),
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


def _normalize_clob_l2_marker_preflight_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:8]
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or "not_available"),
        "mode": clean_text(value.get("mode") or "preflight / review-only"),
        "execution_mode": clean_text(value.get("execution_mode") or "preflight"),
        "clob_base_url_configured": value.get("clob_base_url_configured") is True,
        "clob_base_url_status": clean_text(value.get("clob_base_url_status") or "not_available"),
        "clob_base_url_valid": value.get("clob_base_url_valid") is True,
        "clob_base_url_missing": value.get("clob_base_url_missing") is True,
        "clob_base_url_invalid": value.get("clob_base_url_invalid") is True,
        "public_clob_base_url": clean_text(value.get("public_clob_base_url")),
        "is_production_clob_base_url": value.get("is_production_clob_base_url") is True,
        "auth_marker_presence_detected": value.get("auth_marker_presence_detected") is True,
        "l2_marker_presence_status": clean_text(value.get("l2_marker_presence_status") or "not_available"),
        "l2_marker_set_complete": value.get("l2_marker_set_complete") is True,
        "l2_marker_configured_count": _int_first(value.get("l2_marker_configured_count")),
        "l2_marker_missing_count": _int_first(value.get("l2_marker_missing_count")),
        "unsafe_raw_value_detected": value.get("unsafe_raw_value_detected") is True,
        "auth_boundary_mock_checked": value.get("auth_boundary_mock_checked") is True,
        "no_order_auth_plan_ready": value.get("no_order_auth_plan_ready") is True,
        "authenticated_request_skipped_by_default": True,
        "authenticated_request_performed": False,
        "blocker_count": _int_first(value.get("blocker_count"), len(blockers)),
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "artifact_path": clean_text(value.get("artifact_path")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "review_only": True,
        "preflight_only": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "signing_blocked": True,
        "wallet_connection_blocked": True,
        "balance_read_blocked": True,
        "position_read_blocked": True,
        "live_execution_blocked": True,
        "next_operator_action": clean_text(
            value.get("next_operator_action")
            or "configure safe CLOB base URL and redacted L2 marker variables; no live order available"
        ),
        "execution_enabling": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _normalize_no_order_auth_get_preflight_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:8]
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or "not_available"),
        "mode": clean_text(value.get("mode") or "preflight / review-only"),
        "execution_mode": clean_text(value.get("execution_mode") or "preflight"),
        "no_order_auth_get_status": clean_text(value.get("no_order_auth_get_status") or "not_available"),
        "no_order_auth_get_requested": value.get("no_order_auth_get_requested") is True,
        "real_auth_read_only_requested": value.get("real_auth_read_only_requested") is True,
        "real_auth_read_only_opt_in_present": value.get("real_auth_read_only_opt_in_present") is True,
        "real_authenticated_get_performed": value.get("real_authenticated_get_performed") is True,
        "request_method": clean_text(value.get("request_method") or "GET"),
        "endpoint_path_sanitized": clean_text(value.get("endpoint_path_sanitized")),
        "endpoint_safe_for_no_order_check": value.get("endpoint_safe_for_no_order_check") is True,
        "endpoint_blocked_reason": clean_text(value.get("endpoint_blocked_reason")),
        "status_code": value.get("status_code"),
        "auth_used": value.get("auth_used") is True,
        "credentials_used": "redacted_presence_only",
        "credentials_values_exposed": False,
        "blocker_count": _int_first(value.get("blocker_count"), len(blockers)),
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "artifact_path": clean_text(value.get("artifact_path")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "review_only": True,
        "preflight_only": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "signing_blocked": True,
        "wallet_connection_blocked": True,
        "balance_read_blocked": True,
        "position_read_blocked": True,
        "live_execution_blocked": True,
        "execution_enabling": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _normalize_signer_boundary_preflight_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:8]
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or value.get("market_symbol") or "not_available"),
        "market_symbol": clean_text(value.get("market_symbol") or value.get("market") or "not_available"),
        "strategy_name": clean_text(value.get("strategy_name") or "not_available"),
        "mode": clean_text(value.get("mode") or "preflight / review-only"),
        "execution_mode": clean_text(value.get("execution_mode") or "preflight"),
        "source_paper_intent_path": clean_text(value.get("source_paper_intent_path")),
        "live_candidate_intent_status": clean_text(
            value.get("live_candidate_intent_status")
            or value.get("live_candidate_intent")
            or "not_available"
        ),
        "candidate_outcome": clean_text(value.get("candidate_outcome") or "not_available"),
        "candidate_side": clean_text(value.get("candidate_side") or "not_available"),
        "candidate_limit_price": value.get("candidate_limit_price"),
        "candidate_size": value.get("candidate_size"),
        "candidate_notional": value.get("candidate_notional"),
        "unsigned_plan_status": clean_text(
            value.get("unsigned_plan_status") or value.get("unsigned_payload_plan") or "not_available"
        ),
        "unsigned_plan_created": value.get("unsigned_plan_created") is True,
        "unsigned_plan_is_executable": False,
        "signer_status": clean_text(value.get("signer_status") or value.get("signer") or "blocked"),
        "signed_payload_status": clean_text(
            value.get("signed_payload_status") or value.get("signed_payload") or "unavailable"
        ),
        "order_submission_status": clean_text(
            value.get("order_submission_status") or value.get("order_submission") or "blocked"
        ),
        "signer_config_present": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "blocker_count": _int_first(value.get("blocker_count"), len(blockers)),
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "artifact_path": clean_text(value.get("artifact_path")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "review_only": True,
        "preflight_only": True,
        "signer_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "wallet_connection_blocked": True,
        "balance_read_blocked": True,
        "position_read_blocked": True,
        "live_execution_blocked": True,
        "execution_enabling": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _normalize_tiny_order_scaffold_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    review = _first_mapping(value.get("tiny_order_review"))
    hard_limits_summary = _first_mapping(
        value.get("hard_limits_summary"),
        value.get("tiny_order_hard_limits"),
        review.get("hard_limits_summary"),
    )
    submission_status = _first_mapping(
        value.get("submission_status"),
        value.get("tiny_order_submission_availability"),
        review.get("submission_status"),
    )
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:8]
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or value.get("market_symbol") or "not_available"),
        "market_symbol": clean_text(value.get("market_symbol") or value.get("market") or "not_available"),
        "strategy_name": clean_text(value.get("strategy_name") or "not_available"),
        "mode": clean_text(value.get("mode") or "preflight / review-only"),
        "execution_mode": clean_text(value.get("execution_mode") or "preflight"),
        "source_intent_path": clean_text(value.get("source_intent_path")),
        "source_signer_boundary_path": clean_text(value.get("source_signer_boundary_path")),
        "tiny_candidate": clean_text(value.get("tiny_candidate") or "not_available"),
        "tiny_candidate_status": clean_text(value.get("tiny_candidate_status") or value.get("tiny_candidate") or "not_available"),
        "approval_packet": clean_text(value.get("approval_packet") or "not_available"),
        "approval_packet_status": clean_text(
            value.get("approval_packet_status") or value.get("approval_packet") or "not_available"
        ),
        "approval_packet_path": clean_text(
            value.get("approval_packet_path") or value.get("manual_tiny_order_approval_packet_path")
        ),
        "manual_tiny_order_approval_packet_path": clean_text(
            value.get("manual_tiny_order_approval_packet_path") or value.get("approval_packet_path")
        ),
        "tiny_order_candidate_path": clean_text(value.get("tiny_order_candidate_path")),
        "tiny_order_hard_limits_path": clean_text(value.get("tiny_order_hard_limits_path")),
        "tiny_order_submission_availability_path": clean_text(value.get("tiny_order_submission_availability_path")),
        "operator_approved": False,
        "candidate_outcome": clean_text(value.get("candidate_outcome") or "not_available"),
        "candidate_side": clean_text(value.get("candidate_side") or "not_available"),
        "candidate_limit_price": value.get("candidate_limit_price"),
        "candidate_size": value.get("candidate_size"),
        "candidate_notional": value.get("candidate_notional"),
        "max_notional": value.get("max_notional"),
        "max_size": value.get("max_size"),
        "max_price": value.get("max_price"),
        "hard_limits_passed": value.get("hard_limits_passed") is True
        or hard_limits_summary.get("hard_limits_passed") is True,
        "hard_limits_summary": {
            "available": hard_limits_summary.get("available") is True,
            "status": clean_text(hard_limits_summary.get("status") or "not_available"),
            "hard_limits_passed": value.get("hard_limits_passed") is True
            or hard_limits_summary.get("hard_limits_passed") is True,
            "max_notional": hard_limits_summary.get("max_notional", value.get("max_notional")),
            "max_size": hard_limits_summary.get("max_size", value.get("max_size")),
            "max_price": hard_limits_summary.get("max_price", value.get("max_price")),
            "operator_summary": clean_text(hard_limits_summary.get("operator_summary")),
        },
        "approval_required": True,
        "approval_packet_created": value.get("approval_packet_created") is True,
        "candidate_is_executable": False,
        "blocker_count": _int_first(value.get("blocker_count"), len(blockers)),
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "artifact_path": clean_text(value.get("artifact_path")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "submission_status": {
            "available": submission_status.get("available") is True,
            "status": clean_text(submission_status.get("status") or value.get("order_submission") or "blocked"),
            "signing_blocked": True,
            "signed_payload_unavailable": True,
            "order_submission_blocked": True,
            "order_cancellation_blocked": True,
            "wallet_connection_blocked": True,
            "live_execution_blocked": True,
            "operator_summary": clean_text(submission_status.get("operator_summary")),
        },
        "signing_blocked": True,
        "signer_blocked": True,
        "signed_payload_unavailable": True,
        "wallet_connection_blocked": True,
        "balance_read_blocked": True,
        "position_read_blocked": True,
        "fill_read_blocked": True,
        "live_execution_blocked": True,
        "review_only": True,
        "preflight_only": True,
        "scaffold_only": True,
        "execution_enabling": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
    }


def _normalize_pre_live_tiny_order_gate_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    review = _first_mapping(value.get("pre_live_gate_review"))
    checklist_summary = _first_mapping(value.get("checklist_summary"), review.get("checklist_summary"))
    blockers_summary = _first_mapping(value.get("blockers_summary"), review.get("blockers_summary"))
    readiness_summary = _first_mapping(value.get("readiness_summary"), review.get("readiness_summary"))
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons") or blockers_summary.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:10]
    return {
        "status": clean_text(value.get("status") or value.get("pre_live_gate_status") or "not_available"),
        "market": clean_text(value.get("market") or value.get("market_symbol") or "not_available"),
        "market_symbol": clean_text(value.get("market_symbol") or value.get("market") or "not_available"),
        "strategy_name": clean_text(value.get("strategy_name") or "not_available"),
        "mode": clean_text(value.get("mode") or "preflight / review-only"),
        "execution_mode": clean_text(value.get("execution_mode") or "preflight"),
        "source_tiny_scaffold_path": clean_text(value.get("source_tiny_scaffold_path")),
        "source_signer_boundary_path": clean_text(value.get("source_signer_boundary_path")),
        "source_auth_preflight_path": clean_text(value.get("source_auth_preflight_path")),
        "source_safety_scan_path": clean_text(value.get("source_safety_scan_path")),
        "checklist_path": clean_text(value.get("checklist_path")),
        "blockers_path": clean_text(value.get("blockers_path")),
        "readiness_summary_path": clean_text(value.get("readiness_summary_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "checklist_summary": checklist_summary,
        "blockers_summary": blockers_summary,
        "readiness_summary": readiness_summary,
        "tiny_candidate_present": value.get("tiny_candidate_present") is True
        or checklist_summary.get("tiny_candidate_present") is True,
        "approval_packet_present": value.get("approval_packet_present") is True
        or checklist_summary.get("approval_packet_present") is True,
        "hard_limits_passed": value.get("hard_limits_passed") is True
        or checklist_summary.get("hard_limits_passed") is True,
        "market_whitelisted": value.get("market_whitelisted") is True
        or checklist_summary.get("market_whitelisted") is True,
        "signer_boundary_present": value.get("signer_boundary_present") is True,
        "auth_preflight_present": value.get("auth_preflight_present") is True,
        "safety_scan_present": value.get("safety_scan_present") is True,
        "readiness_status": clean_text(readiness_summary.get("status") or value.get("readiness_status") or "blocked"),
        "next_operator_action": clean_text(
            readiness_summary.get("next_operator_action") or value.get("next_operator_action")
        ),
        "blocker_count": _int_first(
            value.get("blocker_count"),
            blockers_summary.get("blocker_count"),
            len(blockers),
        ),
        "resolved_blocker_count": 0,
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "operator_approved": False,
        "candidate_is_executable": False,
        "signing_available": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "wallet_available": False,
        "cancel_plan_present": False,
        "failure_plan_present": False,
        "live_execution_approved": False,
        "ready_for_future_live_enablement": False,
        "allowed_for_live": False,
        "signing_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "review_only": True,
        "preflight_only": True,
        "gate_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
    }


def _normalize_supervised_tiny_live_enablement_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    review = _first_mapping(value.get("supervised_live_enablement_review_063t_status"))
    checklist_summary = _first_mapping(value.get("operator_checklist_summary"), review.get("operator_checklist_summary"))
    blockers_summary = _first_mapping(value.get("blockers_summary"), review.get("blockers_summary"))
    risk_limits_summary = _first_mapping(value.get("risk_limits_summary"), review.get("risk_limits_summary"))
    kill_switch_plan_summary = _first_mapping(
        value.get("kill_switch_plan_summary"),
        review.get("kill_switch_plan_summary"),
    )
    cancel_plan_summary = _first_mapping(value.get("cancel_plan_summary"), review.get("cancel_plan_summary"))
    failure_plan_summary = _first_mapping(value.get("failure_plan_summary"), review.get("failure_plan_summary"))
    env_readiness_summary = _first_mapping(value.get("env_readiness_summary"), review.get("env_readiness_summary"))
    manual_approval_packet_summary = _first_mapping(
        value.get("manual_approval_packet_summary"),
        review.get("manual_approval_packet_summary"),
    )
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons") or blockers_summary.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:10]
    return {
        "status": clean_text(
            value.get("status")
            or value.get("source_status")
            or value.get("supervised_live_enablement_status")
            or "not_available"
        ),
        "market": clean_text(value.get("market") or value.get("market_symbol") or "not_available"),
        "market_symbol": clean_text(value.get("market_symbol") or value.get("market") or "not_available"),
        "strategy_name": clean_text(value.get("strategy_name") or "not_available"),
        "mode": clean_text(value.get("mode") or "supervised tiny live enablement preparation / review-only"),
        "execution_mode": clean_text(value.get("execution_mode") or "preflight"),
        "source_pre_live_gate_path": clean_text(value.get("source_pre_live_gate_path")),
        "source_tiny_scaffold_path": clean_text(value.get("source_tiny_scaffold_path")),
        "operator_checklist_path": clean_text(value.get("operator_checklist_path")),
        "blockers_path": clean_text(value.get("blockers_path")),
        "risk_limits_path": clean_text(value.get("risk_limits_path")),
        "kill_switch_plan_path": clean_text(value.get("kill_switch_plan_path")),
        "cancel_plan_path": clean_text(value.get("cancel_plan_path")),
        "failure_plan_path": clean_text(value.get("failure_plan_path")),
        "env_readiness_path": clean_text(value.get("env_readiness_path")),
        "manual_approval_packet_path": clean_text(value.get("manual_approval_packet_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "operator_checklist_summary": checklist_summary,
        "blockers_summary": blockers_summary,
        "risk_limits_summary": risk_limits_summary,
        "kill_switch_plan_summary": kill_switch_plan_summary,
        "cancel_plan_summary": cancel_plan_summary,
        "failure_plan_summary": failure_plan_summary,
        "env_readiness_summary": env_readiness_summary,
        "manual_approval_packet_summary": manual_approval_packet_summary,
        "blocker_count": _int_first(
            value.get("blocker_count"),
            blockers_summary.get("blocker_count"),
            len(blockers),
        ),
        "resolved_blocker_count": 0,
        "missing_env_marker_count": _int_first(
            value.get("missing_env_marker_count"),
            env_readiness_summary.get("missing_marker_count"),
        ),
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "operator_approved": False,
        "candidate_is_executable": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "signing_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "review_only": True,
        "preflight_only": True,
        "preparation_only": True,
        "gate_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
    }


def _normalize_credentials_readiness_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    review = _first_mapping(value.get("credentials_readiness_review"))
    marker_summary = _first_mapping(value.get("marker_summary"), review.get("marker_summary"))
    blockers_summary = _first_mapping(value.get("blockers_summary"), review.get("blockers_summary"))
    operator_boundary = _first_mapping(
        value.get("operator_approval_boundary_summary"),
        review.get("operator_approval_boundary_summary"),
    )
    safety_policy = _first_mapping(
        value.get("safety_policy_validation_summary"),
        review.get("safety_policy_validation_summary"),
    )
    required_markers = [
        dict(row)
        for row in (value.get("required_marker_presence") or review.get("required_marker_presence") or [])
        if isinstance(row, Mapping)
    ]
    missing_marker_blockers = [
        dict(row)
        for row in (value.get("missing_marker_blockers") or review.get("missing_marker_blockers") or [])
        if isinstance(row, Mapping)
    ]
    missing_required_markers = _clean_list(
        value.get("missing_required_markers") or review.get("missing_required_markers")
    )
    top_blockers = value.get("top_blocker_reasons") or blockers_summary.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in missing_marker_blockers
            if clean_text(row.get("reason"))
        ][:10]
    required_marker_count = _int_first(marker_summary.get("required_marker_count"), len(required_markers))
    missing_required_marker_count = _int_first(
        value.get("missing_required_marker_count"),
        marker_summary.get("missing_required_marker_count"),
        len(missing_required_markers),
    )
    present_execution_flag_count = _int_first(
        value.get("present_execution_flag_count"),
        marker_summary.get("present_execution_flag_count"),
    )
    return {
        "status": clean_text(
            value.get("status")
            or value.get("source_status")
            or value.get("credentials_readiness_status")
            or "not_available"
        ),
        "market": clean_text(value.get("market") or value.get("market_symbol") or "not_available"),
        "market_symbol": clean_text(value.get("market_symbol") or value.get("market") or "not_available"),
        "strategy_name": clean_text(value.get("strategy_name") or "not_available"),
        "mode": clean_text(value.get("mode") or "explicit live credentials readiness / review-only"),
        "execution_mode": clean_text(value.get("execution_mode") or "preflight"),
        "readiness_status": clean_text(value.get("readiness_status") or "blocked"),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "marker_presence_path": clean_text(value.get("marker_presence_path")),
        "operator_approval_boundary_path": clean_text(value.get("operator_approval_boundary_path")),
        "safety_policy_validation_path": clean_text(value.get("safety_policy_validation_path")),
        "blockers_path": clean_text(value.get("blockers_path")),
        "operator_checklist_path": clean_text(value.get("operator_checklist_path")),
        "readiness_summary_path": clean_text(value.get("readiness_summary_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "marker_summary": marker_summary,
        "required_marker_presence": required_markers,
        "missing_required_markers": missing_required_markers,
        "missing_marker_blockers": missing_marker_blockers,
        "operator_approval_boundary_summary": operator_boundary,
        "safety_policy_validation_summary": safety_policy,
        "blockers_summary": blockers_summary,
        "marker_count": _int_first(marker_summary.get("marker_count"), len(required_markers)),
        "required_marker_count": required_marker_count,
        "missing_required_marker_count": missing_required_marker_count,
        "present_execution_flag_count": present_execution_flag_count,
        "blocker_count": _int_first(
            value.get("blocker_count"),
            blockers_summary.get("blocker_count"),
            len(missing_marker_blockers),
        ),
        "resolved_blocker_count": 0,
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "redacted_presence_review_ready": value.get("redacted_presence_review_ready") is True,
        "presence_only": True,
        "values_never_shown": True,
        "redacted_labels_only": True,
        "credential_values_read": False,
        "credentials_values_read": False,
        "raw_values_emitted": False,
        "broad_environment_scan_performed": False,
        "environment_values_read": False,
        "allowed_for_live": False,
        "live_ready": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "live_connector_enabled": False,
        "signing_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "review_only": True,
        "preflight_only": True,
        "preparation_only": True,
        "gate_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
    }


def _normalize_connection_status_067e_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    return {
        "status": clean_text(value.get("status") or "telegram_wallet_auth_status_missing"),
        "mode": clean_text(value.get("mode") or "local_status_dashboard_only"),
        "execution_mode": clean_text(value.get("execution_mode") or "dry_run_status_read"),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "result_path": clean_text(value.get("result_path")),
        "credentials_marker_artifact_available": value.get("credentials_marker_artifact_available") is True,
        "credentials_marker_path": clean_text(value.get("credentials_marker_path")),
        "clob_l2_auth_readonly_probe_artifact_available": (
            value.get("clob_l2_auth_readonly_probe_artifact_available") is True
        ),
        "clob_l2_auth_readonly_probe_path": clean_text(value.get("clob_l2_auth_readonly_probe_path")),
        "api_keys_added": value.get("api_keys_added") is True,
        "api_keys_status": clean_text(value.get("api_keys_status") or "not_added"),
        "api_keys_display_ru": clean_text(value.get("api_keys_display_ru") or "не добавлены"),
        "api_keys_display_en": clean_text(value.get("api_keys_display_en") or "not added"),
        "private_key_added": value.get("private_key_added") is True,
        "private_key_status": clean_text(value.get("private_key_status") or "not_added"),
        "private_key_display_ru": clean_text(value.get("private_key_display_ru") or "не добавлен"),
        "private_key_display_en": clean_text(value.get("private_key_display_en") or "not added"),
        "wallet_display": clean_text(value.get("wallet_display") or "missing"),
        "signature_type_display": clean_text(value.get("signature_type_display") or "missing"),
        "funder_display": clean_text(value.get("funder_display") or "missing"),
        "l2_auth_probe_status": clean_text(value.get("l2_auth_probe_status") or "not_run"),
        "l2_auth_probe_display": clean_text(value.get("l2_auth_probe_display") or "not run"),
        "open_orders_status": clean_text(value.get("open_orders_status") or "unknown"),
        "balance_allowance_status": clean_text(value.get("balance_allowance_status") or "unknown"),
        "values_never_shown": True,
        "redacted_presence_only": True,
        "local_artifact_read_only": True,
        "dashboard_does_not_run_probe": True,
        "latest_067c_probe_artifact_only": True,
        "credential_values_read": False,
        "credentials_values_read": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "real_authenticated_get_performed": False,
        "wallet_connection_attempted": False,
        "private_key_read": False,
        "signing_attempted": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "balance_read_attempted": False,
        "balance_values_emitted": False,
        "allowance_values_emitted": False,
        "fake_balance_added": False,
        "fake_pnl_added": False,
        "fake_trades_added": False,
        "allowed_for_live": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "live_connector_enabled": False,
        "signing_blocked": True,
        "signed_payload_unavailable": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def _normalize_authenticated_clob_preflight_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    marker_summary = _normalize_clob_l2_marker_preflight_summary(
        dict(value.get("clob_l2_marker_preflight_status_summary") or {})
    )
    no_order_auth_get_summary = _normalize_no_order_auth_get_preflight_summary(
        dict(value.get("no_order_auth_get_preflight_status_summary") or {})
    )
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:8]
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or "not_available"),
        "mode": clean_text(value.get("mode") or "preflight / review-only"),
        "execution_mode": clean_text(value.get("execution_mode") or "preflight"),
        "auth_presence_status": clean_text(
            value.get("auth_presence_status") or value.get("auth_presence") or "not_available"
        ),
        "auth_presence_checked": value.get("auth_presence_check_performed") is True,
        "auth_presence_detected": value.get("auth_presence_detected") is True,
        "clob_base_url_status": clean_text(
            value.get("clob_base_url_status") or value.get("clob_base_url") or "not_available"
        ),
        "header_boundary_status": clean_text(
            value.get("auth_header_boundary_status")
            or value.get("auth_header_boundary")
            or value.get("header_boundary_status")
            or "not_available"
        ),
        "auth_boundary_checked": value.get("auth_boundary_checked") is True,
        "no_order_auth_check_status": clean_text(value.get("no_order_auth_check_status") or "not_available"),
        "no_order_auth_check_performed": value.get("no_order_auth_check_performed") is True,
        "clob_l2_marker_preflight_status_summary": marker_summary,
        "no_order_auth_get_preflight_status_summary": no_order_auth_get_summary,
        "clob_l2_marker_preflight_status": clean_text(
            marker_summary.get("status") or value.get("clob_l2_marker_preflight_status") or "not_available"
        ),
        "clob_base_url_configured": marker_summary.get("clob_base_url_configured") is True
        or value.get("clob_base_url_configured") is True,
        "auth_marker_presence_detected": marker_summary.get("auth_marker_presence_detected") is True
        or value.get("auth_marker_presence_detected") is True,
        "l2_marker_set_complete": marker_summary.get("l2_marker_set_complete") is True,
        "unsafe_l2_marker_detected": marker_summary.get("unsafe_raw_value_detected") is True,
        "auth_boundary_mock_checked": marker_summary.get("auth_boundary_mock_checked") is True
        or value.get("auth_boundary_mock_checked") is True,
        "no_order_auth_plan_ready": marker_summary.get("no_order_auth_plan_ready") is True
        or value.get("no_order_auth_plan_ready") is True,
        "no_order_auth_get_status": clean_text(
            no_order_auth_get_summary.get("no_order_auth_get_status")
            or value.get("no_order_auth_get_status")
            or "not_available"
        ),
        "real_auth_read_only_requested": no_order_auth_get_summary.get("real_auth_read_only_requested") is True
        or value.get("real_auth_read_only_requested") is True,
        "real_auth_read_only_opt_in_present": (
            no_order_auth_get_summary.get("real_auth_read_only_opt_in_present") is True
            or value.get("real_auth_read_only_opt_in_present") is True
        ),
        "real_authenticated_get_performed": (
            no_order_auth_get_summary.get("real_authenticated_get_performed") is True
            or value.get("real_authenticated_get_performed") is True
        ),
        "blocker_count": _int_first(value.get("blocker_count"), len(blockers)),
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "artifact_path": clean_text(value.get("artifact_path")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "review_only": True,
        "preflight_only": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "signing_blocked": True,
        "wallet_connection_blocked": True,
        "balance_read_blocked": True,
        "position_read_blocked": True,
        "live_execution_blocked": True,
        "next_operator_action": clean_text(
            value.get("next_operator_action")
            or "configure redacted L2 presence markers or review blockers; no live order available"
        ),
        "execution_enabling": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
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


def _render_hard_limits_inline(tiny_scaffold: Mapping[str, Any]) -> str:
    value = dict(tiny_scaffold or {})
    hard_limits = dict(value.get("hard_limits_summary", {}))
    return (
        f"status={clean_text(hard_limits.get('status') or 'not_available')}; "
        f"passed={str((hard_limits.get('hard_limits_passed') is True) or (value.get('hard_limits_passed') is True)).lower()}; "
        f"max_notional={_display_known_value(hard_limits.get('max_notional', value.get('max_notional')))}; "
        f"max_size={_display_known_value(hard_limits.get('max_size', value.get('max_size')))}; "
        f"max_price={_display_known_value(hard_limits.get('max_price', value.get('max_price')))}"
    )


def _render_risk_limits_inline(supervised_gate: Mapping[str, Any]) -> str:
    value = dict(supervised_gate or {})
    limits = dict(value.get("risk_limits_summary", {}))
    return (
        f"max_order_notional={_display_known_value(limits.get('max_order_notional_usd'))}; "
        f"max_daily_notional={_display_known_value(limits.get('max_daily_notional_usd'))}; "
        f"max_orders_per_day={_display_known_value(limits.get('max_orders_per_day'))}; "
        f"max_market_count={_display_known_value(limits.get('max_market_count'))}; "
        f"allowed_market={clean_text(limits.get('allowed_market') or 'BTC')}; "
        f"allowed_strategy={clean_text(limits.get('allowed_strategy') or 'tiny-momentum')}; "
        "executable=false"
    )


def _render_plan_inline(supervised_gate: Mapping[str, Any], key: str) -> str:
    plan = dict(dict(supervised_gate or {}).get(key, {}))
    return (
        f"available={str(plan.get('available') is True).lower()}; "
        f"descriptive_only={str(plan.get('plan_is_descriptive_only') is True).lower()}; "
        "executable=false"
    )


def _render_env_readiness_inline(supervised_gate: Mapping[str, Any]) -> str:
    env = dict(dict(supervised_gate or {}).get("env_readiness_summary", {}))
    return (
        f"markers={_display_known_value(env.get('marker_count'))}; "
        f"missing={_display_known_value(env.get('missing_marker_count'))}; "
        "presence_only=true; values_redacted=true; raw_values_emitted=false"
    )


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
        "operator_approved": False,
        "candidate_is_executable": False,
        "signing_available": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "wallet_available": False,
        "ready_for_future_live_enablement": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "credential_values_read": False,
        "credentials_values_read": False,
        "credential_values_serialized": False,
        "credentials_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "raw_values_emitted": False,
        "broad_environment_scan_performed": False,
        "environment_values_read": False,
        "environment_values_serialized": False,
        "environment_values_printed": False,
        "environment_values_stored": False,
        "authenticated_polymarket_enabled": False,
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
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "would_submit_order": False,
        "order_submission_enabled": False,
        "order_cancel_enabled": False,
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
        "resolved_blocker_count": 0,
    }


def _hash_identifier(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    return "telegram-chat-sha256:" + hashlib.sha256(f"pmbot-telegram-chat:{text}".encode("utf-8")).hexdigest()


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
