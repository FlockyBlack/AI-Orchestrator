from __future__ import annotations

from typing import Any, Mapping, Sequence

from pm_bot.operator_runner.telegram_status_registry import telegram_console_button_rows
from pm_bot.trading_core.schemas import clean_text

SUPPORTED_LANGUAGES = ("ru", "en")
DEFAULT_OPERATOR_LANGUAGE = "ru"
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
        (("🔌 Подключение", "pmbot:connection"), ("💰 Баланс", "pmbot:balance")),
        (("📊 Аналитика", "pmbot:analytics"), ("🚀 Запуск", "pmbot:launch")),
        (("⛔ Остановить", "pmbot:stop"), ("🌐 Mini App", "pmbot:panel")),
        (("⚙️ Настройки", "pmbot:settings"),),
    ),
    "en": (
        (("🔌 Connection", "pmbot:connection"), ("💰 Balance", "pmbot:balance")),
        (("📊 Analytics", "pmbot:analytics"), ("🚀 Launch", "pmbot:launch")),
        (("⛔ Stop", "pmbot:stop"), ("🌐 Mini App", "pmbot:panel")),
        (("⚙️ Settings", "pmbot:settings"),),
    ),
}

PANEL_FALLBACK_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🔌 Подключение", "pmbot:connection"), ("💰 Баланс", "pmbot:balance")),
        (("📊 Аналитика", "pmbot:analytics"), ("🚀 Запуск", "pmbot:launch")),
        (("⚙️ Настройки", "pmbot:settings"),),
    ),
    "en": (
        (("🔌 Connection", "pmbot:connection"), ("💰 Balance", "pmbot:balance")),
        (("📊 Analytics", "pmbot:analytics"), ("🚀 Launch", "pmbot:launch")),
        (("⚙️ Settings", "pmbot:settings"),),
    ),
}

PANEL_LAUNCH_BUTTON_LABELS = {
    "ru": "Открыть Mini App",
    "en": "Open Mini App",
}

PRODUCT_DESCRIPTION_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("Главное меню", "pmbot:home"),),
    ),
    "en": (
        (("Main menu", "pmbot:home"),),
    ),
}

CONNECTION_PRODUCT_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🔄 Проверить снова", "pmbot:connection:check"),),
        (("📘 Инструкция", "pmbot:connection:instruction"),),
        (("💰 Перейти к балансу", "pmbot:balance"),),
        (("⬅️ Главное меню", "pmbot:home"),),
    ),
    "en": (
        (("🔄 Check again", "pmbot:connection:check"),),
        (("📘 Guide", "pmbot:connection:instruction"),),
        (("💰 Go to balance", "pmbot:balance"),),
        (("⬅️ Main menu", "pmbot:home"),),
    ),
}

BALANCE_MISSING_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🔌 Перейти к подключению", "pmbot:connection"),),
    ),
    "en": (
        (("🔌 Go to connection", "pmbot:connection"),),
    ),
}

BALANCE_CONNECTION_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🔌 Подключение", "pmbot:connection"),),
    ),
    "en": (
        (("🔌 Connection", "pmbot:connection"),),
    ),
}

BALANCE_PRODUCT_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🔄 Обновить", "pmbot:balance"),),
        (("🔌 Подключение", "pmbot:connection"),),
        (("⬅️ Главное меню", "pmbot:home"),),
    ),
    "en": (
        (("🔄 Refresh", "pmbot:balance"),),
        (("🔌 Connection", "pmbot:connection"),),
        (("⬅️ Main menu", "pmbot:home"),),
    ),
}

ANALYTICS_PRODUCT_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🔄 Обновить", "pmbot:analytics"),),
        (("📈 Подробнее", "pmbot:analytics:details"),),
        (("⬅️ Главное меню", "pmbot:home"),),
    ),
    "en": (
        (("🔄 Refresh", "pmbot:analytics"),),
        (("📈 Details", "pmbot:analytics:details"),),
        (("⬅️ Main menu", "pmbot:home"),),
    ),
}

LAUNCH_PRODUCT_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🔄 Обновить", "pmbot:launch"),),
        (("📋 Подробнее", "pmbot:launch:details"),),
        (("🔌 Подключение", "pmbot:connection"),),
        (("💰 Баланс", "pmbot:balance"),),
        (("⬅️ Главное меню", "pmbot:home"),),
    ),
    "en": (
        (("🔄 Refresh", "pmbot:launch"),),
        (("📋 Details", "pmbot:launch:details"),),
        (("🔌 Connection", "pmbot:connection"),),
        (("💰 Balance", "pmbot:balance"),),
        (("⬅️ Main menu", "pmbot:home"),),
    ),
}

LAUNCH_LIMIT_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("$5", "pmbot:launch:limit:5"), ("$10", "pmbot:launch:limit:10")),
        (("$25", "pmbot:launch:limit:25"), ("$50", "pmbot:launch:limit:50")),
        (("Ввести вручную", "pmbot:launch:limit:manual"),),
        (("⬅️ Запуск", "pmbot:launch"),),
    ),
    "en": (
        (("$5", "pmbot:launch:limit:5"), ("$10", "pmbot:launch:limit:10")),
        (("$25", "pmbot:launch:limit:25"), ("$50", "pmbot:launch:limit:50")),
        (("Enter manually", "pmbot:launch:limit:manual"),),
        (("⬅️ Launch", "pmbot:launch"),),
    ),
}

LAUNCH_MAX_LOSS_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("$1", "pmbot:launch:max_loss:1"), ("$2", "pmbot:launch:max_loss:2")),
        (("$5", "pmbot:launch:max_loss:5"),),
        (("10% от дневного лимита", "pmbot:launch:max_loss:10pct"),),
        (("Ввести вручную", "pmbot:launch:max_loss:manual"),),
        (("⬅️ Запуск", "pmbot:launch"),),
    ),
    "en": (
        (("$1", "pmbot:launch:max_loss:1"), ("$2", "pmbot:launch:max_loss:2")),
        (("$5", "pmbot:launch:max_loss:5"),),
        (("10% of daily limit", "pmbot:launch:max_loss:10pct"),),
        (("Enter manually", "pmbot:launch:max_loss:manual"),),
        (("⬅️ Launch", "pmbot:launch"),),
    ),
}

LAUNCH_MARKET_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("BTC", "pmbot:launch:market:btc"), ("ETH", "pmbot:launch:market:eth")),
        (("Politics", "pmbot:launch:market:politics"), ("Sports", "pmbot:launch:market:sports")),
        (("Esports", "pmbot:launch:market:esports"),),
        (("Добавить рынок", "pmbot:launch:market:add"),),
        (("⬅️ Запуск", "pmbot:launch"),),
    ),
    "en": (
        (("BTC", "pmbot:launch:market:btc"), ("ETH", "pmbot:launch:market:eth")),
        (("Politics", "pmbot:launch:market:politics"), ("Sports", "pmbot:launch:market:sports")),
        (("Esports", "pmbot:launch:market:esports"),),
        (("Add market", "pmbot:launch:market:add"),),
        (("⬅️ Launch", "pmbot:launch"),),
    ),
}

STOP_PRODUCT_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🚀 Перейти к запуску", "pmbot:launch"),),
        (("⬅️ Главное меню", "pmbot:home"),),
    ),
    "en": (
        (("🚀 Go to launch", "pmbot:launch"),),
        (("⬅️ Main menu", "pmbot:home"),),
    ),
}

MINI_APP_PRODUCT_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("⬅️ Главное меню", "pmbot:home"),),
    ),
    "en": (
        (("⬅️ Main menu", "pmbot:home"),),
    ),
}

SETTINGS_PRODUCT_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🌐 Изменить язык", "pmbot:language"),),
        (("⬅️ Главное меню", "pmbot:home"),),
    ),
    "en": (
        (("🌐 Change language", "pmbot:language"),),
        (("⬅️ Main menu", "pmbot:home"),),
    ),
}

CONNECTION_STATUS_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🧪 Проверить подключение", "pmbot:run:connection_status_067e"),),
        (("⬅️ Назад", "pmbot:home"),),
    ),
    "en": (
        (("🧪 Check connection", "pmbot:run:connection_status_067e"),),
        (("⬅️ Back", "pmbot:home"),),
    ),
}

REAL_CHECK_RESULTS_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🔄 Обновить", "pmbot:connection"),),
        (("🧪 Запустить локальную проверку", "pmbot:run:local_real_check_bundle_072c"),),
        (("⬅️ Назад", "pmbot:home"),),
    ),
    "en": (
        (("🔄 Refresh", "pmbot:connection"),),
        (("🧪 Run local check", "pmbot:run:local_real_check_bundle_072c"),),
        (("⬅️ Back", "pmbot:home"),),
    ),
}

ORDER_PREP_STATUS_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("Обновить статус", "pmbot:order_prep_status"),),
        (("Назад", "pmbot:home"),),
    ),
    "en": (
        (("Refresh status", "pmbot:order_prep_status"),),
        (("Back", "pmbot:home"),),
    ),
}

ORDER_PREP_PACKET_STATUS_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("🔄 Обновить", "pmbot:order_prep_status"),),
        (("🔎 Найти рынок", "pmbot:btc"),),
        (("🧪 Проверить подключение", "pmbot:connection_status"),),
        (("⬅️ Назад", "pmbot:home"),),
    ),
    "en": (
        (("🔄 Refresh", "pmbot:order_prep_status"),),
        (("🔎 Find market", "pmbot:btc"),),
        (("🧪 Check connection", "pmbot:connection_status"),),
        (("⬅️ Back", "pmbot:home"),),
    ),
}

OPERATOR_TOKEN_SELECTION_BUTTON_ROWS_BY_LANGUAGE = {
    "ru": (
        (("Обновить", "pmbot:token_selection"),),
        (("Кандидат 1", "pmbot:token_selection:candidate:0"), ("Кандидат 2", "pmbot:token_selection:candidate:1")),
        (("Назад", "pmbot:home"),),
    ),
    "en": (
        (("Refresh", "pmbot:token_selection"),),
        (("Candidate 1", "pmbot:token_selection:candidate:0"), ("Candidate 2", "pmbot:token_selection:candidate:1")),
        (("Back", "pmbot:home"),),
    ),
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

SUPERVISED_LIVE_ENABLEMENT_REVIEW_LABELS = {
    "ru": {
        "section": "Обзор supervised readiness 063",
        "status": "Статус 063",
        "checklist": "Чеклист оператора",
        "blockers": "Матрица блокеров",
        "risk_limits": "Лимиты риска",
        "kill_switch": "Kill switch план",
        "cancel_plan": "Cancel plan",
        "failure_plan": "Failure plan",
        "env_readiness": "Готовность окружения",
        "manual_approval_packet": "Пакет ручного подтверждения",
        "run_dry_run": "Локальная dry-run команда 063",
        "review_only": "Только просмотр",
        "dry_run_only": "Только dry-run",
        "not_executable": "Не исполняется",
        "operator_approval_required": "Требуется подтверждение оператора",
        "operator_approved_false": "Оператор подтвердил: нет",
        "candidate_not_executable": "Кандидат не исполняемый",
        "env_presence_only": "Окружение: только presence/redacted",
        "resolved_zero": "resolved_blocker_count: 0",
        "allowed_live_false": "allowed_for_live: false",
    },
    "en": {
        "section": "Supervised readiness review 063",
        "status": "063 status",
        "checklist": "Operator checklist",
        "blockers": "Blocker matrix",
        "risk_limits": "Risk limits",
        "kill_switch": "Kill switch plan",
        "cancel_plan": "Cancel plan",
        "failure_plan": "Failure plan",
        "env_readiness": "Env readiness",
        "manual_approval_packet": "Manual approval packet",
        "run_dry_run": "Local 063 dry-run command",
        "review_only": "Review only",
        "dry_run_only": "Dry-run only",
        "not_executable": "Not executable",
        "operator_approval_required": "Operator approval required",
        "operator_approved_false": "Operator approved: false",
        "candidate_not_executable": "Candidate is executable: false",
        "env_presence_only": "Env readiness: presence-only/redacted",
        "resolved_zero": "resolved_blocker_count: 0",
        "allowed_live_false": "allowed_for_live: false",
    },
}

CREDENTIALS_READINESS_REVIEW_LABELS = {
    "ru": {
        "section": "Проверка готовности credentials",
        "status": "Статус credentials readiness",
        "readiness": "Readiness status",
        "markers": "Маркеры",
        "missing_markers": "Недостающие маркеры",
        "blockers": "Блокеры маркеров",
        "operator_boundary": "Граница подтверждения оператора",
        "safety_policy": "Проверка safety policy",
        "warning": (
            "Presence-only не проверяет корректность, funding, permissions или безопасность секретов; "
            "проверяются только имена маркеров."
        ),
        "presence_only": "Только наличие маркеров",
        "values_never_shown": "Значения не показываются",
        "not_live_enabled": "Live не включён",
        "dry_run_only": "Только dry-run",
        "run_dry_run": "Dry-run credentials readiness 064",
        "resolved_zero": "resolved_blocker_count: 0",
        "allowed_live_false": "allowed_for_live: false",
    },
    "en": {
        "section": "Credentials readiness review",
        "status": "Credentials readiness status",
        "readiness": "Readiness status",
        "markers": "Markers",
        "missing_markers": "Missing markers",
        "blockers": "Marker blockers",
        "operator_boundary": "Operator approval boundary",
        "safety_policy": "Safety policy validation",
        "warning": (
            "Presence-only cannot validate correctness, funding, permissions, or safety of secrets; "
            "it checks marker names only."
        ),
        "presence_only": "Presence-only",
        "values_never_shown": "Values never shown",
        "not_live_enabled": "Not live-enabled",
        "dry_run_only": "Dry-run only",
        "run_dry_run": "Dry-run credentials readiness 064",
        "resolved_zero": "resolved_blocker_count: 0",
        "allowed_live_false": "allowed_for_live: false",
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


def connection_status_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return CONNECTION_STATUS_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def real_check_results_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return REAL_CHECK_RESULTS_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def order_prep_status_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return ORDER_PREP_STATUS_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def order_prep_packet_status_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return ORDER_PREP_PACKET_STATUS_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def operator_token_selection_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return OPERATOR_TOKEN_SELECTION_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def product_description_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return PRODUCT_DESCRIPTION_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def connection_product_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return CONNECTION_PRODUCT_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def balance_missing_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return BALANCE_MISSING_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def balance_connection_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return BALANCE_CONNECTION_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def balance_product_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return BALANCE_PRODUCT_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def analytics_product_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return ANALYTICS_PRODUCT_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def launch_product_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return LAUNCH_PRODUCT_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def launch_limit_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return LAUNCH_LIMIT_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def launch_max_loss_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return LAUNCH_MAX_LOSS_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def launch_market_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return LAUNCH_MARKET_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def stop_product_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return STOP_PRODUCT_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def mini_app_product_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return MINI_APP_PRODUCT_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def settings_product_button_rows(language: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return SETTINGS_PRODUCT_BUTTON_ROWS_BY_LANGUAGE[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


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


def supervised_live_enablement_review_label(key: str, language: str) -> str:
    labels = SUPERVISED_LIVE_ENABLEMENT_REVIEW_LABELS[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]
    return labels.get(clean_text(key), "")


def credentials_readiness_review_label(key: str, language: str) -> str:
    labels = CREDENTIALS_READINESS_REVIEW_LABELS[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]
    return labels.get(clean_text(key), "")


def all_button_rows() -> tuple[tuple[tuple[str, str], ...], ...]:
    rows: list[tuple[tuple[str, str], ...]] = []
    for language in SUPPORTED_LANGUAGES:
        rows.extend(home_button_rows(language))
        rows.extend(product_description_button_rows(language))
        rows.extend(connection_product_button_rows(language))
        rows.extend(balance_missing_button_rows(language))
        rows.extend(balance_connection_button_rows(language))
        rows.extend(balance_product_button_rows(language))
        rows.extend(analytics_product_button_rows(language))
        rows.extend(launch_product_button_rows(language))
        rows.extend(launch_limit_button_rows(language))
        rows.extend(launch_max_loss_button_rows(language))
        rows.extend(launch_market_button_rows(language))
        rows.extend(stop_product_button_rows(language))
        rows.extend(mini_app_product_button_rows(language))
        rows.extend(settings_product_button_rows(language))
        rows.extend(panel_fallback_button_rows(language))
        rows.extend(operator_console_button_rows(language))
        rows.extend(connection_status_button_rows(language))
        rows.extend(real_check_results_button_rows(language))
        rows.extend(order_prep_status_button_rows(language))
        rows.extend(order_prep_packet_status_button_rows(language))
        rows.extend(operator_token_selection_button_rows(language))
    rows.extend(language_selection_button_rows())
    return tuple(rows)


def callback_data_values(rows: Sequence[Sequence[tuple[str, str]]]) -> tuple[str, ...]:
    return tuple(callback_data for row in rows for _label, callback_data in row)


def render_language_selection_prompt() -> str:
    return "Выберите язык"


def render_home(language: str) -> str:
    if normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE) == "ru":
        return "\n".join(
            [
                "PMBOT",
                "Главное меню",
            ]
        )
    return "\n".join(
        [
            "PMBOT",
            "Main menu",
        ]
    )


def render_language_selected(language: str) -> str:
    if normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE) == "ru":
        return "\n\n".join(
            [
                "PMBOT — торговый помощник для Polymarket.",
                (
                    "Он помогает подключить аккаунт, выбрать рынки, настроить лимиты, "
                    "отслеживать баланс, аналитику и запускать торговлю под вашим контролем."
                ),
                (
                    "Вы можете пользоваться быстрым Telegram-меню или открыть Mini App "
                    "с расширенной панелью, графиками и подробной статистикой."
                ),
            ]
        )
    return "\n\n".join(
        [
            "PMBOT is a trading assistant for Polymarket.",
            (
                "It helps connect your account, choose markets, set limits, monitor balance and analytics, "
                "and launch trading under your control."
            ),
            (
                "You can use the quick Telegram menu or open the Mini App with an expanded dashboard, "
                "charts, and detailed statistics."
            ),
        ]
    )
