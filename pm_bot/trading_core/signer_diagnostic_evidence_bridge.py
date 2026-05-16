from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.guarded_signer_diagnostic_models import DIAGNOSTIC_STATUS_DIAGNOSTIC_OK
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text
from pm_bot.trading_core.signer_diagnostic_evidence_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    MODE,
    REQUIRED_FALSE_FLAGS,
    SIGNER_DIAGNOSTIC_EVIDENCE_LATEST_STATUS_CONTRACT,
    SIGNER_DIAGNOSTIC_EVIDENCE_RESULT_CONTRACT,
    STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_FAILED,
    STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN,
    TASK_ID,
    SignerDiagnosticEvidenceSafetySnapshot,
    signer_diagnostic_evidence_safety_flags,
    validate_signer_diagnostic_evidence_result,
)

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "signer_diagnostic_evidence_bridge_076c"
DEFAULT_GUARDED_SIGNER_DIAGNOSTIC_PATHS = (
    DEFAULT_ARTIFACT_ROOT
    / "guarded_signer_diagnostic_smoke_069a"
    / "latest_guarded_signer_diagnostic_status_069a.json",
    DEFAULT_ARTIFACT_ROOT
    / "guarded_signer_diagnostic_smoke_069a"
    / "guarded_signer_diagnostic_smoke_069a_result.json",
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
    "--allow-private-key-diagnostic",
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

SOURCE_FALSE_FLAGS = (
    "allowed_for_live",
    "order_payload_signing_enabled",
    "order_payload_signing_attempted",
    "order_payload_signed",
    "order_payload_generated",
    "signed_order_generation_enabled",
    "signed_order_generation_attempted",
    "signed_order_generated",
    "signed_order_payload_generated",
    "signed_payload_generated",
    "raw_signed_payload_emitted",
    "full_signed_payload_emitted",
    "raw_signed_order_emitted",
    "full_signed_order_emitted",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "order_cancel_enabled",
    "order_cancel_attempted",
    "order_cancel_performed",
    "order_cancellation_enabled",
    "order_cancellation_attempted",
    "order_cancellation_performed",
    "authenticated_trading_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "authenticated_trading_call_performed",
    "wallet_connection_enabled",
    "wallet_connection_attempted",
    "wallet_enabled",
    "wallet_used",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "real_order_submitted",
    "real_order_cancelled",
    "private_key_value_emitted",
    "raw_private_key_emitted",
    "raw_secret_values_emitted",
    "full_diagnostic_signature_emitted",
    "raw_diagnostic_signature_emitted",
    "diagnostic_challenge_order_payload_fields_present",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)


def signer_diagnostic_evidence_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "signer_diagnostic_evidence_076c_result.json",
        "latest_status": root / "latest_signer_diagnostic_evidence_076c_status.json",
        "operator_md": root / "signer_diagnostic_evidence_076c_operator_summary.md",
    }


def run_signer_diagnostic_evidence_bridge(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    guarded_signer_diagnostic_path: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("signer diagnostic evidence bridge requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    artifact_root_path = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = signer_diagnostic_evidence_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    source_path = _select_source_path(
        artifact_root=artifact_root_path,
        explicit_path=guarded_signer_diagnostic_path,
    )
    source = _load_source_artifact(source_path)
    evidence_summary = _summarize_guarded_signer_diagnostic_source(
        source=source,
        market=market_symbol,
        strategy=strategy_name,
    )
    status = _status_for_evidence(evidence_summary)
    blockers = _build_blockers(status=status, evidence_summary=evidence_summary, generated_at=generated_at)
    safety_snapshot = SignerDiagnosticEvidenceSafetySnapshot(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    latest_status = _build_latest_status(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        evidence_summary=evidence_summary,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    result: dict[str, Any] = {
        "contract_version": SIGNER_DIAGNOSTIC_EVIDENCE_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "signer_diagnostic_evidence_status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "bridge_reads_local_artifacts_only": True,
        "bridge_executes_signer_diagnostic": False,
        "signer_diagnostic_executed_by_bridge": False,
        "signer_diagnostic_evidence_ok_for_payload_dry_run": (
            status == STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN
        ),
        "signer_ready_for_live": False,
        "signer_instantiated": False,
        "signer_instantiation_attempted": False,
        "order_submit_ready": False,
        "full_signed_payload_output": False,
        "signing_by_default": False,
        "live": False,
        "source_guarded_signer_diagnostic": _source_artifact_summary(source),
        "evidence_summary": evidence_summary,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary(status),
        "manual_diagnostic_command_suggestion": (
            "python -m pm_bot.operator_runner.guarded_signer_diagnostic_smoke "
            "--market BTC --strategy tiny-momentum --dry-run --allow-private-key-diagnostic"
        ),
        "generated_at": generated_at,
    }
    result.update(signer_diagnostic_evidence_safety_flags())
    result["status"] = status
    result["signer_diagnostic_evidence_status"] = status
    result["signer_diagnostic_evidence_ok_for_payload_dry_run"] = (
        status == STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN
    )
    result["validation"] = validate_signer_diagnostic_evidence_result(result)

    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_signer_diagnostic_evidence_markdown(result))
    return result


def render_signer_diagnostic_evidence_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    return "\n".join(
        [
            "Signer diagnostic evidence bridge 076C completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
            f"Source artifact available: {str(latest.get('source_artifact_available') is True).lower()}",
            f"Source diagnostic status: {clean_text(latest.get('source_diagnostic_status')) or 'missing'}",
            f"Evidence OK for payload dry-run: {str(value.get('signer_diagnostic_evidence_ok_for_payload_dry_run') is True).lower()}",
            "Signer ready for live: false",
            "Order submit ready: false",
            "Full signed payload output: false",
            "Allowed for live: false",
            f"Artifact: {clean_text(latest.get('artifact_path'))}",
        ]
    )


def render_signer_diagnostic_evidence_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    paths = dict(value.get("artifact_paths", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    summary = dict(value.get("evidence_summary", {}))
    lines = [
        "# PMBOT Signer Diagnostic Evidence Bridge 076C",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        "- Mode: `signer diagnostic evidence bridge / local artifact read-only / no-live`",
        "- signer_diagnostic_evidence_ok_for_payload_dry_run: "
        f"`{str(value.get('signer_diagnostic_evidence_ok_for_payload_dry_run') is True).lower()}`",
        "- signer_ready_for_live: `false`",
        "- order_submit_ready: `false`",
        "- full_signed_payload_output: `false`",
        "- allowed_for_live: `false`",
        "",
        "## Source Evidence",
        "",
        f"- source_artifact_available: `{str(latest.get('source_artifact_available') is True).lower()}`",
        f"- source_status: `{summary.get('source_status') or 'missing'}`",
        f"- source_diagnostic_status: `{summary.get('source_diagnostic_status') or 'missing'}`",
        f"- safe_non_order_challenge_evidence: `{summary.get('safe_non_order_challenge_evidence_status') or 'missing'}`",
        f"- source_safety_flags_ok: `{str(summary.get('source_safety_flags_ok') is True).lower()}`",
        f"- redacted_wallet_evidence_present: `{str(summary.get('redacted_wallet_evidence_present') is True).lower()}`",
        "",
        "## Safety",
        "",
        "- this bridge reads local JSON artifacts only",
        "- it does not read environment variables, secret files, wallets, or browser profiles",
        "- it does not instantiate a signer, sign payloads, generate orders, submit, cancel, or call authenticated endpoints",
        "- it does not store raw private keys, API secrets, passphrases, full signatures, or signed payloads",
        "- OK evidence is only for a future payload dry-run readiness gate, not for live execution",
        "",
        "## Manual Diagnostic Command",
        "",
        f"- `{value.get('manual_diagnostic_command_suggestion')}`",
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
            "signer diagnostic evidence bridge is local-artifact-only/no-live/no-submit; "
            "unsupported live/auth/wallet/sign/order/write/diagnostic flag(s): "
            + ", ".join(requested)
        )


def _select_source_path(*, artifact_root: Path, explicit_path: str | Path | None) -> Path:
    if explicit_path:
        return Path(explicit_path)
    first_default = Path("guarded_signer_diagnostic_smoke_069a/latest_guarded_signer_diagnostic_status_069a.json")
    for relative in (
        first_default,
        Path("guarded_signer_diagnostic_smoke_069a/guarded_signer_diagnostic_smoke_069a_result.json"),
    ):
        candidate = artifact_root / relative
        if candidate.exists() and candidate.is_file():
            return candidate
    return artifact_root / first_default


def _load_source_artifact(path: Path) -> dict[str, Any]:
    path_obj = Path(path)
    if not path_obj.exists() or not path_obj.is_file():
        return {
            "source_id": "guarded_signer_diagnostic_smoke_069a",
            "path": normalize_path(path_obj),
            "available": False,
            "payload": {},
            "status": "missing",
            "contract_version": "",
            "errors": ["artifact_missing"],
        }
    try:
        payload = load_json_object(path_obj, label="076C guarded signer diagnostic source")
    except Exception as exc:
        return {
            "source_id": "guarded_signer_diagnostic_smoke_069a",
            "path": normalize_path(path_obj),
            "available": False,
            "payload": {},
            "status": "unreadable",
            "contract_version": "",
            "errors": [f"artifact_unreadable:{type(exc).__name__}"],
        }
    return {
        "source_id": "guarded_signer_diagnostic_smoke_069a",
        "path": normalize_path(path_obj),
        "available": True,
        "payload": payload,
        "status": clean_text(payload.get("status")),
        "contract_version": clean_text(payload.get("contract_version")),
        "errors": [],
    }


def _source_artifact_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": clean_text(source.get("source_id")),
        "path": clean_text(source.get("path")),
        "available": source.get("available") is True,
        "contract_version": clean_text(source.get("contract_version")),
        "status": clean_text(source.get("status")),
        "errors": [clean_text(item) for item in source.get("errors", [])],
        "source_payload_embedded": False,
        "raw_secret_values_embedded": False,
    }


def _summarize_guarded_signer_diagnostic_source(
    *,
    source: Mapping[str, Any],
    market: str,
    strategy: str,
) -> dict[str, Any]:
    payload = dict(source.get("payload", {})) if isinstance(source.get("payload"), Mapping) else {}
    source_status = clean_text(payload.get("status")) or clean_text(source.get("status")) or "missing"
    source_diagnostic_status = clean_text(payload.get("diagnostic_status") or source_status) or "missing"
    source_available = source.get("available") is True
    source_safety_flags_ok = _source_false_flags_ok(payload, SOURCE_FALSE_FLAGS)
    scope_matches = _scope_matches(payload, market=market, strategy=strategy) if source_available else False
    challenge_not_order_payload = (
        payload.get("diagnostic_challenge_is_order_payload") is False
        or "diagnostic_challenge_is_order_payload" not in payload
    )
    safe_challenge_signed = payload.get("diagnostic_challenge_signed") is True
    diagnostic_requested = payload.get("diagnostic_requested") is True
    redacted_wallet = _redacted_wallet_evidence(payload)
    evidence_ok = (
        source_available
        and source_diagnostic_status == DIAGNOSTIC_STATUS_DIAGNOSTIC_OK
        and source_status == DIAGNOSTIC_STATUS_DIAGNOSTIC_OK
        and diagnostic_requested
        and safe_challenge_signed
        and challenge_not_order_payload
        and source_safety_flags_ok
        and scope_matches
        and payload.get("allowed_for_live") is False
    )
    return {
        "source_artifact_available": source_available,
        "source_path": clean_text(source.get("path")),
        "source_contract_version": clean_text(payload.get("contract_version")),
        "source_status": source_status,
        "source_diagnostic_status": source_diagnostic_status,
        "source_scope_matches": scope_matches,
        "source_diagnostic_requested": diagnostic_requested,
        "safe_non_order_challenge_evidence_status": (
            "signed_fixed_non_order_challenge"
            if safe_challenge_signed and challenge_not_order_payload
            else "not_signed_or_not_proven_safe"
        ),
        "source_dependency_status": clean_text(payload.get("dependency_status")) or "unknown",
        "source_block_reason": clean_text(payload.get("block_reason")),
        "redacted_wallet_evidence_present": bool(redacted_wallet),
        "redacted_wallet_evidence": redacted_wallet,
        "source_safety_flags_ok": source_safety_flags_ok,
        "signer_diagnostic_evidence_ok_for_payload_dry_run": evidence_ok,
        "source_payload_embedded": False,
        "raw_secret_values_embedded": False,
        "full_signed_payload_embedded": False,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _status_for_evidence(evidence_summary: Mapping[str, Any]) -> str:
    if evidence_summary.get("source_artifact_available") is not True:
        return STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE
    if evidence_summary.get("signer_diagnostic_evidence_ok_for_payload_dry_run") is True:
        return STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN
    return STATUS_BLOCKED_SIGNER_DIAGNOSTIC_FAILED


def _build_latest_status(
    *,
    status: str,
    market: str,
    strategy: str,
    evidence_summary: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SIGNER_DIAGNOSTIC_EVIDENCE_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "signer_diagnostic_evidence_status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": clean_text(market).upper(),
        "market_symbol": clean_text(market).upper(),
        "strategy": clean_text(strategy),
        "strategy_name": clean_text(strategy),
        "source_artifact_available": evidence_summary.get("source_artifact_available") is True,
        "source_status": clean_text(evidence_summary.get("source_status")),
        "source_diagnostic_status": clean_text(evidence_summary.get("source_diagnostic_status")),
        "source_scope_matches": evidence_summary.get("source_scope_matches") is True,
        "source_safety_flags_ok": evidence_summary.get("source_safety_flags_ok") is True,
        "signer_diagnostic_evidence_ok_for_payload_dry_run": (
            status == STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN
        ),
        "signer_ready_for_live": False,
        "order_submit_ready": False,
        "full_signed_payload_output": False,
        "signing_by_default": False,
        "live": False,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "operator_summary": _operator_summary(status),
        "generated_at": generated_at,
    }
    value.update(signer_diagnostic_evidence_safety_flags())
    value["status"] = clean_text(status)
    value["signer_diagnostic_evidence_status"] = clean_text(status)
    value["signer_diagnostic_evidence_ok_for_payload_dry_run"] = (
        status == STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN
    )
    return value


def _build_blockers(
    *,
    status: str,
    evidence_summary: Mapping[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if status == STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE:
        blockers.append(
            _blocker(
                "blocked_missing_signer_diagnostic_evidence",
                "signer_diagnostic_evidence",
                "No local guarded signer diagnostic artifact is available for the 076C evidence bridge.",
                generated_at=generated_at,
            )
        )
    elif status == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_FAILED:
        source_status = clean_text(evidence_summary.get("source_diagnostic_status")) or "missing"
        blockers.append(
            _blocker(
                "blocked_signer_diagnostic_failed",
                "signer_diagnostic_evidence",
                f"Guarded signer diagnostic evidence is present but not OK for payload dry-run: {source_status}.",
                generated_at=generated_at,
            )
        )
        if evidence_summary.get("source_safety_flags_ok") is not True:
            blockers.append(
                _blocker(
                    "blocked_signer_diagnostic_source_safety_flags",
                    "source_safety",
                    "Guarded signer diagnostic source did not preserve required no-live/no-submit safety flags.",
                    generated_at=generated_at,
                )
            )
    blockers.extend(
        [
            _blocker(
                "signer_diagnostic_evidence_not_live_approval",
                "live_execution",
                "076C signer diagnostic evidence is only for payload dry-run readiness; allowed_for_live=false remains enforced.",
                generated_at=generated_at,
            ),
            _blocker(
                "signer_not_ready_for_live",
                "signer",
                "signer_ready_for_live=false; this bridge cannot authorize live signer use.",
                generated_at=generated_at,
            ),
            _blocker(
                "order_submit_still_blocked",
                "submit",
                "order_submit_ready=false; this bridge cannot authorize order submission.",
                generated_at=generated_at,
            ),
        ]
    )
    return _dedupe_blockers(blockers)


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_signer_diagnostic_evidence_bridge_076c_blocker.v1",
        "task_id": TASK_ID,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
        "blocks_submit": True,
        "allowed_for_live": False,
        "signer_ready_for_live": False,
        "order_submit_ready": False,
        "full_signed_payload_output": False,
        "generated_at": generated_at,
    }
    value.update(signer_diagnostic_evidence_safety_flags())
    return value


def _operator_summary(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING_SIGNER_DIAGNOSTIC_EVIDENCE:
        return "Signer diagnostic evidence is missing; run the guarded diagnostic explicitly before this bridge can report OK."
    if status == STATUS_SIGNER_DIAGNOSTIC_EVIDENCE_OK_FOR_PAYLOAD_DRY_RUN:
        return (
            "Signer diagnostic evidence is OK for a future payload dry-run readiness gate only; "
            "live signer use, signing by default, submit, and cancel remain blocked."
        )
    return "Signer diagnostic evidence is present but failed or is not proven safe for payload dry-run."


def _scope_matches(payload: Mapping[str, Any], *, market: str, strategy: str) -> bool:
    market_value = clean_text(payload.get("market_symbol") or payload.get("market")).upper()
    strategy_value = clean_text(payload.get("strategy_name") or payload.get("strategy"))
    if market_value and market_value != clean_text(market).upper():
        return False
    if strategy_value and strategy_value != clean_text(strategy):
        return False
    return True


def _source_false_flags_ok(payload: Mapping[str, Any], fields: Sequence[str]) -> bool:
    for field in fields:
        if field in payload and payload.get(field) is not False:
            return False
    return True


def _redacted_wallet_evidence(payload: Mapping[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for source_key, output_key in (
        ("expected_wallet_address_redacted", "expected_wallet_address_redacted"),
        ("derived_wallet_address_redacted", "derived_wallet_address_redacted"),
    ):
        rendered = _safe_redacted_value(payload.get(source_key))
        if rendered:
            values[output_key] = rendered
    return values


def _safe_redacted_value(value: Any) -> str:
    text = clean_text(value)
    if not text or text in {"missing", "not_read", "not_derived"}:
        return text
    if "..." in text or text.startswith("redacted:"):
        return text
    return "present_redacted_value_not_embedded"


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
