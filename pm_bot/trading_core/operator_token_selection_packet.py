from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.operator_token_selection_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    MODE,
    OPERATOR_TOKEN_SELECTION_CANDIDATES_CONTRACT,
    OPERATOR_TOKEN_SELECTION_LATEST_STATUS_CONTRACT,
    OPERATOR_TOKEN_SELECTION_PACKET_CONTRACT,
    OPERATOR_TOKEN_SELECTION_RESULT_CONTRACT,
    SOURCE_DISCOVERY_TO_TOKEN_071D,
    SOURCE_PUBLIC_DISCOVERY_071A,
    STATUS_INVALID_SELECTION,
    STATUS_NO_CANDIDATES,
    STATUS_SELECTED_OPERATOR_UNVERIFIED,
    STATUS_SELECTED_SOURCE_BACKED,
    STATUS_SELECTION_REQUIRED,
    TASK_ID,
    OperatorTokenSelectionCandidate,
    OperatorTokenSelectionConfig,
    build_safety_snapshot,
    looks_like_placeholder_token_id,
    operator_token_selection_safety_flags,
    stable_operator_token_selection_id,
    validate_operator_token_selection_result,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "operator_token_selection_packet_073b"
DEFAULT_DISCOVERY_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "public_market_token_discovery_071a"
DEFAULT_BRIDGE_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "discovery_to_token_resolver_bridge_071d"

TOKEN_ID_PATTERN = re.compile(r"^[1-9][0-9]{0,77}$")
MARKET_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,198}[a-z0-9]$")
CONDITION_ID_PATTERN = re.compile(r"^0x[0-9a-fA-F]{64}$")

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


def operator_token_selection_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "operator_token_selection_packet_073b_result.json",
        "latest_status": root / "latest_operator_token_selection_status_073b.json",
        "candidates": root / "operator_token_selection_candidates_073b.json",
        "packet": root / "operator_token_selection_packet_073b.json",
        "instructions": root / "operator_token_selection_instructions_073b.md",
        "safety_snapshot": root / "operator_token_selection_safety_snapshot_073b.json",
    }


def run_operator_token_selection_packet(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    candidate_index: int | str | None = None,
    token_id: str = "",
    market_slug: str = "",
    condition_id: str = "",
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    discovery_result_path: str | Path | None = None,
    bridge_result_path: str | Path | None = None,
    discovery_artifacts_dir: str | Path | None = None,
    bridge_artifacts_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("operator token selection packet requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    artifact_root_path = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    discovery_dir = Path(discovery_artifacts_dir) if discovery_artifacts_dir else artifact_root_path / "public_market_token_discovery_071a"
    bridge_dir = Path(bridge_artifacts_dir) if bridge_artifacts_dir else artifact_root_path / "discovery_to_token_resolver_bridge_071d"
    paths = operator_token_selection_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    discovery_artifact = _load_latest_artifact(
        explicit_path=discovery_result_path,
        artifact_dir=discovery_dir,
        filenames=(
            "public_market_token_discovery_071a_result.json",
            "public_outcome_token_candidates_071a.json",
        ),
        source_id=SOURCE_PUBLIC_DISCOVERY_071A,
        label="071A public market token discovery",
        generated_at=generated_at,
    )
    bridge_artifact = _load_latest_artifact(
        explicit_path=bridge_result_path,
        artifact_dir=bridge_dir,
        filenames=(
            "discovery_to_token_resolver_bridge_071d_result.json",
            "discovery_to_token_operator_selection_required_071d.json",
            "discovery_to_token_candidate_contract_071d.json",
        ),
        source_id=SOURCE_DISCOVERY_TO_TOKEN_071D,
        label="071D discovery to token resolver bridge",
        generated_at=generated_at,
    )
    source_artifacts = {
        SOURCE_PUBLIC_DISCOVERY_071A: _artifact_summary(discovery_artifact),
        SOURCE_DISCOVERY_TO_TOKEN_071D: _artifact_summary(bridge_artifact),
    }
    candidates = _collect_source_backed_candidates(
        discovery_artifact=discovery_artifact,
        bridge_artifact=bridge_artifact,
        generated_at=generated_at,
    )
    parsed_index = _parse_candidate_index(candidate_index)
    token_format_status = validate_token_id_format(token_id)
    market_slug_format_status = validate_market_slug_format(market_slug)
    condition_id_format_status = validate_condition_id_format(condition_id)
    selection = _select_token(
        candidates=candidates,
        candidate_index=parsed_index,
        token_id=token_id,
        token_id_format_status=token_format_status,
        market_slug=market_slug,
        market_slug_format_status=market_slug_format_status,
        condition_id=condition_id,
        condition_id_format_status=condition_id_format_status,
        generated_at=generated_at,
    )
    status = clean_text(selection.get("status")) or STATUS_SELECTION_REQUIRED
    blockers = _build_blockers(
        status=status,
        candidate_count=len(candidates),
        selection=selection,
        parsed_index=parsed_index,
        token_id=token_id,
        token_id_format_status=token_format_status,
        market_slug_format_status=market_slug_format_status,
        condition_id_format_status=condition_id_format_status,
        generated_at=generated_at,
    )
    safety_snapshot = build_safety_snapshot(status=status, generated_at=generated_at)
    candidates_artifact = _build_candidates_artifact(
        status=status,
        candidates=candidates,
        source_artifacts=source_artifacts,
        generated_at=generated_at,
    )
    packet = _build_packet(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        candidates=candidates,
        selection=selection,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        candidates=candidates,
        selection=selection,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    config = OperatorTokenSelectionConfig(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        artifact_root=normalize_path(artifact_root_path),
        discovery_result_path=clean_text(discovery_result_path) if discovery_result_path else "",
        bridge_result_path=clean_text(bridge_result_path) if bridge_result_path else "",
        candidate_index=clean_text(candidate_index),
        token_id_provided=bool(clean_text(token_id)),
        market_slug_provided=bool(clean_text(market_slug)),
        condition_id_provided=bool(clean_text(condition_id)),
        generated_at=generated_at,
    ).to_dict()
    result: dict[str, Any] = {
        "contract_version": OPERATOR_TOKEN_SELECTION_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "source_artifacts": source_artifacts,
        "source_backed_candidate_count": len(candidates),
        "source_backed_candidates": candidates,
        "candidate_index_base": 0,
        "selection": selection,
        "selected_token_id": clean_text(selection.get("selected_token_id")),
        "selected_token_id_present": bool(clean_text(selection.get("selected_token_id"))),
        "selected_token_source_backed": selection.get("source_backed") is True,
        "operator_provided": selection.get("operator_provided") is True,
        "operator_provided_unverified": selection.get("operator_provided_unverified") is True,
        "operator_selection_required": status == STATUS_SELECTION_REQUIRED,
        "packet": packet,
        "candidates_artifact": candidates_artifact,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "config": config,
        "operator_summary": _operator_summary(status, candidates=candidates, selection=selection),
        "generated_at": generated_at,
    }
    result.update(operator_token_selection_safety_flags())
    result["validation"] = validate_operator_token_selection_result(result)

    write_json(paths["candidates"], candidates_artifact)
    write_json(paths["packet"], packet)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["instructions"], render_operator_token_selection_instructions(result))
    return result


def validate_token_id_format(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "missing_optional"
    if looks_like_placeholder_token_id(text):
        return "invalid_placeholder"
    return "valid" if TOKEN_ID_PATTERN.fullmatch(text) else "invalid"


def validate_market_slug_format(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "missing_optional"
    return "valid" if MARKET_SLUG_PATTERN.fullmatch(text) else "invalid"


def validate_condition_id_format(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "missing_optional"
    return "valid" if CONDITION_ID_PATTERN.fullmatch(text) else "invalid"


def render_operator_token_selection_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    return "\n".join(
        [
            "Operator token selection packet 073B completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
            f"Source-backed candidates: {int(value.get('source_backed_candidate_count', 0) or 0)}",
            f"Selected token id present: {str(value.get('selected_token_id_present') is True).lower()}",
            f"Source backed selection: {str(value.get('selected_token_source_backed') is True).lower()}",
            f"Operator provided: {str(value.get('operator_provided') is True).lower()}",
            f"Operator selection required: {str(value.get('operator_selection_required') is True).lower()}",
            "Allowed for live: false",
            "Token selection executable: false",
            "Order payload generation: blocked",
            "Signing: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Authenticated trading: blocked",
            f"Artifact: {clean_text(latest.get('artifact_path'))}",
        ]
    )


def render_operator_token_selection_instructions(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    packet = dict(value.get("packet", {}))
    candidates = [dict(row) for row in value.get("source_backed_candidates", []) if isinstance(row, Mapping)]
    selection = dict(value.get("selection", {}))
    next_cli = dict(packet.get("safe_next_cli", {}))
    lines = [
        "# PMBOT Operator Token Selection Packet 073B",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        "- Mode: `operator token selection packet / dry-run / no-trading`",
        "- allowed_for_live: `false`",
        "- token_selection_executable: `false`",
        "- candidate_index_base: `0`",
        "",
        "## Candidates",
        "",
        *bullet_lines(
            f"index `{row.get('candidate_index')}` token_id `{row.get('token_id')}` market `{row.get('market_slug') or 'missing'}` outcome `{row.get('outcome_name') or 'missing'}` sources `{', '.join(row.get('source_ids', []))}`"
            for row in candidates
        ),
        "",
        "## Selection",
        "",
        f"- selected_token_id_present: `{str(bool(clean_text(selection.get('selected_token_id')))).lower()}`",
        f"- selected_token_source_backed: `{str(selection.get('source_backed') is True).lower()}`",
        f"- operator_provided: `{str(selection.get('operator_provided') is True).lower()}`",
        f"- token_id_format_status: `{selection.get('token_id_format_status') or 'missing'}`",
        "",
        "## Operator Commands",
        "",
        "- Review the candidate list. To select a source-backed candidate, rerun this packet with:",
        "",
        "```powershell",
        "python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --candidate-index 0",
        "```",
        "",
        "- To validate a manually supplied token ID without claiming it is source-backed, rerun with:",
        "",
        "```powershell",
        "python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --token-id <TOKEN_ID>",
        "```",
        "",
        "## Safe Next CLI Path",
        "",
        *bullet_lines(_format_cli(row) for row in _cli_rows(next_cli)),
        "",
        "## Safety",
        "",
        "- This packet is review-only and non-executable.",
        "- It does not invent token IDs.",
        "- It does not build an order payload.",
        "- It does not sign, submit, cancel, connect a wallet, read secrets, or call authenticated trading endpoints.",
        "- The selected token, if any, still requires separate supervised validation through 070B/072A before any future task can even be reviewed.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "operator token selection packet is no-trading; unsupported live/auth/wallet/sign/order/write/browser flag(s): "
            + ", ".join(requested)
        )


def _load_latest_artifact(
    *,
    explicit_path: str | Path | None,
    artifact_dir: Path,
    filenames: Sequence[str],
    source_id: str,
    label: str,
    generated_at: str,
) -> dict[str, Any]:
    candidates: list[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path))
    for filename in filenames:
        candidates.append(artifact_dir / filename)
    existing = [path for path in candidates if path.exists() and path.is_file()]
    if not existing:
        return {
            "source_id": source_id,
            "available": False,
            "path": "",
            "payload": {},
            "status": "missing",
            "contract_version": "",
            "load_error": "",
            "generated_at": generated_at,
            **operator_token_selection_safety_flags(),
        }
    latest = max(existing, key=lambda path: path.stat().st_mtime)
    try:
        payload = load_json_object(latest, label=label)
        return {
            "source_id": source_id,
            "available": True,
            "path": normalize_path(latest),
            "payload": payload,
            "status": clean_text(_latest_payload(payload).get("status") or payload.get("status")) or "available",
            "contract_version": clean_text(_latest_payload(payload).get("contract_version") or payload.get("contract_version")),
            "load_error": "",
            "generated_at": generated_at,
            **operator_token_selection_safety_flags(),
        }
    except Exception as exc:
        return {
            "source_id": source_id,
            "available": False,
            "path": normalize_path(latest),
            "payload": {},
            "status": "unreadable",
            "contract_version": "",
            "load_error": type(exc).__name__,
            "generated_at": generated_at,
            **operator_token_selection_safety_flags(),
        }


def _artifact_summary(artifact: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(artifact or {})
    return {
        "source_id": clean_text(value.get("source_id")),
        "available": value.get("available") is True,
        "path": clean_text(value.get("path")),
        "status": clean_text(value.get("status")),
        "contract_version": clean_text(value.get("contract_version")),
        "load_error": clean_text(value.get("load_error")),
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **operator_token_selection_safety_flags(),
    }


def _latest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    latest = dict(payload or {}).get("latest_status")
    return dict(latest) if isinstance(latest, Mapping) else dict(payload or {})


def _collect_source_backed_candidates(
    *,
    discovery_artifact: Mapping[str, Any],
    bridge_artifact: Mapping[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(_candidates_from_bridge(dict(bridge_artifact), generated_at=generated_at))
    rows.extend(_candidates_from_discovery(dict(discovery_artifact), generated_at=generated_at))
    deduped = _dedupe_candidates(rows)
    result: list[dict[str, Any]] = []
    for index, row in enumerate(deduped):
        candidate = OperatorTokenSelectionCandidate(
            candidate_index=index,
            display_index=index + 1,
            candidate_id=clean_text(row.get("candidate_id")),
            source_ids=tuple(row.get("source_ids", ())),
            source_paths=tuple(row.get("source_paths", ())),
            bridge_candidate_id=clean_text(row.get("bridge_candidate_id")),
            source_token_candidate_id=clean_text(row.get("source_token_candidate_id")),
            market_candidate_id=clean_text(row.get("market_candidate_id")),
            market_id=clean_text(row.get("market_id")),
            market_slug=clean_text(row.get("market_slug")),
            condition_id=clean_text(row.get("condition_id")),
            question=clean_text(row.get("question")),
            outcome_name=clean_text(row.get("outcome_name")),
            outcome_index=_safe_int(row.get("outcome_index")),
            token_id=clean_text(row.get("token_id")),
            token_id_format_status=clean_text(row.get("token_id_format_status")) or "valid",
            generated_at=generated_at,
        ).to_dict()
        if candidate["token_id_format_valid"] is True and candidate["token_id_is_fixture_or_placeholder"] is False:
            result.append(candidate)
    return result


def _candidates_from_bridge(artifact: Mapping[str, Any], *, generated_at: str) -> list[dict[str, Any]]:
    if artifact.get("available") is not True:
        return []
    payload = dict(artifact.get("payload", {}))
    source_path = clean_text(artifact.get("path"))
    rows: list[dict[str, Any]] = []
    for key in ("valid_source_backed_candidates", "source_backed_candidates"):
        rows.extend(
            _candidate_base_from_bridge_row(row, source_path=source_path, generated_at=generated_at)
            for row in _rows(payload.get(key))
        )
    selection = payload.get("operator_selection_required")
    if isinstance(selection, Mapping):
        rows.extend(
            _candidate_base_from_bridge_row(row, source_path=source_path, generated_at=generated_at)
            for row in _rows(selection.get("candidates"))
        )
    return [row for row in rows if row]


def _candidate_base_from_bridge_row(row: Mapping[str, Any], *, source_path: str, generated_at: str) -> dict[str, Any]:
    value = dict(row or {})
    if value.get("source_backed") is not True and value.get("token_id_source_backed") is not True:
        return {}
    token_id = clean_text(value.get("token_id"))
    if not _token_id_allowed(token_id):
        return {}
    market_id = clean_text(value.get("market_id"))
    return _candidate_base(
        source_id=SOURCE_DISCOVERY_TO_TOKEN_071D,
        source_path=source_path,
        token_id=token_id,
        bridge_candidate_id=clean_text(value.get("bridge_candidate_id")),
        source_token_candidate_id=clean_text(value.get("source_token_candidate_id")),
        market_candidate_id=clean_text(value.get("market_candidate_id")),
        market_id=market_id,
        market_slug=clean_text(value.get("market_slug")),
        condition_id=_condition_id_from_market_id(market_id),
        question=clean_text(value.get("question")),
        outcome_name=clean_text(value.get("outcome_name")),
        outcome_index=_safe_int(value.get("outcome_index")),
        generated_at=generated_at,
    )


def _candidates_from_discovery(artifact: Mapping[str, Any], *, generated_at: str) -> list[dict[str, Any]]:
    if artifact.get("available") is not True:
        return []
    payload = dict(artifact.get("payload", {}))
    source_path = clean_text(artifact.get("path"))
    market_by_id = {
        clean_text(row.get("market_candidate_id")): dict(row)
        for row in _rows(payload.get("market_candidates"))
        if clean_text(row.get("market_candidate_id"))
    }
    rows: list[dict[str, Any]] = []
    for row in _rows(payload.get("outcome_token_candidates")):
        value = dict(row)
        if value.get("source_backed") is not True and value.get("token_id_is_source_backed") is not True:
            continue
        if value.get("token_id_is_generated") is True:
            continue
        token_id = clean_text(value.get("token_id"))
        if not _token_id_allowed(token_id):
            continue
        market_candidate_id = clean_text(value.get("market_candidate_id"))
        market_row = market_by_id.get(market_candidate_id, {})
        market_id = clean_text(value.get("market_id") or market_row.get("market_id"))
        rows.append(
            _candidate_base(
                source_id=SOURCE_PUBLIC_DISCOVERY_071A,
                source_path=source_path,
                token_id=token_id,
                bridge_candidate_id="",
                source_token_candidate_id=clean_text(value.get("token_candidate_id")),
                market_candidate_id=market_candidate_id,
                market_id=market_id,
                market_slug=clean_text(value.get("market_slug") or market_row.get("market_slug")),
                condition_id=_condition_id_from_market_id(market_id),
                question=clean_text(value.get("question") or market_row.get("question")),
                outcome_name=clean_text(value.get("outcome_name")),
                outcome_index=_safe_int(value.get("outcome_index")),
                generated_at=generated_at,
            )
        )
    return [row for row in rows if row]


def _candidate_base(
    *,
    source_id: str,
    source_path: str,
    token_id: str,
    bridge_candidate_id: str,
    source_token_candidate_id: str,
    market_candidate_id: str,
    market_id: str,
    market_slug: str,
    condition_id: str,
    question: str,
    outcome_name: str,
    outcome_index: int,
    generated_at: str,
) -> dict[str, Any]:
    token_id_text = clean_text(token_id)
    candidate_id = stable_operator_token_selection_id(
        "operator-token-selection-candidate-073b",
        {
            "token_id": token_id_text,
            "market_slug": clean_text(market_slug),
            "outcome_name": clean_text(outcome_name),
            "source_token_candidate_id": clean_text(source_token_candidate_id),
        },
    )
    return {
        "candidate_id": candidate_id,
        "source_ids": [clean_text(source_id)],
        "source_paths": [clean_text(source_path)] if clean_text(source_path) else [],
        "bridge_candidate_id": clean_text(bridge_candidate_id),
        "source_token_candidate_id": clean_text(source_token_candidate_id),
        "market_candidate_id": clean_text(market_candidate_id),
        "market_id": clean_text(market_id),
        "market_slug": clean_text(market_slug),
        "condition_id": clean_text(condition_id),
        "question": clean_text(question),
        "outcome_name": clean_text(outcome_name),
        "outcome_index": int(outcome_index or 0),
        "token_id": token_id_text,
        "token_id_format_status": validate_token_id_format(token_id_text),
        "generated_at": generated_at,
    }


def _dedupe_candidates(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    order: list[tuple[str, str, str]] = []
    for row in rows:
        value = dict(row)
        key = (
            clean_text(value.get("token_id")),
            clean_text(value.get("market_slug")),
            clean_text(value.get("outcome_name")),
        )
        if not key[0]:
            continue
        if key not in merged:
            merged[key] = value
            order.append(key)
            continue
        current = merged[key]
        current["source_ids"] = _dedupe_texts([*current.get("source_ids", []), *value.get("source_ids", [])])
        current["source_paths"] = _dedupe_texts([*current.get("source_paths", []), *value.get("source_paths", [])])
        for field in ("bridge_candidate_id", "source_token_candidate_id", "market_candidate_id", "market_id", "condition_id", "question"):
            if not clean_text(current.get(field)) and clean_text(value.get(field)):
                current[field] = clean_text(value.get(field))
    return [merged[key] for key in order]


def _parse_candidate_index(value: Any) -> dict[str, Any]:
    text = clean_text(value)
    if not text:
        return {"provided": False, "valid": True, "value": None, "status": "missing_optional"}
    try:
        parsed = int(text)
    except (TypeError, ValueError):
        return {"provided": True, "valid": False, "value": None, "status": "invalid_integer"}
    if parsed < 0:
        return {"provided": True, "valid": False, "value": parsed, "status": "invalid_negative"}
    return {"provided": True, "valid": True, "value": parsed, "status": "valid"}


def _select_token(
    *,
    candidates: Sequence[Mapping[str, Any]],
    candidate_index: Mapping[str, Any],
    token_id: str,
    token_id_format_status: str,
    market_slug: str,
    market_slug_format_status: str,
    condition_id: str,
    condition_id_format_status: str,
    generated_at: str,
) -> dict[str, Any]:
    token_text = clean_text(token_id)
    provided_slug = clean_text(market_slug)
    provided_condition = clean_text(condition_id)
    if market_slug_format_status == "invalid" or condition_id_format_status == "invalid":
        return _invalid_selection(
            "invalid_market_slug_or_condition_id",
            token_id_format_status=token_id_format_status,
            candidate_index=candidate_index,
            generated_at=generated_at,
        )
    if token_text and token_id_format_status != "valid":
        return _invalid_selection(
            "invalid_token_id_format",
            token_id_format_status=token_id_format_status,
            candidate_index=candidate_index,
            generated_at=generated_at,
        )
    if candidate_index.get("provided") is True:
        if candidate_index.get("valid") is not True:
            return _invalid_selection(
                "invalid_candidate_index_format",
                token_id_format_status=token_id_format_status,
                candidate_index=candidate_index,
                generated_at=generated_at,
            )
        index_value = candidate_index.get("value")
        if not isinstance(index_value, int) or index_value >= len(candidates):
            return _invalid_selection(
                "candidate_index_out_of_range",
                token_id_format_status=token_id_format_status,
                candidate_index=candidate_index,
                generated_at=generated_at,
            )
        selected = dict(candidates[index_value])
        if token_text and token_text != clean_text(selected.get("token_id")):
            return _invalid_selection(
                "candidate_index_token_id_mismatch",
                token_id_format_status=token_id_format_status,
                candidate_index=candidate_index,
                generated_at=generated_at,
            )
        if not _provided_metadata_matches(selected, market_slug=provided_slug, condition_id=provided_condition):
            return _invalid_selection(
                "candidate_metadata_mismatch",
                token_id_format_status=token_id_format_status,
                candidate_index=candidate_index,
                generated_at=generated_at,
            )
        return _selected_source_backed_candidate(
            selected,
            operator_provided=bool(token_text),
            candidate_index=candidate_index,
            generated_at=generated_at,
        )
    if token_text:
        matching = _find_candidate_by_token(candidates, token_text)
        if matching:
            if not _provided_metadata_matches(matching, market_slug=provided_slug, condition_id=provided_condition):
                return _invalid_selection(
                    "provided_metadata_mismatch",
                    token_id_format_status=token_id_format_status,
                    candidate_index=candidate_index,
                    generated_at=generated_at,
                )
            return _selected_source_backed_candidate(
                matching,
                operator_provided=True,
                candidate_index=candidate_index,
                generated_at=generated_at,
            )
        return _selected_operator_unverified(
            token_id=token_text,
            market_slug=provided_slug,
            condition_id=provided_condition,
            token_id_format_status=token_id_format_status,
            generated_at=generated_at,
        )
    if not candidates:
        return _base_selection(
            status=STATUS_NO_CANDIDATES,
            selection_status="blocked_no_source_backed_candidates",
            selected_token_id="",
            token_id_format_status="missing_optional",
            source_backed=False,
            operator_provided=False,
            operator_provided_unverified=False,
            candidate_index=candidate_index,
            generated_at=generated_at,
        )
    return _base_selection(
        status=STATUS_SELECTION_REQUIRED,
        selection_status="operator_selection_required",
        selected_token_id="",
        token_id_format_status="missing_optional",
        source_backed=False,
        operator_provided=False,
        operator_provided_unverified=False,
        candidate_index=candidate_index,
        generated_at=generated_at,
    )


def _invalid_selection(
    reason: str,
    *,
    token_id_format_status: str,
    candidate_index: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    selection = _base_selection(
        status=STATUS_INVALID_SELECTION,
        selection_status=reason,
        selected_token_id="",
        token_id_format_status=token_id_format_status,
        source_backed=False,
        operator_provided=False,
        operator_provided_unverified=False,
        candidate_index=candidate_index,
        generated_at=generated_at,
    )
    selection["selection_valid"] = False
    return selection


def _selected_source_backed_candidate(
    candidate: Mapping[str, Any],
    *,
    operator_provided: bool,
    candidate_index: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    selected = dict(candidate)
    selection = _base_selection(
        status=STATUS_SELECTED_SOURCE_BACKED,
        selection_status="selected_source_backed_candidate",
        selected_token_id=clean_text(selected.get("token_id")),
        token_id_format_status=clean_text(selected.get("token_id_format_status")) or "valid",
        source_backed=True,
        operator_provided=operator_provided,
        operator_provided_unverified=False,
        candidate_index=candidate_index,
        generated_at=generated_at,
    )
    selection.update(
        {
            "selected_candidate": selected,
            "selected_candidate_index": selected.get("candidate_index"),
            "selected_candidate_id": clean_text(selected.get("candidate_id")),
            "market_slug": clean_text(selected.get("market_slug")),
            "condition_id": clean_text(selected.get("condition_id")),
            "outcome_name": clean_text(selected.get("outcome_name")),
            "source_ids": list(selected.get("source_ids", [])),
        }
    )
    selection.update(operator_token_selection_safety_flags())
    return selection


def _selected_operator_unverified(
    *,
    token_id: str,
    market_slug: str,
    condition_id: str,
    token_id_format_status: str,
    generated_at: str,
) -> dict[str, Any]:
    selection = _base_selection(
        status=STATUS_SELECTED_OPERATOR_UNVERIFIED,
        selection_status="selected_operator_provided_unverified",
        selected_token_id=clean_text(token_id),
        token_id_format_status=token_id_format_status,
        source_backed=False,
        operator_provided=True,
        operator_provided_unverified=True,
        candidate_index={"provided": False, "valid": True, "value": None, "status": "missing_optional"},
        generated_at=generated_at,
    )
    selection.update(
        {
            "market_slug": clean_text(market_slug),
            "condition_id": clean_text(condition_id),
            "outcome_name": "",
            "source_ids": [],
            "selected_candidate": {},
            "selected_candidate_index": None,
            "selected_candidate_id": "",
        }
    )
    selection.update(operator_token_selection_safety_flags())
    return selection


def _base_selection(
    *,
    status: str,
    selection_status: str,
    selected_token_id: str,
    token_id_format_status: str,
    source_backed: bool,
    operator_provided: bool,
    operator_provided_unverified: bool,
    candidate_index: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "status": status,
        "selection_status": clean_text(selection_status),
        "selection_valid": status != STATUS_INVALID_SELECTION,
        "selected_token_id": clean_text(selected_token_id),
        "selected_token_id_present": bool(clean_text(selected_token_id)),
        "token_id_format_status": clean_text(token_id_format_status),
        "token_id_format_valid": clean_text(token_id_format_status) == "valid",
        "source_backed": source_backed is True,
        "operator_provided": operator_provided is True,
        "operator_provided_unverified": operator_provided_unverified is True,
        "candidate_index_requested": candidate_index.get("value"),
        "candidate_index_provided": candidate_index.get("provided") is True,
        "candidate_index_status": clean_text(candidate_index.get("status")),
        "candidate_index_base": 0,
        "token_id_generated": False,
        "fake_token_id_generated": False,
        "generated_at": generated_at,
    }
    value.update(operator_token_selection_safety_flags())
    return value


def _provided_metadata_matches(candidate: Mapping[str, Any], *, market_slug: str, condition_id: str) -> bool:
    if market_slug and clean_text(candidate.get("market_slug")) and market_slug != clean_text(candidate.get("market_slug")):
        return False
    if condition_id and clean_text(candidate.get("condition_id")) and condition_id != clean_text(candidate.get("condition_id")):
        return False
    return True


def _find_candidate_by_token(candidates: Sequence[Mapping[str, Any]], token_id: str) -> dict[str, Any]:
    token_text = clean_text(token_id)
    for row in candidates:
        value = dict(row)
        if clean_text(value.get("token_id")) == token_text:
            return value
    return {}


def _build_blockers(
    *,
    status: str,
    candidate_count: int,
    selection: Mapping[str, Any],
    parsed_index: Mapping[str, Any],
    token_id: str,
    token_id_format_status: str,
    market_slug_format_status: str,
    condition_id_format_status: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if status == STATUS_NO_CANDIDATES:
        blockers.append(
            _blocker(
                "no_source_backed_candidates",
                "token_discovery",
                "No source-backed public token candidates were available; no token_id was invented.",
                generated_at=generated_at,
            )
        )
    if status == STATUS_SELECTION_REQUIRED:
        blockers.append(
            _blocker(
                "operator_selection_required",
                "token_selection",
                f"{candidate_count} source-backed candidate(s) are available; choose one with --candidate-index or provide a token_id for validation.",
                generated_at=generated_at,
            )
        )
    if status == STATUS_INVALID_SELECTION:
        blockers.append(
            _blocker(
                clean_text(selection.get("selection_status")) or "invalid_selection",
                "token_selection",
                _invalid_selection_reason(selection, parsed_index=parsed_index, token_id=token_id),
                generated_at=generated_at,
            )
        )
    if token_id_format_status not in {"valid", "missing_optional"}:
        blockers.append(
            _blocker(
                "invalid_operator_token_id_format",
                "token_id",
                "Provided token_id did not pass positive decimal format validation and was not selected.",
                generated_at=generated_at,
            )
        )
    if market_slug_format_status == "invalid":
        blockers.append(
            _blocker(
                "invalid_market_slug_format",
                "market_slug",
                "Provided market slug format is invalid.",
                generated_at=generated_at,
            )
        )
    if condition_id_format_status == "invalid":
        blockers.append(
            _blocker(
                "invalid_condition_id_format",
                "condition_id",
                "Provided condition_id format is invalid.",
                generated_at=generated_at,
            )
        )
    blockers.extend(
        [
            _blocker(
                "live_execution_blocked",
                "live_execution",
                "allowed_for_live=false and this packet cannot authorize live execution.",
                generated_at=generated_at,
            ),
            _blocker(
                "token_selection_not_executable",
                "execution",
                "token_selection_executable=false; the packet only records operator review state.",
                generated_at=generated_at,
            ),
            _blocker(
                "order_generation_blocked",
                "order_generation",
                "No order payload is generated by 073B.",
                generated_at=generated_at,
            ),
            _blocker(
                "signing_blocked",
                "signing",
                "Signing and signed payload generation remain blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "submission_and_cancel_blocked",
                "submission",
                "Order submission and cancellation remain blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "authenticated_trading_blocked",
                "authenticated_trading",
                "Authenticated trading calls are not performed by 073B.",
                generated_at=generated_at,
            ),
        ]
    )
    return _dedupe_blockers(blockers)


def _build_candidates_artifact(
    *,
    status: str,
    candidates: Sequence[Mapping[str, Any]],
    source_artifacts: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": OPERATOR_TOKEN_SELECTION_CANDIDATES_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "candidate_index_base": 0,
        "source_backed_candidate_count": len(candidates),
        "source_backed_candidates": [dict(row) for row in candidates],
        "source_artifacts": {key: dict(row) for key, row in source_artifacts.items()},
        "generated_at": generated_at,
    }
    value.update(operator_token_selection_safety_flags())
    return value


def _build_packet(
    *,
    status: str,
    market: str,
    strategy: str,
    candidates: Sequence[Mapping[str, Any]],
    selection: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    selected_token = clean_text(selection.get("selected_token_id"))
    value = {
        "contract_version": OPERATOR_TOKEN_SELECTION_PACKET_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        "candidate_index_base": 0,
        "source_backed_candidate_count": len(candidates),
        "source_backed_candidates": [dict(row) for row in candidates],
        "selected_token_id": selected_token,
        "selected_token_id_present": bool(selected_token),
        "selected_token_source_backed": selection.get("source_backed") is True,
        "operator_provided": selection.get("operator_provided") is True,
        "operator_provided_unverified": selection.get("operator_provided_unverified") is True,
        "selection": dict(selection),
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "safe_next_cli": _safe_next_cli(
            market=market,
            strategy=strategy,
            selection=selection,
        ),
        "artifact_paths": dict(artifact_paths),
        "generated_at": generated_at,
    }
    value.update(operator_token_selection_safety_flags())
    return value


def _build_latest_status(
    *,
    status: str,
    market: str,
    strategy: str,
    candidates: Sequence[Mapping[str, Any]],
    selection: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    selected_token = clean_text(selection.get("selected_token_id"))
    value = {
        "contract_version": OPERATOR_TOKEN_SELECTION_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        "source_backed_candidate_count": len(candidates),
        "selected_token_id_present": bool(selected_token),
        "selected_token_source_backed": selection.get("source_backed") is True,
        "operator_provided": selection.get("operator_provided") is True,
        "operator_provided_unverified": selection.get("operator_provided_unverified") is True,
        "operator_selection_required": status == STATUS_SELECTION_REQUIRED,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "live_execution": "blocked",
        "token_selection_execution": "blocked",
        "order_generation": "blocked",
        "signing": "blocked",
        "order_submission": "blocked",
        "order_cancellation": "blocked",
        "authenticated_trading": "blocked",
        "next_operator_action": _next_operator_action(status, selection=selection),
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "candidates_path": clean_text(artifact_paths.get("candidates")),
        "packet_path": clean_text(artifact_paths.get("packet")),
        "instructions_path": clean_text(artifact_paths.get("instructions")),
        "safety_snapshot_path": clean_text(artifact_paths.get("safety_snapshot")),
        "generated_at": generated_at,
    }
    value.update(operator_token_selection_safety_flags())
    return value


def _safe_next_cli(*, market: str, strategy: str, selection: Mapping[str, Any]) -> dict[str, Any]:
    selected_token = clean_text(selection.get("selected_token_id"))
    if not selected_token:
        return {
            "status": "blocked_no_selected_token_id",
            "first_order_market_token_resolver_070b": [],
            "order_prep_packet_072a": [],
            "note": "Select or validate a token_id before using the downstream review-only CLI path.",
            **operator_token_selection_safety_flags(),
        }
    resolver_args = [
        "python",
        "-m",
        "pm_bot.operator_runner.first_order_market_token_resolver",
        "--market",
        clean_text(market).upper() or DEFAULT_MARKET,
        "--strategy",
        clean_text(strategy) or DEFAULT_STRATEGY,
        "--dry-run",
        "--token-id",
        selected_token,
    ]
    market_slug = clean_text(selection.get("market_slug"))
    condition_id = clean_text(selection.get("condition_id"))
    outcome_name = clean_text(selection.get("outcome_name"))
    if market_slug:
        resolver_args.extend(["--market-slug", market_slug])
    if condition_id:
        resolver_args.extend(["--condition-id", condition_id])
    if outcome_name:
        resolver_args.extend(["--outcome", outcome_name])
    packet_args = [
        "python",
        "-m",
        "pm_bot.operator_runner.order_prep_packet",
        "--market",
        clean_text(market).upper() or DEFAULT_MARKET,
        "--strategy",
        clean_text(strategy) or DEFAULT_STRATEGY,
        "--dry-run",
    ]
    value = {
        "status": "review_only_cli_available",
        "first_order_market_token_resolver_070b": resolver_args,
        "order_prep_packet_072a": packet_args,
        "note": "Run 070B first to write its review-only artifact, then run 072A. Neither command authorizes live trading.",
    }
    value.update(operator_token_selection_safety_flags())
    return value


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_operator_token_selection_blocker_073b.v1",
        "task_id": TASK_ID,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
        "generated_at": generated_at,
    }
    value.update(operator_token_selection_safety_flags())
    return value


def _dedupe_blockers(blockers: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in blockers:
        value = dict(row)
        blocker_id = clean_text(value.get("blocker_id"))
        if blocker_id in seen:
            continue
        seen.add(blocker_id)
        result.append(value)
    return result


def _invalid_selection_reason(selection: Mapping[str, Any], *, parsed_index: Mapping[str, Any], token_id: str) -> str:
    status = clean_text(selection.get("selection_status"))
    if status == "invalid_candidate_index_format":
        return "candidate-index must be a non-negative integer matching the emitted zero-based candidate_index."
    if status == "candidate_index_out_of_range":
        return "candidate-index did not match any emitted source-backed candidate."
    if status == "invalid_token_id_format":
        return "Provided token_id failed positive decimal format validation."
    if status == "candidate_index_token_id_mismatch":
        return "Provided token_id does not match the selected source-backed candidate_index."
    if status in {"candidate_metadata_mismatch", "provided_metadata_mismatch"}:
        return "Provided market_slug or condition_id conflicts with the matching source-backed candidate."
    if parsed_index.get("provided") is True:
        return "Candidate selection is invalid."
    if clean_text(token_id):
        return "Provided token_id is invalid."
    return "Operator selection is invalid."


def _next_operator_action(status: str, *, selection: Mapping[str, Any]) -> str:
    if status == STATUS_NO_CANDIDATES:
        return "run 071A public discovery first or provide a valid token_id manually for unverified review"
    if status == STATUS_SELECTION_REQUIRED:
        return "choose one emitted zero-based candidate_index or provide a token_id manually for validation"
    if status == STATUS_SELECTED_SOURCE_BACKED:
        return "review the selected source-backed token, then use the safe 070B/072A dry-run CLI path if appropriate"
    if status == STATUS_SELECTED_OPERATOR_UNVERIFIED:
        return "review the manually provided unverified token carefully before any downstream dry-run validation"
    return "correct the invalid token selection input and rerun the packet"


def _operator_summary(status: str, *, candidates: Sequence[Mapping[str, Any]], selection: Mapping[str, Any]) -> str:
    if status == STATUS_NO_CANDIDATES:
        return "No source-backed public token candidates were available and no token_id was selected or invented."
    if status == STATUS_SELECTION_REQUIRED:
        return f"{len(candidates)} source-backed candidate(s) are listed; operator selection is required."
    if status == STATUS_SELECTED_SOURCE_BACKED:
        return "Operator selection resolved to a source-backed public token candidate; packet remains non-executable."
    if status == STATUS_SELECTED_OPERATOR_UNVERIFIED:
        return "Operator provided a format-valid token_id that did not match a source-backed candidate; it is marked unverified."
    return f"Operator token selection is invalid: {clean_text(selection.get('selection_status'))}."


def _format_cli(parts: Sequence[Any]) -> str:
    items = [clean_text(part) for part in parts if clean_text(part)]
    return "`" + " ".join(items) + "`" if items else ""


def _cli_rows(value: Mapping[str, Any]) -> list[Sequence[Any]]:
    rows: list[Sequence[Any]] = []
    for key in ("first_order_market_token_resolver_070b", "order_prep_packet_072a"):
        item = value.get(key)
        if isinstance(item, list) and item:
            rows.append(item)
    return rows


def _token_id_allowed(token_id: Any) -> bool:
    text = clean_text(token_id)
    return bool(text) and validate_token_id_format(text) == "valid"


def _condition_id_from_market_id(market_id: Any) -> str:
    text = clean_text(market_id)
    return text if CONDITION_ID_PATTERN.fullmatch(text) else ""


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _dedupe_texts(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
