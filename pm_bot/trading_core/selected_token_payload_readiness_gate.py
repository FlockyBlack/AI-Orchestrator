from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text
from pm_bot.trading_core.selected_token_payload_readiness_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    EXECUTION_MODE,
    MODE,
    REQUIRED_FALSE_FLAGS,
    SELECTED_TOKEN_PAYLOAD_READINESS_BLOCKERS_CONTRACT,
    SELECTED_TOKEN_PAYLOAD_READINESS_LATEST_STATUS_CONTRACT,
    SELECTED_TOKEN_PAYLOAD_READINESS_RESULT_CONTRACT,
    SELECTED_TOKEN_PAYLOAD_READINESS_SOURCES_CONTRACT,
    STATUS_BLOCKED_APPROVAL_CONTRACT_NOT_READY,
    STATUS_BLOCKED_MISSING_APPROVAL_CONTRACT,
    STATUS_BLOCKED_MISSING_SELECTED_TOKEN,
    STATUS_BLOCKED_MISSING_SIGNED_PAYLOAD_DRY_RUN,
    STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC,
    STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_SOURCE_SAFETY_NOT_READY,
    STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
    STATUS_READY,
    TASK_ID,
    SelectedTokenPayloadReadinessSafetySnapshot,
    selected_token_payload_readiness_safety_flags,
    validate_selected_token_payload_readiness_gate_result,
)

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/selected_token_payload_readiness_gate_073c")
DEFAULT_SELECTED_CANDIDATE_ARTIFACT_PATHS = (
    Path("pm_bot/trading_core/artifacts/selected_candidate_artifact_075d/selected_candidate_artifact_075d.json"),
    Path("pm_bot/trading_core/artifacts/selected_candidate_artifact_075d/selected_candidate_artifact_075d_result.json"),
    Path("pm_bot/trading_core/artifacts/selected_candidate_artifact_075d/latest_selected_candidate_artifact_075d.json"),
)
DEFAULT_OPERATOR_TOKEN_SELECTION_PACKET_PATHS = (
    Path("pm_bot/trading_core/artifacts/operator_token_selection_packet_073b/latest_operator_token_selection_packet_073b.json"),
    Path("pm_bot/trading_core/artifacts/operator_token_selection_packet_073b/operator_token_selection_packet_073b_result.json"),
    Path("pm_bot/trading_core/artifacts/operator_token_selection_packet_073b/operator_token_selection_packet_073b.json"),
)
DEFAULT_FIRST_ORDER_MARKET_TOKEN_CONTRACT_PATH = Path(
    "pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b/first_order_market_token_contract_070b.json"
)
DEFAULT_SIGNER_DIAGNOSTIC_STATUS_PATH = Path(
    "pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/latest_guarded_signer_diagnostic_status_069a.json"
)
DEFAULT_APPROVAL_CONTRACT_STATUS_PATH = Path(
    "pm_bot/trading_core/artifacts/first_live_order_approval_contract_065d/latest_first_live_order_approval_contract_status_065d.json"
)
DEFAULT_SIGNED_PAYLOAD_DRY_RUN_STATUS_PATH = Path(
    "pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/latest_signed_order_payload_dry_run_status_070a.json"
)
DEFAULT_SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_STATUS_PATH = Path(
    "pm_bot/trading_core/artifacts/signed_payload_diagnostic_adapter_072e/latest_signed_payload_diagnostic_adapter_status_072e.json"
)

TOKEN_ID_PATTERN = re.compile(r"^[1-9][0-9]{0,77}$")
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SIGNER_OK_STATUS = "diagnostic_ok"
APPROVAL_DEFINED_STATUS = "approval_contract_defined_execution_blocked"

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--wallet-connect",
    "--sign",
    "--signing",
    "--submit",
    "--cancel",
    "--approve-live",
    "--record-approval",
    "--private-key",
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
)


def selected_token_payload_readiness_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "selected_token_payload_readiness_gate_073c_result.json",
        "latest_status": root / "latest_selected_token_payload_readiness_status_073c.json",
        "sources": root / "selected_token_payload_readiness_sources_073c.json",
        "blockers": root / "selected_token_payload_readiness_blockers_073c.json",
        "safety_snapshot": root / "selected_token_payload_readiness_safety_snapshot_073c.json",
        "operator_md": root / "selected_token_payload_readiness_operator_summary_073c.md",
    }


def run_selected_token_payload_readiness_gate(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    selected_candidate_artifact_path: str | Path | None = None,
    operator_token_selection_packet_path: str | Path | None = None,
    first_order_market_token_contract_path: str | Path | None = None,
    signer_diagnostic_status_path: str | Path | None = None,
    approval_contract_status_path: str | Path | None = None,
    signed_payload_dry_run_status_path: str | Path | None = None,
    signed_payload_diagnostic_adapter_status_path: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("selected token payload readiness gate requires --dry-run; submit/cancel/live is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = selected_token_payload_readiness_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    selection_path = _select_first_existing_path(
        explicit_path=operator_token_selection_packet_path,
        default_paths=DEFAULT_OPERATOR_TOKEN_SELECTION_PACKET_PATHS,
    )
    selected_candidate_path = _select_first_existing_path(
        explicit_path=selected_candidate_artifact_path,
        default_paths=DEFAULT_SELECTED_CANDIDATE_ARTIFACT_PATHS,
    )
    source_artifacts = {
        "selected_candidate_artifact_075d": _load_source_artifact(
            selected_candidate_path,
            "selected candidate artifact 075D",
        ),
        "operator_token_selection_packet_073b": _load_source_artifact(
            selection_path,
            "operator token selection packet 073B",
        ),
        "first_order_market_token_resolver_070b": _load_source_artifact(
            Path(first_order_market_token_contract_path)
            if first_order_market_token_contract_path
            else DEFAULT_FIRST_ORDER_MARKET_TOKEN_CONTRACT_PATH,
            "first order market token resolver 070B",
        ),
        "guarded_signer_diagnostic_smoke_069a": _load_source_artifact(
            Path(signer_diagnostic_status_path)
            if signer_diagnostic_status_path
            else DEFAULT_SIGNER_DIAGNOSTIC_STATUS_PATH,
            "guarded signer diagnostic smoke 069A",
        ),
        "first_live_order_approval_contract_065d": _load_source_artifact(
            Path(approval_contract_status_path)
            if approval_contract_status_path
            else DEFAULT_APPROVAL_CONTRACT_STATUS_PATH,
            "first live order approval contract 065D",
        ),
        "signed_order_payload_dry_run_070a": _load_source_artifact(
            Path(signed_payload_dry_run_status_path)
            if signed_payload_dry_run_status_path
            else DEFAULT_SIGNED_PAYLOAD_DRY_RUN_STATUS_PATH,
            "signed order payload dry-run 070A",
        ),
        "signed_payload_diagnostic_adapter_072e": _load_source_artifact(
            Path(signed_payload_diagnostic_adapter_status_path)
            if signed_payload_diagnostic_adapter_status_path
            else DEFAULT_SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_STATUS_PATH,
            "signed payload diagnostic adapter 072E",
        ),
    }

    selected_token = _summarize_selected_token(
        selected_candidate_source=source_artifacts["selected_candidate_artifact_075d"],
        selection_source=source_artifacts["operator_token_selection_packet_073b"],
        resolver_source=source_artifacts["first_order_market_token_resolver_070b"],
        market_symbol=market_symbol,
        strategy_name=strategy_name,
    )
    signer_diagnostic = _summarize_signer_diagnostic(
        source_artifacts["guarded_signer_diagnostic_smoke_069a"]
    )
    approval_contract = _summarize_approval_contract(
        source_artifacts["first_live_order_approval_contract_065d"]
    )
    signed_payload_dry_run = _summarize_signed_payload_dry_run(
        source_artifacts["signed_order_payload_dry_run_070a"]
    )
    diagnostic_adapter = _summarize_diagnostic_adapter(
        source_artifacts["signed_payload_diagnostic_adapter_072e"]
    )

    readiness_summaries = {
        "selected_token": selected_token,
        "signer_diagnostic": signer_diagnostic,
        "approval_contract": approval_contract,
        "signed_payload_dry_run": signed_payload_dry_run,
        "diagnostic_adapter": diagnostic_adapter,
    }
    blockers = _build_blockers(readiness_summaries, generated_at=generated_at)
    status = _status_for_summaries(readiness_summaries)
    safety_snapshot = SelectedTokenPayloadReadinessSafetySnapshot(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    sources = _build_sources_artifact(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        source_artifacts=source_artifacts,
        readiness_summaries=readiness_summaries,
        generated_at=generated_at,
    )
    blockers_artifact = _build_blockers_artifact(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        blockers=blockers,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        readiness_summaries=readiness_summaries,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )

    result: dict[str, Any] = {
        "contract_version": SELECTED_TOKEN_PAYLOAD_READINESS_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "dry_run": True,
        "readiness_gate_only": True,
        "local_artifact_read_only": True,
        "selected_token_payload_ready_for_submit": False,
        "ready_for_signed_payload_diagnostic": status == STATUS_READY,
        "readiness_summaries": readiness_summaries,
        "source_artifacts": {
            key: _source_artifact_summary(value) for key, value in source_artifacts.items()
        },
        "sources": sources,
        "blockers_artifact": blockers_artifact,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary(status),
        "generated_at": generated_at,
    }
    result.update(selected_token_payload_readiness_safety_flags())
    result["validation"] = validate_selected_token_payload_readiness_gate_result(result, generated_at=generated_at)

    write_json(paths["sources"], sources)
    write_json(paths["blockers"], blockers_artifact)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_selected_token_payload_readiness_markdown(result))
    return result


def render_selected_token_payload_readiness_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Selected token payload readiness gate 073C completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Selected token: {clean_text(value.get('selected_token_status'))}",
            f"Selected token verified: {str(value.get('selected_token_verified') is True).lower()}",
            f"Signer diagnostic: {clean_text(value.get('signer_diagnostic_status'))}",
            f"Approval contract: {clean_text(value.get('approval_contract_status'))}",
            f"Signed payload dry-run: {clean_text(value.get('signed_payload_dry_run_status'))}",
            f"Ready for signed payload diagnostic: {str(value.get('ready_for_signed_payload_diagnostic') is True).lower()}",
            "Selected token payload ready for submit: false",
            "Signing by default: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Trading writes: blocked",
            "Allowed for live: false",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_selected_token_payload_readiness_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    paths = dict(value.get("artifact_paths", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Selected Token Payload Readiness Gate 073C",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `selected token signed payload readiness gate / dry-run / no-submit`",
        "- selected_token_payload_ready_for_submit: `false`",
        "- allowed_for_live: `false`",
        "",
        "## Readiness",
        "",
        f"- selected_token_status: `{latest.get('selected_token_status')}`",
        f"- selected_token_verified: `{str(latest.get('selected_token_verified') is True).lower()}`",
        f"- selected_token_fingerprint_sha256: `{latest.get('selected_token_fingerprint_sha256') or 'missing'}`",
        f"- signer_diagnostic_status: `{latest.get('signer_diagnostic_status')}`",
        f"- approval_contract_status: `{latest.get('approval_contract_status')}`",
        f"- signed_payload_dry_run_status: `{latest.get('signed_payload_dry_run_status')}`",
        f"- diagnostic_adapter_status: `{latest.get('diagnostic_adapter_status')}`",
        f"- ready_for_signed_payload_diagnostic: `{str(latest.get('ready_for_signed_payload_diagnostic') is True).lower()}`",
        "",
        "## Safety",
        "",
        "- this gate reads local JSON artifacts only",
        "- no private key, seed phrase, API secret, passphrase, wallet file, or browser wallet is read",
        "- no payload is signed or generated by this gate",
        "- no signed payload or signed order is printed, stored, or fingerprinted by this gate",
        "- no submit, cancel, authenticated trading write, scheduler, daemon, or background worker is available",
        "- readiness for a future diagnostic is not readiness for submit",
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"`{path}`" for path in paths.values()),
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
        "",
        "## Required False Flags",
        "",
        *bullet_lines(f"`{field}=false`" for field in REQUIRED_FALSE_FLAGS),
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "selected token payload readiness gate is no-submit/no-cancel/no-trading-write; "
            "unsupported live/auth/wallet/order flag(s): "
            + ", ".join(requested)
        )


def _select_first_existing_path(
    *,
    explicit_path: str | Path | None,
    default_paths: Sequence[Path],
) -> Path:
    if explicit_path:
        return Path(explicit_path)
    for path in default_paths:
        if path.exists() and path.is_file():
            return path
    return default_paths[0]


def _load_source_artifact(path: Path, label: str) -> dict[str, Any]:
    path_obj = Path(path)
    if not path_obj.exists() or not path_obj.is_file():
        return {
            "label": clean_text(label),
            "path": normalize_path(path_obj),
            "available": False,
            "payload": {},
            "errors": ["artifact_missing"],
        }
    try:
        payload = load_json_object(path_obj, label=label)
    except Exception as exc:
        return {
            "label": clean_text(label),
            "path": normalize_path(path_obj),
            "available": True,
            "payload": {},
            "errors": [f"artifact_unreadable:{type(exc).__name__}"],
        }
    return {
        "label": clean_text(label),
        "path": normalize_path(path_obj),
        "available": True,
        "payload": payload,
        "errors": [],
    }


def _source_artifact_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    return {
        "label": clean_text(source.get("label")),
        "path": clean_text(source.get("path")),
        "available": source.get("available") is True,
        "contract_version": clean_text(payload.get("contract_version")),
        "status": clean_text(payload.get("status")),
        "errors": [clean_text(item) for item in source.get("errors", [])],
        "payload_values_embedded": False,
    }


def _summarize_selected_token(
    *,
    selected_candidate_source: Mapping[str, Any],
    selection_source: Mapping[str, Any],
    resolver_source: Mapping[str, Any],
    market_symbol: str,
    strategy_name: str,
) -> dict[str, Any]:
    selected_candidate_payload = (
        dict(selected_candidate_source.get("payload", {}))
        if isinstance(selected_candidate_source.get("payload"), Mapping)
        else {}
    )
    selection_payload = (
        dict(selection_source.get("payload", {})) if isinstance(selection_source.get("payload"), Mapping) else {}
    )
    resolver_payload = (
        dict(resolver_source.get("payload", {})) if isinstance(resolver_source.get("payload"), Mapping) else {}
    )
    selection_token = _extract_token_id(selection_payload)
    resolver_token = _extract_token_id(resolver_payload)
    selected_token = selection_token or resolver_token
    selected_candidate_hash = clean_text(
        selected_candidate_payload.get("token_id_hash")
        or selected_candidate_payload.get("token_id_sha256")
        or selected_candidate_payload.get("selected_token_fingerprint_sha256")
    )
    selected_candidate_available = selected_candidate_source.get("available") is True
    selected_candidate_valid = (
        selected_candidate_available
        and clean_text(selected_candidate_payload.get("status") or "selected_candidate_artifact_recorded")
        in {"", "selected_candidate_artifact_recorded"}
        and selected_candidate_payload.get("selected_by_operator") is True
        and selected_candidate_payload.get("source_backed") is True
        and selected_candidate_payload.get("allowed_for_live") is False
        and selected_candidate_payload.get("selected_candidate_executable_for_live") is False
        and SHA256_HEX_PATTERN.fullmatch(selected_candidate_hash) is not None
    )
    token_format_valid = (
        _token_format_valid(selected_token, selection_payload, resolver_payload)
        if selected_token
        else selected_candidate_valid
    )
    selection_available = selection_source.get("available") is True
    resolver_available = resolver_source.get("available") is True
    selected_candidate_scope_matches = (
        _scope_matches(selected_candidate_payload, market_symbol, strategy_name)
        if selected_candidate_available
        else False
    )
    selection_scope_matches = (
        _scope_matches(selection_payload, market_symbol, strategy_name)
        if selection_available
        else selected_candidate_scope_matches
    )
    resolver_scope_matches = _scope_matches(resolver_payload, market_symbol, strategy_name) if resolver_available else False
    resolver_ready = (
        resolver_available
        and resolver_payload.get("token_id_present") is True
        and resolver_payload.get("token_id_format_valid") is True
        and _source_false_flags_ok(
            resolver_payload,
            (
                "allowed_for_live",
                "fake_token_id_generated",
                "token_id_generated",
                "order_payload_generated",
                "signed_payload_generated",
                "order_submission_enabled",
                "order_cancellation_enabled",
            ),
        )
    )
    if selected_candidate_hash and resolver_token:
        token_matches_resolver = _sha256_text(resolver_token) == selected_candidate_hash
    else:
        token_matches_resolver = not (selection_token and resolver_token) or selection_token == resolver_token
    operator_verified = selected_candidate_valid or (
        _operator_selection_verified(selection_payload) if selection_available else False
    )
    token_generation_safe = (
        _token_generation_safe(selected_candidate_payload)
        and _token_generation_safe(selection_payload)
        and _token_generation_safe(resolver_payload)
    )
    source_safety_flags_ok = (
        _source_false_flags_ok(
            selected_candidate_payload,
            (
                "allowed_for_live",
                "fake_token_id_generated",
                "token_id_generated",
                "order_payload_generated",
                "signed_payload_generated",
                "order_submission_enabled",
                "order_cancellation_enabled",
                "private_key_read",
                "selected_candidate_executable_for_live",
                "selected_candidate_submit_ready",
            ),
        )
        and _source_false_flags_ok(
            selection_payload,
            (
                "allowed_for_live",
                "fake_token_id_generated",
                "order_payload_generated",
                "signed_payload_generated",
                "order_submission_enabled",
                "order_cancellation_enabled",
                "private_key_read",
            ),
        )
        and _source_false_flags_ok(
            resolver_payload,
            (
                "allowed_for_live",
                "fake_token_id_generated",
                "order_payload_generated",
                "signed_payload_generated",
                "order_submission_enabled",
                "order_cancellation_enabled",
                "private_key_read",
            ),
        )
    )
    selected_token_present = bool(selected_token) or selected_candidate_valid
    verified = (
        selected_token_present
        and (selection_available or selected_candidate_valid)
        and operator_verified
        and resolver_ready
        and token_matches_resolver
        and token_format_valid
        and token_generation_safe
        and selection_scope_matches
        and resolver_scope_matches
        and source_safety_flags_ok
    )
    fingerprint = selected_candidate_hash if selected_candidate_valid else ""
    if not fingerprint and selected_token and token_format_valid:
        fingerprint = _sha256_text(selected_token)
    return {
        "selected_candidate_artifact_available": selected_candidate_available,
        "selected_candidate_artifact_path": clean_text(selected_candidate_source.get("path")),
        "selected_candidate_artifact_verified": selected_candidate_valid,
        "selection_packet_available": selection_available,
        "selection_packet_path": clean_text(selection_source.get("path")),
        "resolver_contract_available": resolver_available,
        "resolver_contract_path": clean_text(resolver_source.get("path")),
        "selection_contract_version": clean_text(selection_payload.get("contract_version")),
        "selection_status": clean_text(selection_payload.get("status")) or "missing",
        "resolver_contract_version": clean_text(resolver_payload.get("contract_version")),
        "resolver_status": clean_text(resolver_payload.get("status")) or "missing",
        "selected_token_present": selected_token_present,
        "selected_token_verified": verified,
        "operator_selection_verified": operator_verified,
        "resolver_token_ready": resolver_ready,
        "selection_scope_matches": selection_scope_matches,
        "resolver_scope_matches": resolver_scope_matches,
        "token_id_format_valid": token_format_valid,
        "token_matches_resolver": token_matches_resolver,
        "token_generation_safe": token_generation_safe,
        "selected_token_fingerprint_sha256": fingerprint,
        "raw_token_id_emitted": False,
        "source_safety_flags_ok": source_safety_flags_ok,
        "errors": [
            *[clean_text(item) for item in selected_candidate_source.get("errors", [])],
            *[clean_text(item) for item in selection_source.get("errors", [])],
            *[clean_text(item) for item in resolver_source.get("errors", [])],
        ],
    }


def _summarize_signer_diagnostic(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    diagnostic_status = clean_text(payload.get("diagnostic_status") or payload.get("status")) or "missing"
    source_safety_flags_ok = _source_false_flags_ok(
        payload,
        (
            "allowed_for_live",
            "order_payload_signing_enabled",
            "order_payload_signing_attempted",
            "order_submission_enabled",
            "order_cancellation_enabled",
            "private_key_value_emitted",
            "raw_private_key_emitted",
            "raw_secret_values_emitted",
            "raw_diagnostic_signature_emitted",
            "full_diagnostic_signature_emitted",
            "authenticated_trading_enabled",
            "authenticated_trading_call_performed",
        ),
    )
    diagnostic_ok = (
        source.get("available") is True
        and diagnostic_status == SIGNER_OK_STATUS
        and payload.get("diagnostic_challenge_signed") is True
        and source_safety_flags_ok
    )
    return {
        "available": source.get("available") is True,
        "path": clean_text(source.get("path")),
        "contract_version": clean_text(payload.get("contract_version")),
        "status": clean_text(payload.get("status")) or "missing",
        "diagnostic_status": diagnostic_status,
        "diagnostic_ok": diagnostic_ok,
        "diagnostic_challenge_status": "signed_diagnostic_challenge" if payload.get("diagnostic_challenge_signed") is True else "not_signed",
        "source_safety_flags_ok": source_safety_flags_ok,
        "raw_secret_values_emitted": False,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _summarize_approval_contract(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    source_safety_flags_ok = _source_false_flags_ok(
        payload,
        (
            "allowed_for_live",
            "live_execution_approved",
            "approval_consumed",
            "approval_contract_executable",
            "contract_can_execute",
            "real_execution_performed",
            "authenticated_trading_calls_made",
            "credential_values_read",
            "credential_values_serialized",
            "fill_or_pnl_recorded",
            "scheduler_or_daemon_allowed",
            "background_loop_allowed",
            "autonomous_repeat_allowed",
        ),
    )
    contract_defined = (
        source.get("available") is True
        and clean_text(payload.get("status")) == APPROVAL_DEFINED_STATUS
        and payload.get("approval_contract_executable") is False
        and payload.get("contract_can_execute") is False
        and payload.get("definition_only") is True
        and bool(clean_text(payload.get("required_approval_text")))
        and source_safety_flags_ok
    )
    return {
        "available": source.get("available") is True,
        "path": clean_text(source.get("path")),
        "contract_version": clean_text(payload.get("contract_version")),
        "status": clean_text(payload.get("status")) or "missing",
        "approval_contract_defined": contract_defined,
        "approval_contract_executable": False,
        "approval_required_before_future_execution": payload.get("approval_required_before_future_execution") is True,
        "no_approval_means_no_execution": payload.get("no_approval_means_no_execution") is True,
        "required_approval_text_present": bool(clean_text(payload.get("required_approval_text"))),
        "source_safety_flags_ok": source_safety_flags_ok,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _summarize_signed_payload_dry_run(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    fingerprint = clean_text(payload.get("payload_contract_fingerprint_sha256"))
    source_safety_flags_ok = _source_false_flags_ok(
        payload,
        (
            "allowed_for_live",
            "local_payload_signed",
            "local_payload_signing_attempted",
            "order_payload_signing_attempted",
            "signed_payload_generated",
            "signed_payload_submit_enabled",
            "signed_payload_submit_attempted",
            "signed_payload_submitted",
            "order_submission_enabled",
            "order_submission_attempted",
            "order_cancellation_enabled",
            "order_cancellation_attempted",
            "network_write_performed",
            "network_post_performed",
            "network_put_performed",
            "network_patch_performed",
            "network_delete_performed",
            "raw_signed_payload_emitted",
            "full_signed_payload_emitted",
            "raw_signed_order_emitted",
            "full_signed_order_emitted",
            "private_key_value_emitted",
            "raw_private_key_emitted",
            "raw_secret_values_emitted",
        ),
    )
    contract_ready = (
        source.get("available") is True
        and SHA256_HEX_PATTERN.fullmatch(fingerprint) is not None
        and source_safety_flags_ok
    )
    return {
        "available": source.get("available") is True,
        "path": clean_text(source.get("path")),
        "contract_version": clean_text(payload.get("contract_version")),
        "status": clean_text(payload.get("status")) or "missing",
        "local_signing_diagnostic_status": clean_text(payload.get("local_signing_diagnostic_status")) or "missing",
        "dry_run_contract_ready": contract_ready,
        "payload_contract_fingerprint_sha256": fingerprint,
        "source_safety_flags_ok": source_safety_flags_ok,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _summarize_diagnostic_adapter(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    source_safety_flags_ok = _source_false_flags_ok(
        payload,
        (
            "allowed_for_live",
            "order_payload_signing_attempted",
            "signed_payload_generated",
            "signed_payload_generation_attempted",
            "signed_payload_submit_enabled",
            "signed_payload_submit_attempted",
            "order_submission_enabled",
            "order_cancellation_enabled",
            "network_write_performed",
            "network_post_performed",
            "network_put_performed",
            "network_patch_performed",
            "network_delete_performed",
            "raw_signed_payload_emitted",
            "full_signed_payload_emitted",
            "private_key_read",
            "raw_private_key_emitted",
            "raw_secret_values_emitted",
        ),
    )
    return {
        "available": source.get("available") is True,
        "path": clean_text(source.get("path")),
        "contract_version": clean_text(payload.get("contract_version")),
        "status": clean_text(payload.get("status")) or "missing",
        "adapter_present": source.get("available") is True,
        "source_safety_flags_ok": source_safety_flags_ok,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _build_sources_artifact(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    source_artifacts: Mapping[str, Mapping[str, Any]],
    readiness_summaries: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_TOKEN_PAYLOAD_READINESS_SOURCES_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "source_artifacts": {
            key: _source_artifact_summary(source) for key, source in source_artifacts.items()
        },
        "readiness_summaries": {
            key: dict(summary) for key, summary in readiness_summaries.items()
        },
        "payload_values_embedded": False,
        "generated_at": generated_at,
    }
    value.update(selected_token_payload_readiness_safety_flags())
    return value


def _build_blockers_artifact(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    blockers: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SELECTED_TOKEN_PAYLOAD_READINESS_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "generated_at": generated_at,
    }
    value.update(selected_token_payload_readiness_safety_flags())
    return value


def _build_latest_status(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    readiness_summaries: Mapping[str, Mapping[str, Any]],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    selected_token = readiness_summaries["selected_token"]
    signer = readiness_summaries["signer_diagnostic"]
    approval = readiness_summaries["approval_contract"]
    dry_run = readiness_summaries["signed_payload_dry_run"]
    adapter = readiness_summaries["diagnostic_adapter"]
    value = {
        "contract_version": SELECTED_TOKEN_PAYLOAD_READINESS_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "ready_for_signed_payload_diagnostic": status == STATUS_READY,
        "selected_token_payload_ready_for_submit": False,
        "selected_token_status": "verified" if selected_token.get("selected_token_verified") is True else "blocked",
        "selected_token_present": selected_token.get("selected_token_present") is True,
        "selected_token_verified": selected_token.get("selected_token_verified") is True,
        "selected_token_fingerprint_sha256": clean_text(selected_token.get("selected_token_fingerprint_sha256")),
        "selected_candidate_artifact_available": selected_token.get("selected_candidate_artifact_available") is True,
        "selected_candidate_artifact_verified": selected_token.get("selected_candidate_artifact_verified") is True,
        "operator_selection_packet_available": selected_token.get("selection_packet_available") is True,
        "resolver_contract_available": selected_token.get("resolver_contract_available") is True,
        "signer_diagnostic_status": "ok" if signer.get("diagnostic_ok") is True else clean_text(signer.get("diagnostic_status")),
        "signer_diagnostic_artifact_available": signer.get("available") is True,
        "approval_contract_status": "defined" if approval.get("approval_contract_defined") is True else clean_text(approval.get("status")),
        "approval_contract_artifact_available": approval.get("available") is True,
        "signed_payload_dry_run_status": "ready" if dry_run.get("dry_run_contract_ready") is True else clean_text(dry_run.get("status")),
        "signed_payload_dry_run_artifact_available": dry_run.get("available") is True,
        "diagnostic_adapter_status": clean_text(adapter.get("status")) or "missing",
        "diagnostic_adapter_artifact_available": adapter.get("available") is True,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "live_execution": "blocked",
        "signing_by_default": "blocked",
        "order_submission": "blocked",
        "order_cancellation": "blocked",
        "trading_writes": "blocked",
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "sources_path": clean_text(artifact_paths.get("sources")),
        "blockers_path": clean_text(artifact_paths.get("blockers")),
        "safety_snapshot_path": clean_text(artifact_paths.get("safety_snapshot")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "operator_summary": _operator_summary(status),
        "generated_at": generated_at,
    }
    value.update(selected_token_payload_readiness_safety_flags())
    return value


def _build_blockers(
    readiness_summaries: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    selected_token = readiness_summaries["selected_token"]
    signer = readiness_summaries["signer_diagnostic"]
    approval = readiness_summaries["approval_contract"]
    dry_run = readiness_summaries["signed_payload_dry_run"]
    adapter = readiness_summaries["diagnostic_adapter"]
    blockers: list[dict[str, Any]] = []

    if selected_token.get("selected_token_present") is not True:
        blockers.append(
            _blocker(
                "selected_token_missing",
                "selected_token",
                "No selected source-backed token is available; the gate must not invent one.",
                generated_at=generated_at,
            )
        )
    elif selected_token.get("selected_token_verified") is not True:
        blockers.append(
            _blocker(
                "selected_token_unverified",
                "selected_token",
                "Selected token is present but is not operator-verified against the resolver contract.",
                generated_at=generated_at,
            )
        )

    if signer.get("available") is not True:
        blockers.append(
            _blocker(
                "signer_diagnostic_missing",
                "signer_diagnostic",
                "Guarded signer diagnostic status artifact is missing.",
                generated_at=generated_at,
            )
        )
    elif signer.get("diagnostic_ok") is not True:
        blockers.append(
            _blocker(
                "signer_diagnostic_not_ok",
                "signer_diagnostic",
                "Guarded signer diagnostic is missing, stale, or not diagnostic_ok.",
                generated_at=generated_at,
            )
        )

    if approval.get("available") is not True:
        blockers.append(
            _blocker(
                "approval_contract_missing",
                "approval_contract",
                "First live order approval contract status artifact is missing.",
                generated_at=generated_at,
            )
        )
    elif approval.get("approval_contract_defined") is not True:
        blockers.append(
            _blocker(
                "approval_contract_not_ready",
                "approval_contract",
                "Approval contract is present but is not a non-executable defined approval contract.",
                generated_at=generated_at,
            )
        )

    if dry_run.get("available") is not True:
        blockers.append(
            _blocker(
                "signed_payload_dry_run_missing",
                "signed_payload_dry_run",
                "Signed payload dry-run contract status artifact is missing.",
                generated_at=generated_at,
            )
        )
    elif dry_run.get("dry_run_contract_ready") is not True:
        blockers.append(
            _blocker(
                "signed_payload_dry_run_not_ready",
                "signed_payload_dry_run",
                "Signed payload dry-run contract is missing its safe non-executable fingerprint or safety flags.",
                generated_at=generated_at,
            )
        )

    if adapter.get("available") is True and adapter.get("source_safety_flags_ok") is not True:
        blockers.append(
            _blocker(
                "signed_payload_diagnostic_adapter_safety_not_ready",
                "signed_payload_diagnostic_adapter",
                "Signed payload diagnostic adapter source exists but does not report safe no-submit flags.",
                generated_at=generated_at,
            )
        )
    return blockers


def _status_for_summaries(readiness_summaries: Mapping[str, Mapping[str, Any]]) -> str:
    selected_token = readiness_summaries["selected_token"]
    signer = readiness_summaries["signer_diagnostic"]
    approval = readiness_summaries["approval_contract"]
    dry_run = readiness_summaries["signed_payload_dry_run"]
    adapter = readiness_summaries["diagnostic_adapter"]

    if selected_token.get("selected_token_present") is not True:
        return STATUS_BLOCKED_MISSING_SELECTED_TOKEN
    if selected_token.get("selected_token_verified") is not True:
        return STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN
    if signer.get("available") is not True:
        return STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC
    if signer.get("diagnostic_ok") is not True:
        return STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK
    if approval.get("available") is not True:
        return STATUS_BLOCKED_MISSING_APPROVAL_CONTRACT
    if approval.get("approval_contract_defined") is not True:
        return STATUS_BLOCKED_APPROVAL_CONTRACT_NOT_READY
    if dry_run.get("available") is not True:
        return STATUS_BLOCKED_MISSING_SIGNED_PAYLOAD_DRY_RUN
    if dry_run.get("dry_run_contract_ready") is not True:
        return STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY
    if adapter.get("available") is True and adapter.get("source_safety_flags_ok") is not True:
        return STATUS_BLOCKED_SOURCE_SAFETY_NOT_READY
    return STATUS_READY


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = {
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_signed_payload_diagnostic": True,
        "blocks_live_execution": True,
        "selected_token_payload_ready_for_submit": False,
        "generated_at": generated_at,
    }
    value.update(selected_token_payload_readiness_safety_flags())
    return value


def _extract_token_id(payload: Mapping[str, Any]) -> str:
    for field in (
        "selected_token_id",
        "selected_outcome_token_id",
        "operator_selected_token_id",
        "target_token_id",
        "token_id",
        "outcome_token_id",
    ):
        text = clean_text(payload.get(field))
        if text:
            return text
    target = payload.get("target_contract")
    if isinstance(target, Mapping):
        return _extract_token_id(target)
    selected = payload.get("selected_token")
    if isinstance(selected, Mapping):
        return _extract_token_id(selected)
    return ""


def _token_format_valid(token_id: str, *payloads: Mapping[str, Any]) -> bool:
    if not token_id or TOKEN_ID_PATTERN.fullmatch(token_id) is None:
        return False
    for payload in payloads:
        if "token_id_format_valid" in payload and payload.get("token_id_format_valid") is not True:
            return False
        if "token_id_format_status" in payload and clean_text(payload.get("token_id_format_status")) != "valid":
            return False
    return True


def _operator_selection_verified(payload: Mapping[str, Any]) -> bool:
    for field in (
        "selected_token_verified",
        "operator_verified",
        "operator_token_selection_verified",
        "selection_verified",
        "token_selection_verified",
        "selected_token_candidate_verified",
        "source_backed_token_verified",
        "verified",
    ):
        if field in payload:
            return payload.get(field) is True
    selected = payload.get("selected_token")
    if isinstance(selected, Mapping):
        return _operator_selection_verified(selected)
    return False


def _scope_matches(payload: Mapping[str, Any], market_symbol: str, strategy_name: str) -> bool:
    if not payload:
        return False
    market_value = clean_text(payload.get("market_symbol") or payload.get("market")).upper()
    strategy_value = clean_text(payload.get("strategy_name") or payload.get("strategy"))
    if market_value and market_value != market_symbol:
        return False
    if strategy_value and strategy_value != strategy_name:
        return False
    return True


def _token_generation_safe(payload: Mapping[str, Any]) -> bool:
    if not payload:
        return True
    for field in (
        "token_id_generated",
        "fake_token_id_generated",
        "fake_selected_token_id_generated",
        "placeholder_token_id_generated",
    ):
        if payload.get(field) is True:
            return False
    token_source = clean_text(payload.get("token_id_source")).lower()
    return not any(marker in token_source for marker in ("fake", "placeholder", "generated"))


def _source_false_flags_ok(payload: Mapping[str, Any], fields: Sequence[str]) -> bool:
    for field in fields:
        if field in payload and payload.get(field) is not False:
            return False
    return True


def _operator_summary(status: str) -> str:
    if status == STATUS_READY:
        return (
            "Local readiness artifacts are sufficient to proceed to a future signed payload diagnostic task. "
            "This gate still cannot sign payloads, submit orders, cancel orders, or enable live trading."
        )
    if status == STATUS_BLOCKED_MISSING_SELECTED_TOKEN:
        return "Readiness is blocked because no selected token is available and no token was invented."
    if status == STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN:
        return "Readiness is blocked because the selected token is not operator-verified against resolver evidence."
    if status == STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC:
        return "Readiness is blocked because the guarded signer diagnostic status artifact is missing."
    if status == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK:
        return "Readiness is blocked because the guarded signer diagnostic is not diagnostic_ok."
    if status == STATUS_BLOCKED_MISSING_APPROVAL_CONTRACT:
        return "Readiness is blocked because the approval contract artifact is missing."
    if status == STATUS_BLOCKED_APPROVAL_CONTRACT_NOT_READY:
        return "Readiness is blocked because the approval contract is not the expected non-executable definition."
    if status == STATUS_BLOCKED_MISSING_SIGNED_PAYLOAD_DRY_RUN:
        return "Readiness is blocked because the signed payload dry-run contract artifact is missing."
    if status == STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY:
        return "Readiness is blocked because the signed payload dry-run contract is not safe and complete."
    return "Readiness is blocked because one or more source safety flags are not acceptable."


def _sha256_text(value: str) -> str:
    return hashlib.sha256(clean_text(value).encode("utf-8")).hexdigest()


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
