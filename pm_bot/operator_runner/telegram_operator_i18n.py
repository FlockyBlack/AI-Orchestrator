from __future__ import annotations

from typing import Any, Mapping, Sequence

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


def language_selection_button_rows() -> tuple[tuple[tuple[str, str], ...], ...]:
    return LANGUAGE_SELECTION_BUTTON_ROWS


def panel_launch_button_label(language: str) -> str:
    return PANEL_LAUNCH_BUTTON_LABELS[
        normalize_operator_language(language, fallback=DEFAULT_OPERATOR_LANGUAGE)
    ]


def all_button_rows() -> tuple[tuple[tuple[str, str], ...], ...]:
    rows: list[tuple[tuple[str, str], ...]] = []
    for language in SUPPORTED_LANGUAGES:
        rows.extend(home_button_rows(language))
        rows.extend(panel_fallback_button_rows(language))
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
