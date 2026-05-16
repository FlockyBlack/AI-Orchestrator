from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text
from pm_bot.trading_core.signed_payload_diagnostic_adapter_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    EXECUTION_MODE,
    MODE,
    REQUIRED_FALSE_FLAGS,
    SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_CONTRACT,
    SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_LATEST_STATUS_CONTRACT,
    SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_RESULT_CONTRACT,
    STATUS_BLOCKED_FUTURE_SIGNING_NOT_IMPLEMENTED,
    STATUS_BLOCKED_MISSING_REQUIRED_ARTIFACTS,
    STATUS_BLOCKED_REQUIRED_FIELDS,
    STATUS_BLOCKED_TOKEN_SELECTION,
    STATUS_UNSIGNED_READY,
    TASK_ID,
    SignedPayloadDiagnosticAdapterRedactionPolicy,
    SignedPayloadDiagnosticAdapterSafetySnapshot,
    signed_payload_diagnostic_adapter_safety_flags,
    validate_signed_payload_diagnostic_adapter_result,
)

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/signed_payload_diagnostic_adapter_072e")
DEFAULT_ORDER_PREP_STATUS_PATH = Path(
    "pm_bot/trading_core/artifacts/telegram_order_prep_status_071e/latest_telegram_order_prep_status_071e.json"
)
DEFAULT_SIGNER_DIAGNOSTIC_STATUS_PATH = Path(
    "pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/latest_guarded_signer_diagnostic_status_069a.json"
)
DEFAULT_SIGNED_PAYLOAD_DRY_RUN_STATUS_PATH = Path(
    "pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/latest_signed_order_payload_dry_run_status_070a.json"
)
DEFAULT_TOKEN_CANDIDATE_PATHS = (
    Path("pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d/discovery_to_token_candidate_contract_071d.json"),
    Path("pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b/first_order_market_token_contract_070b.json"),
)

TOKEN_ID_PATTERN = re.compile(r"^[1-9][0-9]{0,77}$")

TOKEN_CANDIDATE_REQUIRED_FIELDS = (
    "contract_version",
    "status",
    "market_symbol",
    "strategy_name",
    "token_id_or_outcome_token_id",
    "token_id_format_status",
)
ORDER_PREP_REQUIRED_FIELDS = (
    "contract_version",
    "status",
    "allowed_for_live",
    "order_submission_enabled",
    "signed_payload_generated",
)
SIGNER_DIAGNOSTIC_REQUIRED_FIELDS = (
    "contract_version",
    "status",
    "diagnostic_status",
    "private_key_read",
    "diagnostic_challenge_signed",
    "allowed_for_live",
)
SIGNED_PAYLOAD_DRY_RUN_REQUIRED_FIELDS = (
    "contract_version",
    "status",
    "local_signing_diagnostic_status",
    "payload_contract_fingerprint_sha256",
    "signed_payload_generated",
    "allowed_for_live",
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
    "--sign",
    "--signing",
    "--submit",
    "--cancel",
    "--approve-live",
    "--private-key",
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
)


def signed_payload_diagnostic_adapter_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "signed_payload_diagnostic_adapter_072e_result.json",
        "latest_status": root / "latest_signed_payload_diagnostic_adapter_status_072e.json",
        "adapter_contract": root / "signed_payload_diagnostic_adapter_contract_072e.json",
        "redaction_policy": root / "signed_payload_diagnostic_adapter_redaction_policy_072e.json",
        "safety_snapshot": root / "signed_payload_diagnostic_adapter_safety_snapshot_072e.json",
        "operator_md": root / "signed_payload_diagnostic_adapter_operator_summary_072e.md",
    }


def run_signed_payload_diagnostic_adapter(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    token_candidate_path: str | Path | None = None,
    order_prep_artifact_path: str | Path | None = None,
    signer_diagnostic_status_path: str | Path | None = None,
    signed_payload_dry_run_status_path: str | Path | None = None,
    allow_future_signing_diagnostic: bool = False,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("signed payload diagnostic adapter requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = signed_payload_diagnostic_adapter_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    token_source_path = _select_token_candidate_path(token_candidate_path)
    source_artifacts = {
        "selected_token_candidate": _load_source_artifact(token_source_path, "selected token candidate"),
        "order_prep_status": _load_source_artifact(
            Path(order_prep_artifact_path) if order_prep_artifact_path else DEFAULT_ORDER_PREP_STATUS_PATH,
            "order prep status",
        ),
        "signer_diagnostic_status": _load_source_artifact(
            Path(signer_diagnostic_status_path)
            if signer_diagnostic_status_path
            else DEFAULT_SIGNER_DIAGNOSTIC_STATUS_PATH,
            "signer diagnostic status",
        ),
        "signed_payload_dry_run_status": _load_source_artifact(
            Path(signed_payload_dry_run_status_path)
            if signed_payload_dry_run_status_path
            else DEFAULT_SIGNED_PAYLOAD_DRY_RUN_STATUS_PATH,
            "signed payload dry-run status",
        ),
    }

    token_candidate = _summarize_token_candidate(
        source_artifacts["selected_token_candidate"],
        market_symbol=market_symbol,
        strategy_name=strategy_name,
    )
    order_prep = _summarize_order_prep(source_artifacts["order_prep_status"])
    signer_diagnostic = _summarize_signer_diagnostic(source_artifacts["signer_diagnostic_status"])
    payload_dry_run = _summarize_payload_dry_run(source_artifacts["signed_payload_dry_run_status"])
    blockers = _build_blockers(
        token_candidate=token_candidate,
        order_prep=order_prep,
        signer_diagnostic=signer_diagnostic,
        payload_dry_run=payload_dry_run,
        allow_future_signing_diagnostic=allow_future_signing_diagnostic,
        generated_at=generated_at,
    )
    status = _status_for_inputs(
        token_candidate=token_candidate,
        order_prep=order_prep,
        signer_diagnostic=signer_diagnostic,
        payload_dry_run=payload_dry_run,
        allow_future_signing_diagnostic=allow_future_signing_diagnostic,
    )
    redaction_policy = SignedPayloadDiagnosticAdapterRedactionPolicy(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    safety_snapshot = SignedPayloadDiagnosticAdapterSafetySnapshot(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    adapter_contract = _build_adapter_contract(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        token_candidate=token_candidate,
        order_prep=order_prep,
        signer_diagnostic=signer_diagnostic,
        payload_dry_run=payload_dry_run,
        blockers=blockers,
        allow_future_signing_diagnostic=allow_future_signing_diagnostic,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        token_candidate=token_candidate,
        order_prep=order_prep,
        signer_diagnostic=signer_diagnostic,
        payload_dry_run=payload_dry_run,
        blockers=blockers,
        artifact_paths=path_refs,
        allow_future_signing_diagnostic=allow_future_signing_diagnostic,
        generated_at=generated_at,
    )

    result: dict[str, Any] = {
        "contract_version": SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "dry_run": True,
        "unsigned_readiness_only": True,
        "local_artifact_read_only": True,
        "adapter_contract": adapter_contract,
        "redaction_policy": redaction_policy,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "source_artifacts": {
            key: _source_artifact_summary(value) for key, value in source_artifacts.items()
        },
        "token_candidate_summary": token_candidate,
        "order_prep_summary": order_prep,
        "signer_diagnostic_summary": signer_diagnostic,
        "signed_payload_dry_run_summary": payload_dry_run,
        "future_signing_requested": allow_future_signing_diagnostic is True,
        "future_signing_status": "not_implemented_blocked",
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary(status),
        "generated_at": generated_at,
    }
    result.update(signed_payload_diagnostic_adapter_safety_flags())
    result["validation"] = validate_signed_payload_diagnostic_adapter_result(result, generated_at=generated_at)

    write_json(paths["adapter_contract"], adapter_contract)
    write_json(paths["redaction_policy"], redaction_policy)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_signed_payload_diagnostic_adapter_markdown(result))
    return result


def render_signed_payload_diagnostic_adapter_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Signed payload diagnostic adapter 072E completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Unsigned readiness only: {str(value.get('unsigned_readiness_only') is True).lower()}",
            f"Token candidate: {clean_text(value.get('token_candidate_status'))}",
            f"Token id present: {str(value.get('token_id_present') is True).lower()}",
            f"Signer diagnostic: {clean_text(value.get('signer_diagnostic_status'))}",
            f"Signed payload dry-run: {clean_text(value.get('signed_payload_dry_run_status'))}",
            f"Future signing: {clean_text(value.get('future_signing_status'))}",
            "Private key read: false",
            "Order payload signing attempted: false",
            "Signed payload generated: false",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Trading writes: blocked",
            "Allowed for live: false",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_signed_payload_diagnostic_adapter_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    paths = dict(value.get("artifact_paths", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Signed Payload Diagnostic Adapter 072E",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `signed payload diagnostic adapter / dry-run / unsigned-readiness / no-submit`",
        "- unsigned_readiness_only: `true`",
        "- allowed_for_live: `false`",
        "",
        "## Interface Readiness",
        "",
        f"- token_candidate_status: `{latest.get('token_candidate_status')}`",
        f"- token_id_present: `{str(latest.get('token_id_present') is True).lower()}`",
        f"- token_id_fingerprint_sha256: `{latest.get('token_id_fingerprint_sha256') or 'missing'}`",
        f"- order_prep_status: `{latest.get('order_prep_status')}`",
        f"- signer_diagnostic_status: `{latest.get('signer_diagnostic_status')}`",
        f"- signed_payload_dry_run_status: `{latest.get('signed_payload_dry_run_status')}`",
        f"- future_signing_status: `{latest.get('future_signing_status')}`",
        "",
        "## Safety",
        "",
        "- no private key, seed phrase, API secret, passphrase, wallet file, or browser wallet is read",
        "- no order payload is generated or made executable",
        "- no order payload signing is attempted",
        "- no signed payload or signed order is printed, stored, or fingerprinted",
        "- no order submission or cancellation is available",
        "- no network trading write is performed",
        "- future signing remains not implemented and blocked pending a separate approved task",
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
            "signed payload diagnostic adapter is no-submit/no-cancel/no-trading-write; "
            "unsupported live/auth/wallet/order flag(s): "
            + ", ".join(requested)
        )


def _select_token_candidate_path(explicit_path: str | Path | None) -> Path:
    if explicit_path:
        return Path(explicit_path)
    for path in DEFAULT_TOKEN_CANDIDATE_PATHS:
        if path.exists() and path.is_file():
            return path
    return DEFAULT_TOKEN_CANDIDATE_PATHS[0]


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


def _summarize_token_candidate(
    source: Mapping[str, Any],
    *,
    market_symbol: str,
    strategy_name: str,
) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    token_id = clean_text(payload.get("token_id") or payload.get("outcome_token_id"))
    format_status = clean_text(payload.get("token_id_format_status"))
    if not format_status:
        format_status = "valid" if TOKEN_ID_PATTERN.fullmatch(token_id) else "missing_required"
    missing = _missing_fields(
        payload,
        TOKEN_CANDIDATE_REQUIRED_FIELDS,
        aliases={"token_id_or_outcome_token_id": ("token_id", "outcome_token_id")},
    )
    scope_matches = (
        clean_text(payload.get("market_symbol") or payload.get("market")).upper() == market_symbol
        and clean_text(payload.get("strategy_name")) == strategy_name
    )
    token_format_valid = format_status == "valid" and TOKEN_ID_PATTERN.fullmatch(token_id) is not None
    safety_ok = _source_false_flags_ok(
        payload,
        (
            "allowed_for_live",
            "order_payload_generated",
            "signed_payload_generated",
            "order_submission_enabled",
            "order_cancellation_enabled",
            "private_key_read",
        ),
    )
    ready = (
        source.get("available") is True
        and not missing
        and scope_matches
        and bool(token_id)
        and token_format_valid
        and safety_ok
    )
    return {
        "available": source.get("available") is True,
        "path": clean_text(source.get("path")),
        "contract_version": clean_text(payload.get("contract_version")),
        "status": clean_text(payload.get("status")) or "missing",
        "required_fields": list(TOKEN_CANDIDATE_REQUIRED_FIELDS),
        "missing_required_fields": missing,
        "required_fields_present": not missing,
        "scope_matches": scope_matches,
        "token_id_present": bool(token_id),
        "token_id_format_status": format_status,
        "token_id_format_valid": token_format_valid,
        "token_id_fingerprint_sha256": _sha256_text(token_id) if token_id and token_format_valid else "",
        "token_id_source": clean_text(payload.get("token_id_source")) or "unknown",
        "raw_token_id_emitted": False,
        "selected_token_candidate_ready": ready,
        "source_safety_flags_ok": safety_ok,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _summarize_order_prep(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    missing = _missing_fields(payload, ORDER_PREP_REQUIRED_FIELDS)
    safety_ok = _source_false_flags_ok(
        payload,
        (
            "allowed_for_live",
            "order_submission_enabled",
            "order_submission_attempted",
            "signed_payload_generated",
            "signing_attempted",
            "private_key_read",
        ),
    )
    return {
        "available": source.get("available") is True,
        "path": clean_text(source.get("path")),
        "contract_version": clean_text(payload.get("contract_version")),
        "status": clean_text(payload.get("status")) or "missing",
        "required_fields": list(ORDER_PREP_REQUIRED_FIELDS),
        "missing_required_fields": missing,
        "required_fields_present": not missing,
        "market_found": payload.get("market_found") is True,
        "token_id_found": payload.get("token_id_found") is True,
        "signature_contract_ready": payload.get("signature_contract_ready") is True,
        "source_safety_flags_ok": safety_ok,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _summarize_signer_diagnostic(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    missing = _missing_fields(payload, SIGNER_DIAGNOSTIC_REQUIRED_FIELDS)
    safety_ok = _source_false_flags_ok(
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
        ),
    )
    source_explicit_diagnostic_used_sensitive_path = payload.get("private_key_read") is True
    default_no_key_read = source_explicit_diagnostic_used_sensitive_path is False
    return {
        "available": source.get("available") is True,
        "path": clean_text(source.get("path")),
        "contract_version": clean_text(payload.get("contract_version")),
        "status": clean_text(payload.get("status")) or "missing",
        "diagnostic_status": clean_text(payload.get("diagnostic_status")) or "missing",
        "required_fields": list(SIGNER_DIAGNOSTIC_REQUIRED_FIELDS),
        "missing_required_fields": missing,
        "required_fields_present": not missing,
        "private_key_read": False,
        "source_explicit_diagnostic_used_sensitive_path": source_explicit_diagnostic_used_sensitive_path,
        "diagnostic_challenge_signed": payload.get("diagnostic_challenge_signed") is True,
        "default_no_key_read": default_no_key_read,
        "source_safety_flags_ok": safety_ok,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _summarize_payload_dry_run(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    missing = _missing_fields(payload, SIGNED_PAYLOAD_DRY_RUN_REQUIRED_FIELDS)
    safety_ok = _source_false_flags_ok(
        payload,
        (
            "allowed_for_live",
            "order_payload_contract_executable",
            "order_payload_signing_attempted",
            "signed_payload_generated",
            "signed_payload_submit_enabled",
            "order_submission_enabled",
            "order_cancellation_enabled",
            "private_key_read",
            "raw_signed_payload_emitted",
            "full_signed_payload_emitted",
        ),
    )
    return {
        "available": source.get("available") is True,
        "path": clean_text(source.get("path")),
        "contract_version": clean_text(payload.get("contract_version")),
        "status": clean_text(payload.get("status")) or "missing",
        "local_signing_diagnostic_status": clean_text(payload.get("local_signing_diagnostic_status")) or "missing",
        "required_fields": list(SIGNED_PAYLOAD_DRY_RUN_REQUIRED_FIELDS),
        "missing_required_fields": missing,
        "required_fields_present": not missing,
        "token_id_present": payload.get("token_id_present") is True,
        "payload_contract_fingerprint_sha256": clean_text(payload.get("payload_contract_fingerprint_sha256")),
        "source_safety_flags_ok": safety_ok,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _build_adapter_contract(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    token_candidate: Mapping[str, Any],
    order_prep: Mapping[str, Any],
    signer_diagnostic: Mapping[str, Any],
    payload_dry_run: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    allow_future_signing_diagnostic: bool,
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "adapter_scope": "token_selection_to_signer_diagnostic_to_signed_payload_dry_run_interface",
        "unsigned_readiness_only": True,
        "contract_only": True,
        "adapter_executable": False,
        "token_candidate": dict(token_candidate),
        "order_prep": dict(order_prep),
        "signer_diagnostic": dict(signer_diagnostic),
        "signed_payload_dry_run": dict(payload_dry_run),
        "required_interfaces": [
            _required_interface("selected_token_candidate", TOKEN_CANDIDATE_REQUIRED_FIELDS, token_candidate),
            _required_interface("order_prep_status", ORDER_PREP_REQUIRED_FIELDS, order_prep),
            _required_interface("signer_diagnostic_status", SIGNER_DIAGNOSTIC_REQUIRED_FIELDS, signer_diagnostic),
            _required_interface(
                "signed_payload_dry_run_status",
                SIGNED_PAYLOAD_DRY_RUN_REQUIRED_FIELDS,
                payload_dry_run,
            ),
        ],
        "future_signing_requested": allow_future_signing_diagnostic is True,
        "future_signing_status": "not_implemented_blocked",
        "future_signing_implemented": False,
        "separate_future_operator_approval_required": True,
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "adapter_contract_fingerprint_sha256": _stable_hash(
            {
                "contract_version": SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_CONTRACT,
                "status": clean_text(status),
                "market_symbol": market_symbol,
                "strategy_name": strategy_name,
                "token_id_present": token_candidate.get("token_id_present") is True,
                "token_id_fingerprint_sha256": clean_text(token_candidate.get("token_id_fingerprint_sha256")),
                "future_signing_requested": allow_future_signing_diagnostic is True,
            }
        ),
        "generated_at": generated_at,
    }
    value.update(signed_payload_diagnostic_adapter_safety_flags())
    return value


def _build_latest_status(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    token_candidate: Mapping[str, Any],
    order_prep: Mapping[str, Any],
    signer_diagnostic: Mapping[str, Any],
    payload_dry_run: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    allow_future_signing_diagnostic: bool,
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SIGNED_PAYLOAD_DIAGNOSTIC_ADAPTER_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "unsigned_readiness_only": True,
        "token_candidate_status": "ready" if token_candidate.get("selected_token_candidate_ready") is True else "blocked",
        "token_candidate_artifact_available": token_candidate.get("available") is True,
        "token_id_present": token_candidate.get("token_id_present") is True,
        "token_id_format_valid": token_candidate.get("token_id_format_valid") is True,
        "token_id_fingerprint_sha256": clean_text(token_candidate.get("token_id_fingerprint_sha256")),
        "order_prep_status": clean_text(order_prep.get("status")) or "missing",
        "order_prep_artifact_available": order_prep.get("available") is True,
        "signer_diagnostic_status": clean_text(signer_diagnostic.get("diagnostic_status")) or "missing",
        "signer_diagnostic_artifact_available": signer_diagnostic.get("available") is True,
        "private_key_read": False,
        "diagnostic_challenge_signed": signer_diagnostic.get("diagnostic_challenge_signed") is True,
        "signed_payload_dry_run_status": clean_text(payload_dry_run.get("local_signing_diagnostic_status")) or "missing",
        "signed_payload_dry_run_artifact_available": payload_dry_run.get("available") is True,
        "future_signing_requested": allow_future_signing_diagnostic is True,
        "future_signing_status": "not_implemented_blocked",
        "future_signing_implemented": False,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "live_execution": "blocked",
        "order_payload_signing": "blocked",
        "signed_payload_generation": "blocked",
        "order_submission": "blocked",
        "order_cancellation": "blocked",
        "trading_writes": "blocked",
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "adapter_contract_path": clean_text(artifact_paths.get("adapter_contract")),
        "redaction_policy_path": clean_text(artifact_paths.get("redaction_policy")),
        "safety_snapshot_path": clean_text(artifact_paths.get("safety_snapshot")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "operator_summary": _operator_summary(status),
        "generated_at": generated_at,
    }
    value.update(signed_payload_diagnostic_adapter_safety_flags())
    return value


def _required_interface(
    interface_name: str,
    required_fields: Sequence[str],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "interface_name": clean_text(interface_name),
        "required_fields": [clean_text(field) for field in required_fields],
        "artifact_available": summary.get("available") is True,
        "required_fields_present": summary.get("required_fields_present") is True,
        "missing_required_fields": [clean_text(field) for field in summary.get("missing_required_fields", [])],
        "source_safety_flags_ok": summary.get("source_safety_flags_ok") is True,
    }


def _status_for_inputs(
    *,
    token_candidate: Mapping[str, Any],
    order_prep: Mapping[str, Any],
    signer_diagnostic: Mapping[str, Any],
    payload_dry_run: Mapping[str, Any],
    allow_future_signing_diagnostic: bool,
) -> str:
    if allow_future_signing_diagnostic is True:
        return STATUS_BLOCKED_FUTURE_SIGNING_NOT_IMPLEMENTED
    summaries = (token_candidate, order_prep, signer_diagnostic, payload_dry_run)
    if any(summary.get("available") is not True for summary in summaries):
        return STATUS_BLOCKED_MISSING_REQUIRED_ARTIFACTS
    if any(summary.get("required_fields_present") is not True for summary in summaries):
        return STATUS_BLOCKED_REQUIRED_FIELDS
    if token_candidate.get("selected_token_candidate_ready") is not True:
        return STATUS_BLOCKED_TOKEN_SELECTION
    if any(summary.get("source_safety_flags_ok") is not True for summary in summaries):
        return STATUS_BLOCKED_REQUIRED_FIELDS
    return STATUS_UNSIGNED_READY


def _build_blockers(
    *,
    token_candidate: Mapping[str, Any],
    order_prep: Mapping[str, Any],
    signer_diagnostic: Mapping[str, Any],
    payload_dry_run: Mapping[str, Any],
    allow_future_signing_diagnostic: bool,
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    source_summaries = (
        ("selected_token_candidate", token_candidate),
        ("order_prep_status", order_prep),
        ("signer_diagnostic_status", signer_diagnostic),
        ("signed_payload_dry_run_status", payload_dry_run),
    )
    for name, summary in source_summaries:
        if summary.get("available") is not True:
            blockers.append(
                _blocker(
                    f"{name}_missing",
                    "local_artifact",
                    f"Required local artifact is missing for {name}.",
                    generated_at=generated_at,
                )
            )
        if summary.get("missing_required_fields"):
            missing = ", ".join(clean_text(field) for field in summary.get("missing_required_fields", []))
            blockers.append(
                _blocker(
                    f"{name}_required_fields_missing",
                    "schema",
                    f"Required field(s) missing in {name}: {missing}.",
                    generated_at=generated_at,
                )
            )
        if summary.get("source_safety_flags_ok") is False:
            blockers.append(
                _blocker(
                    f"{name}_safety_flags_not_ready",
                    "safety",
                    f"Source artifact safety flags are not acceptable for {name}.",
                    generated_at=generated_at,
                )
            )
    if token_candidate.get("scope_matches") is False:
        blockers.append(
            _blocker(
                "selected_token_candidate_scope_mismatch",
                "scope",
                "Selected token candidate does not match BTC/tiny-momentum scope.",
                generated_at=generated_at,
            )
        )
    if token_candidate.get("token_id_present") is not True:
        blockers.append(
            _blocker(
                "selected_token_candidate_missing_token_id",
                "token_id",
                "No selected source-backed token_id is available; the adapter must not invent one.",
                generated_at=generated_at,
            )
        )
    elif token_candidate.get("token_id_format_valid") is not True:
        blockers.append(
            _blocker(
                "selected_token_candidate_invalid_token_id",
                "token_id",
                "Selected token_id format is not valid for diagnostic readiness.",
                generated_at=generated_at,
            )
        )
    if allow_future_signing_diagnostic is True:
        blockers.append(
            _blocker(
                "future_signing_not_implemented",
                "signing",
                "Future signed payload diagnostic implementation is intentionally blocked in 072E.",
                generated_at=generated_at,
            )
        )
    blockers.extend(
        [
            _blocker(
                "live_execution_blocked",
                "live_execution",
                "allowed_for_live=false and this task does not authorize live execution.",
                generated_at=generated_at,
            ),
            _blocker(
                "signing_blocked",
                "signing",
                "Order payload signing and signed payload generation remain blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "submission_and_cancel_blocked",
                "submission",
                "Order submission and cancellation remain blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "trading_writes_blocked",
                "trading_write",
                "Network trading writes are not available in this adapter.",
                generated_at=generated_at,
            ),
        ]
    )
    return blockers


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
    value.update(signed_payload_diagnostic_adapter_safety_flags())
    return value


def _missing_fields(
    payload: Mapping[str, Any],
    fields: Sequence[str],
    *,
    aliases: Mapping[str, Sequence[str]] | None = None,
) -> list[str]:
    alias_map = dict(aliases or {})
    missing: list[str] = []
    for field in fields:
        alias_fields = alias_map.get(field, (field,))
        if not any(alias in payload for alias in alias_fields):
            missing.append(clean_text(field))
    return missing


def _source_false_flags_ok(payload: Mapping[str, Any], fields: Sequence[str]) -> bool:
    for field in fields:
        if field in payload and payload.get(field) is not False:
            return False
    return True


def _operator_summary(status: str) -> str:
    if status == STATUS_UNSIGNED_READY:
        return (
            "Unsigned readiness is prepared from local artifacts only. No private key was read, no payload was "
            "signed, no signed material was emitted, and no submit/cancel/write path is available."
        )
    if status == STATUS_BLOCKED_MISSING_REQUIRED_ARTIFACTS:
        return "Adapter blocked because one or more required local source artifacts are missing."
    if status == STATUS_BLOCKED_REQUIRED_FIELDS:
        return "Adapter blocked because required source fields or source safety flags are not ready."
    if status == STATUS_BLOCKED_FUTURE_SIGNING_NOT_IMPLEMENTED:
        return "Future signing diagnostic was requested, but 072E intentionally leaves signing not implemented."
    return "Adapter blocked because a selected source-backed token candidate is not ready."


def _sha256_text(value: str) -> str:
    return hashlib.sha256(clean_text(value).encode("utf-8")).hexdigest()


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
