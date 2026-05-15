from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, normalize_path, write_json
from pm_bot.trading_core.telegram_order_prep_status_071e import (
    ARTIFACT_DIR_NAME as TELEGRAM_ORDER_PREP_STATUS_071E_ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME as TELEGRAM_ORDER_PREP_STATUS_071E_LATEST_STATUS_FILENAME,
)

TASK_ID = "ORCH-PMBOT-TELEGRAM-072B-ORDER-PREP-PACKET-SCREEN-NO-LIVE"

STATUS_CONTRACT = "pmbot_telegram_order_prep_packet_screen_072b.v1"
RESULT_CONTRACT = "pmbot_telegram_order_prep_packet_screen_072b_result.v1"
MENU_SNAPSHOT_CONTRACT = "pmbot_telegram_order_prep_packet_screen_072b_menu_snapshot.v1"
SAFETY_SNAPSHOT_CONTRACT = "pmbot_telegram_order_prep_packet_screen_072b_safety_snapshot.v1"

ARTIFACT_DIR_NAME = "telegram_order_prep_packet_screen_072b"
RESULT_FILENAME = "telegram_order_prep_packet_screen_072b_result.json"
LATEST_STATUS_FILENAME = "latest_telegram_order_prep_packet_screen_072b.json"
MENU_SNAPSHOT_FILENAME = "telegram_order_prep_packet_screen_menu_snapshot_072b.json"
SAFETY_SNAPSHOT_FILENAME = "telegram_order_prep_packet_screen_safety_snapshot_072b.json"

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME

ORDER_PREP_PACKET_072A_DIR_NAMES = (
    "order_prep_packet_072a",
    "first_order_prep_packet_072a",
    "order_prep_packet_from_discovery_072a",
    "first_order_prep_packet_from_discovery_072a",
    "first_order_preparation_packet_072a",
)
ORDER_PREP_PACKET_072A_FILENAMES = (
    "latest_order_prep_packet_072a.json",
    "latest_first_order_prep_packet_072a.json",
    "latest_order_prep_packet_from_discovery_072a.json",
    "order_prep_packet_072a_result.json",
    "first_order_prep_packet_072a_result.json",
    "order_prep_packet_from_discovery_072a_result.json",
)

LEGACY_071E_DIR_NAMES = (TELEGRAM_ORDER_PREP_STATUS_071E_ARTIFACT_DIR_NAME,)
LEGACY_071E_FILENAMES = (TELEGRAM_ORDER_PREP_STATUS_071E_LATEST_STATUS_FILENAME,)

CONTROL_BUTTON_ROWS_RU = (
    (("🔄 Обновить", "pmbot:order_prep_status"),),
    (("🔎 Найти рынок", "pmbot:btc"),),
    (("🧪 Проверить подключение", "pmbot:connection_status"),),
    (("⬅️ Назад", "pmbot:home"),),
)
CONTROL_BUTTON_ROWS_EN = (
    (("🔄 Refresh", "pmbot:order_prep_status"),),
    (("🔎 Find market", "pmbot:btc"),),
    (("🧪 Check connection", "pmbot:connection_status"),),
    (("⬅️ Back", "pmbot:home"),),
)

_ABSENT_TEXT = {
    "",
    "0",
    "false",
    "missing",
    "none",
    "not_available",
    "not available",
    "not_found",
    "not found",
    "unknown",
    "unavailable",
    "null",
}


def telegram_order_prep_packet_status_artifact_paths(
    output_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(output_dir) if output_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / RESULT_FILENAME,
        "latest_status": root / LATEST_STATUS_FILENAME,
        "menu_snapshot": root / MENU_SNAPSHOT_FILENAME,
        "safety_snapshot": root / SAFETY_SNAPSHOT_FILENAME,
    }


def build_telegram_order_prep_packet_status(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    packet_path = find_latest_order_prep_packet_072a_artifact(root)
    legacy_071e_path = _first_existing_path(_candidate_paths(root, LEGACY_071E_DIR_NAMES, LEGACY_071E_FILENAMES))

    raw_packet = _load_optional_json(packet_path, "072A order prep packet")
    packet = _extract_packet_payload(raw_packet)
    legacy_071e = _load_optional_json(legacy_071e_path, "071E order prep status")
    packet_available = bool(packet)

    market_display_ru, market_display_en, market_found = _market_display(packet, available=packet_available)
    token_display_ru, token_display_en, token_selected = _token_display(packet, available=packet_available)
    account_display_ru, account_display_en, account_readonly_ok = _account_display(packet, available=packet_available)
    l2_display_ru, l2_display_en, l2_auth_ok = _l2_auth_display(packet, available=packet_available)
    signer_display_ru, signer_display_en, signer_ok = _signer_display(packet, available=packet_available)
    approval_display_ru, approval_display_en, approval_ready = _approval_display(packet, available=packet_available)
    payload_display_ru, payload_display_en, payload_dry_run_ready = _payload_dry_run_display(
        packet,
        available=packet_available,
    )

    latest_status: dict[str, Any] = {
        "contract_version": STATUS_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "packet_ready_for_review" if packet_available else "packet_not_built",
        "mode": "local_artifact_packet_screen_only",
        "execution_mode": "local_artifact_read_only",
        "telegram_screen_title_ru": "🧪 Подготовка первого ордера",
        "telegram_screen_title_en": "First order prep",
        "artifact_root": normalize_path(root),
        "order_prep_packet_072a_artifact_available": packet_available,
        "order_prep_packet_072a_artifact_path": normalize_path(packet_path) if packet_path else "",
        "legacy_071e_artifact_available": bool(legacy_071e),
        "legacy_071e_artifact_path": normalize_path(legacy_071e_path) if legacy_071e_path else "",
        "missing_packet_message_ru": "" if packet_available else "Пакет подготовки ещё не собран",
        "missing_packet_message_en": "" if packet_available else "Preparation packet has not been built yet",
        "market_found": market_found,
        "market_display_ru": market_display_ru,
        "market_display_en": market_display_en,
        "token_id_selected": token_selected,
        "token_id_display_ru": token_display_ru,
        "token_id_display_en": token_display_en,
        "account_readonly_ok": account_readonly_ok,
        "account_display_ru": account_display_ru,
        "account_display_en": account_display_en,
        "l2_auth_ok": l2_auth_ok,
        "l2_auth_display_ru": l2_display_ru,
        "l2_auth_display_en": l2_display_en,
        "signer_ok": signer_ok,
        "signer_display_ru": signer_display_ru,
        "signer_display_en": signer_display_en,
        "approval_ready": approval_ready,
        "approval_display_ru": approval_display_ru,
        "approval_display_en": approval_display_en,
        "payload_dry_run_ready": payload_dry_run_ready,
        "payload_dry_run_display_ru": payload_display_ru,
        "payload_dry_run_display_en": payload_display_en,
        "live_display_ru": "выключен",
        "live_display_en": "disabled",
        "order_submission_display_ru": "выключена",
        "order_submission_display_en": "disabled",
        "screen_buttons": [
            {"label_ru": label, "callback_data": callback_data}
            for row in CONTROL_BUTTON_ROWS_RU
            for label, callback_data in row
        ],
        "source_artifacts": {
            "order_prep_packet_072a": _artifact_summary(packet_path, raw_packet),
            "legacy_071e": _artifact_summary(legacy_071e_path, legacy_071e),
        },
        "raw_token_id_exposed": False,
        "raw_account_values_exposed": False,
        "raw_secret_output": False,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **telegram_order_prep_packet_status_safety_flags(),
    }
    latest_status["status_text_ru"] = render_telegram_order_prep_packet_status_text(latest_status, language="ru")
    latest_status["status_text_en"] = render_telegram_order_prep_packet_status_text(latest_status, language="en")
    return latest_status


def write_telegram_order_prep_packet_status_072b_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    status = build_telegram_order_prep_packet_status(artifact_root=artifact_root, generated_at=generated_at)
    paths = telegram_order_prep_packet_status_artifact_paths(output_dir)
    menu = build_telegram_order_prep_packet_status_menu_snapshot(generated_at=generated_at)
    safety = build_telegram_order_prep_packet_status_safety_snapshot(generated_at=generated_at)
    result = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "completed_review_only",
        "latest_status_path": normalize_path(paths["latest_status"]),
        "menu_snapshot_path": normalize_path(paths["menu_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "telegram_order_prep_packet_status_072b": status,
        "menu_snapshot": menu,
        "safety_snapshot": safety,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **telegram_order_prep_packet_status_safety_flags(),
    }
    write_json(paths["latest_status"], status)
    write_json(paths["menu_snapshot"], menu)
    write_json(paths["safety_snapshot"], safety)
    write_json(paths["result"], result)
    return {
        "result_path": normalize_path(paths["result"]),
        "latest_status_path": normalize_path(paths["latest_status"]),
        "menu_snapshot_path": normalize_path(paths["menu_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "result": result,
        "latest_status": status,
        "menu_snapshot": menu,
        "safety_snapshot": safety,
    }


def build_telegram_order_prep_packet_status_menu_snapshot(
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    buttons = [
        *_button_rows("ru", CONTROL_BUTTON_ROWS_RU),
        *_button_rows("en", CONTROL_BUTTON_ROWS_EN),
    ]
    return {
        "contract_version": MENU_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "title_ru": "🧪 Подготовка первого ордера",
        "title_en": "First order prep",
        "buttons": buttons,
        "button_count": len(buttons),
        "allowed_callbacks": [
            "pmbot:order_prep_status",
            "pmbot:btc",
            "pmbot:connection_status",
            "pmbot:home",
        ],
        "primary_button_labels_avoid_technical_terms": True,
        "forbidden_live_controls_added": False,
        "submit_cancel_controls_added": False,
        "signing_controls_added": False,
        "wallet_controls_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_order_prep_packet_status_safety_flags(),
    }


def build_telegram_order_prep_packet_status_safety_snapshot(
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "safe_local_packet_screen_only",
        "allowed_inputs": [
            "local 072A order prep packet artifacts when present",
            "local 071E status artifacts for compatibility metadata when present",
        ],
        "forbidden_actions": [
            "wallet connection",
            "signing",
            "order submission",
            "order cancellation",
            "authenticated calls from Telegram",
            "live enablement",
            "fake balances, trades, or PnL",
        ],
        "local_artifact_read_only": True,
        "same_message_navigation_preserved": True,
        "no_static_safety_invariant_report_button": True,
        "no_fake_balance_pnl_or_trades": True,
        **telegram_order_prep_packet_status_safety_flags(),
    }


def render_telegram_order_prep_packet_status_text(status: Mapping[str, Any], *, language: str = "ru") -> str:
    value = dict(status or {})
    if clean_text(language).lower() == "ru":
        lines = ["🧪 Подготовка первого ордера"]
        missing = clean_text(value.get("missing_packet_message_ru"))
        if missing:
            lines.append(missing)
        lines.extend(
            [
                f"Рынок: {clean_text(value.get('market_display_ru') or 'не найден')}",
                f"Token ID: {clean_text(value.get('token_id_display_ru') or 'требуется выбор')}",
                f"Аккаунт: {clean_text(value.get('account_display_ru') or 'не проверен')}",
                f"L2 auth: {clean_text(value.get('l2_auth_display_ru') or 'unknown')}",
                f"Signer: {clean_text(value.get('signer_display_ru') or 'не проверен')}",
                f"Approval: {clean_text(value.get('approval_display_ru') or 'не найден')}",
                f"Payload dry-run: {clean_text(value.get('payload_dry_run_display_ru') or 'заблокирован')}",
                f"Live: {clean_text(value.get('live_display_ru') or 'выключен')}",
                f"Отправка ордера: {clean_text(value.get('order_submission_display_ru') or 'выключена')}",
            ]
        )
        return "\n".join(lines)

    lines = ["First order prep"]
    missing = clean_text(value.get("missing_packet_message_en"))
    if missing:
        lines.append(missing)
    lines.extend(
        [
            f"Market: {clean_text(value.get('market_display_en') or 'not found')}",
            f"Token ID: {clean_text(value.get('token_id_display_en') or 'selection required')}",
            f"Account: {clean_text(value.get('account_display_en') or 'not checked')}",
            f"L2 auth: {clean_text(value.get('l2_auth_display_en') or 'unknown')}",
            f"Signer: {clean_text(value.get('signer_display_en') or 'not checked')}",
            f"Approval: {clean_text(value.get('approval_display_en') or 'not found')}",
            f"Payload dry-run: {clean_text(value.get('payload_dry_run_display_en') or 'blocked')}",
            f"Live: {clean_text(value.get('live_display_en') or 'disabled')}",
            f"Order sending: {clean_text(value.get('order_submission_display_en') or 'disabled')}",
        ]
    )
    return "\n".join(lines)


def normalize_telegram_order_prep_packet_status_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    contract_version = clean_text(value.get("contract_version"))
    screen_available = contract_version == STATUS_CONTRACT
    return {
        "contract_version": contract_version,
        "screen_available": screen_available,
        "status": clean_text(value.get("status") or "packet_status_missing"),
        "mode": clean_text(value.get("mode") or "local_artifact_packet_screen_only"),
        "execution_mode": clean_text(value.get("execution_mode") or "local_artifact_read_only"),
        "telegram_screen_title_ru": clean_text(value.get("telegram_screen_title_ru") or "🧪 Подготовка первого ордера"),
        "telegram_screen_title_en": clean_text(value.get("telegram_screen_title_en") or "First order prep"),
        "order_prep_packet_072a_artifact_available": value.get("order_prep_packet_072a_artifact_available") is True,
        "order_prep_packet_072a_artifact_path": clean_text(value.get("order_prep_packet_072a_artifact_path")),
        "legacy_071e_artifact_available": value.get("legacy_071e_artifact_available") is True,
        "legacy_071e_artifact_path": clean_text(value.get("legacy_071e_artifact_path")),
        "missing_packet_message_ru": clean_text(value.get("missing_packet_message_ru")),
        "missing_packet_message_en": clean_text(value.get("missing_packet_message_en")),
        "market_found": value.get("market_found") is True,
        "market_display_ru": clean_text(value.get("market_display_ru") or "не найден"),
        "market_display_en": clean_text(value.get("market_display_en") or "not found"),
        "token_id_selected": value.get("token_id_selected") is True,
        "token_id_display_ru": clean_text(value.get("token_id_display_ru") or "требуется выбор"),
        "token_id_display_en": clean_text(value.get("token_id_display_en") or "selection required"),
        "account_readonly_ok": value.get("account_readonly_ok") is True,
        "account_display_ru": clean_text(value.get("account_display_ru") or "не проверен"),
        "account_display_en": clean_text(value.get("account_display_en") or "not checked"),
        "l2_auth_ok": value.get("l2_auth_ok") is True,
        "l2_auth_display_ru": clean_text(value.get("l2_auth_display_ru") or "unknown"),
        "l2_auth_display_en": clean_text(value.get("l2_auth_display_en") or "unknown"),
        "signer_ok": value.get("signer_ok") is True,
        "signer_display_ru": clean_text(value.get("signer_display_ru") or "не проверен"),
        "signer_display_en": clean_text(value.get("signer_display_en") or "not checked"),
        "approval_ready": value.get("approval_ready") is True,
        "approval_display_ru": clean_text(value.get("approval_display_ru") or "не найден"),
        "approval_display_en": clean_text(value.get("approval_display_en") or "not found"),
        "payload_dry_run_ready": value.get("payload_dry_run_ready") is True,
        "payload_dry_run_display_ru": clean_text(value.get("payload_dry_run_display_ru") or "заблокирован"),
        "payload_dry_run_display_en": clean_text(value.get("payload_dry_run_display_en") or "blocked"),
        "live_display_ru": clean_text(value.get("live_display_ru") or "выключен"),
        "live_display_en": clean_text(value.get("live_display_en") or "disabled"),
        "order_submission_display_ru": clean_text(value.get("order_submission_display_ru") or "выключена"),
        "order_submission_display_en": clean_text(value.get("order_submission_display_en") or "disabled"),
        "status_text_ru": clean_text(value.get("status_text_ru")),
        "status_text_en": clean_text(value.get("status_text_en")),
        "local_artifact_read_only": True,
        "raw_token_id_exposed": False,
        "raw_account_values_exposed": False,
        "raw_secret_output": False,
        **telegram_order_prep_packet_status_safety_flags(),
    }


def telegram_order_prep_packet_status_safety_flags() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "dry_run_only": True,
        "preflight_only": True,
        "local_artifact_read_only": True,
        "network_used": False,
        "external_api_calls_performed": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "telegram_authenticated_call_performed": False,
        "wallet_connection_attempted": False,
        "wallet_connection_enabled": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "credential_values_read": False,
        "credentials_values_read": False,
        "credential_values_serialized": False,
        "credential_values_printed": False,
        "credential_values_stored": False,
        "environment_values_read": False,
        "environment_values_serialized": False,
        "environment_values_printed": False,
        "environment_values_stored": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "credentials_values_exposed": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_available": False,
        "signed_payload_generation_enabled": False,
        "signed_payload_generated": False,
        "signed_order_generation_enabled": False,
        "signed_order_payload_generated": False,
        "order_submission_available": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "order_cancel_enabled": False,
        "real_order_submitted": False,
        "real_order_cancelled": False,
        "balance_read_attempted": False,
        "balance_values_emitted": False,
        "allowance_values_emitted": False,
        "position_read_attempted": False,
        "fill_read_attempted": False,
        "pnl_read_attempted": False,
        "fake_balance_added": False,
        "fake_pnl_added": False,
        "fake_trades_added": False,
        "live_trading_enabled": False,
        "live_execution_allowed": False,
        "live_execution_approved": False,
        "live_execution_performed": False,
        "allowed_for_live": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "live_connector_enabled": False,
        "authenticated_polymarket_enabled": False,
        "telegram_live_order_controls_added": False,
        "telegram_signing_controls_added": False,
        "telegram_wallet_controls_added": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def find_latest_order_prep_packet_072a_artifact(root: Path) -> Path | None:
    explicit = _first_existing_path(_candidate_paths(root, ORDER_PREP_PACKET_072A_DIR_NAMES, ORDER_PREP_PACKET_072A_FILENAMES))
    if explicit is not None:
        return explicit
    discovered = [
        path
        for path in root.glob("**/*072a*.json")
        if path.is_file()
        and "telegram_order_prep_packet_screen_072b" not in normalize_path(path)
        and "order" in path.name.lower()
        and "prep" in path.name.lower()
        and "packet" in path.name.lower()
    ]
    if not discovered:
        return None
    discovered.sort(
        key=lambda path: (
            0 if path.name.lower().startswith("latest") else 1,
            -path.stat().st_mtime,
            normalize_path(path),
        )
    )
    return discovered[0]


def _candidate_paths(root: Path, dir_names: Sequence[str], filenames: Sequence[str]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for dirname in dir_names:
        for filename in filenames:
            paths.append(root / dirname / filename)
    for filename in filenames:
        paths.append(root / filename)
    return _dedupe_paths(paths)


def _dedupe_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(path)
    return tuple(unique)


def _first_existing_path(paths: Sequence[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def _load_optional_json(path: Path | None, label: str) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return load_json_object(path, label=label)
    except Exception:
        return {}


def _extract_packet_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(payload or {})
    for key in (
        "order_prep_packet_072a",
        "first_order_prep_packet_072a",
        "order_prep_packet",
        "first_order_prep_packet",
        "preparation_packet",
        "packet",
        "latest_status",
    ):
        nested = value.get(key)
        if isinstance(nested, Mapping):
            return dict(nested)
    return value


def _artifact_summary(path: Path | None, payload: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(payload or {})
    return {
        "available": bool(value),
        "path": normalize_path(path) if path else "",
        "status": clean_text(value.get("status") or "not_available") if value else "missing",
        "contract_version": clean_text(value.get("contract_version")) if value else "",
    }


def _market_display(payload: Mapping[str, Any], *, available: bool) -> tuple[str, str, bool]:
    if not available:
        return "не найден", "not found", False
    found = _has_true_value(
        payload,
        "market_found",
        "market_selected",
        "market_resolved",
        "market_available",
    ) or _has_found_status(
        payload,
        "market_status",
        "market_display",
        "market_display_status",
    ) or _has_positive_int(
        payload,
        "market_candidate_count",
        "market_count",
        "candidate_market_count",
        "discovered_market_count",
        "matched_market_count",
    ) or _has_present_text(
        payload,
        "market",
        "market_id",
        "market_slug",
        "selected_market_slug",
        "resolved_market_slug",
        "condition_id",
        "question",
        "title",
    ) or _has_nonempty_list(payload, "market_candidates", "candidate_markets", "markets", "matched_markets")
    return ("найден", "found", True) if found else ("не найден", "not found", False)


def _token_display(payload: Mapping[str, Any], *, available: bool) -> tuple[str, str, bool]:
    if not available:
        return "требуется выбор", "selection required", False
    selected = _has_true_value(
        payload,
        "token_id_selected",
        "token_selected",
        "target_token_selected",
        "token_id_present",
        "token_resolved",
    ) or _has_selected_status(
        payload,
        "token_id_status",
        "token_status",
        "token_id_display",
        "token_display",
    ) or _has_present_text(
        payload,
        "token_id",
        "selected_token_id",
        "target_token_id",
        "outcome_token_id",
        "clob_token_id",
        "resolved_token_id",
    )
    return ("выбран", "selected", True) if selected else ("требуется выбор", "selection required", False)


def _account_display(payload: Mapping[str, Any], *, available: bool) -> tuple[str, str, bool]:
    if not available:
        return "не проверен", "not checked", False
    account_status_keys = (
        "account_status",
        "account_readonly_status",
        "readonly_account_status",
        "account_display",
        "account_readonly_display",
    )
    if _has_error_status(payload, *account_status_keys):
        return "ошибка", "error", False
    ok = _has_true_value(
        payload,
        "account_readonly_ok",
        "account_read_only_ok",
        "read_only_ok",
        "readonly_ok",
        "readonly_probe_ok",
        "account_state_probe_performed",
    ) or _has_ok_status(payload, *account_status_keys)
    checked = ok or _has_present_text(payload, *account_status_keys)
    if ok:
        return "read-only OK", "read-only OK", True
    if checked:
        return "ошибка", "error", False
    return "не проверен", "not checked", False


def _l2_auth_display(payload: Mapping[str, Any], *, available: bool) -> tuple[str, str, bool]:
    if not available:
        return "unknown", "unknown", False
    if _has_true_value(payload, "l2_auth_ok", "l2_authenticated", "clob_l2_auth_ok") or _has_ok_status(
        payload,
        "l2_auth_status",
        "l2_auth_display",
        "clob_l2_auth_status",
        "clob_l2_auth_display",
        "l2_status",
        "auth_status",
    ):
        return "OK", "OK", True
    if _has_true_value(payload, "l2_auth_blocked", "clob_l2_auth_blocked") or _has_blocked_status(
        payload,
        "l2_auth_status",
        "l2_auth_display",
        "clob_l2_auth_status",
        "clob_l2_auth_display",
        "l2_status",
        "auth_status",
    ):
        return "blocked", "blocked", False
    return "unknown", "unknown", False


def _signer_display(payload: Mapping[str, Any], *, available: bool) -> tuple[str, str, bool]:
    if not available:
        return "не проверен", "not checked", False
    signer_status_keys = ("signer_status", "signing_status", "signer_check_status", "signer_display")
    if _has_error_status(payload, *signer_status_keys):
        return "ошибка", "error", False
    ok = _has_true_value(payload, "signer_ok", "signer_checked_ok", "signer_available") or _has_ok_status(
        payload,
        *signer_status_keys,
    )
    if ok:
        return "OK", "OK", True
    checked = _has_present_text(payload, *signer_status_keys)
    if checked:
        return "ошибка", "error", False
    return "не проверен", "not checked", False


def _approval_display(payload: Mapping[str, Any], *, available: bool) -> tuple[str, str, bool]:
    if not available:
        return "не найден", "not found", False
    approval_status_keys = (
        "approval_status",
        "operator_approval_status",
        "manual_approval_status",
        "approval_display",
    )
    if _has_true_value(
        payload,
        "approval_ready",
        "approval_packet_ready",
        "approval_found",
        "manual_approval_packet_found",
    ) or _has_present_text(
        payload,
        "approval_packet_path",
        "manual_approval_packet_path",
        "approval_artifact_path",
    ) or _has_ok_status(
        payload,
        *approval_status_keys,
    ):
        return "готов", "ready", True
    if _has_true_value(payload, "approval_required", "operator_approval_required", "manual_approval_required"):
        return "требуется", "required", False
    for text in _all_present_text(payload, *approval_status_keys):
        lower = text.lower()
        if any(term in lower for term in ("required", "pending", "needed", "missing approval", "треб")):
            return "требуется", "required", False
        if any(term in lower for term in ("missing", "not_found", "not found", "none", "absent")):
            return "не найден", "not found", False
    return "не найден", "not found", False


def _payload_dry_run_display(payload: Mapping[str, Any], *, available: bool) -> tuple[str, str, bool]:
    if not available:
        return "заблокирован", "blocked", False
    ready = _has_true_value(
        payload,
        "payload_dry_run_ready",
        "payload_ready",
        "order_payload_contract_built",
        "payload_contract_ready",
        "dry_run_payload_ready",
    ) or _has_present_text(
        payload,
        "payload_contract_path",
        "order_payload_contract_path",
        "payload_contract_fingerprint",
        "contract_fingerprint",
    ) or _has_ok_status(
        payload,
        "payload_dry_run_status",
        "payload_dry_run_display",
        "payload_status",
        "dry_run_status",
    )
    blocked = _has_true_value(payload, "payload_dry_run_blocked", "payload_blocked") or _has_blocked_status(
        payload,
        "payload_dry_run_status",
        "payload_dry_run_display",
        "payload_status",
        "dry_run_status",
    )
    if ready and not blocked:
        return "готов", "ready", True
    return "заблокирован", "blocked", False


def _has_true_value(payload: Mapping[str, Any], *keys: str) -> bool:
    return any(value is True for mapping in _walk_mappings(payload) for key, value in mapping.items() if key in keys)


def _has_present_text(payload: Mapping[str, Any], *keys: str) -> bool:
    return any(_present_text(value) for value in _values_for_keys(payload, keys))


def _all_present_text(payload: Mapping[str, Any], *keys: str) -> tuple[str, ...]:
    return tuple(clean_text(value) for value in _values_for_keys(payload, keys) if _present_text(value))


def _has_positive_int(payload: Mapping[str, Any], *keys: str) -> bool:
    return any(_positive_int(value) for value in _values_for_keys(payload, keys))


def _has_nonempty_list(payload: Mapping[str, Any], *keys: str) -> bool:
    return any(isinstance(value, list) and bool(value) for value in _values_for_keys(payload, keys))


def _has_found_status(payload: Mapping[str, Any], *keys: str) -> bool:
    found_terms = ("found", "selected", "resolved", "available", "matched", "present", "найден")
    bad_terms = ("not_found", "not found", "missing", "none", "absent", "не найден")
    return any(
        any(term in text.lower() for term in found_terms)
        and not any(term in text.lower() for term in bad_terms)
        for text in _all_present_text(payload, *keys)
    )


def _has_selected_status(payload: Mapping[str, Any], *keys: str) -> bool:
    selected_terms = ("selected", "resolved", "present", "ready", "chosen", "выбран")
    bad_terms = ("selection required", "required", "missing", "none", "absent", "требуется")
    return any(
        any(term in text.lower() for term in selected_terms)
        and not any(term in text.lower() for term in bad_terms)
        for text in _all_present_text(payload, *keys)
    )


def _has_ok_status(payload: Mapping[str, Any], *keys: str) -> bool:
    ok_terms = ("ok", "success", "succeeded", "completed", "ready", "valid", "configured", "read-only", "readonly")
    bad_terms = ("error", "failed", "failure", "invalid", "blocked", "missing", "not_checked", "not checked")
    return any(
        any(term in text.lower() for term in ok_terms)
        and not any(term in text.lower() for term in bad_terms)
        for text in _all_present_text(payload, *keys)
    )


def _has_error_status(payload: Mapping[str, Any], *keys: str) -> bool:
    return any(
        any(term in text.lower() for term in ("error", "failed", "failure", "invalid"))
        for text in _all_present_text(payload, *keys)
    )


def _has_blocked_status(payload: Mapping[str, Any], *keys: str) -> bool:
    return any(
        any(term in text.lower() for term in ("blocked", "disabled", "missing", "not configured", "not_configured"))
        or any(term in text.lower() for term in ("error", "failed", "failure", "invalid"))
        for text in _all_present_text(payload, *keys)
    )


def _values_for_keys(payload: Mapping[str, Any], keys: Sequence[str]) -> tuple[Any, ...]:
    values: list[Any] = []
    key_set = set(keys)
    for mapping in _walk_mappings(payload):
        for key, value in mapping.items():
            if key in key_set:
                values.append(value)
    return tuple(values)


def _walk_mappings(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    rows: list[Mapping[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            rows.append(value)
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(payload)
    return tuple(rows)


def _present_text(value: Any) -> bool:
    text = clean_text(value)
    return bool(text) and text.lower() not in _ABSENT_TEXT


def _positive_int(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _button_rows(language: str, rows: Sequence[Sequence[tuple[str, str]]]) -> list[dict[str, str]]:
    return [
        {
            "language": language,
            "label": label,
            "callback_data": callback_data,
        }
        for row in rows
        for label, callback_data in row
    ]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the 072B Telegram order prep packet screen artifacts.")
    parser.add_argument("--artifact-root", default="", help="Root directory containing local source artifacts.")
    parser.add_argument("--output-dir", default="", help="Directory for 072B output artifacts.")
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--json", action="store_true", help="Print the generated result JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generated = write_telegram_order_prep_packet_status_072b_artifacts(
        artifact_root=args.artifact_root or None,
        output_dir=args.output_dir or None,
        generated_at=args.generated_at,
    )
    if args.json:
        import json

        print(json.dumps(generated["result"], indent=2, sort_keys=True, ensure_ascii=False))
    else:
        status = generated["latest_status"]
        _safe_print(status["status_text_ru"])
        _safe_print(f"result_path: {generated['result_path']}")
    return 0


def _safe_print(value: str) -> None:
    text = str(value)
    try:
        print(text)
    except UnicodeEncodeError:
        import sys

        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


if __name__ == "__main__":
    raise SystemExit(main())
