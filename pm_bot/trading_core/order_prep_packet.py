from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.order_prep_packet_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    MODE,
    ORDER_PREP_PACKET_BLOCKERS_CONTRACT,
    ORDER_PREP_PACKET_LATEST_STATUS_CONTRACT,
    ORDER_PREP_PACKET_OPERATOR_REVIEW_CONTRACT,
    ORDER_PREP_PACKET_RESULT_CONTRACT,
    ORDER_PREP_PACKET_SOURCES_CONTRACT,
    SOURCE_ACCOUNT_PROBE_070C,
    SOURCE_APPROVAL_CONTRACT_065D,
    SOURCE_DISCOVERY_TO_TOKEN_071D,
    SOURCE_FIRST_ORDER_TOKEN_070B,
    SOURCE_IDS,
    SOURCE_LIVE_READONLY_071B,
    SOURCE_PUBLIC_DISCOVERY_071A,
    SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A,
    SOURCE_SIGNER_DIAGNOSTIC_069A,
    STATUS_BLOCKED,
    STATUS_REVIEW_READY,
    TASK_ID,
    OrderPrepPacketConfig,
    OrderPrepPacketReadinessItem,
    OrderPrepPacketSource,
    build_blocker,
    build_safety_snapshot,
    order_prep_packet_safety_flags,
    validate_order_prep_packet_result,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "order_prep_packet_072a"

SOURCE_SPECS: dict[str, dict[str, Any]] = {
    SOURCE_PUBLIC_DISCOVERY_071A: {
        "label": "071A public market/token discovery",
        "dir_names": ("public_market_token_discovery_071a",),
        "filenames": (
            "public_market_token_discovery_071a_result.json",
            "latest_public_market_token_discovery_status_071a.json",
            "public_outcome_token_candidates_071a.json",
        ),
    },
    SOURCE_DISCOVERY_TO_TOKEN_071D: {
        "label": "071D discovery-to-token resolver bridge",
        "dir_names": ("discovery_to_token_resolver_bridge_071d",),
        "filenames": (
            "discovery_to_token_resolver_bridge_071d_result.json",
            "latest_discovery_to_token_resolver_bridge_status_071d.json",
            "discovery_to_token_candidate_contract_071d.json",
            "discovery_to_token_operator_selection_required_071d.json",
        ),
    },
    SOURCE_FIRST_ORDER_TOKEN_070B: {
        "label": "070B first-order market/token resolver",
        "dir_names": ("first_order_market_token_resolver_070b",),
        "filenames": (
            "first_order_market_token_resolver_070b_result.json",
            "latest_first_order_market_token_status_070b.json",
            "first_order_market_token_contract_070b.json",
        ),
    },
    SOURCE_ACCOUNT_PROBE_070C: {
        "label": "070C live account read-only state probe",
        "dir_names": ("live_account_readonly_state_probe_070c",),
        "filenames": (
            "live_account_readonly_state_probe_070c_result.json",
            "latest_live_account_readonly_state_status_070c.json",
        ),
    },
    SOURCE_LIVE_READONLY_071B: {
        "label": "071B live read-only status aggregator",
        "dir_names": ("live_readonly_status_aggregator_071b",),
        "filenames": (
            "live_readonly_status_aggregator_071b_result.json",
            "latest_live_readonly_status_071b.json",
        ),
    },
    SOURCE_SIGNER_DIAGNOSTIC_069A: {
        "label": "069A guarded signer diagnostic smoke",
        "dir_names": ("guarded_signer_diagnostic_smoke_069a",),
        "filenames": (
            "guarded_signer_diagnostic_smoke_069a_result.json",
            "latest_guarded_signer_diagnostic_status_069a.json",
        ),
    },
    SOURCE_APPROVAL_CONTRACT_065D: {
        "label": "065D first live order approval contract",
        "dir_names": ("first_live_order_approval_contract_065d",),
        "filenames": (
            "first_live_order_approval_contract_065d_result.json",
            "latest_first_live_order_approval_contract_status_065d.json",
            "first_live_order_required_approval_text_065d.json",
        ),
    },
    SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A: {
        "label": "070A signed order payload dry-run",
        "dir_names": ("signed_order_payload_dry_run_070a",),
        "filenames": (
            "signed_order_payload_dry_run_070a_result.json",
            "latest_signed_order_payload_dry_run_status_070a.json",
            "signed_order_payload_contract_070a.json",
        ),
    },
}

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--wallet-connect",
    "--private-key",
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
    "--sign",
    "--signing",
    "--order",
    "--submit",
    "--cancel",
    "--approve-live",
    "--post",
    "--put",
    "--patch",
    "--delete",
    "--browser",
    "--loop",
    "--daemon",
    "--scheduler",
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
    "blocked",
}


def order_prep_packet_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "order_prep_packet_072a_result.json",
        "latest_status": root / "latest_order_prep_packet_status_072a.json",
        "sources": root / "order_prep_packet_sources_072a.json",
        "operator_review": root / "order_prep_packet_operator_review_072a.json",
        "blockers": root / "order_prep_packet_blockers_072a.json",
        "safety_snapshot": root / "order_prep_packet_safety_snapshot_072a.json",
        "operator_summary": root / "order_prep_packet_operator_summary_072a.md",
    }


def run_order_prep_packet(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("order prep packet requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = order_prep_packet_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    config = OrderPrepPacketConfig(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        artifact_root=normalize_path(root),
        generated_at=generated_at,
    ).to_dict()

    source_rows, source_payloads = load_order_prep_packet_sources(artifact_root=root, generated_at=generated_at)
    token_candidates = _extract_source_backed_token_candidates(source_payloads, source_rows, generated_at=generated_at)
    selected_token = _selected_token_id(source_payloads)
    bridge_selection_required = _bridge_selection_required(source_payloads)
    operator_selection_required = (len(token_candidates) > 1 and not selected_token) or bridge_selection_required
    readiness = _build_readiness_items(
        source_rows=source_rows,
        source_payloads=source_payloads,
        selected_token_id=selected_token,
        operator_selection_required=operator_selection_required,
        generated_at=generated_at,
    )
    blockers = _build_packet_blockers(
        source_rows=source_rows,
        readiness=readiness,
        selected_token_id=selected_token,
        operator_selection_required=operator_selection_required,
        token_candidate_count=len(token_candidates),
        generated_at=generated_at,
    )
    packet_blocked = bool(blockers)
    status = STATUS_BLOCKED if packet_blocked else STATUS_REVIEW_READY
    safety_snapshot = build_safety_snapshot(status=status, generated_at=generated_at)
    sources_artifact = _build_sources_artifact(
        source_rows=source_rows,
        artifact_root=root,
        generated_at=generated_at,
    )
    blockers_artifact = _build_blockers_artifact(status=status, blockers=blockers, generated_at=generated_at)
    operator_review = _build_operator_review(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        source_rows=source_rows,
        readiness=readiness,
        token_candidates=token_candidates,
        selected_token_id=selected_token,
        operator_selection_required=operator_selection_required,
        blockers=blockers,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        selected_token_id=selected_token,
        operator_selection_required=operator_selection_required,
        readiness=readiness,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    result = {
        "contract_version": ORDER_PREP_PACKET_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "packet_blocked": packet_blocked,
        "packet_ready_for_operator_review": packet_blocked is not True,
        "selected_token_id": selected_token,
        "selected_token_id_present": bool(selected_token),
        "operator_selection_required": operator_selection_required,
        "source_backed_token_candidate_count": len(token_candidates),
        "source_backed_token_candidates": token_candidates,
        "readiness": readiness,
        "readiness_item_count": len(readiness),
        "sources": sources_artifact,
        "operator_review": operator_review,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "config": config,
        "operator_summary": _operator_summary(status, blockers),
        "generated_at": generated_at,
    }
    result.update(order_prep_packet_safety_flags())
    result["validation"] = validate_order_prep_packet_result(result)

    write_json(paths["sources"], sources_artifact)
    write_json(paths["operator_review"], operator_review)
    write_json(paths["blockers"], blockers_artifact)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_summary"], render_order_prep_packet_markdown(result))
    return result


def load_order_prep_packet_sources(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    source_rows: dict[str, dict[str, Any]] = {}
    source_payloads: dict[str, dict[str, Any]] = {}
    for source_id in SOURCE_IDS:
        row, payload = _load_source(source_id, root=root, generated_at=generated_at)
        source_rows[source_id] = row
        source_payloads[source_id] = payload
    return source_rows, source_payloads


def render_order_prep_packet_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    return "\n".join(
        [
            "Order prep packet 072A completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
            f"Packet blocked: {str(value.get('packet_blocked') is True).lower()}",
            f"Selected token id present: {str(value.get('selected_token_id_present') is True).lower()}",
            f"Operator selection required: {str(value.get('operator_selection_required') is True).lower()}",
            f"Blocker count: {int(value.get('blocker_count', 0) or 0)}",
            "Allowed for live: false",
            "Order prep packet executable: false",
            "Order submission enabled: false",
            "Order cancellation enabled: false",
            "Signing enabled: false",
            "Wallet connection enabled: false",
            f"Artifact: {clean_text(latest.get('artifact_path'))}",
        ]
    )


def render_order_prep_packet_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    readiness = [dict(row) for row in value.get("readiness", []) if isinstance(row, Mapping)]
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    sources = dict(dict(value.get("sources", {})).get("sources", {}))
    lines = [
        "# PMBOT Order Prep Packet 072A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        "- Mode: `order prep packet / dry-run / no-submit`",
        "- allowed_for_live: `false`",
        "- order_prep_packet_executable: `false`",
        "- order_submission_enabled: `false`",
        "",
        "## Readiness",
        "",
        *bullet_lines(
            f"`{row.get('readiness_id')}` status=`{row.get('status')}` ready=`{str(row.get('ready') is True).lower()}`"
            for row in readiness
        ),
        "",
        "## Sources",
        "",
        *bullet_lines(
            f"`{source_id}` available=`{str(dict(row).get('available') is True).lower()}` status=`{dict(row).get('status')}`"
            for source_id, row in sources.items()
        ),
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
        "",
        "## Safety",
        "",
        "- local artifact reads only",
        "- no order submission",
        "- no order cancellation",
        "- no default real order payload signing",
        "- no wallet connection UI or wallet connection attempt",
        "- no authenticated trading write call",
        "- no full signed payload, private key, API secret, passphrase, account values, fills, PnL, order IDs, or transaction hashes emitted",
        "- no scheduler, daemon, background worker, or autonomous loop added",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "order prep packet is local-artifact-only/no-submit; unsupported live/auth/wallet/sign/order/write flag(s): "
            + ", ".join(requested)
        )


def _load_source(source_id: str, *, root: Path, generated_at: str) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = SOURCE_SPECS[source_id]
    paths = _candidate_paths(root, spec)
    candidate_strings = tuple(normalize_path(path) for path in paths)
    selected = _latest_existing_path(paths)
    if selected is None:
        row = OrderPrepPacketSource(
            source_id=source_id,
            label=clean_text(spec["label"]),
            available=False,
            selected_path="",
            status="missing",
            contract_version_seen="",
            generated_at=generated_at,
        ).to_dict()
        row["candidate_paths"] = candidate_strings
        return row, {}
    try:
        payload = load_json_object(selected, label=clean_text(spec["label"]))
        latest_payload = _latest_payload(payload)
        status = _safe_status(latest_payload.get("status") or payload.get("status")) or "available"
        row = OrderPrepPacketSource(
            source_id=source_id,
            label=clean_text(spec["label"]),
            available=True,
            selected_path=normalize_path(selected),
            status=status,
            contract_version_seen=clean_text(latest_payload.get("contract_version") or payload.get("contract_version")),
            generated_at=generated_at,
        ).to_dict()
        row["candidate_paths"] = candidate_strings
        return row, payload
    except Exception as exc:
        row = OrderPrepPacketSource(
            source_id=source_id,
            label=clean_text(spec["label"]),
            available=False,
            selected_path=normalize_path(selected),
            status="unreadable",
            contract_version_seen="",
            load_error=type(exc).__name__,
            generated_at=generated_at,
        ).to_dict()
        row["candidate_paths"] = candidate_strings
        return row, {}


def _candidate_paths(root: Path, spec: Mapping[str, Any]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for dirname in tuple(spec.get("dir_names", ())):
        for filename in tuple(spec.get("filenames", ())):
            paths.append(root / clean_text(dirname) / clean_text(filename))
    for filename in tuple(spec.get("filenames", ())):
        paths.append(root / clean_text(filename))
    return _dedupe_paths(paths)


def _dedupe_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(path)
    return tuple(result)


def _latest_existing_path(paths: Sequence[Path]) -> Path | None:
    existing = [path for path in paths if path.exists() and path.is_file()]
    if not existing:
        return None
    return max(existing, key=lambda path: path.stat().st_mtime)


def _latest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    latest = dict(payload or {}).get("latest_status")
    return dict(latest) if isinstance(latest, Mapping) else dict(payload or {})


def _extract_source_backed_token_candidates(
    source_payloads: Mapping[str, Mapping[str, Any]],
    source_rows: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bridge = dict(source_payloads.get(SOURCE_DISCOVERY_TO_TOKEN_071D, {}))
    for key in ("valid_source_backed_candidates", "source_backed_candidates"):
        rows.extend(
            _token_candidate_from_bridge(
                row,
                source_row=dict(source_rows.get(SOURCE_DISCOVERY_TO_TOKEN_071D, {})),
                generated_at=generated_at,
            )
            for row in _rows(bridge.get(key))
        )
    selection = bridge.get("operator_selection_required")
    if isinstance(selection, Mapping):
        rows.extend(
            _token_candidate_from_bridge(
                row,
                source_row=dict(source_rows.get(SOURCE_DISCOVERY_TO_TOKEN_071D, {})),
                generated_at=generated_at,
            )
            for row in _rows(selection.get("candidates"))
        )

    discovery = dict(source_payloads.get(SOURCE_PUBLIC_DISCOVERY_071A, {}))
    rows.extend(
        _token_candidate_from_discovery(
            row,
            source_row=dict(source_rows.get(SOURCE_PUBLIC_DISCOVERY_071A, {})),
            generated_at=generated_at,
        )
        for row in _rows(discovery.get("outcome_token_candidates"))
    )
    rows = [row for row in rows if row and row.get("source_backed") is True and _present_text(row.get("token_id"))]
    return _dedupe_by_key(rows, "token_id")


def _token_candidate_from_bridge(row: Mapping[str, Any], *, source_row: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    value = dict(row or {})
    token_id = clean_text(value.get("token_id"))
    return {
        "contract_version": "pmbot_order_prep_packet_token_candidate_072a.v1",
        "task_id": TASK_ID,
        "source_id": SOURCE_DISCOVERY_TO_TOKEN_071D,
        "source_path": clean_text(source_row.get("selected_path")),
        "token_candidate_id": clean_text(value.get("bridge_candidate_id") or value.get("source_token_candidate_id")),
        "market_candidate_id": clean_text(value.get("market_candidate_id")),
        "market_slug": _safe_status(value.get("market_slug")),
        "outcome_name": _safe_status(value.get("outcome_name")),
        "token_id": token_id,
        "token_id_present": bool(token_id),
        "source_backed": True,
        "token_id_generated": False,
        "fake_token_id_generated": False,
        "operator_selected": False,
        "generated_at": generated_at,
        **order_prep_packet_safety_flags(),
    }


def _token_candidate_from_discovery(row: Mapping[str, Any], *, source_row: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    value = dict(row or {})
    if value.get("source_backed") is not True and value.get("token_id_is_source_backed") is not True:
        return {}
    if value.get("token_id_is_generated") is True:
        return {}
    token_id = clean_text(value.get("token_id"))
    return {
        "contract_version": "pmbot_order_prep_packet_token_candidate_072a.v1",
        "task_id": TASK_ID,
        "source_id": SOURCE_PUBLIC_DISCOVERY_071A,
        "source_path": clean_text(source_row.get("selected_path")),
        "token_candidate_id": clean_text(value.get("token_candidate_id")),
        "market_candidate_id": clean_text(value.get("market_candidate_id")),
        "market_slug": _safe_status(value.get("market_slug")),
        "outcome_name": _safe_status(value.get("outcome_name")),
        "token_id": token_id,
        "token_id_present": bool(token_id),
        "source_backed": True,
        "token_id_generated": False,
        "fake_token_id_generated": False,
        "operator_selected": False,
        "generated_at": generated_at,
        **order_prep_packet_safety_flags(),
    }


def _selected_token_id(source_payloads: Mapping[str, Mapping[str, Any]]) -> str:
    for source_id in (SOURCE_DISCOVERY_TO_TOKEN_071D, SOURCE_FIRST_ORDER_TOKEN_070B):
        payload = dict(source_payloads.get(source_id, {}))
        token = _nested_token_id(payload)
        if _present_text(token):
            return clean_text(token)
    return ""


def _nested_token_id(payload: Mapping[str, Any]) -> str:
    value = dict(payload or {})
    for key in ("selected_token_id", "token_id", "outcome_token_id", "target_token_id"):
        text = clean_text(value.get(key))
        if _present_text(text):
            return text
    for key in ("target_contract", "latest_status"):
        nested = value.get(key)
        if isinstance(nested, Mapping):
            text = _nested_token_id(nested)
            if _present_text(text):
                return text
    return ""


def _bridge_selection_required(source_payloads: Mapping[str, Mapping[str, Any]]) -> bool:
    bridge = dict(source_payloads.get(SOURCE_DISCOVERY_TO_TOKEN_071D, {}))
    latest = bridge.get("latest_status")
    selection = bridge.get("operator_selection_required")
    target = bridge.get("target_contract")
    return any(
        dict(row).get("operator_selection_required") is True or dict(row).get("selection_required") is True
        for row in (bridge, latest, selection, target)
        if isinstance(row, Mapping)
    )


def _build_readiness_items(
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    selected_token_id: str,
    operator_selection_required: bool,
    generated_at: str,
) -> list[dict[str, Any]]:
    return [
        _readiness(
            readiness_id="local_source_artifacts",
            ready=all(dict(source_rows.get(source_id, {})).get("available") is True for source_id in SOURCE_IDS),
            source_id="all_sources",
            source_row={},
            evidence_key="available",
            blocker_id="missing_required_source_artifact",
            reason="One or more required local source artifacts are missing or unreadable.",
            generated_at=generated_at,
        ),
        _readiness(
            readiness_id="token_selection",
            ready=bool(selected_token_id) and operator_selection_required is not True,
            source_id=SOURCE_DISCOVERY_TO_TOKEN_071D,
            source_row=dict(source_rows.get(SOURCE_DISCOVERY_TO_TOKEN_071D, {})),
            evidence_key="target_contract.token_id",
            blocker_id="missing_selected_token_id",
            reason="No selected source-backed token_id is present; the packet stays blocked.",
            generated_at=generated_at,
            status_override="operator_selection_required" if operator_selection_required else "",
        ),
        _readiness(
            readiness_id="account_probe",
            ready=_account_probe_ready(source_payloads.get(SOURCE_ACCOUNT_PROBE_070C, {})),
            source_id=SOURCE_ACCOUNT_PROBE_070C,
            source_row=dict(source_rows.get(SOURCE_ACCOUNT_PROBE_070C, {})),
            evidence_key="account_state_probe_performed",
            blocker_id="account_probe_missing_or_failed",
            reason="The 070C live account read-only probe is missing, blocked, or failed.",
            generated_at=generated_at,
        ),
        _readiness(
            readiness_id="signer_diagnostic",
            ready=_signer_diagnostic_ready(source_payloads.get(SOURCE_SIGNER_DIAGNOSTIC_069A, {})),
            source_id=SOURCE_SIGNER_DIAGNOSTIC_069A,
            source_row=dict(source_rows.get(SOURCE_SIGNER_DIAGNOSTIC_069A, {})),
            evidence_key="diagnostic_status",
            blocker_id="signer_diagnostic_missing_or_not_ok",
            reason="The 069A signer diagnostic is missing or did not reach diagnostic_ok.",
            generated_at=generated_at,
        ),
        _readiness(
            readiness_id="operator_approval",
            ready=_operator_approval_ready(source_payloads.get(SOURCE_APPROVAL_CONTRACT_065D, {})),
            source_id=SOURCE_APPROVAL_CONTRACT_065D,
            source_row=dict(source_rows.get(SOURCE_APPROVAL_CONTRACT_065D, {})),
            evidence_key="operator_approval_recorded",
            blocker_id="operator_approval_missing",
            reason="No operator approval record is present; the approval contract alone is not approval.",
            generated_at=generated_at,
        ),
        _readiness(
            readiness_id="signed_payload_dry_run",
            ready=_signed_payload_dry_run_ready(source_payloads.get(SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A, {})),
            source_id=SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A,
            source_row=dict(source_rows.get(SOURCE_SIGNED_PAYLOAD_DRY_RUN_070A, {})),
            evidence_key="order_payload_contract_built",
            blocker_id="signed_payload_dry_run_missing",
            reason="The 070A signed payload dry-run artifact is missing or did not build a non-executable contract.",
            generated_at=generated_at,
        ),
    ]


def _readiness(
    *,
    readiness_id: str,
    ready: bool,
    source_id: str,
    source_row: Mapping[str, Any],
    evidence_key: str,
    blocker_id: str,
    reason: str,
    generated_at: str,
    status_override: str = "",
) -> dict[str, Any]:
    source_available = dict(source_row).get("available") is True if source_row else ready
    status = clean_text(status_override) or ("ready" if ready else "blocked")
    return OrderPrepPacketReadinessItem(
        readiness_id=readiness_id,
        status=status,
        ready=ready is True,
        source_id=source_id,
        source_available=source_available,
        source_path=clean_text(source_row.get("selected_path")) if source_row else "",
        evidence_key=evidence_key,
        blocker_id=blocker_id,
        reason=reason,
        generated_at=generated_at,
    ).to_dict()


def _build_packet_blockers(
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    readiness: Sequence[Mapping[str, Any]],
    selected_token_id: str,
    operator_selection_required: bool,
    token_candidate_count: int,
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        row = dict(source_rows.get(source_id, {}))
        if row.get("available") is not True:
            blockers.append(
                build_blocker(
                    f"missing_{source_id}",
                    "source_artifact",
                    f"Required local source artifact {source_id} is missing or unreadable.",
                    source_id=source_id,
                    generated_at=generated_at,
                )
            )
    if operator_selection_required:
        blockers.append(
            build_blocker(
                "operator_selection_required",
                "token_selection",
                "Multiple source-backed token candidates are present; operator selection is required before a token_id can be selected.",
                source_id=SOURCE_PUBLIC_DISCOVERY_071A,
                generated_at=generated_at,
            )
        )
    if not clean_text(selected_token_id):
        blockers.append(
            build_blocker(
                "missing_selected_token_id",
                "token_selection",
                "No selected token_id is present; no token_id is invented or auto-selected.",
                source_id=SOURCE_DISCOVERY_TO_TOKEN_071D,
                generated_at=generated_at,
            )
        )
    if token_candidate_count <= 0:
        blockers.append(
            build_blocker(
                "missing_source_backed_token_candidates",
                "token_discovery",
                "No source-backed token candidate was found in the local discovery or bridge artifacts.",
                source_id=SOURCE_PUBLIC_DISCOVERY_071A,
                generated_at=generated_at,
            )
        )
    for row in readiness:
        item = dict(row)
        if item.get("ready") is True:
            continue
        blocker_id = clean_text(item.get("blocker_id"))
        if blocker_id in {clean_text(blocker.get("blocker_id")) for blocker in blockers}:
            continue
        blockers.append(
            build_blocker(
                blocker_id,
                clean_text(item.get("readiness_id")),
                clean_text(item.get("reason")),
                source_id=clean_text(item.get("source_id")),
                generated_at=generated_at,
            )
        )
    return blockers


def _build_sources_artifact(
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    artifact_root: Path,
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": ORDER_PREP_PACKET_SOURCES_CONTRACT,
        "task_id": TASK_ID,
        "status": "sources_loaded_with_missing_preserved",
        "artifact_root": normalize_path(artifact_root),
        "sources": {source_id: dict(source_rows.get(source_id, {})) for source_id in SOURCE_IDS},
        "source_count": len(SOURCE_IDS),
        "available_source_count": sum(1 for row in source_rows.values() if dict(row).get("available") is True),
        "missing_source_count": sum(1 for row in source_rows.values() if dict(row).get("available") is not True),
        "generated_at": generated_at,
    }
    value.update(order_prep_packet_safety_flags())
    return value


def _build_blockers_artifact(*, status: str, blockers: Sequence[Mapping[str, Any]], generated_at: str) -> dict[str, Any]:
    value = {
        "contract_version": ORDER_PREP_PACKET_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "packet_blocked": bool(blockers),
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "generated_at": generated_at,
    }
    value.update(order_prep_packet_safety_flags())
    return value


def _build_operator_review(
    *,
    status: str,
    market: str,
    strategy: str,
    source_rows: Mapping[str, Mapping[str, Any]],
    readiness: Sequence[Mapping[str, Any]],
    token_candidates: Sequence[Mapping[str, Any]],
    selected_token_id: str,
    operator_selection_required: bool,
    blockers: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": ORDER_PREP_PACKET_OPERATOR_REVIEW_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        "packet_blocked": bool(blockers),
        "selected_token_id": clean_text(selected_token_id),
        "selected_token_id_present": bool(clean_text(selected_token_id)),
        "operator_selection_required": operator_selection_required is True,
        "source_backed_token_candidate_count": len(token_candidates),
        "source_backed_token_candidates": [dict(row) for row in token_candidates],
        "readiness": [dict(row) for row in readiness],
        "source_artifact_status": {
            source_id: {
                "available": dict(source_rows.get(source_id, {})).get("available") is True,
                "status": clean_text(dict(source_rows.get(source_id, {})).get("status")),
                "path": clean_text(dict(source_rows.get(source_id, {})).get("selected_path")),
            }
            for source_id in SOURCE_IDS
        },
        "blocker_count": len(blockers),
        "blockers": [dict(row) for row in blockers],
        "next_operator_action": _next_operator_action(
            selected_token_id=selected_token_id,
            operator_selection_required=operator_selection_required,
            blockers=blockers,
        ),
        "generated_at": generated_at,
    }
    value.update(order_prep_packet_safety_flags())
    return value


def _build_latest_status(
    *,
    status: str,
    market: str,
    strategy: str,
    selected_token_id: str,
    operator_selection_required: bool,
    readiness: Sequence[Mapping[str, Any]],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    readiness_by_id = {clean_text(row.get("readiness_id")): dict(row) for row in readiness}
    value = {
        "contract_version": ORDER_PREP_PACKET_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        "packet_blocked": bool(blockers),
        "selected_token_id_present": bool(clean_text(selected_token_id)),
        "operator_selection_required": operator_selection_required is True,
        "account_probe_status": clean_text(readiness_by_id.get("account_probe", {}).get("status")) or "unknown",
        "signer_diagnostic_status": clean_text(readiness_by_id.get("signer_diagnostic", {}).get("status")) or "unknown",
        "operator_approval_status": clean_text(readiness_by_id.get("operator_approval", {}).get("status")) or "unknown",
        "signed_payload_dry_run_status": clean_text(readiness_by_id.get("signed_payload_dry_run", {}).get("status")) or "unknown",
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "sources_path": clean_text(artifact_paths.get("sources")),
        "operator_review_path": clean_text(artifact_paths.get("operator_review")),
        "blockers_path": clean_text(artifact_paths.get("blockers")),
        "safety_snapshot_path": clean_text(artifact_paths.get("safety_snapshot")),
        "operator_summary_path": clean_text(artifact_paths.get("operator_summary")),
        "next_operator_action": _next_operator_action(
            selected_token_id=selected_token_id,
            operator_selection_required=operator_selection_required,
            blockers=blockers,
        ),
        "generated_at": generated_at,
    }
    value.update(order_prep_packet_safety_flags())
    return value


def _operator_summary(status: str, blockers: Sequence[Mapping[str, Any]]) -> str:
    if clean_text(status) == STATUS_REVIEW_READY:
        return "Order prep packet is ready for operator review only; live execution remains disabled."
    return f"Order prep packet is blocked with {len(blockers)} unresolved blocker(s); no live execution, signing, submission, or cancellation is enabled."


def _next_operator_action(*, selected_token_id: str, operator_selection_required: bool, blockers: Sequence[Mapping[str, Any]]) -> str:
    if operator_selection_required:
        return "select exactly one source-backed token candidate in a separate review step; do not submit, cancel, sign, or enable live trading"
    if not clean_text(selected_token_id):
        return "produce or provide a selected source-backed token_id via 071D or 070B before review can continue"
    if blockers:
        return "resolve the listed readiness blockers before any separate future approval or execution task"
    return "review this packet only; a separate explicitly approved future task would still be required for any live-capable action"


def _account_probe_ready(payload: Mapping[str, Any]) -> bool:
    value = dict(payload or {})
    if not value:
        return False
    status = clean_text(value.get("status")).lower()
    latest = value.get("latest_status")
    if isinstance(latest, Mapping):
        status = status or clean_text(latest.get("status")).lower()
    if any(term in status for term in ("failed", "failure", "error", "invalid", "blocked")):
        return False
    return any(
        _nested_bool(value, key)
        for key in (
            "account_state_probe_performed",
            "account_readonly_ok",
            "read_only_ok",
            "readonly_ok",
            "readonly_probe_ok",
            "read_only_probe_ok",
        )
    )


def _signer_diagnostic_ready(payload: Mapping[str, Any]) -> bool:
    value = dict(payload or {})
    if not value:
        return False
    status = clean_text(value.get("diagnostic_status") or value.get("status")).lower()
    latest = value.get("latest_status")
    if isinstance(latest, Mapping) and not status:
        status = clean_text(latest.get("diagnostic_status") or latest.get("status")).lower()
    return status == "diagnostic_ok"


def _operator_approval_ready(payload: Mapping[str, Any]) -> bool:
    value = dict(payload or {})
    if not value:
        return False
    return _nested_bool(value, "operator_approval_recorded")


def _signed_payload_dry_run_ready(payload: Mapping[str, Any]) -> bool:
    value = dict(payload or {})
    if not value:
        return False
    if _nested_bool(value, "order_payload_contract_built"):
        return True
    if _nested_bool(value, "contract_only") or _nested_bool(value, "deterministic_contract"):
        return True
    status = clean_text(value.get("status")).lower()
    return "contract" in status and not any(term in status for term in ("failed", "failure", "error", "invalid"))


def _nested_bool(value: Mapping[str, Any], key: str) -> bool:
    if value.get(key) is True:
        return True
    for nested_key in ("latest_status", "account_status", "payload_contract"):
        nested = value.get(nested_key)
        if isinstance(nested, Mapping) and _nested_bool(nested, key):
            return True
    return False


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _dedupe_by_key(rows: Sequence[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        value = dict(row)
        row_key = clean_text(value.get(key)) or clean_text(value.get("token_id"))
        if not row_key or row_key in seen:
            continue
        seen.add(row_key)
        result.append(value)
    return result


def _present_text(value: Any) -> bool:
    text = clean_text(value)
    return bool(text) and text.lower() not in _ABSENT_TEXT


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
        return "redacted_sensitive_status"
    if text.startswith("0x") and len(text) > 12 and "..." not in text:
        return "present_redacted"
    if len(text) > 180:
        return "available_redacted"
    return text
