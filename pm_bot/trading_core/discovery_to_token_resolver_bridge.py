from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.discovery_to_token_resolver_bridge_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    DISCOVERY_TO_TOKEN_BRIDGE_LATEST_STATUS_CONTRACT,
    DISCOVERY_TO_TOKEN_BRIDGE_RESULT_CONTRACT,
    PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT,
    STATUS_BLOCKED_INVALID_SELECTION,
    STATUS_BLOCKED_INVALID_TOKEN_ID,
    STATUS_BLOCKED_NO_DISCOVERY,
    STATUS_BLOCKED_NO_SOURCE_TOKEN,
    STATUS_BLOCKED_SCOPE_MISMATCH,
    STATUS_READY,
    STATUS_SELECTION_REQUIRED,
    TASK_ID,
    DiscoveryToTokenBridgeConfig,
    DiscoveryToTokenCandidateContract,
    DiscoveryToTokenResolverCandidate,
    build_operator_selection_required,
    build_safety_snapshot,
    discovery_to_token_bridge_safety_flags,
    looks_like_placeholder_token_id,
    stable_bridge_id,
    validate_discovery_to_token_resolver_bridge_result,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d")
DEFAULT_DISCOVERY_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/public_market_token_discovery_071a")

TOKEN_ID_PATTERN = re.compile(r"^[1-9][0-9]{0,77}$")
CONDITION_ID_PATTERN = re.compile(r"^0x[0-9a-fA-F]{64}$")


def discovery_to_token_resolver_bridge_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "discovery_to_token_resolver_bridge_071d_result.json",
        "latest_status": root / "latest_discovery_to_token_resolver_bridge_status_071d.json",
        "target_contract": root / "discovery_to_token_candidate_contract_071d.json",
        "operator_selection": root / "discovery_to_token_operator_selection_required_071d.json",
        "safety_snapshot": root / "discovery_to_token_resolver_bridge_safety_snapshot_071d.json",
        "operator_summary": root / "discovery_to_token_resolver_bridge_operator_summary_071d.md",
    }


def run_discovery_to_token_resolver_bridge(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    discovery_result_path: str | Path | None = None,
    discovery_artifacts_dir: str | Path | None = None,
    selected_candidate_id: str = "",
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("discovery to token resolver bridge requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    selected_id = clean_text(selected_candidate_id)
    paths = discovery_to_token_resolver_bridge_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    discovery_dir = Path(discovery_artifacts_dir) if discovery_artifacts_dir else DEFAULT_DISCOVERY_ARTIFACT_DIR
    discovery_path_text = normalize_path(discovery_result_path) if discovery_result_path else ""

    config = DiscoveryToTokenBridgeConfig(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        discovery_result_path=discovery_path_text,
        discovery_artifacts_dir=normalize_path(discovery_dir),
        selected_candidate_id=selected_id,
        generated_at=generated_at,
    ).to_dict()

    discovery_artifact = _load_latest_discovery_artifact(
        discovery_result_path=discovery_result_path,
        discovery_artifacts_dir=discovery_dir,
    )
    discovery_payload = dict(discovery_artifact.get("payload", {})) if discovery_artifact else {}
    discovery_source_path = clean_text(discovery_artifact.get("path")) if discovery_artifact else ""
    discovery_load_errors = list(discovery_artifact.get("errors", [])) if discovery_artifact else []
    candidates = _extract_source_backed_candidates(
        discovery_payload,
        discovery_result_path=discovery_source_path,
        generated_at=generated_at,
    )
    valid_candidates = [row for row in candidates if row.get("token_id_format_status") == "valid"]
    invalid_source_token_count = len(candidates) - len(valid_candidates)
    scope_valid = market_symbol == DEFAULT_ALLOWED_MARKET and strategy_name == DEFAULT_ALLOWED_STRATEGY
    selected_candidate = _select_candidate(valid_candidates, selected_id)
    status = _status_for_bridge(
        scope_valid=scope_valid,
        discovery_artifact_present=bool(discovery_artifact),
        source_candidate_count=len(candidates),
        valid_candidate_count=len(valid_candidates),
        invalid_source_token_count=invalid_source_token_count,
        selected_candidate_id=selected_id,
        selected_candidate=selected_candidate,
    )
    blockers = tuple(
        _build_blockers(
            status=status,
            scope_valid=scope_valid,
            discovery_artifact_present=bool(discovery_artifact),
            source_candidate_count=len(candidates),
            valid_candidate_count=len(valid_candidates),
            invalid_source_token_count=invalid_source_token_count,
            selected_candidate_id=selected_id,
            selected_candidate=selected_candidate,
            generated_at=generated_at,
        )
    )
    target_source = selected_candidate if status == STATUS_READY else {}
    target_contract = DiscoveryToTokenCandidateContract(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        market_slug=clean_text(target_source.get("market_slug")),
        condition_id=_condition_id_from_market_id(target_source.get("market_id")),
        token_id=clean_text(target_source.get("token_id")) if status == STATUS_READY else "",
        outcome_name=clean_text(target_source.get("outcome_name")),
        source_bridge_candidate_id=clean_text(target_source.get("bridge_candidate_id")),
        source_token_candidate_id=clean_text(target_source.get("source_token_candidate_id")),
        market_candidate_id=clean_text(target_source.get("market_candidate_id")),
        source_payload_hash=clean_text(target_source.get("source_payload_hash")),
        discovery_result_path=discovery_source_path,
        token_id_format_status=clean_text(target_source.get("token_id_format_status")) if status == STATUS_READY else "blocked",
        operator_selection_required=status == STATUS_SELECTION_REQUIRED,
        operator_selection_used=bool(selected_id and status == STATUS_READY),
        blockers=blockers,
        generated_at=generated_at,
    ).to_dict()
    operator_selection = build_operator_selection_required(
        status=status,
        candidates=valid_candidates,
        selected_candidate_id=selected_id,
        generated_at=generated_at,
    )
    safety_snapshot = build_safety_snapshot(status=status, generated_at=generated_at)
    latest_status = _build_latest_status(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        discovery_result_path=discovery_source_path,
        candidate_count=len(candidates),
        valid_candidate_count=len(valid_candidates),
        selected_candidate_id=selected_id,
        target_contract=target_contract,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    result: dict[str, Any] = {
        "contract_version": DISCOVERY_TO_TOKEN_BRIDGE_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": "discovery to token resolver bridge / dry-run / no-trading",
        "execution_mode": "preflight",
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "dry_run": True,
        "target_contract_only": True,
        "target_contract_executable": False,
        "config": config,
        "source_discovery_artifact_present": bool(discovery_artifact),
        "source_discovery_result_path": discovery_source_path,
        "source_discovery_contract_version": clean_text(discovery_payload.get("contract_version")),
        "source_discovery_status": clean_text(discovery_payload.get("status")),
        "source_discovery_load_errors": discovery_load_errors,
        "source_backed_candidate_count": len(candidates),
        "valid_source_backed_candidate_count": len(valid_candidates),
        "invalid_source_backed_token_count": invalid_source_token_count,
        "source_backed_candidates": candidates,
        "valid_source_backed_candidates": valid_candidates,
        "target_contract": target_contract,
        "operator_selection_required": operator_selection,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary(status),
        "generated_at": generated_at,
    }
    result.update(discovery_to_token_bridge_safety_flags())
    result["validation"] = validate_discovery_to_token_resolver_bridge_result(result)

    write_json(paths["target_contract"], target_contract)
    write_json(paths["operator_selection"], operator_selection)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_summary"], render_discovery_to_token_resolver_bridge_markdown(result))
    return result


def render_discovery_to_token_resolver_bridge_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    target = dict(value.get("target_contract", {}))
    return "\n".join(
        [
            "Discovery to token resolver bridge 071D completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Source-backed candidates: {int(value.get('source_backed_candidate_count', 0) or 0)}",
            f"Valid token candidates: {int(value.get('valid_source_backed_candidate_count', 0) or 0)}",
            f"Operator selection required: {str(latest.get('operator_selection_required') is True).lower()}",
            f"Target token id: {clean_text(target.get('token_id')) or 'blocked'}",
            "Token id generated: false",
            "Allowed for live: false",
            "Order generation: blocked",
            "Signing: blocked",
            "Order submission: blocked",
            "Authenticated trading: blocked",
            f"Artifact: {clean_text(latest.get('artifact_path'))}",
        ]
    )


def render_discovery_to_token_resolver_bridge_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    target = dict(value.get("target_contract", {}))
    candidates = [dict(row) for row in value.get("valid_source_backed_candidates", []) if isinstance(row, Mapping)]
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Discovery to Token Resolver Bridge 071D",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `discovery to token resolver bridge / dry-run / no-trading`",
        "- target_contract_only: `true`",
        "- target_contract_executable: `false`",
        "- allowed_for_live: `false`",
        "",
        "## Source Discovery",
        "",
        f"- artifact_present: `{str(value.get('source_discovery_artifact_present') is True).lower()}`",
        f"- discovery_result_path: `{value.get('source_discovery_result_path') or 'missing'}`",
        f"- source_backed_candidate_count: `{value.get('source_backed_candidate_count')}`",
        f"- valid_source_backed_candidate_count: `{value.get('valid_source_backed_candidate_count')}`",
        "",
        "## Target Candidate Contract",
        "",
        f"- market_slug: `{target.get('market_slug') or 'blocked'}`",
        f"- condition_id: `{target.get('condition_id') or 'missing_optional'}`",
        f"- token_id: `{target.get('token_id') or 'blocked'}`",
        f"- outcome_name: `{target.get('outcome_name') or 'missing'}`",
        f"- token_id_source: `{target.get('token_id_source')}`",
        "- token_id_generated: `false`",
        "- fake_token_id_generated: `false`",
        "",
        "## Valid Source-Backed Candidates",
        "",
        *bullet_lines(
            f"`{row.get('bridge_candidate_id')}` `{row.get('market_slug')}` `{row.get('outcome_name')}` token_id `{row.get('token_id')}` source `{row.get('source_type')}`"
            for row in candidates[:20]
        ),
        "",
        "## Safety",
        "",
        "- no order payload generated",
        "- no signing attempted",
        "- no order submission attempted",
        "- no order cancellation attempted",
        "- no wallet connection attempted",
        "- no authenticated trading call attempted",
        "- no browser automation added",
        "- no scheduler, daemon, background worker, or autonomous loop added",
        "- token IDs are copied only from source-backed discovery candidates",
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
            "discovery to token resolver bridge is no-trading; unsupported live/auth/wallet/sign/order/browser flag(s): "
            + ", ".join(requested)
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
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--sign",
    "--signing",
    "--order",
    "--submit",
    "--cancel",
    "--approve-live",
    "--browser",
    "--loop",
    "--daemon",
    "--scheduler",
)


def _load_latest_discovery_artifact(
    *,
    discovery_result_path: str | Path | None,
    discovery_artifacts_dir: Path,
) -> dict[str, Any] | None:
    candidates = []
    if discovery_result_path:
        candidates.append(Path(discovery_result_path))
    candidates.append(discovery_artifacts_dir / "public_market_token_discovery_071a_result.json")
    existing = [path for path in candidates if path.exists() and path.is_file()]
    if existing:
        latest = max(existing, key=lambda path: path.stat().st_mtime)
        try:
            payload = load_json_object(latest, label="071A public market token discovery result")
            return {"path": normalize_path(latest), "payload": payload, "errors": []}
        except Exception as exc:
            return {
                "path": normalize_path(latest),
                "payload": {},
                "errors": [
                    {
                        "status": "discovery_artifact_unreadable",
                        "path": normalize_path(latest),
                        "error_type": type(exc).__name__,
                        "message": clean_text(exc),
                    }
                ],
            }

    outcome_path = discovery_artifacts_dir / "public_outcome_token_candidates_071a.json"
    market_path = discovery_artifacts_dir / "public_market_candidates_071a.json"
    if outcome_path.exists() and outcome_path.is_file():
        try:
            outcome_payload = load_json_object(outcome_path, label="071A public outcome token candidates")
            market_payload = load_json_object(market_path, label="071A public market candidates") if market_path.exists() else {}
            payload = {
                "contract_version": PUBLIC_MARKET_TOKEN_DISCOVERY_RESULT_CONTRACT,
                "status": clean_text(outcome_payload.get("status")) or "source_backed_candidates_ready",
                "market_candidates": market_payload.get("market_candidates", []),
                "outcome_token_candidates": outcome_payload.get("outcome_token_candidates", []),
                "generated_at": clean_text(outcome_payload.get("generated_at")) or GENERATED_AT,
            }
            return {"path": normalize_path(outcome_path), "payload": payload, "errors": []}
        except Exception as exc:
            return {
                "path": normalize_path(outcome_path),
                "payload": {},
                "errors": [
                    {
                        "status": "discovery_artifact_unreadable",
                        "path": normalize_path(outcome_path),
                        "error_type": type(exc).__name__,
                        "message": clean_text(exc),
                    }
                ],
            }
    return None


def _extract_source_backed_candidates(
    discovery_payload: Mapping[str, Any],
    *,
    discovery_result_path: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    value = dict(discovery_payload or {})
    market_by_id = {
        clean_text(row.get("market_candidate_id")): dict(row)
        for row in _rows(value.get("market_candidates"))
        if clean_text(row.get("market_candidate_id"))
    }
    result: list[dict[str, Any]] = []
    for row in _rows(value.get("outcome_token_candidates")):
        token_row = dict(row)
        if token_row.get("source_backed") is not True:
            continue
        token_id = clean_text(token_row.get("token_id"))
        if not token_id:
            continue
        if token_row.get("token_id_is_generated") is True:
            continue
        if looks_like_placeholder_token_id(token_id):
            continue
        market_candidate_id = clean_text(token_row.get("market_candidate_id"))
        market_row = market_by_id.get(market_candidate_id, {})
        market_id = clean_text(token_row.get("market_id") or market_row.get("market_id"))
        market_slug = clean_text(token_row.get("market_slug") or market_row.get("market_slug"))
        question = clean_text(token_row.get("question") or market_row.get("question"))
        source_payload_hash = clean_text(token_row.get("source_payload_hash") or market_row.get("source_payload_hash"))
        source_token_candidate_id = clean_text(token_row.get("token_candidate_id"))
        candidate_id = stable_bridge_id(
            "discovery-to-token-candidate-071d",
            {
                "source_token_candidate_id": source_token_candidate_id,
                "market_candidate_id": market_candidate_id,
                "token_id": token_id,
                "outcome_index": token_row.get("outcome_index"),
                "source_payload_hash": source_payload_hash,
            },
        )
        candidate = DiscoveryToTokenResolverCandidate(
            bridge_candidate_id=candidate_id,
            source_token_candidate_id=source_token_candidate_id,
            market_candidate_id=market_candidate_id,
            market_id=market_id,
            market_slug=market_slug,
            question=question,
            outcome_name=clean_text(token_row.get("outcome_name")),
            outcome_index=_safe_int(token_row.get("outcome_index")),
            token_id=token_id,
            token_id_format_status=_token_id_format_status(token_id),
            source_name=clean_text(token_row.get("source_name") or market_row.get("source_name")),
            source_type=clean_text(token_row.get("source_type") or market_row.get("source_type")),
            source_origin=clean_text(token_row.get("source_origin") or market_row.get("source_origin")),
            source_path=clean_text(token_row.get("source_path") or market_row.get("source_path")),
            source_payload_hash=source_payload_hash,
            discovery_result_path=discovery_result_path,
            generated_at=generated_at,
        ).to_dict()
        result.append(candidate)
    return _dedupe_by_id(result, "bridge_candidate_id")


def _select_candidate(candidates: Sequence[Mapping[str, Any]], selected_candidate_id: str) -> dict[str, Any]:
    selected_id = clean_text(selected_candidate_id)
    if not candidates:
        return {}
    if not selected_id and len(candidates) == 1:
        return dict(candidates[0])
    if not selected_id:
        return {}
    for row in candidates:
        value = dict(row)
        if selected_id in {
            clean_text(value.get("bridge_candidate_id")),
            clean_text(value.get("source_token_candidate_id")),
        }:
            return value
    return {}


def _status_for_bridge(
    *,
    scope_valid: bool,
    discovery_artifact_present: bool,
    source_candidate_count: int,
    valid_candidate_count: int,
    invalid_source_token_count: int,
    selected_candidate_id: str,
    selected_candidate: Mapping[str, Any],
) -> str:
    if scope_valid is not True:
        return STATUS_BLOCKED_SCOPE_MISMATCH
    if discovery_artifact_present is not True:
        return STATUS_BLOCKED_NO_DISCOVERY
    if source_candidate_count <= 0:
        return STATUS_BLOCKED_NO_SOURCE_TOKEN
    if valid_candidate_count <= 0 and invalid_source_token_count > 0:
        return STATUS_BLOCKED_INVALID_TOKEN_ID
    if valid_candidate_count <= 0:
        return STATUS_BLOCKED_NO_SOURCE_TOKEN
    if clean_text(selected_candidate_id) and not selected_candidate:
        return STATUS_BLOCKED_INVALID_SELECTION
    if selected_candidate:
        return STATUS_READY
    return STATUS_SELECTION_REQUIRED


def _build_blockers(
    *,
    status: str,
    scope_valid: bool,
    discovery_artifact_present: bool,
    source_candidate_count: int,
    valid_candidate_count: int,
    invalid_source_token_count: int,
    selected_candidate_id: str,
    selected_candidate: Mapping[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if scope_valid is not True:
        blockers.append(_blocker("scope_mismatch", "scope", "Bridge scope is limited to BTC market and tiny-momentum strategy.", generated_at=generated_at))
    if discovery_artifact_present is not True:
        blockers.append(_blocker("missing_071a_discovery_artifact", "discovery", "No latest 071A public discovery artifact was present.", generated_at=generated_at))
    if source_candidate_count <= 0 and discovery_artifact_present:
        blockers.append(_blocker("missing_source_backed_token_id", "token_id", "No source-backed token_id was present in the discovery artifact.", generated_at=generated_at))
    if valid_candidate_count <= 0 and invalid_source_token_count > 0:
        blockers.append(_blocker("invalid_source_backed_token_id_format", "token_id", "Source-backed token_id values were present but not valid 070B decimal token IDs.", generated_at=generated_at))
    if clean_text(selected_candidate_id) and not selected_candidate:
        blockers.append(_blocker("invalid_operator_selection", "operator_selection", "Selected candidate id did not match a valid source-backed token candidate.", generated_at=generated_at))
    if status == STATUS_SELECTION_REQUIRED:
        blockers.append(_blocker("operator_selection_required", "operator_selection", "Multiple source-backed token candidates are available; operator selection is required before producing a populated review contract.", generated_at=generated_at))
    blockers.extend(
        [
            _blocker("live_execution_blocked", "live_execution", "allowed_for_live=false and this task does not authorize live execution.", generated_at=generated_at),
            _blocker("order_generation_blocked", "order_generation", "Only a target candidate contract may be produced; no order payload is generated.", generated_at=generated_at),
            _blocker("signing_blocked", "signing", "Signing and signed payload generation remain blocked.", generated_at=generated_at),
            _blocker("submission_and_cancel_blocked", "submission", "Order submission and cancellation remain blocked.", generated_at=generated_at),
            _blocker("authenticated_trading_blocked", "authenticated_trading", "Authenticated trading calls are not performed by this bridge.", generated_at=generated_at),
        ]
    )
    if status == STATUS_READY:
        blockers.append(_blocker("separate_operator_approval_required", "operator_approval", "A populated target candidate remains review-only and requires a separate operator-approved task.", generated_at=generated_at))
    return blockers


def _build_latest_status(
    *,
    status: str,
    market: str,
    strategy: str,
    discovery_result_path: str,
    candidate_count: int,
    valid_candidate_count: int,
    selected_candidate_id: str,
    target_contract: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": DISCOVERY_TO_TOKEN_BRIDGE_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy_name": clean_text(strategy),
        "source_discovery_result_path": discovery_result_path,
        "source_backed_candidate_count": candidate_count,
        "valid_source_backed_candidate_count": valid_candidate_count,
        "selected_candidate_id": clean_text(selected_candidate_id),
        "operator_selection_required": status == STATUS_SELECTION_REQUIRED,
        "target_token_id_present": bool(clean_text(target_contract.get("token_id"))),
        "target_token_id_source_backed": target_contract.get("token_id_source_backed") is True,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "live_execution": "blocked",
        "order_generation": "blocked",
        "signing": "blocked",
        "order_submission": "blocked",
        "authenticated_trading": "blocked",
        "next_operator_action": _next_operator_action(status),
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "target_contract_path": clean_text(artifact_paths.get("target_contract")),
        "operator_selection_path": clean_text(artifact_paths.get("operator_selection")),
        "safety_snapshot_path": clean_text(artifact_paths.get("safety_snapshot")),
        "operator_summary_path": clean_text(artifact_paths.get("operator_summary")),
        "generated_at": generated_at,
    }
    value.update(discovery_to_token_bridge_safety_flags())
    return value


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = {
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
        "generated_at": generated_at,
    }
    value.update(discovery_to_token_bridge_safety_flags())
    return value


def _next_operator_action(status: str) -> str:
    if status == STATUS_READY:
        return "review the populated 070B candidate contract only; do not trade, sign, submit, cancel, or authenticate"
    if status == STATUS_SELECTION_REQUIRED:
        return "select one source-backed candidate with --select-candidate-id before producing a populated review contract"
    if status == STATUS_BLOCKED_NO_DISCOVERY:
        return "run or provide 071A public discovery first; do not invent token IDs"
    if status == STATUS_BLOCKED_NO_SOURCE_TOKEN:
        return "obtain a source-backed public token_id before continuing"
    if status == STATUS_BLOCKED_INVALID_SELECTION:
        return "choose one of the listed valid source-backed candidate ids"
    return "resolve blockers before reviewing any target contract"


def _operator_summary(status: str) -> str:
    if status == STATUS_READY:
        return "Bridge produced a review-only 070B target candidate using a source-backed discovery token_id."
    if status == STATUS_SELECTION_REQUIRED:
        return "Bridge found multiple source-backed token candidates and blocked auto-selection."
    if status == STATUS_BLOCKED_NO_DISCOVERY:
        return "Bridge blocked because no 071A discovery artifact was present."
    if status == STATUS_BLOCKED_NO_SOURCE_TOKEN:
        return "Bridge blocked because no source-backed token_id was available."
    if status == STATUS_BLOCKED_INVALID_TOKEN_ID:
        return "Bridge blocked because source-backed token_id values were not valid for 070B."
    if status == STATUS_BLOCKED_INVALID_SELECTION:
        return "Bridge blocked because the operator selection did not match a valid candidate."
    return "Bridge blocked on scope or input validation."


def _token_id_format_status(token_id: Any) -> str:
    text = clean_text(token_id)
    if not text:
        return "missing_required"
    if looks_like_placeholder_token_id(text):
        return "invalid_placeholder"
    return "valid" if TOKEN_ID_PATTERN.fullmatch(text) else "invalid"


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


def _dedupe_by_id(rows: Sequence[Mapping[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        value = dict(row)
        row_id = clean_text(value.get(key))
        if row_id in seen:
            continue
        seen.add(row_id)
        result.append(value)
    return result
