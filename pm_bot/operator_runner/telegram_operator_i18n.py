from __future__ import annotations

from typing import Any, Mapping, Sequence

from pm_bot.operator_runner.telegram_status_registry import telegram_console_button_rows
from pm_bot.trading_core.schemas import clean_text

SUPPORTED_LANGUAGES = ("ru", "en")
DEFAULT_OPERATOR_LANGUAGE = "en"
RECOMMENDED_OPERATOR_LANGUAGE = "ru"
LANGUAGE_STATE_FIELD = "operator_language"

LANGUAGE_CALLBACK_DATA = {
    "pmbot:lang:ru": "ru",
    "pmbot:lang:en": "en",
}

LANGUAGE_SELECTION_BUTTON_ROWS = (
    (("🇷🇺 Русский", "pmbot:lang:ru"), ("🇬🇧 English", "pmbot:lang:en")),
)

HOME_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("📊 Статус", "pmbot:status"), ("✅ Go/No-Go", "pmbot:gonogo")),
        (("⚠️ Риски", "pmbot:risk"), ("🚧 Блокеры", "pmbot:blockers")),
        (("📦 Evidence", "pmbot:evidence"), ("🧩 Mini App", "pmbot:panel")),
        (("⏸ Пауза", "pmbot:pause"), ("🛑 Kill-switch", "pmbot:kill")),
        (("🌐 Язык", "pmbot:language"),),
    ),
    "en": (
        (("Status", "pmbot:status"), ("Go/No-Go", "pmbot:gonogo")),
        (("Risk", "pmbot:risk"), ("Blockers", "pmbot:blockers")),
        (("Evidence", "pmbot:evidence"), ("Panel", "pmbot:panel")),
        (("Pause", "pmbot:pause"), ("Kill", "pmbot:kill")),
        (("Language", "pmbot:language"),),
    ),
}

PANEL_FALLBACK_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("📊 Статус", "pmbot:status"), ("✅ Go/No-Go", "pmbot:gonogo")),
        (("🚧 Блокеры", "pmbot:blockers"),),
        (("🌐 Язык", "pmbot:language"),),
    ),
    "en": (
        (("Status", "pmbot:status"), ("Go/No-Go", "pmbot:gonogo")),
        (("Blockers", "pmbot:blockers"),),
        (("Language", "pmbot:language"),),
    ),
}

PANEL_LAUNCH_BUTTON_LABELS = {
    "ru": "Открыть PMBOT Mini App",
    "en": "Open PMBOT Mini App",
}

TINY_ORDER_REVIEW_LABELS = {
    "ru": {
        "section": "Малый ордер",
        "tiny_candidate": "Tiny Candidate",
        "approval_packet": "Пакет ручного подтверждения",
        "hard_limits": "Лимиты",
        "submission_status": "Submission Status",
        "run_dry_run": "Run Tiny Scaffold Dry-Run",
        "operator_approved_false": "Оператор подтвердил: нет",
        "candidate_not_executable": "Кандидат не исполняемый",
        "signing_blocked": "Подписание заблокировано",
        "order_submission_blocked": "Отправка ордера заблокирована",
        "wallet_blocked": "Кошелёк заблокирован",
        "live_blocked": "Live-торговля заблокирована",
    },
    "en": {
        "section": "Tiny Order Review",
        "tiny_candidate": "Tiny Candidate",
        "approval_packet": "Approval Packet",
        "hard_limits": "Hard Limits",
        "submission_status": "Submission Status",
        "run_dry_run": "Run Tiny Scaffold Dry-Run",
        "operator_approved_false": "Operator approved: false",
        "candidate_not_executable": "Candidate is executable: false",
        "signing_blocked": "Signing blocked",
        "order_submission_blocked": "Order submission blocked",
        "wallet_blocked": "Wallet blocked",
        "live_blocked": "Live execution blocked",
    },
}

PRE_LIVE_GATE_REVIEW_LABELS = {
    "ru": {
        "section": "Предлайв-гейт tiny order",
        "status": "Статус 062P",
        "checklist": "Чеклист",
        "blockers": "Блокеры",
        "readiness": "Readiness summary",
        "operator_md": "Операторский markdown",
        "run_dry_run": "Dry-run предлайв-гейта 062P",
        "review_only": "Только обзор",
        "dry_run_only": "Только dry-run",
        "operator_approved_false": "Оператор подтвердил: нет",
        "candidate_not_executable": "Кандидат не исполняемый",
        "signing_unavailable": "Подписание недоступно",
        "order_submission_unavailable": "Отправка ордера недоступна",
        "wallet_unavailable": "Кошелёк недоступен",
        "live_blocked": "Live-торговля заблокирована",
        "ready_future_false": "Готовность к future live enablement: false",
        "allowed_live_false": "allowed_for_live: false",
        "resolved_zero": "resolved_blocker_count: 0",
    },
    "en": {
        "section": "Pre-live tiny order gate",
        "status": "062P status",
        "checklist": "Checklist",
        "blockers": "Blockers",
        "readiness": "Readiness summary",
        "operator_md": "Operator markdown",
        "run_dry_run": "Run Pre-live Gate 062P Dry-Run",
        "review_only": "Review-only",
        "dry_run_only": "Dry-run only",
        "operator_approved_false": "Operator approved: false",
        "candidate_not_executable": "Candidate is executable: false",
        "signing_unavailable": "Signing unavailable",
        "order_submission_unavailable": "Order submission unavailable",
        "wallet_unavailable": "Wallet unavailable",
        "live_blocked": "Live execution blocked",
        "ready_future_false": "Ready for future live enablement: false",
        "allowed_live_false": "allowed_for_live: false",
        "resolved_zero": "resolved_blocker_count: 0",
    },
}


def normalize_operator_language(value: Any, *, fallback: str = "") -> str:
    language = clean_text(value).lower()
    if language in SUPPORTED_LANGUAGES:
        return language
    return fallback if fallback in SUPPORTED_LANGUAGES else ""


def operator_language_from_state(
    state: Mapping[str, Any] | None,
    *,
    fallback: str = DEFAULT_OPERATOR_LANGUAGE,
) -> str:
    state_value = dict(state or {})
    return normalize_operator_language(state_value.get(LANGUAGE_STATE_FIELD), fallback=fallback)


def operator_language_is_selected(state: Mapping[str, Any] | None) -> bool:
    state_value = dict(state or {})
    return bool(normalize_operator_language(state_value.get(LANGUAGE_STATE_FIELD)))


def language_from_callback(callback_data: str) -> str:
    return LANGUAGE_CALLBACK_DATA.get(clean_text(callback_data), "")


def language_from_command_text(text: str) -> str:
    parts = clean_text(text).split(maxsplit=1)
    if len(parts) < 2:
        return ""
    return normalize_operator_language(parts[1])


def home_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return HOME_BUTTON_ROWS_BY_LANGUAGE[normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)]


def panel_fallback_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return PANEL_FALLBACK_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def operator_console_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return telegram_console_button_rows(normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE))


def language_selection_button_rows() -> tuple[tuple[tuple[str, str], ...], ...]:
    return LANGUAGE_SELECTION_BUTTON_ROWS


def panel_launch_button_label(language: str) -> str:
    return PANEL_LAUNCH_BUTTON_LABELS[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def tiny_order_review_label(key: str, language: str) -> str:
    labels = TINY_ORDER_REVIEW_LABELS[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]
    return labels.get(clean_text(key), "")


def pre_live_gate_review_label(key: str, language: str) -> str:
    labels = PRE_LIVE_GATE_REVIEW_LABELS[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]
    return labels.get(clean_text(key), "")


def all_button_rows() -> tuple[tuple[tuple[str, str], ...], ...]:
    rows: list[tuple[tuple[str, str], ...]] = []
    for language in SUPPORTED_LANGUAGES:
        rows.extend(home_button_rows(language))
        rows.extend(panel_fallback_button_rows(language))
        rows.extend(operator_console_button_rows(language))
    rows.extend(language_selection_button_rows())
    return tuple(rows)


def callback_data_values(rows: Sequence[Sequence[tuple[str, str]]]) -> tuple[str, ...]:
    return tuple(callback_data for row in rows for _label, callback_data in row)


def render_language_selection_prompt() -> str:
    return "\n".join(
        [
            "Выбери язык оператора / Choose operator language",
            "🇷🇺 Русский — рекомендуется для первого запуска",
            "🇬🇧 English",
        ]
    )


def render_home(language: str) -> str:
    if normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE) == "ru":
        return "\n".join(
            [
                "PMBOT — операторская панель",
                "Режим: только обзор",
                "Live-торговля: выключена",
                "Ордера: выключены",
                "Кошелёк/подпись: выключены",
            ]
        )
    return "\n".join(
        [
            "PMBOT Operator Control",
            "Review-only",
            "Live blocked",
            "Orders disabled",
            "Wallet/signing disabled",
            "PMBOT Operator Control Bot v1 does not enable live trading, submit orders, connect wallets, "
            "sign payloads, or call authenticated Polymarket endpoints.",
        ]
    )


def render_language_selected(language: str) -> str:
    if normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE) == "ru":
        return "Язык: русский.\n\n" + render_home("ru")
    return "Language: English.\n\n" + render_home("en")
