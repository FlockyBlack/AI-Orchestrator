from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.operator_token_selection_models import looks_like_placeholder_token_id
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text
from pm_bot.trading_core.selected_candidate_instruction_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    MODE,
    SELECTED_CANDIDATE_INSTRUCTION_CANDIDATES_CONTRACT,
    SELECTED_CANDIDATE_INSTRUCTION_LATEST_STATUS_CONTRACT,
    SELECTED_CANDIDATE_INSTRUCTION_PACKET_CONTRACT,
    SELECTED_CANDIDATE_INSTRUCTION_RESULT_CONTRACT,
    STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES,
    STATUS_OPERATOR_SELECTION_REQUIRED,
    TASK_ID,
    SelectedCandidateInstructionCandidate,
    SelectedCandidateInstructionConfig,
    build_safety_snapshot,
    selected_candidate_instruction_safety_flags,
    validate_selected_candidate_instruction_result,
)

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "selected_candidate_instruction_packet_075a"
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


def selected_candidate_instruction_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "selected_candidate_instruction_packet_075a_result.json",
        "latest_status": root / "latest_selected_candidate_instruction_packet_075a.json",
        "candidates": root / "selected_candidate_instruction_candidates_075a.json",
        "packet": root / "selected_candidate_instruction_packet_075a.json",
        "instructions": root / "selected_candidate_instruction_packet_075a.md",
        "safety_snapshot": root / "selected_candidate_instruction_safety_snapshot_075a.json",
    }


def run_selected_candidate_instruction_packet(
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
        raise ValueError("selected candidate instruction packet requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    artifact_root_path = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = selected_candidate_instruction_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    source_artifacts = _load_source_artifacts(
        artifact_root=artifact_root_path,
        explicit_path=operator_token_selection_packet_path,
    )
    source_candidates = _collect_source_backed_candidates(
        source_artifacts=source_artifacts,
        market=market_symbol,
        strategy=strategy_name,
        generated_at=generated_at,
    )
    parsed_index = _parse_candidate_index(candidate_index)
    requested_candidate = _candidate_by_index(source_candidates, parsed_index.get("value"))
    status = (
        STATUS_OPERATOR_SELECTION_REQUIRED
        if source_candidates
        else STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES
    )
    blockers = _build_blockers(
        status=status,
        candidate_count=len(source_candidates),
        requested_candidate_index=parsed_index,
        requested_candidate=requested_candidate,
        generated_at=generated_at,
    )
    safety_snapshot = build_safety_snapshot(status=status, generated_at=generated_at)
    candidates_artifact = _build_candidates_artifact(
        status=status,
        candidates=source_candidates,
        source_artifacts=source_artifacts,
        generated_at=generated_at,
    )
    packet = _build_packet(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        candidates=source_candidates,
        requested_candidate_index=parsed_index,
        requested_candidate=requested_candidate,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        candidates=source_candidates,
        requested_candidate_index=parsed_index,
        requested_candidate=requested_candidate,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    config = SelectedCandidateInstructionConfig(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        artifact_root=normalize_path(artifact_root_path),
        operator_token_selection_packet_path=clean_text(operator_token_selection_packet_path)
        if operator_token_selection_packet_path
        else "",
        candidate_index=clean_text(candidate_index),
        generated_at=generated_at,
    ).to_dict()

    result: dict[str, Any] = {
        "contract_version": SELECTED_CANDIDATE_INSTRUCTION_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "source_artifacts": _source_artifact_summaries(source_artifacts),
        "source_backed_candidate_count": len(source_candidates),
        "source_backed_candidates": source_candidates,
        "candidate_index_base": 0,
        "requested_candidate_index": parsed_index,
        "requested_candidate_available": bool(requested_candidate),
        "requested_candidate_preview": requested_candidate,
        "operator_selection_required": status == STATUS_OPERATOR_SELECTION_REQUIRED,
        "manual_operator_selection_required": True,
        "why_manual_operator_selection_required": _manual_selection_reason(len(source_candidates)),
        "safe_cli_command_template": _safe_selection_cli(market=market_symbol, strategy=strategy_name, candidate_index="N"),
        "safe_cli_command_for_requested_candidate": clean_text(requested_candidate.get("safe_cli_command")),
        "selection_warning": _selection_warning(),
        "packet": packet,
        "candidates_artifact": candidates_artifact,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "config": config,
        "operator_summary": _operator_summary(status, candidate_count=len(source_candidates)),
        "generated_at": generated_at,
    }
    result.update(selected_candidate_instruction_safety_flags())
    result["validation"] = validate_selected_candidate_instruction_result(result)

    write_json(paths["candidates"], candidates_artifact)
    write_json(paths["packet"], packet)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["instructions"], render_selected_candidate_instruction_markdown(result))
    return result


def render_selected_candidate_instruction_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    return "\n".join(
        [
            "Selected candidate instruction packet 075A completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
            f"Source-backed candidates: {int(value.get('source_backed_candidate_count', 0) or 0)}",
            f"Requested candidate available: {str(value.get('requested_candidate_available') is True).lower()}",
            "Manual operator selection required: true",
            "Selected token id present: false",
            "Selected candidate artifact written: false",
            "Selection artifact write performed: false",
            "Allowed for live: false",
            "Instruction packet executable for live: false",
            "Order payload generation: blocked",
            "Signing: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Authenticated trading: blocked",
            f"Artifact: {clean_text(latest.get('artifact_path'))}",
        ]
    )


def render_selected_candidate_instruction_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    candidates = [dict(row) for row in value.get("source_backed_candidates", []) if isinstance(row, Mapping)]
    requested = dict(value.get("requested_candidate_index", {}))
    lines = [
        "# PMBOT Selected Candidate Instruction Packet 075A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        "- Mode: `selected candidate instruction packet / dry-run / review-only / no-live`",
        "- allowed_for_live: `false`",
        "- instruction_packet_executable_for_live: `false`",
        "- selected_candidate_artifact_written: `false`",
        "- selected_token_artifact_written: `false`",
        "- candidate_index_base: `0`",
        "",
        "## Why Manual Selection Is Required",
        "",
        *bullet_lines([value.get("why_manual_operator_selection_required")]),
        "",
        "## Candidates",
        "",
        *_candidate_markdown_lines(candidates),
        "",
        "## Safe CLI Command",
        "",
        "Run the 075D dry-run selected candidate artifact command only after manually choosing the candidate index:",
        "",
        "```powershell",
        clean_text(value.get("safe_cli_command_template")),
        "```",
        "",
        "For a concrete candidate, replace `N` with that candidate's zero-based index.",
        "",
        "## Requested Candidate",
        "",
        f"- candidate_index_provided: `{str(requested.get('provided') is True).lower()}`",
        f"- candidate_index_status: `{requested.get('status') or 'missing_optional'}`",
        f"- requested_candidate_available: `{str(value.get('requested_candidate_available') is True).lower()}`",
        f"- safe_cli_command: `{value.get('safe_cli_command_for_requested_candidate') or 'not available'}`",
        "",
        "## Warnings",
        "",
        *bullet_lines(
            [
                "075A does not select a token automatically.",
                "075A does not write selected-token or selected-candidate artifacts.",
                "Running the displayed 073B dry-run command is still not live trading and is not approval to trade.",
                "No order payload is generated, signed, submitted, or cancelled.",
            ]
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "selected candidate instruction packet is review-only/no-live; unsupported "
            "live/auth/wallet/sign/order/write/browser/token flag(s): "
            + ", ".join(requested)
        )


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
            payload = load_json_object(path, label="075A source 073B artifact")
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
        }
        summary.update(selected_candidate_instruction_safety_flags())
        summaries.append(summary)
    return summaries


def _collect_source_backed_candidates(
    *,
    source_artifacts: Sequence[Mapping[str, Any]],
    market: str,
    strategy: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    raw_rows: list[dict[str, Any]] = []
    for source in source_artifacts:
        if source.get("available") is not True:
            continue
        payload = source.get("payload")
        for raw in _candidate_rows_from_payload(payload):
            candidate = _normalize_candidate(
                raw,
                source_path=source.get("path"),
                source_id=source.get("source_id"),
                market=market,
                strategy=strategy,
                generated_at=generated_at,
            )
            if candidate:
                raw_rows.append(candidate)
    return _dedupe_candidates(raw_rows, market=market, strategy=strategy)


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


def _normalize_candidate(
    raw: Mapping[str, Any],
    *,
    source_path: Any,
    source_id: Any,
    market: str,
    strategy: str,
    generated_at: str,
) -> dict[str, Any]:
    value = dict(raw or {})
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

    candidate_index = _parse_candidate_index(value.get("candidate_index")).get("value")
    market_title = clean_text(
        value.get("question")
        or value.get("market_title")
        or value.get("title")
        or value.get("market_slug")
        or value.get("market_id")
        or "market title unavailable"
    )
    outcome_label = clean_text(
        value.get("outcome_name")
        or value.get("outcome_label")
        or value.get("outcome")
        or value.get("label")
        or "outcome unavailable"
    )
    source_ids = _clean_list(value.get("source_ids"))
    source_id_text = clean_text(source_id)
    if source_id_text and source_id_text not in source_ids:
        source_ids.append(source_id_text)
    source_paths = _clean_list(value.get("source_paths"))
    source_path_text = clean_text(source_path)
    if source_path_text and source_path_text not in source_paths:
        source_paths.append(source_path_text)
    evidence_summary = _evidence_summary(
        candidate_id=clean_text(
            value.get("candidate_id")
            or value.get("bridge_candidate_id")
            or value.get("source_token_candidate_id")
            or value.get("token_candidate_id")
        ),
        source_ids=source_ids,
        source_paths=source_paths,
    )
    candidate = SelectedCandidateInstructionCandidate(
        candidate_index=candidate_index if candidate_index is not None else 0,
        display_index=(candidate_index + 1) if candidate_index is not None else 0,
        candidate_id=clean_text(
            value.get("candidate_id")
            or value.get("bridge_candidate_id")
            or value.get("source_token_candidate_id")
            or value.get("token_candidate_id")
        ),
        market_title=market_title,
        market_slug=clean_text(value.get("market_slug")),
        outcome_label=outcome_label,
        outcome_index=_int_or_zero(value.get("outcome_index")),
        token_id_short=shorten_token_id(token_id),
        source_ids=tuple(source_ids),
        source_paths=tuple(source_paths),
        evidence_summary=tuple(evidence_summary),
        safe_cli_command=_safe_selection_cli(market=market, strategy=strategy, candidate_index=candidate_index),
        generated_at=generated_at,
    ).to_dict()
    candidate["_dedupe_token_id"] = token_id
    return candidate


def _dedupe_candidates(
    candidates: Sequence[Mapping[str, Any]],
    *,
    market: str,
    strategy: str,
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for row in candidates:
        value = dict(row)
        key = (
            clean_text(value.get("_dedupe_token_id")),
            clean_text(value.get("market_slug") or value.get("market_title")),
            clean_text(value.get("outcome_label")),
        )
        if key in seen:
            continue
        seen.add(key)
        assigned = dict(value)
        assigned.pop("_dedupe_token_id", None)
        assigned["candidate_index"] = len(result)
        assigned["display_index"] = len(result) + 1
        assigned["safe_cli_command"] = _safe_selection_cli(
            market=market,
            strategy=strategy,
            candidate_index=len(result),
        )
        result.append(assigned)
    return result


def _build_candidates_artifact(
    *,
    status: str,
    candidates: Sequence[Mapping[str, Any]],
    source_artifacts: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_CANDIDATE_INSTRUCTION_CANDIDATES_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "candidate_index_base": 0,
        "source_backed_candidate_count": len(candidates),
        "source_backed_candidates": [dict(row) for row in candidates],
        "source_artifacts": _source_artifact_summaries(source_artifacts),
        "generated_at": generated_at,
    }
    value.update(selected_candidate_instruction_safety_flags())
    return value


def _build_packet(
    *,
    status: str,
    market: str,
    strategy: str,
    candidates: Sequence[Mapping[str, Any]],
    requested_candidate_index: Mapping[str, Any],
    requested_candidate: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_CANDIDATE_INSTRUCTION_PACKET_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        "candidate_index_base": 0,
        "source_backed_candidate_count": len(candidates),
        "source_backed_candidates": [dict(row) for row in candidates],
        "requested_candidate_index": dict(requested_candidate_index),
        "requested_candidate_available": bool(requested_candidate),
        "requested_candidate_preview": dict(requested_candidate),
        "manual_operator_selection_required": True,
        "why_manual_operator_selection_required": _manual_selection_reason(len(candidates)),
        "safe_cli_command_template": _safe_selection_cli(market=market, strategy=strategy, candidate_index="N"),
        "safe_cli_command_for_requested_candidate": clean_text(requested_candidate.get("safe_cli_command")),
        "selection_warning": _selection_warning(),
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_paths": dict(artifact_paths),
        "generated_at": generated_at,
    }
    value.update(selected_candidate_instruction_safety_flags())
    return value


def _build_latest_status(
    *,
    status: str,
    market: str,
    strategy: str,
    candidates: Sequence[Mapping[str, Any]],
    requested_candidate_index: Mapping[str, Any],
    requested_candidate: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_CANDIDATE_INSTRUCTION_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        "source_backed_candidate_count": len(candidates),
        "operator_selection_required": status == STATUS_OPERATOR_SELECTION_REQUIRED,
        "manual_operator_selection_required": True,
        "requested_candidate_index": requested_candidate_index.get("value"),
        "requested_candidate_index_status": clean_text(requested_candidate_index.get("status")),
        "requested_candidate_available": bool(requested_candidate),
        "selected_token_id_present": False,
        "selected_candidate_artifact_written": False,
        "selected_token_artifact_written": False,
        "selection_artifact_write_performed": False,
        "live_execution": "blocked",
        "token_selection_execution": "blocked",
        "order_generation": "blocked",
        "signing": "blocked",
        "order_submission": "blocked",
        "order_cancellation": "blocked",
        "authenticated_trading": "blocked",
        "next_operator_action": _next_operator_action(status, requested_candidate=requested_candidate),
        "safe_cli_command_for_requested_candidate": clean_text(requested_candidate.get("safe_cli_command")),
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "candidates_path": clean_text(artifact_paths.get("candidates")),
        "packet_path": clean_text(artifact_paths.get("packet")),
        "instructions_path": clean_text(artifact_paths.get("instructions")),
        "safety_snapshot_path": clean_text(artifact_paths.get("safety_snapshot")),
        "operator_summary": _operator_summary(status, candidate_count=len(candidates)),
        "generated_at": generated_at,
    }
    value.update(selected_candidate_instruction_safety_flags())
    return value


def _build_blockers(
    *,
    status: str,
    candidate_count: int,
    requested_candidate_index: Mapping[str, Any],
    requested_candidate: Mapping[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if status == STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES:
        blockers.append(
            _blocker(
                "blocked_missing_source_backed_candidates",
                "candidate_sources",
                "No source-backed 073B candidate artifacts are available; 075A did not invent a token ID.",
                generated_at=generated_at,
            )
        )
    if status == STATUS_OPERATOR_SELECTION_REQUIRED:
        blockers.append(
            _blocker(
                "operator_selection_required",
                "manual_selection",
                f"{candidate_count} source-backed candidate(s) are available; the operator must choose one candidate_index manually.",
                generated_at=generated_at,
            )
        )
    if requested_candidate_index.get("provided") is True and not requested_candidate:
        blockers.append(
            _blocker(
                "requested_candidate_index_unavailable",
                "manual_selection",
                "The requested candidate_index is not present in the local source-backed candidate list.",
                generated_at=generated_at,
            )
        )
    blockers.extend(
        [
            _blocker(
                "instruction_packet_not_executable",
                "execution",
                "instruction_packet_executable_for_live=false; 075A only renders review instructions.",
                generated_at=generated_at,
            ),
            _blocker(
                "selection_artifact_write_blocked",
                "selection_artifact",
                "075A does not write selected-token or selected-candidate artifacts.",
                generated_at=generated_at,
            ),
            _blocker(
                "live_execution_blocked",
                "live_execution",
                "allowed_for_live=false; selection is not live trading and is not approval to trade.",
                generated_at=generated_at,
            ),
            _blocker(
                "order_generation_blocked",
                "order_generation",
                "No order payload is generated by 075A.",
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
                "Authenticated trading calls are not performed by 075A.",
                generated_at=generated_at,
            ),
        ]
    )
    return _dedupe_blockers(blockers)


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_selected_candidate_instruction_blocker_075a.v1",
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
    value.update(selected_candidate_instruction_safety_flags())
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


def _manual_selection_reason(candidate_count: int) -> str:
    if candidate_count <= 0:
        return "No source-backed candidates are available, so manual selection is blocked until a local 073B candidate artifact exists."
    if candidate_count == 1:
        return (
                "A source-backed candidate is available, but 075A is review-only and must not auto-select it; "
                "the operator must explicitly run the 075D dry-run artifact command for the candidate index."
            )
    return (
        "Multiple source-backed candidates are available for different outcomes; 075A must not infer "
        "operator intent or choose a candidate automatically."
    )


def _selection_warning() -> str:
    return (
        "The displayed command only writes a 075D dry-run selected candidate artifact for review. "
        "It is not live trading, not order approval, and not approval to sign, submit, or cancel."
    )


def _next_operator_action(status: str, *, requested_candidate: Mapping[str, Any]) -> str:
    if status == STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES:
        return "run 073B/071A local discovery pipeline first; do not invent a token ID"
    if requested_candidate:
        return "review the requested candidate and run its displayed 075D dry-run command only if it is the intended candidate"
    return "review the candidate list and run the displayed 075D dry-run command with the chosen zero-based candidate_index"


def _operator_summary(status: str, *, candidate_count: int) -> str:
    if status == STATUS_BLOCKED_MISSING_SOURCE_BACKED_CANDIDATES:
        return "No source-backed candidate exists in local artifacts; 075A blocked without inventing a token."
    return (
        f"{candidate_count} source-backed candidate(s) are listed with shortened token IDs; "
        "manual operator selection is still required and no selection artifact was written."
    )


def _candidate_markdown_lines(candidates: Sequence[Mapping[str, Any]]) -> list[str]:
    if not candidates:
        return ["- none"]
    lines: list[str] = []
    for row in candidates:
        value = dict(row)
        lines.extend(
            [
                f"- Candidate index `{value.get('candidate_index')}`",
                f"  Market: `{clean_text(value.get('market_title') or 'missing')}`",
                f"  Outcome: `{clean_text(value.get('outcome_label') or 'missing')}`",
                f"  Token ID: `{clean_text(value.get('token_id_short') or 'missing')}`",
                f"  Evidence: `{'; '.join(value.get('evidence_summary', []))}`",
                f"  Command: `{clean_text(value.get('safe_cli_command'))}`",
            ]
        )
    return lines


def _evidence_summary(*, candidate_id: str, source_ids: Sequence[str], source_paths: Sequence[str]) -> list[str]:
    rows = []
    if candidate_id:
        rows.append(f"source candidate id {candidate_id}")
    if source_ids:
        rows.append("source-backed by " + ", ".join(source_ids))
    if source_paths:
        rows.append("local artifact " + source_paths[0])
    rows.append("full token ID is present only in the source artifact and intentionally shortened here")
    return rows


def _safe_selection_cli(*, market: str, strategy: str, candidate_index: Any) -> str:
    index_text = clean_text(candidate_index)
    return (
        "python -m pm_bot.operator_runner.selected_candidate_artifact "
        f"--market {clean_text(market).upper() or DEFAULT_MARKET} "
        f"--strategy {clean_text(strategy) or DEFAULT_STRATEGY} "
        "--dry-run "
        f"--candidate-index {index_text or 'N'}"
    )


def shorten_token_id(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "missing"
    if len(text) <= 12:
        return text[:2] + "..." + text[-2:]
    return text[:6] + "..." + text[-4:]


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
