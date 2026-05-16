from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.operator_token_selection_models import looks_like_placeholder_token_id
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text
from pm_bot.trading_core.selected_candidate_artifact import shorten_token_id
from pm_bot.trading_core.selected_token_verification_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    MODE,
    SELECTED_TOKEN_VERIFICATION_EVIDENCE_CONTRACT,
    SELECTED_TOKEN_VERIFICATION_LATEST_STATUS_CONTRACT,
    SELECTED_TOKEN_VERIFICATION_RESULT_CONTRACT,
    STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE_ARTIFACT,
    STATUS_BLOCKED_SELECTED_TOKEN_NOT_SOURCE_VERIFIED,
    STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN,
    TASK_ID,
    SelectedTokenVerificationConfig,
    selected_token_verification_safety_flags,
    validate_selected_token_verification_result,
)

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "selected_token_verification_bridge_076a"
DEFAULT_SELECTED_CANDIDATE_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "selected_candidate_artifact_075d"
DEFAULT_OPERATOR_TOKEN_SELECTION_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "operator_token_selection_packet_073b"

SELECTED_CANDIDATE_FILENAMES = (
    "selected_candidate_artifact_075d.json",
    "selected_candidate_artifact_075d_result.json",
    "latest_selected_candidate_artifact_075d.json",
)
SOURCE_073B_FILENAMES = (
    "operator_token_selection_candidates_073b.json",
    "operator_token_selection_packet_073b_result.json",
    "operator_token_selection_packet_073b.json",
    "latest_operator_token_selection_status_073b.json",
)
_CANDIDATE_LIST_KEYS = (
    "source_backed_candidates",
    "source_backed_token_candidates",
    "valid_source_backed_candidates",
    "outcome_token_candidates",
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


def selected_token_verification_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "selected_token_verification_076a_result.json",
        "latest_status": root / "latest_selected_token_verification_076a_status.json",
        "evidence": root / "selected_token_verification_076a_evidence.json",
        "operator_md": root / "selected_token_verification_076a_operator_summary.md",
    }


def run_selected_token_verification_bridge(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    selected_candidate_artifact_path: str | Path | None = None,
    operator_token_selection_packet_path: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("selected token verification bridge requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    artifact_root_path = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = selected_token_verification_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    selected_source = _load_selected_candidate_artifact(
        artifact_root=artifact_root_path,
        explicit_path=selected_candidate_artifact_path,
    )
    source_artifacts = _load_073b_source_artifacts(
        artifact_root=artifact_root_path,
        explicit_path=operator_token_selection_packet_path,
    )
    source_candidates = _collect_source_candidates(source_artifacts=source_artifacts)
    selected_artifact = dict(selected_source.get("artifact", {}))
    verification = _verify_selected_candidate(
        selected_source=selected_source,
        selected_artifact=selected_artifact,
        source_artifacts=source_artifacts,
        source_candidates=source_candidates,
        market=market_symbol,
        strategy=strategy_name,
    )
    status = clean_text(verification.get("status")) or STATUS_BLOCKED_SELECTED_TOKEN_NOT_SOURCE_VERIFIED
    blockers = _build_blockers(status=status, verification=verification, generated_at=generated_at)
    latest_status = _build_latest_status(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        verification=verification,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    evidence = _build_evidence_artifact(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        selected_source=selected_source,
        source_artifacts=source_artifacts,
        source_candidate_count=len(source_candidates),
        verification=verification,
        generated_at=generated_at,
    )
    config = SelectedTokenVerificationConfig(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        artifact_root=normalize_path(artifact_root_path),
        selected_candidate_artifact_path=clean_text(selected_candidate_artifact_path)
        if selected_candidate_artifact_path
        else "",
        operator_token_selection_packet_path=clean_text(operator_token_selection_packet_path)
        if operator_token_selection_packet_path
        else "",
        generated_at=generated_at,
    ).to_dict()

    result: dict[str, Any] = {
        "contract_version": SELECTED_TOKEN_VERIFICATION_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "verification_status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        **_result_fields_from_verification(verification),
        "selected_token_payload_ready_for_submit": False,
        "ready_for_submit": False,
        "submit_ready": False,
        "allowed_for_live": False,
        "selected_token_verification_executable": False,
        "selected_token_verification_approves_live": False,
        "selected_token_verification_approves_submit": False,
        "selected_token_verification_authorizes_order": False,
        "live_ready": False,
        "live_execution_ready": False,
        "signing_ready": False,
        "signer_instantiated": False,
        "wallet_connected": False,
        "payload_written_for_submit": False,
        "source_candidate_count": len(source_candidates),
        "source_artifacts": _source_artifact_summaries(source_artifacts),
        "selected_candidate_source": _selected_source_summary(selected_source),
        "matching_source_candidate": dict(verification.get("matching_source_candidate", {})),
        "verification_checks": dict(verification.get("checks", {})),
        "evidence": evidence,
        "latest_status": latest_status,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_paths": path_refs,
        "config": config,
        "operator_summary": _operator_summary(status),
        "warnings": _warnings(status),
        "generated_at": generated_at,
    }
    result.update(selected_token_verification_safety_flags())
    result["status"] = status
    result["verification_status"] = status
    result["selected_token_verified_for_payload_dry_run"] = (
        status == STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN
    )
    result["validation"] = validate_selected_token_verification_result(result)

    write_json(paths["latest_status"], latest_status)
    write_json(paths["evidence"], evidence)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_selected_token_verification_markdown(result))
    return result


def render_selected_token_verification_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    return "\n".join(
        [
            "Selected token verification bridge 076A completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
            f"Selected candidate artifact present: {str(value.get('selected_candidate_artifact_present') is True).lower()}",
            f"Selected candidate index: {_format_optional(value.get('selected_candidate_index'))}",
            f"Selected by operator: {str(value.get('selected_by_operator') is True).lower()}",
            f"Source backed: {str(value.get('source_backed') is True).lower()}",
            f"Token hash match: {str(value.get('token_hash_match') is True).lower()}",
            f"Known 073B candidate match: {str(value.get('selected_candidate_in_known_candidate_set') is True).lower()}",
            f"Selected token verified for payload dry-run: {str(value.get('selected_token_verified_for_payload_dry_run') is True).lower()}",
            "Selected token payload ready for submit: false",
            "Allowed for live: false",
            "Signing by default: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            f"Artifact: {clean_text(dict(value.get('latest_status', {})).get('artifact_path'))}",
        ]
    )


def render_selected_token_verification_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    match = dict(value.get("matching_source_candidate", {}))
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Selected Token Verification Bridge 076A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy_name')}`",
        "- Mode: `selected token verification bridge / dry-run / no-live / no-submit`",
        "- selected_token_payload_ready_for_submit: `false`",
        "- allowed_for_live: `false`",
        "",
        "## Verification",
        "",
        f"- selected_candidate_artifact_present: `{str(value.get('selected_candidate_artifact_present') is True).lower()}`",
        f"- selected_candidate_index: `{_format_optional(value.get('selected_candidate_index'))}`",
        f"- selected_by_operator: `{str(value.get('selected_by_operator') is True).lower()}`",
        f"- source_backed: `{str(value.get('source_backed') is True).lower()}`",
        f"- token_hash_match: `{str(value.get('token_hash_match') is True).lower()}`",
        f"- token_short_match: `{str(value.get('token_short_match') is True).lower()}`",
        f"- market_match: `{str(value.get('market_match') is True).lower()}`",
        f"- strategy_match: `{str(value.get('strategy_match') is True).lower()}`",
        f"- market_title_match: `{str(value.get('market_title_match') is True).lower()}`",
        f"- outcome_label_match: `{str(value.get('outcome_label_match') is True).lower()}`",
        f"- selected_candidate_in_known_candidate_set: `{str(value.get('selected_candidate_in_known_candidate_set') is True).lower()}`",
        f"- selected_token_verified_for_payload_dry_run: `{str(value.get('selected_token_verified_for_payload_dry_run') is True).lower()}`",
        "",
        "## Matched Candidate",
        "",
        f"- candidate_index: `{_format_optional(match.get('candidate_index'))}`",
        f"- candidate_id: `{match.get('candidate_id') or 'missing'}`",
        f"- market_title: `{match.get('market_title') or 'missing'}`",
        f"- outcome_label: `{match.get('outcome_label') or 'missing'}`",
        f"- token_id_short: `{match.get('token_id_short') or 'missing'}`",
        f"- token_id_hash: `{match.get('token_id_hash') or 'missing'}`",
        "",
        "## Safety",
        "",
        "- this bridge reads local JSON artifacts only",
        "- it verifies the selected candidate against the known 073B source-backed candidate set",
        "- it does not emit the full token ID",
        "- it does not build an order payload, sign, submit, cancel, connect a wallet, read secrets, or call Polymarket",
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"`{path}`" for path in paths.values()),
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
            "selected token verification bridge is dry-run/no-live/no-submit; unsupported "
            "live/auth/wallet/sign/order/write/browser/token flag(s): "
            + ", ".join(requested)
        )


def _load_selected_candidate_artifact(
    *,
    artifact_root: Path,
    explicit_path: str | Path | None,
) -> dict[str, Any]:
    paths: list[Path] = []
    if explicit_path:
        paths.append(Path(explicit_path))
    source_dir = artifact_root / "selected_candidate_artifact_075d"
    for filename in SELECTED_CANDIDATE_FILENAMES:
        paths.append(source_dir / filename)
        paths.append(artifact_root / filename)
    if artifact_root.name == "selected_candidate_artifact_075d":
        for filename in SELECTED_CANDIDATE_FILENAMES:
            paths.append(artifact_root / filename)

    for path in _dedupe_paths(paths):
        if not path.exists() or not path.is_file():
            continue
        try:
            payload = load_json_object(path, label="076A selected candidate artifact source")
        except Exception as exc:
            return {
                "available": False,
                "path": normalize_path(path),
                "payload": {},
                "artifact": {},
                "status": "unreadable",
                "contract_version": "",
                "load_error": type(exc).__name__,
            }
        artifact = _extract_selected_candidate_artifact(payload)
        return {
            "available": bool(artifact),
            "path": normalize_path(path),
            "payload": payload,
            "artifact": artifact,
            "status": clean_text(payload.get("status") or artifact.get("status")) or "available",
            "contract_version": clean_text(payload.get("contract_version") or artifact.get("contract_version")),
            "load_error": "",
        }

    default_path = paths[0] if paths else source_dir / SELECTED_CANDIDATE_FILENAMES[0]
    return {
        "available": False,
        "path": normalize_path(default_path),
        "payload": {},
        "artifact": {},
        "status": "missing",
        "contract_version": "",
        "load_error": "",
    }


def _load_073b_source_artifacts(
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
            payload = load_json_object(path, label="076A source 073B candidate artifact")
        except Exception as exc:
            rows.append(
                {
                    "source_id": "operator_token_selection_packet_073b",
                    "available": False,
                    "path": normalize_path(path),
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
                "available": True,
                "path": normalize_path(path),
                "payload": payload,
                "status": clean_text(payload.get("status") or dict(payload.get("latest_status", {})).get("status")),
                "contract_version": clean_text(
                    payload.get("contract_version") or dict(payload.get("latest_status", {})).get("contract_version")
                ),
                "load_error": "",
            }
        )
    return rows


def _extract_selected_candidate_artifact(payload: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(payload or {})
    nested = value.get("selected_candidate_artifact")
    if isinstance(nested, Mapping) and nested:
        return dict(nested)
    if clean_text(value.get("token_id_hash")) or clean_text(value.get("token_id_short")):
        return value
    latest = value.get("latest_status")
    if isinstance(latest, Mapping) and (clean_text(latest.get("token_id_hash")) or clean_text(latest.get("token_id_short"))):
        return dict(latest)
    return {}


def _collect_source_candidates(*, source_artifacts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    raw_rows: list[dict[str, Any]] = []
    for source in source_artifacts:
        if source.get("available") is not True:
            continue
        payload = source.get("payload")
        source_scope = _source_scope(payload if isinstance(payload, Mapping) else {})
        for raw in _candidate_rows_from_payload(payload):
            normalized = _normalize_source_candidate(
                raw,
                source_id=clean_text(source.get("source_id")),
                source_path=clean_text(source.get("path")),
                source_scope=source_scope,
            )
            if normalized:
                raw_rows.append(normalized)
    return _dedupe_source_candidates(raw_rows)


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


def _normalize_source_candidate(
    row: Mapping[str, Any],
    *,
    source_id: str,
    source_path: str,
    source_scope: Mapping[str, str],
) -> dict[str, Any]:
    value = dict(row or {})
    token_text = clean_text(
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
    token_generated = (
        value.get("token_id_generated") is True
        or value.get("fake_token_id_generated") is True
        or value.get("token_id_is_generated") is True
    )
    if (
        not token_text
        or source_backed is not True
        or token_generated
        or looks_like_placeholder_token_id(token_text)
    ):
        return {}

    source_ids = _clean_list(value.get("source_ids"))
    if source_id and source_id not in source_ids:
        source_ids.append(source_id)
    source_paths = _clean_list(value.get("source_paths"))
    source_path_value = clean_text(value.get("source_path"))
    if source_path_value and source_path_value not in source_paths:
        source_paths.append(source_path_value)
    if source_path and source_path not in source_paths:
        source_paths.append(source_path)

    token_hash = _sha256_text(token_text)
    return {
        "_raw_token_id": token_text,
        "candidate_index": _parse_candidate_index(value.get("candidate_index")),
        "candidate_id": clean_text(
            value.get("candidate_id")
            or value.get("bridge_candidate_id")
            or value.get("source_token_candidate_id")
            or value.get("token_candidate_id")
        ),
        "market": clean_text(value.get("market_symbol") or value.get("market") or source_scope.get("market")).upper(),
        "strategy": clean_text(value.get("strategy_name") or value.get("strategy") or source_scope.get("strategy")),
        "market_title": _candidate_market_title(value),
        "market_slug": clean_text(value.get("market_slug")),
        "outcome_label": _candidate_outcome_label(value),
        "outcome_index": _safe_int(value.get("outcome_index")),
        "token_id_short": shorten_token_id(token_text),
        "token_id_hash": token_hash,
        "source_ids": source_ids,
        "source_paths": source_paths,
        "source_backed": True,
        "token_id_generated": False,
        "fake_token_id_generated": False,
        "allowed_for_live": False,
    }


def _verify_selected_candidate(
    *,
    selected_source: Mapping[str, Any],
    selected_artifact: Mapping[str, Any],
    source_artifacts: Sequence[Mapping[str, Any]],
    source_candidates: Sequence[Mapping[str, Any]],
    market: str,
    strategy: str,
) -> dict[str, Any]:
    selected_present = selected_source.get("available") is True and bool(selected_artifact)
    selected_index = _parse_candidate_index(selected_artifact.get("candidate_index")) if selected_present else None
    candidate_index_exists = selected_index is not None
    selected_by_operator = selected_artifact.get("selected_by_operator") is True
    source_backed = (
        selected_artifact.get("source_backed") is True
        or selected_artifact.get("token_id_source_backed") is True
    )
    selected_hash = clean_text(
        selected_artifact.get("token_id_hash")
        or selected_artifact.get("token_id_sha256")
        or selected_artifact.get("selected_token_fingerprint_sha256")
    )
    selected_short = clean_text(selected_artifact.get("token_id_short"))
    selected_market = clean_text(selected_artifact.get("market_symbol") or selected_artifact.get("market")).upper()
    selected_strategy = clean_text(selected_artifact.get("strategy_name") or selected_artifact.get("strategy"))
    selected_market_title = clean_text(selected_artifact.get("market_title") or selected_artifact.get("question"))
    selected_outcome = clean_text(selected_artifact.get("outcome_label") or selected_artifact.get("outcome_name"))
    selected_outcome_index = _safe_int(selected_artifact.get("outcome_index"))

    matching_candidate = _find_matching_source_candidate(
        candidates=source_candidates,
        selected_index=selected_index,
        selected_hash=selected_hash,
        selected_short=selected_short,
        selected_market_title=selected_market_title,
        selected_outcome=selected_outcome,
        selected_outcome_index=selected_outcome_index,
        market=market,
        strategy=strategy,
    )
    candidate_index_match = bool(matching_candidate) and matching_candidate.get("candidate_index") == selected_index
    token_hash_match = bool(matching_candidate) and clean_text(matching_candidate.get("token_id_hash")) == selected_hash
    token_short_match = bool(matching_candidate) and clean_text(matching_candidate.get("token_id_short")) == selected_short
    market_match = (
        selected_present
        and (not selected_market or selected_market == market)
        and _source_scope_matches(source_artifacts, source_candidates, market=market, strategy=strategy, scope="market")
    )
    strategy_match = (
        selected_present
        and (not selected_strategy or selected_strategy == strategy)
        and _source_scope_matches(source_artifacts, source_candidates, market=market, strategy=strategy, scope="strategy")
    )
    market_title_match = bool(matching_candidate) and _same_text(
        selected_market_title,
        clean_text(matching_candidate.get("market_title")),
    )
    outcome_label_match = bool(matching_candidate) and _same_text(
        selected_outcome,
        clean_text(matching_candidate.get("outcome_label")),
    )
    source_safety_flags_ok = (
        _source_false_flags_ok(selected_artifact, ("allowed_for_live", "selected_candidate_executable_for_live", "selected_candidate_submit_ready"))
        and all(
            _source_false_flags_ok(
                source.get("payload") if isinstance(source.get("payload"), Mapping) else {},
                ("allowed_for_live", "order_payload_generated", "signed_payload_generated", "order_submission_enabled", "order_cancellation_enabled"),
            )
            for source in source_artifacts
        )
    )
    selected_candidate_in_known_candidate_set = (
        bool(matching_candidate)
        and candidate_index_match
        and token_hash_match
        and market_title_match
        and outcome_label_match
    )
    verified = (
        selected_present
        and candidate_index_exists
        and selected_by_operator
        and source_backed
        and selected_hash
        and token_hash_match
        and token_short_match
        and market_match
        and strategy_match
        and selected_candidate_in_known_candidate_set
        and source_safety_flags_ok
    )
    status = (
        STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN
        if verified
        else STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE_ARTIFACT
        if not selected_present
        else STATUS_BLOCKED_SELECTED_TOKEN_NOT_SOURCE_VERIFIED
    )
    checks = {
        "selected_candidate_artifact_present": selected_present,
        "candidate_index_exists": candidate_index_exists,
        "selected_by_operator": selected_by_operator,
        "source_backed": source_backed,
        "token_hash_present": bool(selected_hash),
        "token_short_present": bool(selected_short),
        "token_hash_match": token_hash_match,
        "token_short_match": token_short_match,
        "candidate_index_match": candidate_index_match,
        "market_match": market_match,
        "strategy_match": strategy_match,
        "market_title_match": market_title_match,
        "outcome_label_match": outcome_label_match,
        "selected_candidate_in_known_candidate_set": selected_candidate_in_known_candidate_set,
        "source_safety_flags_ok": source_safety_flags_ok,
    }
    return {
        "status": status,
        "checks": checks,
        "selected_candidate_artifact_present": selected_present,
        "candidate_index_exists": candidate_index_exists,
        "selected_candidate_index": selected_index,
        "selected_by_operator": selected_by_operator,
        "source_backed": source_backed,
        "token_id_hash": selected_hash,
        "token_id_short": selected_short,
        "token_hash_match": token_hash_match,
        "token_short_match": token_short_match,
        "candidate_index_match": candidate_index_match,
        "market_match": market_match,
        "strategy_match": strategy_match,
        "market_title_match": market_title_match,
        "outcome_label_match": outcome_label_match,
        "selected_candidate_in_known_candidate_set": selected_candidate_in_known_candidate_set,
        "selected_token_verified_for_payload_dry_run": verified,
        "matching_source_candidate": _sanitize_source_candidate(matching_candidate),
        "source_safety_flags_ok": source_safety_flags_ok,
    }


def _find_matching_source_candidate(
    *,
    candidates: Sequence[Mapping[str, Any]],
    selected_index: int | None,
    selected_hash: str,
    selected_short: str,
    selected_market_title: str,
    selected_outcome: str,
    selected_outcome_index: int,
    market: str,
    strategy: str,
) -> dict[str, Any]:
    if selected_index is None or not selected_hash:
        return {}
    for row in candidates:
        value = dict(row)
        if value.get("candidate_index") != selected_index:
            continue
        if clean_text(value.get("token_id_hash")) != selected_hash:
            continue
        if selected_short and clean_text(value.get("token_id_short")) != selected_short:
            continue
        if not _candidate_scope_ok(value, market=market, strategy=strategy):
            continue
        if not _same_text(selected_market_title, clean_text(value.get("market_title"))):
            continue
        if not _same_text(selected_outcome, clean_text(value.get("outcome_label"))):
            continue
        if selected_outcome_index != _safe_int(value.get("outcome_index")):
            continue
        return value
    return {}


def _result_fields_from_verification(verification: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "selected_candidate_artifact_present": verification.get("selected_candidate_artifact_present") is True,
        "candidate_index_exists": verification.get("candidate_index_exists") is True,
        "selected_candidate_index": verification.get("selected_candidate_index"),
        "selected_by_operator": verification.get("selected_by_operator") is True,
        "source_backed": verification.get("source_backed") is True,
        "token_id_short": clean_text(verification.get("token_id_short")),
        "token_id_hash": clean_text(verification.get("token_id_hash")),
        "token_hash_match": verification.get("token_hash_match") is True,
        "token_short_match": verification.get("token_short_match") is True,
        "candidate_index_match": verification.get("candidate_index_match") is True,
        "market_match": verification.get("market_match") is True,
        "strategy_match": verification.get("strategy_match") is True,
        "market_title_match": verification.get("market_title_match") is True,
        "outcome_label_match": verification.get("outcome_label_match") is True,
        "selected_candidate_in_known_candidate_set": verification.get("selected_candidate_in_known_candidate_set") is True,
        "selected_token_verified_for_payload_dry_run": verification.get("selected_token_verified_for_payload_dry_run") is True,
        "source_safety_flags_ok": verification.get("source_safety_flags_ok") is True,
    }


def _build_latest_status(
    *,
    status: str,
    market: str,
    strategy: str,
    verification: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_TOKEN_VERIFICATION_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "verification_status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        **_result_fields_from_verification(verification),
        "selected_token_payload_ready_for_submit": False,
        "allowed_for_live": False,
        "live_execution": "blocked",
        "signing": "blocked",
        "order_submission": "blocked",
        "order_cancellation": "blocked",
        "authenticated_trading": "blocked",
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "evidence_path": clean_text(artifact_paths.get("evidence")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "operator_summary": _operator_summary(status),
        "generated_at": generated_at,
    }
    value.update(selected_token_verification_safety_flags())
    value["status"] = clean_text(status)
    value["verification_status"] = clean_text(status)
    value["selected_token_verified_for_payload_dry_run"] = (
        status == STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN
    )
    return value


def _build_evidence_artifact(
    *,
    status: str,
    market: str,
    strategy: str,
    selected_source: Mapping[str, Any],
    source_artifacts: Sequence[Mapping[str, Any]],
    source_candidate_count: int,
    verification: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_TOKEN_VERIFICATION_EVIDENCE_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "verification_status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        "selected_candidate_source": _selected_source_summary(selected_source),
        "source_artifacts": _source_artifact_summaries(source_artifacts),
        "source_candidate_count": source_candidate_count,
        "matching_source_candidate": dict(verification.get("matching_source_candidate", {})),
        "verification_checks": dict(verification.get("checks", {})),
        **_result_fields_from_verification(verification),
        "selected_token_payload_ready_for_submit": False,
        "allowed_for_live": False,
        "source_payloads_embedded": False,
        "raw_token_ids_embedded": False,
        "generated_at": generated_at,
    }
    value.update(selected_token_verification_safety_flags())
    value["status"] = clean_text(status)
    value["verification_status"] = clean_text(status)
    value["selected_token_verified_for_payload_dry_run"] = (
        status == STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN
    )
    return value


def _build_blockers(
    *,
    status: str,
    verification: Mapping[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    checks = dict(verification.get("checks", {}))
    if status == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE_ARTIFACT:
        blockers.append(
            _blocker(
                "blocked_missing_selected_candidate_artifact",
                "selected_candidate_artifact",
                "No local 075D selected candidate artifact is available; the bridge must not infer or invent a token.",
                generated_at=generated_at,
            )
        )
    elif status == STATUS_BLOCKED_SELECTED_TOKEN_NOT_SOURCE_VERIFIED:
        for field, reason in (
            ("candidate_index_exists", "Selected candidate artifact does not contain a candidate_index."),
            ("selected_by_operator", "Selected candidate artifact is not marked selected_by_operator=true."),
            ("source_backed", "Selected candidate artifact is not marked source_backed=true."),
            ("token_hash_present", "Selected candidate artifact does not contain a token_id_hash."),
            ("token_hash_match", "Selected token hash did not match a source-backed 073B candidate."),
            ("token_short_match", "Selected token short representation did not match the 073B candidate."),
            ("candidate_index_match", "Selected candidate_index did not match the matching 073B candidate."),
            ("market_match", "Selected candidate market did not match the requested market or 073B scope."),
            ("strategy_match", "Selected candidate strategy did not match the requested strategy or 073B scope."),
            ("market_title_match", "Selected candidate market title did not match the 073B source evidence."),
            ("outcome_label_match", "Selected candidate outcome label did not match the 073B source evidence."),
            ("selected_candidate_in_known_candidate_set", "Selected candidate was not proven to be in the known 073B candidate set."),
            ("source_safety_flags_ok", "One or more source artifacts did not preserve required no-live/no-submit safety flags."),
        ):
            if checks.get(field) is not True:
                blockers.append(_blocker(field, "verification", reason, generated_at=generated_at))
    blockers.extend(
        [
            _blocker(
                "selected_token_verification_not_live_approval",
                "live_execution",
                "076A verification is only a payload dry-run bridge; allowed_for_live=false remains enforced.",
                generated_at=generated_at,
            ),
            _blocker(
                "selected_token_payload_submit_blocked",
                "submit",
                "selected_token_payload_ready_for_submit=false; this bridge cannot authorize submit.",
                generated_at=generated_at,
            ),
            _blocker(
                "signing_blocked",
                "signing",
                "Signing and signed payload generation remain blocked by default.",
                generated_at=generated_at,
            ),
            _blocker(
                "submission_and_cancel_blocked",
                "submission",
                "Order submission and cancellation remain blocked.",
                generated_at=generated_at,
            ),
        ]
    )
    return _dedupe_blockers(blockers)


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_selected_token_verification_bridge_076a_blocker.v1",
        "task_id": TASK_ID,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
        "blocks_submit": True,
        "selected_token_payload_ready_for_submit": False,
        "allowed_for_live": False,
        "generated_at": generated_at,
    }
    value.update(selected_token_verification_safety_flags())
    return value


def _selected_source_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    artifact = dict(source.get("artifact", {})) if isinstance(source.get("artifact"), Mapping) else {}
    return {
        "available": source.get("available") is True,
        "path": clean_text(source.get("path")),
        "status": clean_text(source.get("status")),
        "contract_version": clean_text(source.get("contract_version")),
        "load_error": clean_text(source.get("load_error")),
        "selected_candidate_index": _parse_candidate_index(artifact.get("candidate_index")),
        "selected_by_operator": artifact.get("selected_by_operator") is True,
        "source_backed": artifact.get("source_backed") is True,
        "token_id_short": clean_text(artifact.get("token_id_short")),
        "token_id_hash": clean_text(artifact.get("token_id_hash")),
        "market_title": clean_text(artifact.get("market_title")),
        "outcome_label": clean_text(artifact.get("outcome_label")),
        "payload_embedded": False,
        "raw_token_ids_embedded": False,
        **selected_token_verification_safety_flags(),
    }


def _source_artifact_summaries(source_artifacts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for source in source_artifacts:
        summaries.append(
            {
                "source_id": clean_text(source.get("source_id")),
                "available": source.get("available") is True,
                "path": clean_text(source.get("path")),
                "status": clean_text(source.get("status")),
                "contract_version": clean_text(source.get("contract_version")),
                "load_error": clean_text(source.get("load_error")),
                "payload_embedded": False,
                "raw_token_ids_embedded": False,
                **selected_token_verification_safety_flags(),
            }
        )
    return summaries


def _sanitize_source_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(candidate or {})
    if not value:
        return {}
    return {
        "candidate_index": value.get("candidate_index"),
        "candidate_id": clean_text(value.get("candidate_id")),
        "market": clean_text(value.get("market")).upper(),
        "strategy": clean_text(value.get("strategy")),
        "market_title": clean_text(value.get("market_title")),
        "market_slug": clean_text(value.get("market_slug")),
        "outcome_label": clean_text(value.get("outcome_label")),
        "outcome_index": _safe_int(value.get("outcome_index")),
        "token_id_short": clean_text(value.get("token_id_short")),
        "token_id_hash": clean_text(value.get("token_id_hash")),
        "source_ids": _clean_list(value.get("source_ids")),
        "source_paths": _clean_list(value.get("source_paths")),
        "source_backed": value.get("source_backed") is True,
        "token_id_generated": False,
        "fake_token_id_generated": False,
        "allowed_for_live": False,
        **selected_token_verification_safety_flags(),
    }


def _source_scope(payload: Mapping[str, Any]) -> dict[str, str]:
    value = dict(payload or {})
    latest = value.get("latest_status")
    latest_value = dict(latest) if isinstance(latest, Mapping) else {}
    return {
        "market": clean_text(value.get("market_symbol") or value.get("market") or latest_value.get("market_symbol") or latest_value.get("market")).upper(),
        "strategy": clean_text(value.get("strategy_name") or value.get("strategy") or latest_value.get("strategy_name") or latest_value.get("strategy")),
    }


def _source_scope_matches(
    source_artifacts: Sequence[Mapping[str, Any]],
    source_candidates: Sequence[Mapping[str, Any]],
    *,
    market: str,
    strategy: str,
    scope: str,
) -> bool:
    if scope == "market":
        expected = clean_text(market).upper()
        values = [
            _source_scope(source.get("payload") if isinstance(source.get("payload"), Mapping) else {}).get("market", "")
            for source in source_artifacts
        ]
        values.extend(clean_text(candidate.get("market")).upper() for candidate in source_candidates)
    else:
        expected = clean_text(strategy)
        values = [
            _source_scope(source.get("payload") if isinstance(source.get("payload"), Mapping) else {}).get("strategy", "")
            for source in source_artifacts
        ]
        values.extend(clean_text(candidate.get("strategy")) for candidate in source_candidates)
    scoped = [value for value in values if clean_text(value)]
    return all(clean_text(value) == expected for value in scoped)


def _candidate_scope_ok(candidate: Mapping[str, Any], *, market: str, strategy: str) -> bool:
    candidate_market = clean_text(candidate.get("market")).upper()
    candidate_strategy = clean_text(candidate.get("strategy"))
    if candidate_market and candidate_market != clean_text(market).upper():
        return False
    if candidate_strategy and candidate_strategy != clean_text(strategy):
        return False
    return True


def _candidate_market_title(value: Mapping[str, Any]) -> str:
    return clean_text(
        value.get("question")
        or value.get("market_title")
        or value.get("title")
        or value.get("market_slug")
        or value.get("market_id")
        or "market title unavailable"
    )


def _candidate_outcome_label(value: Mapping[str, Any]) -> str:
    return clean_text(
        value.get("outcome_name")
        or value.get("outcome_label")
        or value.get("outcome")
        or value.get("label")
        or "outcome unavailable"
    )


def _same_text(left: Any, right: Any) -> bool:
    return clean_text(left).casefold() == clean_text(right).casefold() and bool(clean_text(left))


def _source_false_flags_ok(payload: Mapping[str, Any], fields: Sequence[str]) -> bool:
    for field in fields:
        if field in payload and payload.get(field) is not False:
            return False
    return True


def _parse_candidate_index(value: Any) -> int | None:
    if value is None or isinstance(value, bool) or clean_text(value) == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _dedupe_source_candidates(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[int | None, str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for row in candidates:
        value = dict(row)
        key = (
            _parse_candidate_index(value.get("candidate_index")),
            clean_text(value.get("token_id_hash")),
            clean_text(value.get("market_title")),
            clean_text(value.get("outcome_label")),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


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


def _safe_int(value: Any) -> int:
    if value is None or isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _format_optional(value: Any) -> str:
    text = clean_text(value)
    return text if text else "missing"


def _operator_summary(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE_ARTIFACT:
        return "Verification is blocked because no selected 075D candidate artifact is available."
    if status == STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN:
        return (
            "Selected token is verified against source-backed 073B candidate evidence for payload dry-run only; "
            "submit, signing, cancel, and live execution remain blocked."
        )
    return "Verification is blocked because the selected candidate was not proven against the 073B source-backed candidate set."


def _warnings(status: str) -> list[str]:
    rows = [
        "not live approval",
        "not trading authorization",
        "not submit-ready",
        "no signing by default",
    ]
    if status != STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN:
        rows.append("selected token not source verified")
    return rows


def _sha256_text(value: str) -> str:
    return hashlib.sha256(clean_text(value).encode("utf-8")).hexdigest()
