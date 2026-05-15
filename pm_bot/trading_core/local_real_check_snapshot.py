from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.local_real_check_snapshot_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    MISSING_STATUS,
    NORMALIZED_STATUS_FIELDS,
    SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C,
    SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D,
    SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,
    SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A,
    SOURCE_LABELS,
    SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C,
    SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C,
    SOURCE_ORDER_PREP_PACKET_072A,
    SOURCE_PUBLIC_MARKET_TOKEN_DISCOVERY_071A,
    SOURCE_SEQUENCE,
    STATUS_BLOCKED,
    TASK_ID,
    UNKNOWN_STATUS,
    UNREADABLE_STATUS,
    LocalRealCheckSnapshotLatestStatus,
    LocalRealCheckSnapshotNextAction,
    LocalRealCheckSnapshotNormalizedStatus,
    LocalRealCheckSnapshotResult,
    LocalRealCheckSnapshotSource,
    build_next_actions_artifact,
    build_safety_snapshot,
    build_sources_artifact,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "local_real_check_snapshot_073a"

SOURCE_SPECS: dict[str, dict[str, Any]] = {
    SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C: {
        "dir_names": ("local_real_check_bundle_072c",),
        "latest_filenames": ("latest_local_real_check_bundle_status_072c.json",),
        "result_filenames": ("local_real_check_bundle_072c_result.json",),
    },
    SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C: {
        "dir_names": ("clob_l2_auth_readonly_probe_067c",),
        "latest_filenames": ("latest_clob_l2_auth_readonly_probe_status_067c.json",),
        "result_filenames": ("clob_l2_auth_readonly_probe_067c_result.json",),
    },
    SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C: {
        "dir_names": ("live_account_readonly_state_probe_070c",),
        "latest_filenames": ("latest_live_account_readonly_state_status_070c.json",),
        "result_filenames": ("live_account_readonly_state_probe_070c_result.json",),
    },
    SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A: {
        "dir_names": ("guarded_signer_diagnostic_smoke_069a",),
        "latest_filenames": ("latest_guarded_signer_diagnostic_status_069a.json",),
        "result_filenames": ("guarded_signer_diagnostic_smoke_069a_result.json",),
    },
    SOURCE_PUBLIC_MARKET_TOKEN_DISCOVERY_071A: {
        "dir_names": ("public_market_token_discovery_071a",),
        "latest_filenames": ("latest_public_market_token_discovery_status_071a.json",),
        "result_filenames": ("public_market_token_discovery_071a_result.json",),
    },
    SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D: {
        "dir_names": ("discovery_to_token_resolver_bridge_071d",),
        "latest_filenames": ("latest_discovery_to_token_resolver_bridge_status_071d.json",),
        "result_filenames": ("discovery_to_token_resolver_bridge_071d_result.json",),
    },
    SOURCE_ORDER_PREP_PACKET_072A: {
        "dir_names": ("order_prep_packet_072a",),
        "latest_filenames": ("latest_order_prep_packet_status_072a.json",),
        "result_filenames": ("order_prep_packet_072a_result.json",),
    },
    SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D: {
        "dir_names": ("first_live_order_final_blocker_reducer_072d",),
        "latest_filenames": ("latest_first_live_order_final_blockers_072d.json",),
        "result_filenames": ("first_live_order_final_blocker_reducer_072d_result.json",),
    },
}

STATUS_FIELD_SOURCES: dict[str, tuple[str, tuple[str, ...]]] = {
    "l2_auth_status": (SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C, ("l2_auth_status", "status")),
    "account_readonly_status": (
        SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C,
        ("account_readonly_status", "account_status", "status"),
    ),
    "signer_diagnostic_status": (
        SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A,
        ("diagnostic_status", "signer_diagnostic_status", "status"),
    ),
    "public_discovery_status": (SOURCE_PUBLIC_MARKET_TOKEN_DISCOVERY_071A, ("public_discovery_status", "status")),
    "token_bridge_status": (SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D, ("token_bridge_status", "status")),
    "order_prep_packet_status": (SOURCE_ORDER_PREP_PACKET_072A, ("order_prep_packet_status", "status")),
    "final_blocker_status": (
        SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,
        ("final_blocker_status", "status"),
    ),
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
    "--order-payload",
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


def local_real_check_snapshot_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "local_real_check_snapshot_073a_result.json",
        "latest_status": root / "latest_local_real_check_snapshot_status_073a.json",
        "sources": root / "local_real_check_snapshot_sources_073a.json",
        "normalized_status": root / "local_real_check_snapshot_normalized_status_073a.json",
        "next_actions": root / "local_real_check_snapshot_next_actions_073a.json",
        "safety_snapshot": root / "local_real_check_snapshot_safety_snapshot_073a.json",
        "operator_summary": root / "local_real_check_snapshot_operator_summary_073a.md",
    }


def run_local_real_check_snapshot(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    include_latest_artifacts: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("local real-check snapshot requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = local_real_check_snapshot_artifact_paths(artifact_dir)
    path_refs = {key: _safe_path(path) for key, path in paths.items() if key != "root"}

    source_rows, source_payloads = load_local_real_check_snapshot_sources(
        artifact_root=root,
        include_latest_artifacts=include_latest_artifacts,
        generated_at=generated_at,
    )
    sources_artifact = build_sources_artifact(
        source_rows,
        artifact_root=_safe_path(root),
        include_latest_artifacts=include_latest_artifacts,
        generated_at=generated_at,
    )
    normalized_status = _build_normalized_status(
        market=market_symbol,
        strategy=strategy_name,
        source_rows=source_rows,
        source_payloads=source_payloads,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    next_actions = _build_next_actions(
        source_rows=source_rows,
        normalized_status=normalized_status,
        generated_at=generated_at,
    )
    safety_snapshot = build_safety_snapshot(
        market=market_symbol,
        strategy=strategy_name,
        include_latest_artifacts=include_latest_artifacts,
        generated_at=generated_at,
    )
    latest_status = LocalRealCheckSnapshotLatestStatus(
        market=market_symbol,
        strategy=strategy_name,
        normalized_status=normalized_status,
        sources=sources_artifact,
        next_actions=next_actions,
        artifact_paths=path_refs,
        include_latest_artifacts=include_latest_artifacts,
        generated_at=generated_at,
    ).to_dict()
    result = LocalRealCheckSnapshotResult(
        market=market_symbol,
        strategy=strategy_name,
        sources=sources_artifact,
        normalized_status=normalized_status,
        next_actions=next_actions,
        safety_snapshot=safety_snapshot,
        latest_status=latest_status,
        artifact_paths=path_refs,
        include_latest_artifacts=include_latest_artifacts,
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["sources"], sources_artifact)
    write_json(paths["normalized_status"], normalized_status)
    write_json(paths["next_actions"], next_actions)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_summary"], render_local_real_check_snapshot_markdown(result))
    return result


def load_local_real_check_snapshot_sources(
    *,
    artifact_root: str | Path | None = None,
    include_latest_artifacts: bool = True,
    generated_at: str = GENERATED_AT,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    source_rows: dict[str, dict[str, Any]] = {}
    source_payloads: dict[str, dict[str, Any]] = {}
    for source_id in SOURCE_SEQUENCE:
        row, payload = _load_source(
            source_id,
            root=root,
            include_latest_artifacts=include_latest_artifacts,
            generated_at=generated_at,
        )
        source_rows[source_id] = row
        source_payloads[source_id] = payload
    return source_rows, source_payloads


def render_local_real_check_snapshot_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Local real-check snapshot 073A completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
            f"Sources present: {int(value.get('source_present_count', 0) or 0)}/{int(value.get('source_count', 0) or 0)}",
            f"Sources missing: {int(value.get('source_missing_count', 0) or 0)}",
            f"Sources unreadable: {int(value.get('source_unreadable_count', 0) or 0)}",
            f"Include latest artifacts: {str(value.get('include_latest_artifacts') is True).lower()}",
            "Allowed for live: false",
            "Snapshot executable for live: false",
            "Network calls: false",
            "Environment secret reads: false",
            "Subchecks run by default: false",
            f"L2 auth: {clean_text(value.get('l2_auth_status')) or UNKNOWN_STATUS}",
            f"Account read-only: {clean_text(value.get('account_readonly_status')) or UNKNOWN_STATUS}",
            f"Signer diagnostic: {clean_text(value.get('signer_diagnostic_status')) or UNKNOWN_STATUS}",
            f"Public discovery: {clean_text(value.get('public_discovery_status')) or UNKNOWN_STATUS}",
            f"Token bridge: {clean_text(value.get('token_bridge_status')) or UNKNOWN_STATUS}",
            f"Order prep packet: {clean_text(value.get('order_prep_packet_status')) or UNKNOWN_STATUS}",
            f"Final blocker: {clean_text(value.get('final_blocker_status')) or UNKNOWN_STATUS}",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_local_real_check_snapshot_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    sources_index = dict(value.get("sources", {}))
    sources = [dict(row) for row in dict(sources_index.get("sources", {})).values() if isinstance(row, Mapping)]
    next_actions = [
        dict(row)
        for row in dict(value.get("next_actions", {})).get("next_actions", [])
        if isinstance(row, Mapping)
    ]
    lines = [
        "# PMBOT Local Real-Check Snapshot 073A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        f"- execution_mode: `{EXECUTION_MODE}`",
        "- allowed_for_live: `false`",
        "- snapshot_executable_for_live: `false`",
        "- local artifact reads only",
        "- no network calls, no environment secret reads, no subchecks run by default",
        "",
        "## Normalized Status",
        "",
        *bullet_lines(f"`{field}` = `{value.get(field, UNKNOWN_STATUS)}`" for field in NORMALIZED_STATUS_FIELDS),
        "",
        "## Sources",
        "",
        *bullet_lines(
            f"`{row.get('source_id')}` exists={str(row.get('exists') is True).lower()} "
            f"parsed={str(row.get('parsed') is True).lower()} status=`{row.get('status')}` "
            f"path=`{row.get('selected_path') or 'missing'}`"
            for row in sources
        ),
        "",
        "## Next Actions",
        "",
        *bullet_lines(f"`{row.get('action_id')}` - {row.get('action')}" for row in next_actions),
        "",
        "## Safety",
        "",
        "- this snapshot is not an executable live packet",
        "- missing evidence remains `missing`; unknown evidence remains `unknown`",
        "- raw source payloads are not embedded",
        "- address-like values are redacted to short form when status/path text is reported",
        "- no order submission, cancellation, order payload signing, wallet connection, or trading write endpoint is available",
        f"- latest status artifact: `{latest.get('latest_status_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "local real-check snapshot is local-artifact-only/no-live; unsupported live/auth/wallet/sign/order/write "
            "flag(s): "
            + ", ".join(requested)
        )


def _load_source(
    source_id: str,
    *,
    root: Path,
    include_latest_artifacts: bool,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidates = _candidate_paths(source_id, root=root, include_latest_artifacts=include_latest_artifacts)
    selected = _first_existing(candidates)
    if selected is None:
        row = LocalRealCheckSnapshotSource(
            source_id=source_id,
            label=SOURCE_LABELS.get(source_id, source_id),
            required=True,
            exists=False,
            parsed=False,
            status=MISSING_STATUS,
            selected_path="",
            candidate_paths=tuple(_safe_path(path) for path in candidates),
            generated_at=generated_at,
        ).to_dict()
        return row, {}
    try:
        payload = load_json_object(selected, label=SOURCE_LABELS.get(source_id, source_id))
    except Exception as exc:
        row = LocalRealCheckSnapshotSource(
            source_id=source_id,
            label=SOURCE_LABELS.get(source_id, source_id),
            required=True,
            exists=True,
            parsed=False,
            status=UNREADABLE_STATUS,
            selected_path=_safe_path(selected),
            candidate_paths=tuple(_safe_path(path) for path in candidates),
            file_modified_at=_file_modified_at(selected),
            load_error=_safe_status(type(exc).__name__) or UNREADABLE_STATUS,
            generated_at=generated_at,
        ).to_dict()
        return row, {}
    latest = _latest_payload(payload)
    status = _safe_status(latest.get("status") or payload.get("status")) or UNKNOWN_STATUS
    row = LocalRealCheckSnapshotSource(
        source_id=source_id,
        label=SOURCE_LABELS.get(source_id, source_id),
        required=True,
        exists=True,
        parsed=True,
        status=status,
        selected_path=_safe_path(selected),
        candidate_paths=tuple(_safe_path(path) for path in candidates),
        file_modified_at=_file_modified_at(selected),
        contract_version_seen=_safe_status(latest.get("contract_version") or payload.get("contract_version")),
        generated_at=generated_at,
    ).to_dict()
    return row, payload


def _build_normalized_status(
    *,
    market: str,
    strategy: str,
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    fields: dict[str, str] = {}
    status_sources: dict[str, dict[str, Any]] = {}
    for field_name, (source_id, preferred_keys) in STATUS_FIELD_SOURCES.items():
        status, evidence_key = _status_from_source(
            source_id,
            preferred_keys=preferred_keys,
            source_rows=source_rows,
            source_payloads=source_payloads,
        )
        fields[field_name] = status
        source_row = dict(source_rows.get(source_id, {}))
        status_sources[field_name] = {
            "source_id": source_id,
            "source_label": SOURCE_LABELS.get(source_id, source_id),
            "source_exists": source_row.get("exists") is True,
            "source_parsed": source_row.get("parsed") is True,
            "source_path": clean_text(source_row.get("selected_path")),
            "evidence_key": evidence_key,
            "status": status,
        }
    source_statuses = {
        source_id: clean_text(dict(source_rows.get(source_id, {})).get("status")) or UNKNOWN_STATUS
        for source_id in SOURCE_SEQUENCE
    }
    return LocalRealCheckSnapshotNormalizedStatus(
        market=market,
        strategy=strategy,
        status_fields=fields,
        status_sources=status_sources,
        source_statuses=source_statuses,
        artifact_paths=artifact_paths,
        generated_at=generated_at,
    ).to_dict()


def _build_next_actions(
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    normalized_status: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    for source_id in SOURCE_SEQUENCE:
        row = dict(source_rows.get(source_id, {}))
        if row.get("exists") is not True:
            actions.append(
                LocalRealCheckSnapshotNextAction(
                    action_id=f"provide_missing_{source_id}",
                    source_id=source_id,
                    action=(
                        f"provide the commit-safe {SOURCE_LABELS.get(source_id, source_id)} JSON artifact locally, "
                        "then rerun the 073A snapshot"
                    ),
                    reason="the expected local artifact is missing; no success was inferred",
                    status=MISSING_STATUS,
                    generated_at=generated_at,
                ).to_dict()
            )
        elif row.get("parsed") is not True:
            actions.append(
                LocalRealCheckSnapshotNextAction(
                    action_id=f"repair_unreadable_{source_id}",
                    source_id=source_id,
                    action=f"repair or replace the unreadable {SOURCE_LABELS.get(source_id, source_id)} JSON artifact",
                    reason="the artifact exists but could not be parsed as a JSON object",
                    status=UNREADABLE_STATUS,
                    generated_at=generated_at,
                ).to_dict()
            )
    for field_name in NORMALIZED_STATUS_FIELDS:
        status = clean_text(normalized_status.get(field_name)) or UNKNOWN_STATUS
        if status not in {UNKNOWN_STATUS, MISSING_STATUS, UNREADABLE_STATUS}:
            continue
        source_id = STATUS_FIELD_SOURCES[field_name][0]
        actions.append(
            LocalRealCheckSnapshotNextAction(
                action_id=f"resolve_{field_name}",
                source_id=source_id,
                action=f"collect source-backed evidence for {field_name} without emitting secrets or executable data",
                reason=f"{field_name} is {status}; unknown or missing evidence cannot be promoted",
                status=status,
                generated_at=generated_at,
            ).to_dict()
        )
    actions.append(
        LocalRealCheckSnapshotNextAction(
            action_id="keep_live_execution_blocked",
            source_id="snapshot",
            action="use this snapshot as read-only ingestion input only; keep any live-capable action in a separate approved task",
            reason="073A always sets allowed_for_live=false and snapshot_executable_for_live=false",
            status=STATUS_BLOCKED,
            generated_at=generated_at,
        ).to_dict()
    )
    return build_next_actions_artifact(_dedupe_actions(actions), generated_at=generated_at)


def _candidate_paths(source_id: str, *, root: Path, include_latest_artifacts: bool) -> tuple[Path, ...]:
    spec = SOURCE_SPECS[source_id]
    filenames = []
    if include_latest_artifacts:
        filenames.extend(clean_text(name) for name in spec.get("latest_filenames", ()))
    filenames.extend(clean_text(name) for name in spec.get("result_filenames", ()))
    paths: list[Path] = []
    for dirname in tuple(spec.get("dir_names", ())):
        for filename in filenames:
            paths.append(root / clean_text(dirname) / filename)
    for filename in filenames:
        paths.append(root / filename)
    return _dedupe_paths(paths)


def _first_existing(paths: Sequence[Path]) -> Path | None:
    for path in paths:
        if path.exists() and path.is_file():
            return path
    return None


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


def _latest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(payload or {})
    latest = value.get("latest_status")
    if isinstance(latest, Mapping):
        return dict(latest)
    return value


def _status_from_source(
    source_id: str,
    *,
    preferred_keys: Sequence[str],
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
) -> tuple[str, str]:
    source_row = dict(source_rows.get(source_id, {}))
    if source_row.get("exists") is not True:
        return MISSING_STATUS, "artifact_missing"
    if source_row.get("parsed") is not True:
        return UNREADABLE_STATUS, "artifact_unreadable"
    payload = dict(source_payloads.get(source_id, {}))
    latest = _latest_payload(payload)
    for key in preferred_keys:
        for candidate in (latest, payload):
            if key in candidate:
                status = _safe_status(candidate.get(key))
                if status:
                    return status, key
    return UNKNOWN_STATUS, "status"


def _safe_status(value: Any) -> str:
    text = _redact_text(clean_text(value))
    if not text:
        return ""
    lowered = text.lower()
    if any(
        term in lowered
        for term in (
            "private key",
            "private_key",
            "api secret",
            "api_secret",
            "passphrase",
            "mnemonic",
            "seed phrase",
            "seed_phrase",
            "auth token",
            "auth_token",
            "signed payload",
            "signed_payload",
        )
    ):
        return "redacted_sensitive_status"
    if re.fullmatch(r"\d{24,}", text):
        return "present_redacted"
    if len(text) > 180:
        return "available_redacted"
    return text


def _safe_path(path: str | Path) -> str:
    return _redact_text(normalize_path(path))


def _redact_text(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    redacted = re.sub(r"0x[0-9a-fA-F]{64}", "[REDACTED_HEX_64]", text)
    redacted = re.sub(r"0x([0-9a-fA-F]{4})[0-9a-fA-F]{32}([0-9a-fA-F]{4})", r"0x\1...\2", redacted)
    redacted = re.sub(
        r"(?i)\b(private[_-]?key|api[_-]?secret|passphrase|mnemonic|seed[_-]?phrase|auth[_-]?token)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        redacted,
    )
    return redacted[:500]


def _file_modified_at(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()
    except OSError:
        return ""


def _dedupe_actions(actions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in actions:
        value = dict(row)
        action_id = clean_text(value.get("action_id"))
        if not action_id or action_id in seen:
            continue
        seen.add(action_id)
        result.append(value)
    return result


__all__ = [
    "DEFAULT_ARTIFACT_DIR",
    "DEFAULT_ARTIFACT_ROOT",
    "fail_closed_for_forbidden_flags",
    "local_real_check_snapshot_artifact_paths",
    "load_local_real_check_snapshot_sources",
    "render_local_real_check_snapshot_cli_summary",
    "render_local_real_check_snapshot_markdown",
    "run_local_real_check_snapshot",
    "TASK_ID",
]
