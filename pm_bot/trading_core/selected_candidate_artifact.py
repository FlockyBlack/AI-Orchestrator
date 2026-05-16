from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.operator_token_selection_models import looks_like_placeholder_token_id
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text
from pm_bot.trading_core.selected_candidate_artifact_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    EXPLICIT_WARNINGS,
    MODE,
    SELECTED_CANDIDATE_ARTIFACT_LATEST_STATUS_CONTRACT,
    SELECTED_CANDIDATE_ARTIFACT_RESULT_CONTRACT,
    SELECTED_CANDIDATE_ARTIFACT_SOURCE_SNAPSHOT_CONTRACT,
    STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED,
    STATUS_BLOCKED_INVALID_CANDIDATE_INDEX,
    STATUS_OPERATOR_SELECTION_REQUIRED,
    STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED,
    TASK_ID,
    SelectedCandidateArtifact,
    SelectedCandidateArtifactConfig,
    build_safety_snapshot,
    selected_candidate_artifact_safety_flags,
    validate_selected_candidate_artifact_result,
)

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "selected_candidate_artifact_075d"
DEFAULT_OPERATOR_TOKEN_SELECTION_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "operator_token_selection_packet_073b"

SOURCE_073B_FILENAMES = (
    "operator_token_selection_candidates_073b.json",
    "operator_token_selection_packet_073b_result.json",
    "operator_token_selection_packet_073b.json",
    "latest_operator_token_selection_status_073b.json",
)

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
    "--token-id",
)

_CANDIDATE_LIST_KEYS = (
    "source_backed_candidates",
    "source_backed_token_candidates",
    "valid_source_backed_candidates",
    "outcome_token_candidates",
)


def selected_candidate_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "selected_candidate_artifact_075d_result.json",
        "latest_status": root / "latest_selected_candidate_artifact_075d.json",
        "artifact": root / "selected_candidate_artifact_075d.json",
        "source_snapshot": root / "selected_candidate_artifact_source_snapshot_075d.json",
        "safety_snapshot": root / "selected_candidate_artifact_safety_snapshot_075d.json",
        "operator_md": root / "selected_candidate_artifact_075d.md",
    }


def run_selected_candidate_artifact(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    candidate_index: int | str | None = None,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    operator_token_selection_packet_path: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("selected candidate artifact requires --dry-run; live execution is blocked")

    created_at = generated_at
    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    artifact_root_path = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = selected_candidate_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    artifact_preexisting = paths["artifact"].exists()

    source_artifacts = _load_source_artifacts(
        artifact_root=artifact_root_path,
        explicit_path=operator_token_selection_packet_path,
    )
    source_candidates = _collect_candidate_rows(source_artifacts=source_artifacts)
    parsed_index = _parse_candidate_index(candidate_index)
    requested_candidate = _candidate_by_index(source_candidates, parsed_index.get("value"))
    normalized_candidate = _normalize_candidate_for_artifact(
        requested_candidate,
        market=market_symbol,
        strategy=strategy_name,
        created_at=created_at,
    )
    selected_artifact = _build_selected_candidate_artifact(normalized_candidate)
    status = _status_for_selection(
        parsed_index=parsed_index,
        requested_candidate=requested_candidate,
        selected_artifact=selected_artifact,
    )
    blockers = _build_blockers(
        status=status,
        parsed_index=parsed_index,
        requested_candidate=requested_candidate,
        candidate_count=len(source_candidates),
        created_at=created_at,
    )
    safety_snapshot = build_safety_snapshot(status=status, created_at=created_at)
    source_snapshot = _build_source_snapshot(
        status=status,
        source_artifacts=source_artifacts,
        source_candidates=source_candidates,
        created_at=created_at,
    )
    latest_status = _build_latest_status(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        parsed_index=parsed_index,
        selected_artifact=selected_artifact,
        blockers=blockers,
        artifact_paths=path_refs,
        artifact_preexisting=artifact_preexisting,
        created_at=created_at,
    )
    config = SelectedCandidateArtifactConfig(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        artifact_root=normalize_path(artifact_root_path),
        operator_token_selection_packet_path=clean_text(operator_token_selection_packet_path)
        if operator_token_selection_packet_path
        else "",
        candidate_index=clean_text(candidate_index),
        created_at=created_at,
    ).to_dict()

    result: dict[str, Any] = {
        "contract_version": SELECTED_CANDIDATE_ARTIFACT_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "candidate_index_base": 0,
        "candidate_index": parsed_index.get("value"),
        "candidate_index_provided": parsed_index.get("provided") is True,
        "candidate_index_valid": parsed_index.get("valid") is True and bool(requested_candidate),
        "candidate_index_status": clean_text(parsed_index.get("status")),
        "source_candidate_count": len(source_candidates),
        "requested_candidate_found": bool(requested_candidate),
        "selected_candidate_source_backed": bool(selected_artifact),
        "selected_by_operator": status == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED,
        "selected_candidate_artifact_written": status == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED,
        "selected_candidate_artifact_recorded": status == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED,
        "selected_candidate_artifact_preexisting": artifact_preexisting,
        "selected_candidate_artifact": selected_artifact,
        "explicit_warnings": list(EXPLICIT_WARNINGS),
        "warnings": list(EXPLICIT_WARNINGS),
        "source_artifacts": _source_artifact_summaries(source_artifacts),
        "source_snapshot": source_snapshot,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "config": config,
        "operator_summary": _operator_summary(status, candidate_count=len(source_candidates)),
        "created_at": created_at,
        "generated_at": created_at,
    }
    result.update(selected_candidate_artifact_safety_flags())
    result["validation"] = validate_selected_candidate_artifact_result(result)

    write_json(paths["source_snapshot"], source_snapshot)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_selected_candidate_artifact_markdown(result))
    if status == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED:
        write_json(paths["artifact"], selected_artifact)
    return result


def render_selected_candidate_artifact_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    artifact = dict(value.get("selected_candidate_artifact", {}))
    return "\n".join(
        [
            "Selected candidate artifact 075D completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
            f"Candidate index provided: {str(value.get('candidate_index_provided') is True).lower()}",
            f"Candidate index: {clean_text(value.get('candidate_index')) if value.get('candidate_index') is not None else 'missing'}",
            f"Source candidate count: {int(value.get('source_candidate_count', 0) or 0)}",
            f"Selected candidate source-backed: {str(value.get('selected_candidate_source_backed') is True).lower()}",
            f"Selected by operator: {str(value.get('selected_by_operator') is True).lower()}",
            f"Token ID: {clean_text(artifact.get('token_id_short') or 'not selected')}",
            "Selected candidate executable for live: false",
            "Allowed for live: false",
            "Live approval: false",
            "Trading authorization: false",
            "Submit-ready: false",
            "Order payload generation: blocked",
            "Signing: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Authenticated trading: blocked",
            f"Artifact: {clean_text(latest.get('artifact_path'))}",
        ]
    )


def render_selected_candidate_artifact_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    artifact = dict(value.get("selected_candidate_artifact", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Selected Candidate Artifact 075D",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        "- Mode: `selected candidate artifact / dry-run / review-only / no-live`",
        "- allowed_for_live: `false`",
        "- selected_candidate_executable_for_live: `false`",
        "- selected_candidate_submit_ready: `false`",
        "- candidate_index_base: `0`",
        "",
        "## Selected Candidate",
        "",
        f"- candidate_index: `{artifact.get('candidate_index') if artifact else 'missing'}`",
        f"- market_title: `{artifact.get('market_title') or 'missing'}`",
        f"- outcome_label: `{artifact.get('outcome_label') or 'missing'}`",
        f"- token_id_short: `{artifact.get('token_id_short') or 'missing'}`",
        f"- token_id_hash: `{artifact.get('token_id_hash') or 'missing'}`",
        f"- source_backed: `{str(artifact.get('source_backed') is True).lower()}`",
        f"- selected_by_operator: `{str(artifact.get('selected_by_operator') is True).lower()}`",
        "",
        "## Warnings",
        "",
        *bullet_lines(value.get("explicit_warnings", [])),
        "",
        "## Safety",
        "",
        "- this artifact is review-only and local",
        "- it is not live approval",
        "- it is not trading authorization",
        "- it is not submit-ready",
        "- it does not emit the full token ID",
        "- it does not build an order payload, sign, submit, cancel, connect a wallet, read secrets, or call Polymarket",
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "selected candidate artifact is review-only/no-live; unsupported "
            "live/auth/wallet/sign/order/write/browser/token flag(s): "
            + ", ".join(requested)
        )


def shorten_token_id(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "missing"
    if len(text) <= 12:
        return text[:2] + "..." + text[-2:]
    return text[:6] + "..." + text[-4:]


def _load_source_artifacts(
    *,
    artifact_root: Path,
    explicit_path: str | Path | None,
) -> list[dict[str, Any]]:
    paths: list[Path] = []
    if explicit_path:
        paths.append(Path(explicit_path))
    source_dir = artifact_root / "operator_token_selection_packet_073b"
    for filename in SOURCE_073B_FILENAMES:
        paths.append(source_dir / filename)
        paths.append(artifact_root / filename)
    if artifact_root.name == "operator_token_selection_packet_073b":
        for filename in SOURCE_073B_FILENAMES:
            paths.append(artifact_root / filename)

    rows: list[dict[str, Any]] = []
    for path in _dedupe_paths(paths):
        if not path.exists() or not path.is_file():
            continue
        try:
            payload = load_json_object(path, label="075D source 073B artifact")
        except Exception as exc:
            rows.append(
                {
                    "source_id": "operator_token_selection_packet_073b",
                    "path": normalize_path(path),
                    "available": False,
                    "payload": {},
                    "status": "unreadable",
                    "contract_version": "",
                    "load_error": type(exc).__name__,
                }
            )
            continue
        rows.append(
            {
                "source_id": "operator_token_selection_packet_073b",
                "path": normalize_path(path),
                "available": True,
                "payload": payload,
                "status": clean_text(payload.get("status") or dict(payload.get("latest_status", {})).get("status")),
                "contract_version": clean_text(
                    payload.get("contract_version") or dict(payload.get("latest_status", {})).get("contract_version")
                ),
                "load_error": "",
            }
        )
    return rows


def _collect_candidate_rows(*, source_artifacts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    raw_rows: list[dict[str, Any]] = []
    for source in source_artifacts:
        if source.get("available") is not True:
            continue
        payload = source.get("payload")
        for raw in _candidate_rows_from_payload(payload):
            value = dict(raw)
            value["_source_id"] = clean_text(source.get("source_id"))
            value["_source_path"] = clean_text(source.get("path"))
            raw_rows.append(value)
    return _dedupe_candidate_rows(raw_rows)


def _candidate_rows_from_payload(payload: Any) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for key in _CANDIDATE_LIST_KEYS:
                nested = value.get(key)
                if isinstance(nested, list):
                    rows.extend(row for row in nested if isinstance(row, Mapping))
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(payload)
    return rows


def _dedupe_candidate_rows(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for row in candidates:
        value = dict(row)
        candidate_index = _parse_candidate_index(value.get("candidate_index")).get("value")
        token_marker = clean_text(
            value.get("token_id")
            or value.get("selected_token_id")
            or value.get("target_token_id")
            or value.get("outcome_token_id")
            or value.get("clob_token_id")
        )
        key = (
            clean_text(candidate_index),
            token_marker,
            clean_text(value.get("outcome_name") or value.get("outcome_label")),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _normalize_candidate_for_artifact(
    candidate: Mapping[str, Any],
    *,
    market: str,
    strategy: str,
    created_at: str,
) -> dict[str, Any]:
    value = dict(candidate or {})
    if not value:
        return {}
    token_id = clean_text(
        value.get("token_id")
        or value.get("selected_token_id")
        or value.get("target_token_id")
        or value.get("outcome_token_id")
        or value.get("clob_token_id")
    )
    source_backed = (
        value.get("source_backed") is True
        or value.get("token_id_source_backed") is True
        or value.get("token_id_is_source_backed") is True
    )
    token_generated = value.get("token_id_generated") is True or value.get("fake_token_id_generated") is True
    if not token_id or source_backed is not True or token_generated or looks_like_placeholder_token_id(token_id):
        return {}

    source_ids = _clean_list(value.get("source_ids"))
    source_id_text = clean_text(value.get("_source_id"))
    if source_id_text and source_id_text not in source_ids:
        source_ids.append(source_id_text)
    source_paths = _clean_list(value.get("source_paths"))
    source_path_text = clean_text(value.get("_source_path"))
    if source_path_text and source_path_text not in source_paths:
        source_paths.append(source_path_text)

    return SelectedCandidateArtifact(
        market=market,
        strategy=strategy,
        candidate_index=_parse_candidate_index(value.get("candidate_index")).get("value") or 0,
        candidate_id=clean_text(
            value.get("candidate_id")
            or value.get("bridge_candidate_id")
            or value.get("source_token_candidate_id")
            or value.get("token_candidate_id")
        ),
        market_title=clean_text(
            value.get("question")
            or value.get("market_title")
            or value.get("title")
            or value.get("market_slug")
            or value.get("market_id")
            or "market title unavailable"
        ),
        market_slug=clean_text(value.get("market_slug")),
        outcome_label=clean_text(
            value.get("outcome_name")
            or value.get("outcome_label")
            or value.get("outcome")
            or value.get("label")
            or "outcome unavailable"
        ),
        outcome_index=_int_or_zero(value.get("outcome_index")),
        token_id_short=shorten_token_id(token_id),
        token_id_hash=hashlib.sha256(token_id.encode("utf-8")).hexdigest(),
        source_ids=tuple(source_ids),
        source_paths=tuple(source_paths),
        created_at=created_at,
    ).to_dict()


def _build_selected_candidate_artifact(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return dict(candidate or {})


def _status_for_selection(
    *,
    parsed_index: Mapping[str, Any],
    requested_candidate: Mapping[str, Any],
    selected_artifact: Mapping[str, Any],
) -> str:
    if parsed_index.get("provided") is not True:
        return STATUS_OPERATOR_SELECTION_REQUIRED
    if parsed_index.get("valid") is not True or not requested_candidate:
        return STATUS_BLOCKED_INVALID_CANDIDATE_INDEX
    if not selected_artifact:
        return STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED
    return STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED


def _build_source_snapshot(
    *,
    status: str,
    source_artifacts: Sequence[Mapping[str, Any]],
    source_candidates: Sequence[Mapping[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_CANDIDATE_ARTIFACT_SOURCE_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "source_artifacts": _source_artifact_summaries(source_artifacts),
        "source_candidate_count": len(source_candidates),
        "source_payloads_embedded": False,
        "raw_token_ids_embedded": False,
        "created_at": created_at,
        "generated_at": created_at,
    }
    value.update(selected_candidate_artifact_safety_flags())
    return value


def _build_latest_status(
    *,
    status: str,
    market: str,
    strategy: str,
    parsed_index: Mapping[str, Any],
    selected_artifact: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    artifact_preexisting: bool,
    created_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_CANDIDATE_ARTIFACT_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        "candidate_index": parsed_index.get("value"),
        "candidate_index_provided": parsed_index.get("provided") is True,
        "candidate_index_status": clean_text(parsed_index.get("status")),
        "selected_candidate_artifact_recorded": status == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED,
        "selected_candidate_artifact_preexisting": artifact_preexisting,
        "selected_by_operator": status == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED,
        "source_backed": selected_artifact.get("source_backed") is True,
        "token_id_short": clean_text(selected_artifact.get("token_id_short")),
        "token_id_hash": clean_text(selected_artifact.get("token_id_hash")),
        "market_title": clean_text(selected_artifact.get("market_title")),
        "outcome_label": clean_text(selected_artifact.get("outcome_label")),
        "explicit_warnings": list(EXPLICIT_WARNINGS),
        "live_execution": "blocked",
        "token_selection_execution": "blocked",
        "order_generation": "blocked",
        "signing": "blocked",
        "order_submission": "blocked",
        "order_cancellation": "blocked",
        "authenticated_trading": "blocked",
        "next_operator_action": _next_operator_action(status),
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_path": clean_text(artifact_paths.get("artifact")),
        "result_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "source_snapshot_path": clean_text(artifact_paths.get("source_snapshot")),
        "safety_snapshot_path": clean_text(artifact_paths.get("safety_snapshot")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "operator_summary": _operator_summary(status, candidate_count=0),
        "created_at": created_at,
        "generated_at": created_at,
    }
    value.update(selected_candidate_artifact_safety_flags())
    return value


def _build_blockers(
    *,
    status: str,
    parsed_index: Mapping[str, Any],
    requested_candidate: Mapping[str, Any],
    candidate_count: int,
    created_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if status == STATUS_OPERATOR_SELECTION_REQUIRED:
        blockers.append(
            _blocker(
                "operator_selection_required",
                "manual_selection",
                f"{candidate_count} local candidate row(s) are available; operator must provide --candidate-index.",
                created_at=created_at,
            )
        )
    if status == STATUS_BLOCKED_INVALID_CANDIDATE_INDEX:
        blockers.append(
            _blocker(
                "blocked_invalid_candidate_index",
                "manual_selection",
                _invalid_candidate_index_reason(parsed_index=parsed_index, candidate_count=candidate_count),
                created_at=created_at,
            )
        )
    if status == STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED:
        blockers.append(
            _blocker(
                "blocked_candidate_not_source_backed",
                "candidate_sources",
                "The requested candidate exists but is not a source-backed non-generated token candidate.",
                created_at=created_at,
            )
        )
    blockers.extend(
        [
            _blocker(
                "selected_candidate_not_live_approval",
                "live_execution",
                "The selected candidate artifact is not live approval.",
                created_at=created_at,
            ),
            _blocker(
                "selected_candidate_not_trading_authorization",
                "trading_authorization",
                "The selected candidate artifact is not trading authorization.",
                created_at=created_at,
            ),
            _blocker(
                "selected_candidate_not_submit_ready",
                "submit",
                "The selected candidate artifact is not submit-ready.",
                created_at=created_at,
            ),
            _blocker(
                "order_generation_blocked",
                "order_generation",
                "No order payload is generated by 075D.",
                created_at=created_at,
            ),
            _blocker(
                "signing_blocked",
                "signing",
                "Signing and signed payload generation remain blocked.",
                created_at=created_at,
            ),
            _blocker(
                "submission_and_cancel_blocked",
                "submission",
                "Order submission and cancellation remain blocked.",
                created_at=created_at,
            ),
            _blocker(
                "authenticated_trading_blocked",
                "authenticated_trading",
                "Authenticated trading calls are not performed by 075D.",
                created_at=created_at,
            ),
        ]
    )
    if requested_candidate and status != STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED:
        blockers = [row for row in blockers if row["blocker_id"] != "blocked_candidate_not_source_backed"]
    return _dedupe_blockers(blockers)


def _blocker(blocker_id: str, category: str, reason: str, *, created_at: str) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_selected_candidate_artifact_blocker_075d.v1",
        "task_id": TASK_ID,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
        "created_at": created_at,
        "generated_at": created_at,
    }
    value.update(selected_candidate_artifact_safety_flags())
    return value


def _source_artifact_summaries(source_artifacts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for source in source_artifacts:
        summary = {
            "source_id": clean_text(source.get("source_id")),
            "available": source.get("available") is True,
            "path": clean_text(source.get("path")),
            "status": clean_text(source.get("status")),
            "contract_version": clean_text(source.get("contract_version")),
            "load_error": clean_text(source.get("load_error")),
            "payload_embedded": False,
            "raw_token_ids_embedded": False,
        }
        summary.update(selected_candidate_artifact_safety_flags())
        summaries.append(summary)
    return summaries


def _candidate_by_index(candidates: Sequence[Mapping[str, Any]], candidate_index: int | None) -> dict[str, Any]:
    if candidate_index is None:
        return {}
    for row in candidates:
        value = dict(row)
        if _parse_candidate_index(value.get("candidate_index")).get("value") == candidate_index:
            return value
    return {}


def _parse_candidate_index(value: int | str | None) -> dict[str, Any]:
    if value is None or clean_text(value) == "":
        return {"provided": False, "valid": True, "value": None, "status": "missing_optional"}
    if isinstance(value, bool):
        return {"provided": True, "valid": False, "value": None, "status": "invalid_format"}
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return {"provided": True, "valid": False, "value": None, "status": "invalid_format"}
    if parsed < 0:
        return {"provided": True, "valid": False, "value": None, "status": "invalid_negative"}
    return {"provided": True, "valid": True, "value": parsed, "status": "valid"}


def _invalid_candidate_index_reason(*, parsed_index: Mapping[str, Any], candidate_count: int) -> str:
    if parsed_index.get("valid") is not True:
        return "candidate-index must be a non-negative integer matching a local 073B candidate_index."
    return f"candidate-index did not match any local 073B candidate row; available row count is {candidate_count}."


def _next_operator_action(status: str) -> str:
    if status == STATUS_OPERATOR_SELECTION_REQUIRED:
        return "rerun with --candidate-index N from the local 073B candidate list"
    if status == STATUS_BLOCKED_INVALID_CANDIDATE_INDEX:
        return "choose an existing zero-based candidate_index from the 073B candidate artifact"
    if status == STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED:
        return "rerun 073B and select only a source-backed non-generated token candidate"
    return "use this local artifact only for downstream dry-run readiness checks; it is not live approval"


def _operator_summary(status: str, *, candidate_count: int) -> str:
    if status == STATUS_OPERATOR_SELECTION_REQUIRED:
        return f"Operator selection is required; {candidate_count} local candidate row(s) were found."
    if status == STATUS_BLOCKED_INVALID_CANDIDATE_INDEX:
        return "Selected candidate artifact was blocked because the requested candidate index is invalid."
    if status == STATUS_BLOCKED_CANDIDATE_NOT_SOURCE_BACKED:
        return "Selected candidate artifact was blocked because the requested candidate is not source-backed."
    return "Selected candidate artifact was recorded for review-only downstream dry-run readiness checks."


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


def _clean_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        text = clean_text(values)
        return [text] if text else []
    try:
        return [clean_text(item) for item in values if clean_text(item)]
    except TypeError:
        return []


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


def _int_or_zero(value: Any) -> int:
    if value is None or isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
