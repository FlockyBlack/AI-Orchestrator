from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.live_readonly_status_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    SOURCE_067C,
    SOURCE_067E,
    SOURCE_070C,
    STATUS_FIELDS,
    TASK_ID,
    UNKNOWN_STATUS,
    LiveReadonlyLatestStatus,
    LiveReadonlyStatusAggregatorResult,
    LiveReadonlyStatusField,
    LiveReadonlyStatusSource,
    build_live_readonly_status_safety_snapshot,
    build_source_index,
    live_readonly_status_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "live_readonly_status_aggregator_071b"

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--wallet",
    "--wallet-connect",
    "--private-key",
    "--signing",
    "--sign",
    "--submit",
    "--cancel",
    "--order",
    "--post",
    "--put",
    "--patch",
    "--delete",
    "--derive-api-key",
    "--create-api-key",
)

SOURCE_CANDIDATES = {
    SOURCE_067C: {
        "label": "067C CLOB L2 auth read-only probe",
        "source_kind": "clob_l2_auth_readonly_probe",
        "required": True,
        "dir_names": (
            "clob_l2_auth_readonly_probe_067c",
            "clob_l2_auth_read_only_probe_067c",
            "clob_l2_auth_probe_067c",
        ),
        "filenames": (
            "latest_clob_l2_auth_readonly_probe_status_067c.json",
            "latest_clob_l2_auth_readonly_probe_067c.json",
            "latest_clob_l2_auth_read_only_probe_status_067c.json",
            "latest_clob_l2_auth_probe_status_067c.json",
            "clob_l2_auth_readonly_probe_067c_result.json",
        ),
    },
    SOURCE_070C: {
        "label": "070C live account read-only state probe",
        "source_kind": "live_account_readonly_state_probe",
        "required": False,
        "dir_names": (
            "live_account_readonly_state_probe_070c",
            "live_account_read_only_state_probe_070c",
            "live_account_state_probe_070c",
        ),
        "filenames": (
            "latest_live_account_readonly_state_status_070c.json",
            "latest_live_account_read_only_state_status_070c.json",
            "latest_live_account_state_status_070c.json",
            "live_account_readonly_state_probe_070c_result.json",
        ),
    },
    SOURCE_067E: {
        "label": "067E Telegram wallet/auth status dashboard",
        "source_kind": "telegram_wallet_auth_status",
        "required": False,
        "dir_names": (
            "telegram_wallet_auth_status_067e",
        ),
        "filenames": (
            "latest_telegram_wallet_auth_status_067e.json",
            "telegram_wallet_auth_status_067e_result.json",
        ),
    },
}


def live_readonly_status_aggregator_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "live_readonly_status_aggregator_071b_result.json",
        "latest_status": root / "latest_live_readonly_status_071b.json",
        "sources": root / "live_readonly_status_sources_071b.json",
        "safety_snapshot": root / "live_readonly_status_safety_snapshot_071b.json",
        "operator_md": root / "live_readonly_status_operator_summary_071b.md",
    }


def run_live_readonly_status_aggregator(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("live read-only status aggregation requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    source_root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = live_readonly_status_aggregator_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    source_rows, source_payloads = load_live_readonly_status_sources(
        artifact_root=source_root,
        generated_at=generated_at,
    )
    sources = build_source_index(
        source_rows,
        artifact_root=normalize_path(source_root),
        generated_at=generated_at,
    )
    fields = build_live_readonly_status_fields(
        source_rows=source_rows,
        source_payloads=source_payloads,
        generated_at=generated_at,
    )
    latest_status = LiveReadonlyLatestStatus(
        market=market_symbol,
        strategy=strategy_name,
        status="live_readonly_status_aggregated",
        fields=fields,
        sources=source_rows,
        source_paths={
            source_id: clean_text(row.get("selected_path"))
            for source_id, row in source_rows.items()
            if clean_text(row.get("selected_path"))
        },
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()
    safety_snapshot = build_live_readonly_status_safety_snapshot(generated_at=generated_at)
    result = LiveReadonlyStatusAggregatorResult(
        market=market_symbol,
        strategy=strategy_name,
        latest_status=latest_status,
        sources=sources,
        safety_snapshot=safety_snapshot,
        artifact_paths=path_refs,
        operator_summary=_operator_summary(latest_status),
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["sources"], sources)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_live_readonly_status_aggregator_markdown(result))
    return result


def load_live_readonly_status_sources(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    source_rows: dict[str, dict[str, Any]] = {}
    source_payloads: dict[str, dict[str, Any]] = {}
    for source_id in (SOURCE_067C, SOURCE_070C, SOURCE_067E):
        row, payload = _load_source(source_id, root=root, generated_at=generated_at)
        source_rows[source_id] = row
        source_payloads[source_id] = payload
    return source_rows, source_payloads


def build_live_readonly_status_fields(
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    generated_at: str = GENERATED_AT,
) -> dict[str, dict[str, Any]]:
    payload_067c = dict(source_payloads.get(SOURCE_067C, {}))
    payload_070c = dict(source_payloads.get(SOURCE_070C, {}))
    payload_067e = dict(source_payloads.get(SOURCE_067E, {}))

    fields = {
        "l2_auth_status": _field_from_candidates(
            "l2_auth_status",
            (
                _candidate(SOURCE_067C, source_rows, "status", payload_067c.get("status")),
                _candidate(SOURCE_067E, source_rows, "l2_auth_probe_status", payload_067e.get("l2_auth_probe_status")),
            ),
            generated_at=generated_at,
        ),
        "open_orders_status": _field_from_candidates(
            "open_orders_status",
            (
                _candidate(SOURCE_070C, source_rows, "open_orders_status", payload_070c.get("open_orders_status")),
                _candidate(SOURCE_067C, source_rows, "open_order_count", _open_orders_status_from_067c(payload_067c)),
                _candidate(SOURCE_067E, source_rows, "open_orders_status", payload_067e.get("open_orders_status")),
            ),
            generated_at=generated_at,
        ),
        "balance_status": _field_from_candidates(
            "balance_status",
            (
                _candidate(SOURCE_070C, source_rows, "balance_allowance_availability_status", _balance_status_from_070c(payload_070c)),
                _candidate(SOURCE_067C, source_rows, "balance_allowance_probe_status", _balance_or_allowance_status(payload_067c.get("balance_allowance_probe_status"))),
                _candidate(SOURCE_067E, source_rows, "balance_allowance_status", _balance_or_allowance_status(payload_067e.get("balance_allowance_status"))),
            ),
            generated_at=generated_at,
        ),
        "allowance_status": _field_from_candidates(
            "allowance_status",
            (
                _candidate(SOURCE_070C, source_rows, "balance_allowance_availability_status", _allowance_status_from_070c(payload_070c)),
                _candidate(SOURCE_067C, source_rows, "balance_allowance_probe_status", _balance_or_allowance_status(payload_067c.get("balance_allowance_probe_status"))),
                _candidate(SOURCE_067E, source_rows, "balance_allowance_status", _balance_or_allowance_status(payload_067e.get("balance_allowance_status"))),
            ),
            generated_at=generated_at,
        ),
        "wallet_address_status": _field_from_candidates(
            "wallet_address_status",
            (
                _candidate(SOURCE_070C, source_rows, "wallet_address_status", payload_070c.get("wallet_address_status")),
                _candidate(SOURCE_067E, source_rows, "wallet_display", _display_status(payload_067e.get("wallet_display"))),
            ),
            generated_at=generated_at,
        ),
        "funder_status": _field_from_candidates(
            "funder_status",
            (
                _candidate(SOURCE_070C, source_rows, "funder_address_status", payload_070c.get("funder_address_status")),
                _candidate(SOURCE_067E, source_rows, "funder_display", _display_status(payload_067e.get("funder_display"))),
            ),
            generated_at=generated_at,
        ),
        "signature_type_status": _field_from_candidates(
            "signature_type_status",
            (
                _candidate(SOURCE_070C, source_rows, "signature_type_status", payload_070c.get("signature_type_status")),
                _candidate(SOURCE_067E, source_rows, "signature_type_display", _display_status(payload_067e.get("signature_type_display"))),
            ),
            generated_at=generated_at,
        ),
    }
    return fields


def render_live_readonly_status_aggregator_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Live read-only status aggregation completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy'))}",
            "Local artifacts only: true",
            "Allowed for live: false",
            "Private key read: false",
            "Network calls: false",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Signing: blocked",
            "Wallet connection: blocked",
            f"L2 auth: {clean_text(value.get('l2_auth_status')) or UNKNOWN_STATUS}",
            f"Open orders: {clean_text(value.get('open_orders_status')) or UNKNOWN_STATUS}",
            f"Balance: {clean_text(value.get('balance_status')) or UNKNOWN_STATUS}",
            f"Allowance: {clean_text(value.get('allowance_status')) or UNKNOWN_STATUS}",
            f"Wallet address: {clean_text(value.get('wallet_address_status')) or UNKNOWN_STATUS}",
            f"Funder: {clean_text(value.get('funder_status')) or UNKNOWN_STATUS}",
            f"Signature type: {clean_text(value.get('signature_type_status')) or UNKNOWN_STATUS}",
            f"Artifact: {clean_text(value.get('artifact_paths', {}).get('result') if isinstance(value.get('artifact_paths'), Mapping) else '')}",
        ]
    )


def render_live_readonly_status_aggregator_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    source_index = dict(value.get("sources", {}))
    sources = {
        clean_text(key): dict(row)
        for key, row in dict(source_index.get("sources", {})).items()
        if isinstance(row, Mapping)
    }
    fields = {
        clean_text(key): dict(row)
        for key, row in dict(latest.get("fields", {})).items()
        if isinstance(row, Mapping)
    }
    lines = [
        "# PMBOT Live Read-Only Status Aggregator 071B",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market')}`",
        f"- Strategy: `{value.get('strategy')}`",
        f"- execution_mode: `{EXECUTION_MODE}`",
        "- local_artifact_read_only: `true`",
        "- allowed_for_live: `false`",
        "- private_key_read: `false`",
        "- network_access_performed: `false`",
        "",
        "## Aggregated Status",
        "",
        *bullet_lines(
            f"`{field_name}` = `{dict(fields.get(field_name, {})).get('status', UNKNOWN_STATUS)}`"
            for field_name in STATUS_FIELDS
        ),
        "",
        "## Sources",
        "",
        *bullet_lines(
            f"`{source_id}` available=`{str(row.get('available') is True).lower()}` path=`{row.get('selected_path') or 'none'}`"
            for source_id, row in sources.items()
        ),
        "",
        "## Safety",
        "",
        "- no network call is made by this aggregator",
        "- no environment value is read",
        "- no private key, wallet file, or credential store is read",
        "- no order write, cancellation, signing, signer, or wallet connection path is added",
        "- no fake balances, PnL, order rows, fills, or positions are created",
        "- absent inputs remain `unknown`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "live read-only status aggregation blocks live/wallet/signing/order/write flags: "
            + ", ".join(requested)
        )


def _load_source(
    source_id: str,
    *,
    root: Path,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = SOURCE_CANDIDATES[source_id]
    candidates = _candidate_paths(root, config)
    candidate_strings = tuple(normalize_path(path) for path in candidates)
    selected = next((path for path in candidates if path.exists()), None)
    if selected is None:
        row = LiveReadonlyStatusSource(
            source_id=source_id,
            label=clean_text(config["label"]),
            source_kind=clean_text(config["source_kind"]),
            required=config["required"] is True,
            available=False,
            selected_path="",
            candidate_paths=candidate_strings,
            status=UNKNOWN_STATUS,
            generated_at=generated_at,
        ).to_dict()
        return row, {}
    try:
        loaded = load_json_object(selected, label=clean_text(config["label"]))
        payload = _latest_payload(source_id, loaded)
        status = clean_text(payload.get("status")) or clean_text(loaded.get("status")) or "available"
        row = LiveReadonlyStatusSource(
            source_id=source_id,
            label=clean_text(config["label"]),
            source_kind=clean_text(config["source_kind"]),
            required=config["required"] is True,
            available=True,
            selected_path=normalize_path(selected),
            candidate_paths=candidate_strings,
            status=status,
            contract_version_seen=clean_text(payload.get("contract_version") or loaded.get("contract_version")),
            generated_at=generated_at,
        ).to_dict()
        return row, payload
    except Exception as exc:
        row = LiveReadonlyStatusSource(
            source_id=source_id,
            label=clean_text(config["label"]),
            source_kind=clean_text(config["source_kind"]),
            required=config["required"] is True,
            available=False,
            selected_path=normalize_path(selected),
            candidate_paths=candidate_strings,
            status="unreadable",
            load_error=type(exc).__name__,
            generated_at=generated_at,
        ).to_dict()
        return row, {}


def _candidate_paths(root: Path, config: Mapping[str, Any]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for dirname in tuple(config.get("dir_names", ())):
        for filename in tuple(config.get("filenames", ())):
            paths.append(root / clean_text(dirname) / clean_text(filename))
    for filename in tuple(config.get("filenames", ())):
        paths.append(root / clean_text(filename))
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


def _latest_payload(source_id: str, loaded: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(loaded or {})
    latest = value.get("latest_status")
    if isinstance(latest, Mapping):
        return dict(latest)
    if source_id == SOURCE_067E:
        nested = value.get("telegram_wallet_auth_status_067e")
        if isinstance(nested, Mapping):
            return dict(nested)
    return value


def _candidate(
    source_id: str,
    source_rows: Mapping[str, Mapping[str, Any]],
    evidence_key: str,
    status: Any,
) -> dict[str, str]:
    row = dict(source_rows.get(source_id, {}))
    if row.get("available") is not True:
        return {}
    status_text = _safe_status(status)
    if not status_text:
        return {}
    return {
        "source_id": source_id,
        "source_path": clean_text(row.get("selected_path")),
        "evidence_key": clean_text(evidence_key),
        "status": status_text,
    }


def _field_from_candidates(
    field_name: str,
    candidates: Sequence[Mapping[str, str]],
    *,
    generated_at: str,
) -> dict[str, Any]:
    for candidate in candidates:
        status = clean_text(candidate.get("status"))
        if not status:
            continue
        return LiveReadonlyStatusField(
            field_name=field_name,
            status=status,
            source_id=clean_text(candidate.get("source_id")),
            source_path=clean_text(candidate.get("source_path")),
            evidence_key=clean_text(candidate.get("evidence_key")),
            generated_at=generated_at,
        ).to_dict()
    return LiveReadonlyStatusField(
        field_name=field_name,
        status=UNKNOWN_STATUS,
        source_id="none",
        source_path="",
        evidence_key="",
        note="no local source artifact provided this status",
        generated_at=generated_at,
    ).to_dict()


def _open_orders_status_from_067c(payload: Mapping[str, Any]) -> str:
    if not payload:
        return ""
    value = payload.get("open_order_count")
    if isinstance(value, int) and not isinstance(value, bool):
        return "count_available_redacted"
    if payload.get("l2_authenticated_readonly_probe_performed") is True:
        return "count_unavailable"
    if clean_text(payload.get("status")):
        return "not_available"
    return ""


def _balance_status_from_070c(payload: Mapping[str, Any]) -> str:
    availability = clean_text(payload.get("balance_allowance_availability_status"))
    direct = clean_text(payload.get("balance_allowance_status"))
    if "balance" in availability:
        return "available_redacted"
    return direct or availability


def _allowance_status_from_070c(payload: Mapping[str, Any]) -> str:
    availability = clean_text(payload.get("balance_allowance_availability_status"))
    direct = clean_text(payload.get("balance_allowance_status"))
    if "allowance" in availability:
        return "available_redacted"
    return direct or availability


def _balance_or_allowance_status(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if text == "unknown":
        return UNKNOWN_STATUS
    return text


def _display_status(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    lowered = text.lower()
    if lowered in {"missing", "not added", "not_added", "not run", "not_run", "unknown"}:
        return "missing" if lowered == "missing" else lowered.replace(" ", "_")
    if "..." in text or "redacted" in lowered or text.isdigit():
        return "present_redacted"
    if lowered.startswith("configured"):
        return "present_redacted"
    return "present_redacted"


def _safe_status(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    lowered = text.lower()
    forbidden_terms = (
        "private key",
        "private_key",
        "api secret",
        "api_secret",
        "passphrase",
        "mnemonic",
        "seed phrase",
        "seed_phrase",
        "signed payload",
        "signed_payload",
    )
    if any(term in lowered for term in forbidden_terms):
        return "available_redacted"
    if text.startswith("0x") and len(text) > 12 and "..." not in text:
        return "present_redacted"
    if len(text) > 120:
        return "available_redacted"
    return text


def _operator_summary(latest_status: Mapping[str, Any]) -> str:
    value = dict(latest_status or {})
    return (
        "Live read-only status aggregation completed with local artifacts only; "
        + "l2_auth_status="
        + clean_text(value.get("l2_auth_status", UNKNOWN_STATUS))
        + "; open_orders_status="
        + clean_text(value.get("open_orders_status", UNKNOWN_STATUS))
        + "; balance_status="
        + clean_text(value.get("balance_status", UNKNOWN_STATUS))
        + "; allowance_status="
        + clean_text(value.get("allowance_status", UNKNOWN_STATUS))
        + "; allowed_for_live=false; no network, environment secret, private-key, wallet connection, signing, order write, cancellation, or fake account data path was used."
    )
