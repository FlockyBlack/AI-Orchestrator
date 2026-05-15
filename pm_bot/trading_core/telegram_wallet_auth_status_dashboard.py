from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, normalize_path, write_json

TASK_ID = "ORCH-PMBOT-TELEGRAM-067E-WALLET-AUTH-STATUS-DASHBOARD-NO-LIVE"

STATUS_CONTRACT = "pmbot_telegram_wallet_auth_status_067e.v1"
RESULT_CONTRACT = "pmbot_telegram_wallet_auth_status_067e_result.v1"
MENU_SNAPSHOT_CONTRACT = "pmbot_telegram_wallet_auth_status_067e_menu_snapshot.v1"
SAFETY_SNAPSHOT_CONTRACT = "pmbot_telegram_wallet_auth_status_067e_safety_snapshot.v1"

ARTIFACT_DIR_NAME = "telegram_wallet_auth_status_067e"
RESULT_FILENAME = "telegram_wallet_auth_status_067e_result.json"
LATEST_STATUS_FILENAME = "latest_telegram_wallet_auth_status_067e.json"
MENU_SNAPSHOT_FILENAME = "telegram_wallet_auth_status_menu_snapshot_067e.json"
SAFETY_SNAPSHOT_FILENAME = "telegram_wallet_auth_status_safety_snapshot_067e.json"

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME

CREDENTIALS_064_DIR_NAME = "explicit_live_credentials_readiness_gate_064"
CREDENTIALS_064_MARKER_FILENAME = "redacted_marker_presence_064.json"
CREDENTIALS_064_LATEST_FILENAME = "latest_explicit_live_credentials_readiness_gate_status_064.json"

CLOB_L2_MARKER_058_DIR_NAME = "clob_l2_marker_preflight_058"
CLOB_L2_MARKER_058_FILENAME = "redacted_l2_marker_presence_058.json"
CLOB_L2_MARKER_058_LATEST_FILENAME = "latest_clob_l2_marker_preflight_status_058.json"

PROBE_067C_DIR_NAMES = (
    "clob_l2_auth_readonly_probe_067c",
    "clob_l2_auth_read_only_probe_067c",
    "clob_l2_auth_probe_067c",
)
PROBE_067C_LATEST_FILENAMES = (
    "latest_clob_l2_auth_readonly_probe_status_067c.json",
    "latest_clob_l2_auth_readonly_probe_067c.json",
    "latest_clob_l2_auth_read_only_probe_status_067c.json",
    "latest_clob_l2_auth_probe_status_067c.json",
    "clob_l2_auth_readonly_probe_067c_result.json",
)

API_KEY_MARKERS = (
    "PMBOT_POLYMARKET_L2_API_KEY_PRESENT",
    "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT",
    "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT",
)
PRIVATE_KEY_MARKERS = (
    "PMBOT_PRIVATE_KEY_CONFIGURED",
    "PMBOT_WALLET_PRIVATE_KEY_CONFIGURED",
    "PMBOT_POLYMARKET_PRIVATE_KEY_CONFIGURED",
    "PMBOT_SIGNING_PRIVATE_KEY_CONFIGURED",
)
WALLET_MARKERS = ("PMBOT_WALLET_ADDRESS_CONFIGURED",)
FUNDER_MARKERS = ("PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED",)

CONTROL_BUTTON_ROWS_RU = (
    (("Обновить статус", "pmbot:connection_status"),),
    (("Запустить read-only проверку", "pmbot:run:connection_status_067e"),),
    (("Назад", "pmbot:home"),),
)
CONTROL_BUTTON_ROWS_EN = (
    (("Refresh status", "pmbot:connection_status"),),
    (("Run read-only status check", "pmbot:run:connection_status_067e"),),
    (("Back", "pmbot:home"),),
)

_ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")


def telegram_wallet_auth_status_artifact_paths(
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


def build_telegram_wallet_auth_status(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    credentials_marker_path = _first_existing_path(_credential_marker_paths(root))
    credentials_latest_path = _first_existing_path(_credential_latest_paths(root))
    l2_marker_path = _first_existing_path(_l2_marker_paths(root))
    l2_latest_path = _first_existing_path(_l2_latest_paths(root))
    probe_path = _first_existing_path(_probe_067c_paths(root))

    credentials_marker = _load_optional_json(credentials_marker_path, "067E credentials marker presence")
    credentials_latest = _load_optional_json(credentials_latest_path, "067E credentials latest status")
    l2_marker = _load_optional_json(l2_marker_path, "067E L2 marker presence")
    l2_latest = _load_optional_json(l2_latest_path, "067E L2 latest status")
    probe = _load_optional_json(probe_path, "067E CLOB L2 auth read-only probe")

    marker_presence = _marker_presence_map(credentials_marker)
    l2_presence = _l2_presence_map(l2_marker)
    api_keys_added = _all_markers_present(API_KEY_MARKERS, marker_presence, l2_presence)
    private_key_added = _any_marker_present(PRIVATE_KEY_MARKERS, marker_presence)
    wallet_marker_added = _any_marker_present(WALLET_MARKERS, marker_presence)
    funder_marker_added = _any_marker_present(FUNDER_MARKERS, marker_presence)

    wallet_display = _display_address_or_presence(
        _first_text(
            probe.get("wallet_address_redacted"),
            probe.get("wallet_address"),
            probe.get("wallet"),
            credentials_latest.get("wallet_address_redacted"),
        ),
        marker_present=wallet_marker_added,
    )
    funder_display = _display_address_or_presence(
        _first_text(
            probe.get("funder_address_redacted"),
            probe.get("funder_address"),
            probe.get("funder"),
            credentials_latest.get("funder_address_redacted"),
        ),
        marker_present=funder_marker_added,
    )
    signature_type_display = _display_signature_type(
        _first_text(
            probe.get("signature_type"),
            probe.get("signature_type_redacted"),
            credentials_latest.get("signature_type"),
        )
    )
    probe_status = _normalize_probe_status(probe)
    probe_available = bool(probe)

    latest_status = {
        "contract_version": STATUS_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "telegram_wallet_auth_status_ready_review_only",
        "mode": "local_status_dashboard_only",
        "execution_mode": "dry_run_status_read",
        "artifact_root": normalize_path(root),
        "credentials_marker_artifact_available": bool(credentials_marker),
        "credentials_marker_path": normalize_path(credentials_marker_path) if credentials_marker_path else "",
        "credentials_latest_artifact_available": bool(credentials_latest),
        "credentials_latest_path": normalize_path(credentials_latest_path) if credentials_latest_path else "",
        "clob_l2_marker_artifact_available": bool(l2_marker),
        "clob_l2_marker_path": normalize_path(l2_marker_path) if l2_marker_path else "",
        "clob_l2_latest_artifact_available": bool(l2_latest),
        "clob_l2_latest_path": normalize_path(l2_latest_path) if l2_latest_path else "",
        "clob_l2_auth_readonly_probe_artifact_available": probe_available,
        "clob_l2_auth_readonly_probe_path": normalize_path(probe_path) if probe_path else "",
        "api_keys_added": api_keys_added,
        "api_keys_status": "added" if api_keys_added else "not_added",
        "api_keys_display_ru": "добавлены" if api_keys_added else "не добавлены",
        "api_keys_display_en": "added" if api_keys_added else "not added",
        "private_key_added": private_key_added,
        "private_key_status": "added" if private_key_added else "not_added",
        "private_key_display_ru": "добавлен" if private_key_added else "не добавлен",
        "private_key_display_en": "added" if private_key_added else "not added",
        "wallet_marker_added": wallet_marker_added,
        "wallet_display": wallet_display,
        "signature_type_display": signature_type_display,
        "funder_marker_added": funder_marker_added,
        "funder_display": funder_display,
        "l2_auth_probe_status": probe_status,
        "l2_auth_probe_display": _probe_display(probe_status),
        "open_orders_status": _probe_scoped_status(
            probe,
            probe_available=probe_available,
            status_keys=("open_orders_status", "open_orders_read_status", "orders_status"),
            data_keys=("open_orders", "open_orders_count"),
        ),
        "balance_allowance_status": _probe_scoped_status(
            probe,
            probe_available=probe_available,
            status_keys=("balance_allowance_status", "balance_status", "allowance_status"),
            data_keys=("balance", "balances", "allowance", "allowances"),
        ),
        "values_never_shown": True,
        "redacted_presence_only": True,
        "local_artifact_read_only": True,
        "dashboard_does_not_run_probe": True,
        "latest_067c_probe_artifact_only": True,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_wallet_auth_status_safety_flags(),
    }
    latest_status["status_text_ru"] = render_telegram_wallet_auth_status_text(latest_status, language="ru")
    latest_status["status_text_en"] = render_telegram_wallet_auth_status_text(latest_status, language="en")
    return latest_status


def write_telegram_wallet_auth_status_067e_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    status = build_telegram_wallet_auth_status(artifact_root=artifact_root, generated_at=generated_at)
    paths = telegram_wallet_auth_status_artifact_paths(output_dir)
    menu = build_telegram_wallet_auth_status_menu_snapshot(generated_at=generated_at)
    safety = build_telegram_wallet_auth_status_safety_snapshot(generated_at=generated_at)
    result = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "completed_review_only",
        "latest_status_path": normalize_path(paths["latest_status"]),
        "menu_snapshot_path": normalize_path(paths["menu_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "telegram_wallet_auth_status_067e": status,
        "menu_snapshot": menu,
        "safety_snapshot": safety,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_wallet_auth_status_safety_flags(),
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


def build_telegram_wallet_auth_status_menu_snapshot(
    *,
    mini_app_url_configured: bool = False,
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
        "title_ru": "🔐 Подключение",
        "title_en": "Connection",
        "buttons": buttons,
        "button_count": len(buttons),
        "mini_app_button_label_ru": "🖥 Открыть PMBOT",
        "mini_app_button_label_en": "🖥 Open PMBOT",
        "mini_app_button_added_only_when_url_configured": True,
        "mini_app_url_configured": mini_app_url_configured is True,
        "forbidden_live_controls_added": False,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_wallet_auth_status_safety_flags(),
    }


def build_telegram_wallet_auth_status_safety_snapshot(
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "safe_review_only_status_dashboard",
        "allowed_inputs": [
            "redacted credential presence artifacts",
            "latest 067C CLOB L2 auth read-only probe artifacts when present",
        ],
        "forbidden_inputs": [
            "raw private key values",
            "raw API secret values",
            "raw passphrase values",
            "wallet files",
            "credential stores",
        ],
        "forbidden_actions": [
            "wallet connection",
            "signing",
            "order submission",
            "order cancellation",
            "authenticated calls from this dashboard",
            "live enablement",
        ],
        "values_never_shown": True,
        "no_fake_balance_pnl_or_trades": True,
        **telegram_wallet_auth_status_safety_flags(),
    }


def render_telegram_wallet_auth_status_text(status: Mapping[str, Any], *, language: str = "ru") -> str:
    value = dict(status or {})
    if clean_text(language).lower() == "ru":
        return "\n".join(
            [
                "🔐 Подключение",
                f"API ключи: {clean_text(value.get('api_keys_display_ru') or 'не добавлены')}",
                f"Private key: {clean_text(value.get('private_key_display_ru') or 'не добавлен')}",
                f"Wallet: {clean_text(value.get('wallet_display') or 'missing')}",
                f"Signature type: {clean_text(value.get('signature_type_display') or 'missing')}",
                f"Funder: {clean_text(value.get('funder_display') or 'missing')}",
                f"L2 auth probe: {clean_text(value.get('l2_auth_probe_display') or 'not run')}",
                f"Open orders: {clean_text(value.get('open_orders_status') or 'unknown')}",
                f"Balance/allowance: {clean_text(value.get('balance_allowance_status') or 'unknown')}",
                "Values never shown",
                "Только статус; live-торговля, подпись, подключение кошелька и submit/cancel не выполняются.",
            ]
        )
    return "\n".join(
        [
            "Connection",
            f"API keys: {clean_text(value.get('api_keys_display_en') or 'not added')}",
            f"Private key: {clean_text(value.get('private_key_display_en') or 'not added')}",
            f"Wallet: {clean_text(value.get('wallet_display') or 'missing')}",
            f"Signature type: {clean_text(value.get('signature_type_display') or 'missing')}",
            f"Funder: {clean_text(value.get('funder_display') or 'missing')}",
            f"L2 auth probe: {clean_text(value.get('l2_auth_probe_display') or 'not run')}",
            f"Open orders: {clean_text(value.get('open_orders_status') or 'unknown')}",
            f"Balance/allowance: {clean_text(value.get('balance_allowance_status') or 'unknown')}",
            "Values never shown",
            "Status only; no live trading, signing, wallet connection, submit, or cancel action is performed.",
        ]
    )


def telegram_wallet_auth_status_safety_flags() -> dict[str, Any]:
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
        "real_authenticated_get_performed": False,
        "dashboard_authenticated_call_performed": False,
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


def _credential_marker_paths(root: Path) -> tuple[Path, ...]:
    return _dedupe_paths(
        (
            root / CREDENTIALS_064_DIR_NAME / CREDENTIALS_064_MARKER_FILENAME,
            root / CREDENTIALS_064_MARKER_FILENAME,
        )
    )


def _credential_latest_paths(root: Path) -> tuple[Path, ...]:
    return _dedupe_paths(
        (
            root / CREDENTIALS_064_DIR_NAME / CREDENTIALS_064_LATEST_FILENAME,
            root / CREDENTIALS_064_LATEST_FILENAME,
        )
    )


def _l2_marker_paths(root: Path) -> tuple[Path, ...]:
    return _dedupe_paths(
        (
            root / CLOB_L2_MARKER_058_DIR_NAME / CLOB_L2_MARKER_058_FILENAME,
            root / CLOB_L2_MARKER_058_FILENAME,
        )
    )


def _l2_latest_paths(root: Path) -> tuple[Path, ...]:
    return _dedupe_paths(
        (
            root / CLOB_L2_MARKER_058_DIR_NAME / CLOB_L2_MARKER_058_LATEST_FILENAME,
            root / CLOB_L2_MARKER_058_LATEST_FILENAME,
        )
    )


def _probe_067c_paths(root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for dirname in PROBE_067C_DIR_NAMES:
        for filename in PROBE_067C_LATEST_FILENAMES:
            paths.append(root / dirname / filename)
    for filename in PROBE_067C_LATEST_FILENAMES:
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


def _marker_presence_map(marker_presence: Mapping[str, Any]) -> dict[str, bool]:
    rows = marker_presence.get("marker_checks") if isinstance(marker_presence.get("marker_checks"), list) else []
    return {
        clean_text(row.get("marker_label")): row.get("present") is True
        for row in rows
        if isinstance(row, Mapping) and clean_text(row.get("marker_label"))
    }


def _l2_presence_map(marker_presence: Mapping[str, Any]) -> dict[str, bool]:
    rows = marker_presence.get("env_presence_items") if isinstance(marker_presence.get("env_presence_items"), list) else []
    return {
        clean_text(row.get("env_var_name")): row.get("present") is True
        for row in rows
        if isinstance(row, Mapping) and clean_text(row.get("env_var_name"))
    }


def _all_markers_present(
    markers: Sequence[str],
    primary: Mapping[str, bool],
    fallback: Mapping[str, bool] | None = None,
) -> bool:
    secondary = dict(fallback or {})
    return all(primary.get(marker) is True or secondary.get(marker) is True for marker in markers)


def _any_marker_present(markers: Sequence[str], primary: Mapping[str, bool]) -> bool:
    return any(primary.get(marker) is True for marker in markers)


def _display_address_or_presence(value: str, *, marker_present: bool) -> str:
    text = clean_text(value)
    if text:
        redacted = _redact_address(text)
        if _safe_display_value(redacted):
            return redacted
    if marker_present:
        return "configured:redacted"
    return "missing"


def _display_signature_type(value: str) -> str:
    text = clean_text(value)
    if not text:
        return "missing"
    if text.isdecimal() and len(text) <= 2:
        return text
    if text in {"configured:redacted", "missing"}:
        return text
    return "configured:redacted"


def _redact_address(value: str) -> str:
    text = clean_text(value)
    match = _ADDRESS_RE.search(text)
    if match:
        address = match.group(0)
        return f"{address[:6]}...{address[-4:]}"
    if "..." in text and text.lower().startswith("0x"):
        return text
    return text


def _safe_display_value(value: str) -> bool:
    lowered = value.lower()
    forbidden = ("private", "secret", "seed", "mnemonic", "passphrase", "signed_payload", "signature:")
    return not any(term in lowered for term in forbidden)


def _normalize_probe_status(probe: Mapping[str, Any]) -> str:
    if not probe:
        return "not_run"
    raw = clean_text(
        probe.get("l2_auth_probe_status")
        or probe.get("probe_status")
        or probe.get("readonly_probe_status")
        or probe.get("status")
    ).lower()
    if not raw:
        return "failed"
    if "blocked" in raw:
        return "blocked"
    if "fail" in raw or "error" in raw:
        return "failed"
    if "ok" in raw or "success" in raw or "ready" in raw or "completed" in raw:
        return "ok"
    if "not_run" in raw or "not run" in raw or "skipped" in raw:
        return "not_run"
    return raw


def _probe_display(status: str) -> str:
    value = clean_text(status) or "not_run"
    return "not run" if value == "not_run" else value


def _probe_scoped_status(
    probe: Mapping[str, Any],
    *,
    probe_available: bool,
    status_keys: Sequence[str],
    data_keys: Sequence[str],
) -> str:
    if not probe_available:
        return "unknown"
    for key in status_keys:
        status = clean_text(probe.get(key))
        if status:
            return _safe_probe_status_text(status)
    for key in data_keys:
        if key in probe:
            return "available_from_probe"
    return "unknown"


def _safe_probe_status_text(value: str) -> str:
    text = clean_text(value)
    lowered = text.lower()
    if any(term in lowered for term in ("secret", "private", "passphrase", "seed", "mnemonic")):
        return "available_from_probe"
    if _ADDRESS_RE.search(text):
        return "available_from_probe"
    if len(text) > 80:
        return "available_from_probe"
    return text


def _first_text(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def _button_rows(language: str, rows: Sequence[Sequence[tuple[str, str]]]) -> list[dict[str, Any]]:
    rendered: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        for button_index, (label, callback_data) in enumerate(row):
            rendered.append(
                {
                    "language": language,
                    "row": row_index,
                    "column": button_index,
                    "label": label,
                    "callback_data": callback_data,
                    "review_only": True,
                    "execution_enabling": False,
                }
            )
    return rendered
