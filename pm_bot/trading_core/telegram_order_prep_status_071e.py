from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, normalize_path, write_json

TASK_ID = "ORCH-PMBOT-TELEGRAM-071E-ORDER-PREP-STATUS-SCREEN-NO-LIVE"

STATUS_CONTRACT = "pmbot_telegram_order_prep_status_071e.v1"
RESULT_CONTRACT = "pmbot_telegram_order_prep_status_071e_result.v1"
MENU_SNAPSHOT_CONTRACT = "pmbot_telegram_order_prep_status_071e_menu_snapshot.v1"
SAFETY_SNAPSHOT_CONTRACT = "pmbot_telegram_order_prep_status_071e_safety_snapshot.v1"

ARTIFACT_DIR_NAME = "telegram_order_prep_status_071e"
RESULT_FILENAME = "telegram_order_prep_status_071e_result.json"
LATEST_STATUS_FILENAME = "latest_telegram_order_prep_status_071e.json"
MENU_SNAPSHOT_FILENAME = "telegram_order_prep_status_menu_snapshot_071e.json"
SAFETY_SNAPSHOT_FILENAME = "telegram_order_prep_status_safety_snapshot_071e.json"

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME

DISCOVERY_071A_DIR_NAMES = ("public_market_token_discovery_071a",)
DISCOVERY_071A_FILENAMES = (
    "latest_public_market_token_discovery_status_071a.json",
    "public_market_token_discovery_071a_result.json",
)
TOKEN_RESOLVER_070B_DIR_NAMES = ("first_order_market_token_resolver_070b",)
TOKEN_RESOLVER_070B_FILENAMES = (
    "latest_first_order_market_token_status_070b.json",
    "first_order_market_token_resolver_070b_result.json",
)
ACCOUNT_070C_DIR_NAMES = ("live_account_readonly_state_probe_070c",)
ACCOUNT_070C_FILENAMES = (
    "latest_live_account_readonly_state_status_070c.json",
    "live_account_readonly_state_probe_070c_result.json",
)
SIGNED_PAYLOAD_070A_DIR_NAMES = ("signed_order_payload_dry_run_070a",)
SIGNED_PAYLOAD_070A_FILENAMES = (
    "latest_signed_order_payload_dry_run_status_070a.json",
    "signed_order_payload_dry_run_070a_result.json",
    "signed_order_payload_contract_070a.json",
)

CONTROL_BUTTON_ROWS_RU = (
    (("Обновить статус", "pmbot:order_prep_status"),),
    (("Назад", "pmbot:home"),),
)
CONTROL_BUTTON_ROWS_EN = (
    (("Refresh status", "pmbot:order_prep_status"),),
    (("Back", "pmbot:home"),),
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


def telegram_order_prep_status_artifact_paths(
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


def build_telegram_order_prep_status(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    discovery_path = _first_existing_path(_candidate_paths(root, DISCOVERY_071A_DIR_NAMES, DISCOVERY_071A_FILENAMES))
    token_path = _first_existing_path(
        _candidate_paths(root, TOKEN_RESOLVER_070B_DIR_NAMES, TOKEN_RESOLVER_070B_FILENAMES)
    )
    account_path = _first_existing_path(_candidate_paths(root, ACCOUNT_070C_DIR_NAMES, ACCOUNT_070C_FILENAMES))
    signed_payload_path = _first_existing_path(
        _candidate_paths(root, SIGNED_PAYLOAD_070A_DIR_NAMES, SIGNED_PAYLOAD_070A_FILENAMES)
    )

    discovery = _load_optional_json(discovery_path, "071E market discovery status")
    token = _load_optional_json(token_path, "071E token resolver status")
    account = _load_optional_json(account_path, "071E read-only account status")
    signed_payload = _load_optional_json(signed_payload_path, "071E signed-payload dry-run status")

    market_found = any(_payload_has_market(payload) for payload in (discovery, token, signed_payload))
    token_id_found = any(_payload_has_token_id(payload) for payload in (token, signed_payload))
    account_display_ru, account_display_en, account_checked, account_readonly_ok = _account_display(
        account,
        available=bool(account),
    )
    signature_display_ru, signature_display_en, signature_contract_ready = _signature_display(
        signed_payload,
        available=bool(signed_payload),
    )

    latest_status: dict[str, Any] = {
        "contract_version": STATUS_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "telegram_order_prep_status_ready_review_only",
        "mode": "local_artifact_status_screen_only",
        "execution_mode": "local_artifact_read_only",
        "telegram_screen_title_ru": "🧪 Подготовка первого ордера",
        "telegram_screen_title_en": "First order prep",
        "artifact_root": normalize_path(root),
        "market_discovery_artifact_available": bool(discovery),
        "market_discovery_artifact_path": normalize_path(discovery_path) if discovery_path else "",
        "token_resolver_artifact_available": bool(token),
        "token_resolver_artifact_path": normalize_path(token_path) if token_path else "",
        "account_readonly_artifact_available": bool(account),
        "account_readonly_artifact_path": normalize_path(account_path) if account_path else "",
        "signed_payload_dry_run_artifact_available": bool(signed_payload),
        "signed_payload_dry_run_artifact_path": normalize_path(signed_payload_path) if signed_payload_path else "",
        "market_found": market_found,
        "market_display_ru": "найден" if market_found else "не найден",
        "market_display_en": "found" if market_found else "not found",
        "token_id_found": token_id_found,
        "token_id_display_ru": "найден" if token_id_found else "требуется выбор",
        "token_id_display_en": "found" if token_id_found else "selection required",
        "account_checked": account_checked,
        "account_readonly_ok": account_readonly_ok,
        "account_display_ru": account_display_ru,
        "account_display_en": account_display_en,
        "signature_contract_ready": signature_contract_ready,
        "signature_display_ru": signature_display_ru,
        "signature_display_en": signature_display_en,
        "order_submission_enabled": False,
        "order_submission_display_ru": "выключена",
        "order_submission_display_en": "disabled",
        "live_trading_enabled": False,
        "live_display_ru": "выключен",
        "live_display_en": "disabled",
        "screen_buttons": [
            {"label_ru": "Обновить статус", "label_en": "Refresh status", "callback_data": "pmbot:order_prep_status"},
            {"label_ru": "Назад", "label_en": "Back", "callback_data": "pmbot:home"},
        ],
        "source_artifacts": {
            "market_discovery_071a": _artifact_summary(discovery_path, discovery),
            "token_resolver_070b": _artifact_summary(token_path, token),
            "account_readonly_070c": _artifact_summary(account_path, account),
            "signed_payload_dry_run_070a": _artifact_summary(signed_payload_path, signed_payload),
        },
        "raw_token_id_exposed": False,
        "raw_account_values_exposed": False,
        "fake_balance_added": False,
        "fake_trades_added": False,
        "fake_pnl_added": False,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **telegram_order_prep_status_safety_flags(),
    }
    latest_status["status_text_ru"] = render_telegram_order_prep_status_text(latest_status, language="ru")
    latest_status["status_text_en"] = render_telegram_order_prep_status_text(latest_status, language="en")
    return latest_status


def write_telegram_order_prep_status_071e_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    status = build_telegram_order_prep_status(artifact_root=artifact_root, generated_at=generated_at)
    paths = telegram_order_prep_status_artifact_paths(output_dir)
    menu = build_telegram_order_prep_status_menu_snapshot(generated_at=generated_at)
    safety = build_telegram_order_prep_status_safety_snapshot(generated_at=generated_at)
    result = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "completed_review_only",
        "latest_status_path": normalize_path(paths["latest_status"]),
        "menu_snapshot_path": normalize_path(paths["menu_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "telegram_order_prep_status_071e": status,
        "menu_snapshot": menu,
        "safety_snapshot": safety,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **telegram_order_prep_status_safety_flags(),
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


def build_telegram_order_prep_status_menu_snapshot(
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
        "primary_button_labels_avoid_technical_terms": True,
        "forbidden_live_controls_added": False,
        "submit_cancel_controls_added": False,
        "signing_controls_added": False,
        "wallet_controls_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_order_prep_status_safety_flags(),
    }


def build_telegram_order_prep_status_safety_snapshot(
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "safe_local_status_screen_only",
        "allowed_inputs": [
            "local 071A public market/token discovery artifacts when present",
            "local 070B token resolver artifacts when present",
            "local 070C read-only account artifacts when present",
            "local 070A signed-payload contract dry-run artifacts when present",
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
        "no_static_safety_invariant_report_button": True,
        "no_fake_balance_pnl_or_trades": True,
        **telegram_order_prep_status_safety_flags(),
    }


def render_telegram_order_prep_status_text(status: Mapping[str, Any], *, language: str = "ru") -> str:
    value = dict(status or {})
    if clean_text(language).lower() == "ru":
        return "\n".join(
            [
                "🧪 Подготовка первого ордера",
                f"Рынок: {clean_text(value.get('market_display_ru') or 'не найден')}",
                f"Token ID: {clean_text(value.get('token_id_display_ru') or 'требуется выбор')}",
                f"Аккаунт: {clean_text(value.get('account_display_ru') or 'не проверен')}",
                f"Подпись: {clean_text(value.get('signature_display_ru') or 'не выполнялась')}",
                f"Отправка ордера: {clean_text(value.get('order_submission_display_ru') or 'выключена')}",
                f"Live: {clean_text(value.get('live_display_ru') or 'выключен')}",
            ]
        )
    return "\n".join(
        [
            "First order prep",
            f"Market: {clean_text(value.get('market_display_en') or 'not found')}",
            f"Token ID: {clean_text(value.get('token_id_display_en') or 'selection required')}",
            f"Account: {clean_text(value.get('account_display_en') or 'not checked')}",
            f"Signature: {clean_text(value.get('signature_display_en') or 'not run')}",
            f"Order sending: {clean_text(value.get('order_submission_display_en') or 'disabled')}",
            f"Live: {clean_text(value.get('live_display_en') or 'disabled')}",
        ]
    )


def telegram_order_prep_status_safety_flags() -> dict[str, Any]:
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


def _artifact_summary(path: Path | None, payload: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(payload or {})
    return {
        "available": bool(value),
        "path": normalize_path(path) if path else "",
        "status": clean_text(value.get("status") or "not_available") if value else "missing",
        "contract_version": clean_text(value.get("contract_version")) if value else "",
    }


def _payload_has_market(payload: Mapping[str, Any]) -> bool:
    value = dict(payload or {})
    if not value:
        return False
    for key in (
        "market_candidate_count",
        "market_count",
        "candidate_market_count",
        "discovered_market_count",
        "matched_market_count",
    ):
        if _positive_int(value.get(key)):
            return True
    for key in (
        "market",
        "market_id",
        "market_slug",
        "market_symbol",
        "condition_id",
        "question",
        "title",
        "selected_market_slug",
        "resolved_market_slug",
    ):
        if _present_text(value.get(key)):
            return True
    for key in ("market_candidates", "candidate_markets", "markets", "matched_markets"):
        rows = value.get(key)
        if isinstance(rows, list) and rows:
            return True
    target = value.get("target_contract")
    if isinstance(target, Mapping):
        return _payload_has_market(target)
    return False


def _payload_has_token_id(payload: Mapping[str, Any]) -> bool:
    value = dict(payload or {})
    if not value:
        return False
    for key in ("token_id_present", "target_token_selected", "token_selected", "token_resolved"):
        if value.get(key) is True:
            return True
    for key in (
        "token_id",
        "selected_token_id",
        "target_token_id",
        "outcome_token_id",
        "clob_token_id",
        "resolved_token_id",
    ):
        if _present_text(value.get(key)):
            return True
    token_ids = value.get("token_ids")
    if isinstance(token_ids, list) and any(_present_text(item) for item in token_ids):
        return True
    for key in ("target_contract", "order_payload_contract", "payload_contract"):
        nested = value.get(key)
        if isinstance(nested, Mapping) and _payload_has_token_id(nested):
            return True
    return False


def _account_display(payload: Mapping[str, Any], *, available: bool) -> tuple[str, str, bool, bool]:
    if not available:
        return "не проверен", "not checked", False, False
    value = dict(payload or {})
    status = clean_text(value.get("status")).lower()
    readonly_ok = any(
        value.get(key) is True
        for key in (
            "account_state_probe_performed",
            "account_readonly_ok",
            "read_only_ok",
            "readonly_ok",
            "readonly_probe_ok",
            "read_only_probe_ok",
        )
    )
    status_ok = any(term in status for term in ("ok", "success", "succeeded", "completed", "ready", "read-only", "readonly"))
    status_error = any(term in status for term in ("error", "failed", "failure", "invalid"))
    if readonly_ok or (status_ok and not status_error):
        return "read-only OK", "read-only OK", True, True
    return "ошибка", "error", True, False


def _signature_display(payload: Mapping[str, Any], *, available: bool) -> tuple[str, str, bool]:
    if not available:
        return "не выполнялась", "not run", False
    value = dict(payload or {})
    status = clean_text(value.get("status")).lower()
    ready = any(
        value.get(key) is True
        for key in (
            "order_payload_contract_built",
            "payload_contract_ready",
            "contract_ready",
            "contract_only",
            "dry_run_contract_ready",
        )
    )
    ready = ready or any(
        _present_text(value.get(key))
        for key in (
            "payload_contract_path",
            "signed_order_payload_contract_path",
            "order_payload_contract_path",
            "contract_path",
            "payload_contract_fingerprint",
            "contract_fingerprint",
        )
    )
    status_failed = any(term in status for term in ("error", "failed", "failure", "invalid"))
    ready = ready or (not status_failed and any(term in status for term in ("contract", "ready", "completed")))
    if ready:
        return "dry-run контракт готов", "dry-run contract ready", True
    return "не выполнялась", "not run", False


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
    parser = argparse.ArgumentParser(description="Build the 071E Telegram order prep status screen artifacts.")
    parser.add_argument("--artifact-root", default="", help="Root directory containing local source artifacts.")
    parser.add_argument("--output-dir", default="", help="Directory for 071E output artifacts.")
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--json", action="store_true", help="Print the generated result JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    generated = write_telegram_order_prep_status_071e_artifacts(
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
