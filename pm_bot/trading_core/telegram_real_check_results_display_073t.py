from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.local_real_check_bundle_models import (
    CLOB_SUBCHECK_ID,
    DISCOVERY_BRIDGE_SUBCHECK_ID,
    GUARDED_SIGNER_SUBCHECK_ID,
    LIVE_ACCOUNT_SUBCHECK_ID,
    LIVE_STATUS_SUBCHECK_ID,
    PUBLIC_DISCOVERY_SUBCHECK_ID,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, mapping_rows, normalize_path, write_json

TASK_ID = "ORCH-PMBOT-TELEGRAM-073T-REAL-CHECK-RESULTS-DISPLAY-NO-LIVE"

STATUS_CONTRACT = "pmbot_telegram_real_check_results_status_073t.v1"
RESULT_CONTRACT = "pmbot_telegram_real_check_results_result_073t.v1"
MENU_SNAPSHOT_CONTRACT = "pmbot_telegram_real_check_results_menu_snapshot_073t.v1"
MINI_APP_SNAPSHOT_CONTRACT = "pmbot_telegram_real_check_results_mini_app_snapshot_073t.v1"
SAFETY_SNAPSHOT_CONTRACT = "pmbot_telegram_real_check_results_safety_snapshot_073t.v1"

ARTIFACT_DIR_NAME = "telegram_real_check_results_073t"
RESULT_FILENAME = "telegram_real_check_results_073t_result.json"
LATEST_STATUS_FILENAME = "latest_telegram_real_check_results_status_073t.json"
MENU_SNAPSHOT_FILENAME = "telegram_real_check_results_menu_snapshot_073t.json"
MINI_APP_SNAPSHOT_FILENAME = "telegram_real_check_results_mini_app_snapshot_073t.json"
SAFETY_SNAPSHOT_FILENAME = "telegram_real_check_results_safety_snapshot_073t.json"

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME

LOCAL_REAL_CHECK_072C_DIR_NAMES = ("local_real_check_bundle_072c",)
LOCAL_REAL_CHECK_072C_FILENAMES = (
    "local_real_check_bundle_072c_result.json",
    "latest_local_real_check_bundle_status_072c.json",
)
REAL_CHECK_SNAPSHOT_073A_DIR_NAMES = (
    "local_real_check_result_snapshot_pack_073a",
    "real_check_result_snapshot_pack_073a",
    "local_real_check_results_073a",
    "real_check_results_073a",
)
REAL_CHECK_SNAPSHOT_073A_FILENAMES = (
    "latest_local_real_check_result_snapshot_status_073a.json",
    "latest_real_check_result_snapshot_status_073a.json",
    "local_real_check_result_snapshot_pack_073a_result.json",
    "real_check_result_snapshot_pack_073a_result.json",
)

CONTROL_BUTTON_ROWS_RU = (
    (("🔄 Обновить", "pmbot:connection"),),
    (("🧪 Запустить локальную проверку", "pmbot:run:local_real_check_bundle_072c"),),
    (("⬅️ Назад", "pmbot:home"),),
)
CONTROL_BUTTON_ROWS_EN = (
    (("🔄 Refresh", "pmbot:connection"),),
    (("🧪 Run local check", "pmbot:run:local_real_check_bundle_072c"),),
    (("⬅️ Back", "pmbot:home"),),
)

_OK_TERMS = ("ok", "success", "succeeded", "ready", "verified", "authenticated", "aggregated")
_ERROR_TERMS = ("error", "failed", "failure", "blocked", "missing", "invalid", "unavailable")
_NOT_CHECKED_TERMS = ("not_run", "not run", "not_checked", "not checked", "not_requested", "unknown", "")


def telegram_real_check_results_artifact_paths(output_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(output_dir) if output_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / RESULT_FILENAME,
        "latest_status": root / LATEST_STATUS_FILENAME,
        "menu_snapshot": root / MENU_SNAPSHOT_FILENAME,
        "mini_app_snapshot": root / MINI_APP_SNAPSHOT_FILENAME,
        "safety_snapshot": root / SAFETY_SNAPSHOT_FILENAME,
    }


def build_telegram_real_check_results_status(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    bundle_path = find_latest_local_real_check_072c_artifact(root)
    snapshot_073a_path = find_latest_real_check_snapshot_073a_artifact(root)
    bundle = _load_optional_json(bundle_path, "072C local real-check bundle")
    snapshot_073a = _load_optional_json(snapshot_073a_path, "073A real-check snapshot")
    source = _prefer_snapshot_payload(snapshot_073a, bundle)
    source_available = bool(source)

    subchecks = _subcheck_rows(source)
    clob = _subcheck_by_id(subchecks, CLOB_SUBCHECK_ID)
    account = _subcheck_by_id(subchecks, LIVE_ACCOUNT_SUBCHECK_ID)
    signer = _subcheck_by_id(subchecks, GUARDED_SIGNER_SUBCHECK_ID)
    market = _subcheck_by_id(subchecks, PUBLIC_DISCOVERY_SUBCHECK_ID)
    token = _subcheck_by_id(subchecks, DISCOVERY_BRIDGE_SUBCHECK_ID)
    aggregate = _subcheck_by_id(subchecks, LIVE_STATUS_SUBCHECK_ID)

    api_keys_found = _api_keys_found(source, clob, aggregate, source_available=source_available)
    l2_display_ru, l2_display_en, l2_status = _check_display(
        _first_text(
            _status_field(clob, "l2_authenticated_readonly_probe_performed"),
            _status_field(clob, "auth_verified"),
            _status_field(aggregate, "l2_auth_status"),
            clob.get("status"),
        ),
        source_available=source_available,
        not_checked_ru="не проверено",
        not_checked_en="not checked",
    )
    account_display_ru, account_display_en, account_status = _check_display(
        _first_text(
            _status_field(account, "account_state_probe_performed"),
            _status_field(account, "account_status"),
            _status_field(account, "credential_presence_status"),
            account.get("status"),
        ),
        source_available=source_available,
        not_checked_ru="не проверен",
        not_checked_en="not checked",
    )
    signer_display_ru, signer_display_en, signer_status = _signer_display(signer, source_available=source_available)
    market_found = _market_found(source, market, source_available=source_available)
    token_selected = _token_selected(source, token, source_available=source_available)

    status: dict[str, Any] = {
        "contract_version": STATUS_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "real_check_results_available" if source_available else "real_check_results_missing",
        "mode": "local_real_check_results_display_only",
        "execution_mode": "local_artifact_read_only_display",
        "telegram_screen_title_ru": "🔐 Проверка подключения",
        "telegram_screen_title_en": "Connection check",
        "artifact_root": normalize_path(root),
        "source_artifact_available": source_available,
        "local_real_check_bundle_072c_artifact_available": bool(bundle),
        "local_real_check_bundle_072c_artifact_path": normalize_path(bundle_path) if bundle_path else "",
        "real_check_snapshot_073a_artifact_available": bool(snapshot_073a),
        "real_check_snapshot_073a_artifact_path": normalize_path(snapshot_073a_path) if snapshot_073a_path else "",
        "missing_artifacts_message_ru": "" if source_available else "Проверка ещё не запускалась",
        "missing_artifacts_message_en": "" if source_available else "Check has not been run yet",
        "api_keys_found": api_keys_found,
        "api_keys_display_ru": "найдены" if api_keys_found else "не найдены",
        "api_keys_display_en": "found" if api_keys_found else "not found",
        "l2_auth_status": l2_status,
        "l2_auth_display_ru": l2_display_ru,
        "l2_auth_display_en": l2_display_en,
        "account_status": account_status,
        "account_display_ru": account_display_ru,
        "account_display_en": account_display_en,
        "signer_status": signer_status,
        "signer_display_ru": signer_display_ru,
        "signer_display_en": signer_display_en,
        "market_found": market_found,
        "market_display_ru": "найден" if market_found else "не найден",
        "market_display_en": "found" if market_found else "not found",
        "token_id_selected": token_selected,
        "token_id_display_ru": "выбран" if token_selected else "требуется выбор",
        "token_id_display_en": "selected" if token_selected else "selection required",
        "live_enabled": False,
        "live_display_ru": "выключен",
        "live_display_en": "off",
        "screen_buttons": [
            {"label_ru": label, "callback_data": callback_data}
            for row in CONTROL_BUTTON_ROWS_RU
            for label, callback_data in row
        ],
        "source_artifacts": {
            "local_real_check_bundle_072c": _artifact_summary(bundle_path, bundle),
            "real_check_snapshot_073a": _artifact_summary(snapshot_073a_path, snapshot_073a),
        },
        "raw_token_id_exposed": False,
        "raw_account_values_exposed": False,
        "raw_secret_output": False,
        "local_artifact_read_only": True,
        "display_only": True,
        "execution_enabling": False,
        **telegram_real_check_results_safety_flags(),
    }
    status["status_text_ru"] = render_telegram_real_check_results_status_text(status, language="ru")
    status["status_text_en"] = render_telegram_real_check_results_status_text(status, language="en")
    return status


def write_telegram_real_check_results_073t_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    status = build_telegram_real_check_results_status(artifact_root=artifact_root, generated_at=generated_at)
    paths = telegram_real_check_results_artifact_paths(output_dir)
    menu = build_telegram_real_check_results_menu_snapshot(generated_at=generated_at)
    mini_app = build_telegram_real_check_results_mini_app_snapshot(status, generated_at=generated_at)
    safety = build_telegram_real_check_results_safety_snapshot(generated_at=generated_at)
    result = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "completed_display_only",
        "latest_status_path": normalize_path(paths["latest_status"]),
        "menu_snapshot_path": normalize_path(paths["menu_snapshot"]),
        "mini_app_snapshot_path": normalize_path(paths["mini_app_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "telegram_real_check_results_073t": status,
        "menu_snapshot": menu,
        "mini_app_snapshot": mini_app,
        "safety_snapshot": safety,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "display_only": True,
        "execution_enabling": False,
        **telegram_real_check_results_safety_flags(),
    }
    write_json(paths["latest_status"], status)
    write_json(paths["menu_snapshot"], menu)
    write_json(paths["mini_app_snapshot"], mini_app)
    write_json(paths["safety_snapshot"], safety)
    write_json(paths["result"], result)
    return {
        "result_path": normalize_path(paths["result"]),
        "latest_status_path": normalize_path(paths["latest_status"]),
        "menu_snapshot_path": normalize_path(paths["menu_snapshot"]),
        "mini_app_snapshot_path": normalize_path(paths["mini_app_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "result": result,
        "latest_status": status,
        "menu_snapshot": menu,
        "mini_app_snapshot": mini_app,
        "safety_snapshot": safety,
    }


def build_telegram_real_check_results_menu_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    buttons = [*_button_rows("ru", CONTROL_BUTTON_ROWS_RU), *_button_rows("en", CONTROL_BUTTON_ROWS_EN)]
    return {
        "contract_version": MENU_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "title_ru": "🔐 Проверка подключения",
        "title_en": "Connection check",
        "buttons": buttons,
        "button_count": len(buttons),
        "allowed_callbacks": [
            "pmbot:connection",
            "pmbot:run:local_real_check_bundle_072c",
            "pmbot:home",
        ],
        "run_local_check_action_id": "run_local_real_check_bundle_072c",
        "run_local_check_command": [
            "python",
            "-m",
            "pm_bot.operator_runner.local_real_check_bundle",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
        ],
        "run_local_check_background": False,
        "run_local_check_dry_run_only": True,
        "forbidden_live_controls_added": False,
        "submit_cancel_controls_added": False,
        "signing_controls_added": False,
        "wallet_controls_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_real_check_results_safety_flags(),
    }


def build_telegram_real_check_results_mini_app_snapshot(
    status: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = normalize_telegram_real_check_results_status_summary(status)
    return {
        "contract_version": MINI_APP_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "card_title_ru": "Проверка подключения",
        "source_artifact_available": value["source_artifact_available"],
        "missing_artifacts_message_ru": value["missing_artifacts_message_ru"],
        "statuses": {
            "api_keys": {"label_ru": "API ключи", "display_ru": value["api_keys_display_ru"]},
            "l2_auth": {"label_ru": "L2 auth", "display_ru": value["l2_auth_display_ru"]},
            "account": {"label_ru": "Аккаунт", "display_ru": value["account_display_ru"]},
            "signer": {"label_ru": "Signer", "display_ru": value["signer_display_ru"]},
            "market": {"label_ru": "Рынок", "display_ru": value["market_display_ru"]},
            "token_id": {"label_ru": "Token ID", "display_ru": value["token_id_display_ru"]},
            "live": {"label_ru": "Live", "display_ru": value["live_display_ru"]},
        },
        "static_review_only": True,
        "local_static_artifacts_only": True,
        "no_network_fetch": True,
        "no_secret_forms": True,
        "no_secret_inputs": True,
        "no_secret_persistence": True,
        **telegram_real_check_results_safety_flags(),
    }


def build_telegram_real_check_results_safety_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "safe_local_real_check_results_display_only",
        "allowed_inputs": [
            "local 072C real-check bundle artifacts when present",
            "local 073A real-check snapshot artifacts when present",
        ],
        "forbidden_actions": [
            "live trading",
            "order submission",
            "order cancellation",
            "wallet connection",
            "signing",
            "secret display",
            "authenticated calls from display rendering",
            "fake balances, trades, or PnL",
        ],
        "same_message_navigation_preserved": True,
        "mini_app_static_no_fetch": True,
        "display_does_not_run_probe": True,
        "local_check_button_maps_to_safe_dry_run_action": True,
        "local_check_button_background_execution": False,
        **telegram_real_check_results_safety_flags(),
    }


def render_telegram_real_check_results_status_text(status: Mapping[str, Any], *, language: str = "ru") -> str:
    value = normalize_telegram_real_check_results_status_summary(status)
    if clean_text(language).lower() == "ru":
        lines = ["🔐 Проверка подключения"]
        missing = clean_text(value.get("missing_artifacts_message_ru"))
        if missing:
            lines.append(missing)
        lines.extend(
            [
                f"API ключи: {value['api_keys_display_ru']}",
                f"L2 auth: {value['l2_auth_display_ru']}",
                f"Аккаунт: {value['account_display_ru']}",
                f"Signer: {value['signer_display_ru']}",
                f"Рынок: {value['market_display_ru']}",
                f"Token ID: {value['token_id_display_ru']}",
                f"Live: {value['live_display_ru']}",
            ]
        )
        return "\n".join(lines)
    lines = ["Connection check"]
    missing = clean_text(value.get("missing_artifacts_message_en"))
    if missing:
        lines.append(missing)
    lines.extend(
        [
            f"API keys: {value['api_keys_display_en']}",
            f"L2 auth: {value['l2_auth_display_en']}",
            f"Account: {value['account_display_en']}",
            f"Signer: {value['signer_display_en']}",
            f"Market: {value['market_display_en']}",
            f"Token ID: {value['token_id_display_en']}",
            f"Live: {value['live_display_en']}",
        ]
    )
    return "\n".join(lines)


def normalize_telegram_real_check_results_status_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    return {
        "contract_version": clean_text(value.get("contract_version")),
        "screen_available": clean_text(value.get("contract_version")) == STATUS_CONTRACT,
        "status": clean_text(value.get("status") or "real_check_results_missing"),
        "mode": clean_text(value.get("mode") or "local_real_check_results_display_only"),
        "execution_mode": clean_text(value.get("execution_mode") or "local_artifact_read_only_display"),
        "telegram_screen_title_ru": clean_text(value.get("telegram_screen_title_ru") or "🔐 Проверка подключения"),
        "telegram_screen_title_en": clean_text(value.get("telegram_screen_title_en") or "Connection check"),
        "source_artifact_available": value.get("source_artifact_available") is True,
        "local_real_check_bundle_072c_artifact_available": value.get("local_real_check_bundle_072c_artifact_available") is True,
        "local_real_check_bundle_072c_artifact_path": clean_text(value.get("local_real_check_bundle_072c_artifact_path")),
        "real_check_snapshot_073a_artifact_available": value.get("real_check_snapshot_073a_artifact_available") is True,
        "real_check_snapshot_073a_artifact_path": clean_text(value.get("real_check_snapshot_073a_artifact_path")),
        "missing_artifacts_message_ru": clean_text(value.get("missing_artifacts_message_ru")),
        "missing_artifacts_message_en": clean_text(value.get("missing_artifacts_message_en")),
        "api_keys_found": value.get("api_keys_found") is True,
        "api_keys_display_ru": clean_text(value.get("api_keys_display_ru") or "не найдены"),
        "api_keys_display_en": clean_text(value.get("api_keys_display_en") or "not found"),
        "l2_auth_status": clean_text(value.get("l2_auth_status") or "not_checked"),
        "l2_auth_display_ru": clean_text(value.get("l2_auth_display_ru") or "не проверено"),
        "l2_auth_display_en": clean_text(value.get("l2_auth_display_en") or "not checked"),
        "account_status": clean_text(value.get("account_status") or "not_checked"),
        "account_display_ru": clean_text(value.get("account_display_ru") or "не проверен"),
        "account_display_en": clean_text(value.get("account_display_en") or "not checked"),
        "signer_status": clean_text(value.get("signer_status") or "not_checked"),
        "signer_display_ru": clean_text(value.get("signer_display_ru") or "не проверен"),
        "signer_display_en": clean_text(value.get("signer_display_en") or "not checked"),
        "market_found": value.get("market_found") is True,
        "market_display_ru": clean_text(value.get("market_display_ru") or "не найден"),
        "market_display_en": clean_text(value.get("market_display_en") or "not found"),
        "token_id_selected": value.get("token_id_selected") is True,
        "token_id_display_ru": clean_text(value.get("token_id_display_ru") or "требуется выбор"),
        "token_id_display_en": clean_text(value.get("token_id_display_en") or "selection required"),
        "live_enabled": False,
        "live_display_ru": clean_text(value.get("live_display_ru") or "выключен"),
        "live_display_en": clean_text(value.get("live_display_en") or "off"),
        "raw_token_id_exposed": False,
        "raw_account_values_exposed": False,
        "raw_secret_output": False,
        "local_artifact_read_only": True,
        "display_only": True,
        "execution_enabling": False,
        **telegram_real_check_results_safety_flags(),
    }


def telegram_real_check_results_safety_flags() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "display_only": True,
        "network_used": False,
        "external_api_calls_performed": False,
        "authenticated_endpoint_call_performed": False,
        "authenticated_request_performed": False,
        "telegram_authenticated_call_performed": False,
        "mini_app_network_fetch": False,
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
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "credentials_values_exposed": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "order_submission_available": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_cancellation_attempted": False,
        "order_cancel_enabled": False,
        "real_order_submitted": False,
        "real_order_cancelled": False,
        "fake_balance_added": False,
        "fake_pnl_added": False,
        "fake_trades_added": False,
        "live_trading_enabled": False,
        "allowed_for_live": False,
        "operator_approved": False,
        "candidate_is_executable": False,
        "live_execution_approved": False,
        "live_execution_performed": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "live_connector_enabled": False,
        "telegram_live_order_controls_added": False,
        "telegram_signing_controls_added": False,
        "telegram_wallet_controls_added": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def find_latest_local_real_check_072c_artifact(root: Path) -> Path | None:
    return _first_existing_path(_candidate_paths(root, LOCAL_REAL_CHECK_072C_DIR_NAMES, LOCAL_REAL_CHECK_072C_FILENAMES))


def find_latest_real_check_snapshot_073a_artifact(root: Path) -> Path | None:
    explicit = _first_existing_path(_candidate_paths(root, REAL_CHECK_SNAPSHOT_073A_DIR_NAMES, REAL_CHECK_SNAPSHOT_073A_FILENAMES))
    if explicit is not None:
        return explicit
    discovered = [
        path
        for path in root.glob("**/*073a*.json")
        if path.is_file()
        and "real" in path.name.lower()
        and "check" in path.name.lower()
        and ARTIFACT_DIR_NAME not in normalize_path(path)
    ]
    if not discovered:
        return None
    discovered.sort(key=lambda path: (0 if path.name.lower().startswith("latest") else 1, -path.stat().st_mtime, normalize_path(path)))
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


def _prefer_snapshot_payload(snapshot_073a: Mapping[str, Any], bundle_072c: Mapping[str, Any]) -> dict[str, Any]:
    if snapshot_073a:
        for key in ("latest_status", "real_check_results", "real_check_snapshot", "status"):
            nested = snapshot_073a.get(key)
            if isinstance(nested, Mapping):
                return dict(nested)
        return dict(snapshot_073a)
    return dict(bundle_072c or {})


def _subcheck_rows(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = [dict(row) for row in mapping_rows(source.get("subchecks"))]
    if rows:
        return rows
    latest = source.get("latest_status")
    if isinstance(latest, Mapping):
        return [dict(row) for row in mapping_rows(latest.get("subchecks"))]
    return []


def _subcheck_by_id(rows: Sequence[Mapping[str, Any]], subcheck_id: str) -> dict[str, Any]:
    return next((dict(row) for row in rows if clean_text(row.get("subcheck_id")) == subcheck_id), {})


def _status_field(row: Mapping[str, Any], key: str) -> Any:
    fields = row.get("status_fields")
    if isinstance(fields, Mapping):
        return fields.get(key)
    return None


def _api_keys_found(
    source: Mapping[str, Any],
    clob: Mapping[str, Any],
    aggregate: Mapping[str, Any],
    *,
    source_available: bool,
) -> bool:
    if not source_available:
        return False
    direct_values = (
        source.get("api_keys_found"),
        source.get("api_keys_present"),
        _status_field(clob, "auth_verified"),
        _status_field(clob, "l2_authenticated_readonly_probe_performed"),
    )
    if any(value is True for value in direct_values):
        return True
    statuses = (
        _status_field(clob, "credential_presence_status"),
        _status_field(clob, "l2_auth_status"),
        _status_field(aggregate, "l2_auth_status"),
        clob.get("status"),
    )
    return any(_status_is_ok(value) and "missing" not in clean_text(value).lower() for value in statuses)


def _check_display(
    value: Any,
    *,
    source_available: bool,
    not_checked_ru: str,
    not_checked_en: str,
) -> tuple[str, str, str]:
    if not source_available:
        return not_checked_ru, not_checked_en, "not_checked"
    if isinstance(value, bool):
        return ("OK", "OK", "ok") if value else ("ошибка", "error", "error")
    text = clean_text(value)
    lowered = text.lower().replace("_", " ")
    if any(term in lowered for term in _OK_TERMS) and not any(term in lowered for term in _ERROR_TERMS):
        return "OK", "OK", "ok"
    if any(term in lowered for term in _ERROR_TERMS):
        return "ошибка", "error", "error"
    if any(term in lowered for term in _NOT_CHECKED_TERMS):
        return not_checked_ru, not_checked_en, "not_checked"
    return not_checked_ru, not_checked_en, "not_checked"


def _signer_display(row: Mapping[str, Any], *, source_available: bool) -> tuple[str, str, str]:
    if not source_available:
        return "не проверен", "not checked", "not_checked"
    if _status_field(row, "diagnostic_challenge_signed") is True or clean_text(_status_field(row, "diagnostic_status")).lower() == "diagnostic_ok":
        return "OK", "OK", "ok"
    diagnostic_requested = _status_field(row, "diagnostic_requested") is True
    status = clean_text(row.get("status") or _status_field(row, "diagnostic_status"))
    lowered = status.lower().replace("_", " ")
    if not diagnostic_requested or "not requested" in lowered:
        return "не проверен", "not checked", "not_checked"
    if any(term in lowered for term in _ERROR_TERMS):
        return "ошибка", "error", "error"
    return "не проверен", "not checked", "not_checked"


def _market_found(source: Mapping[str, Any], row: Mapping[str, Any], *, source_available: bool) -> bool:
    if not source_available:
        return False
    if source.get("market_found") is True or row.get("classification") == "reported_success":
        return True
    for key in ("market_candidate_count", "source_records_attempted"):
        if _positive_int(_status_field(row, key)) or _positive_int(source.get(key)):
            return True
    return _status_is_ok(row.get("status"))


def _token_selected(source: Mapping[str, Any], row: Mapping[str, Any], *, source_available: bool) -> bool:
    if not source_available:
        return False
    if source.get("token_id_selected") is True or _status_field(row, "target_token_id_present") is True:
        return True
    status = clean_text(row.get("status") or source.get("token_id_status")).lower()
    return any(term in status for term in ("selected", "resolved", "present")) and "required" not in status


def _status_is_ok(value: Any) -> bool:
    text = clean_text(value).lower().replace("_", " ")
    return bool(text) and any(term in text for term in _OK_TERMS) and not any(term in text for term in _ERROR_TERMS)


def _positive_int(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def _first_text(*values: Any) -> Any:
    for value in values:
        if isinstance(value, bool):
            return value
        if clean_text(value):
            return value
    return ""


def _artifact_summary(path: Path | None, payload: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(payload or {})
    return {
        "available": bool(value),
        "path": normalize_path(path) if path else "",
        "status": clean_text(value.get("status") or "not_available") if value else "missing",
        "contract_version": clean_text(value.get("contract_version")) if value else "",
    }


def _button_rows(language: str, rows: Sequence[Sequence[tuple[str, str]]]) -> list[dict[str, str]]:
    return [{"language": language, "label": label, "callback_data": callback_data} for row in rows for label, callback_data in row]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build 073T Telegram real-check results display artifacts.")
    parser.add_argument("--artifact-root", default="", help="Root directory containing local source artifacts.")
    parser.add_argument("--output-dir", default="", help="Directory for 073T output artifacts.")
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--json", action="store_true", help="Print the generated result JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generated = write_telegram_real_check_results_073t_artifacts(
        artifact_root=args.artifact_root or None,
        output_dir=args.output_dir or None,
        generated_at=args.generated_at,
    )
    if args.json:
        import json

        _safe_print(json.dumps(generated["result"], indent=2, sort_keys=True, ensure_ascii=False))
    else:
        _safe_print(generated["latest_status"]["status_text_ru"])
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
