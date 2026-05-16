from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.payload_dry_run_readiness_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    MODE,
    PAYLOAD_DRY_RUN_READINESS_BLOCKERS_CONTRACT,
    PAYLOAD_DRY_RUN_READINESS_LATEST_STATUS_CONTRACT,
    PAYLOAD_DRY_RUN_READINESS_RESULT_CONTRACT,
    PayloadDryRunReadinessConfig,
    STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE,
    STATUS_BLOCKED_RISK_ENGINE_REVIEW,
    STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
    STATUS_READY_FOR_OPERATOR_REVIEW,
    TASK_ID,
    payload_dry_run_readiness_safety_flags,
    validate_payload_dry_run_readiness_result,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "payload_dry_run_readiness_076d"

STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN = "selected_token_verified_for_payload_dry_run"
STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED = "selected_candidate_artifact_recorded"
STATUS_SELECTED_TOKEN_PAYLOAD_READY = "ready_for_signed_payload_diagnostic"
STATUS_SIGNED_PAYLOAD_ADAPTER_READY = "unsigned_diagnostic_readiness_ready_no_signing"
STATUS_ORDER_PREP_READY = "order_prep_packet_ready_for_operator_review_non_executable"
STATUS_RISK_ENGINE_PASSED = "passed_review_check_no_live"
STATUS_STATIC_SAFETY_PASSED = {"passed", "passed_with_warnings"}

SOURCE_CANDIDATES: dict[str, tuple[Path, ...]] = {
    "local_real_check_bundle_072c": (
        Path("local_real_check_bundle_072c/latest_local_real_check_bundle_status_072c.json"),
        Path("local_real_check_bundle_072c/local_real_check_bundle_072c_result.json"),
    ),
    "local_real_check_snapshot_073a": (
        Path("local_real_check_snapshot_073a/latest_local_real_check_snapshot_status_073a.json"),
        Path("local_real_check_snapshot_073a/local_real_check_snapshot_073a_result.json"),
    ),
    "operator_token_selection_packet_073b": (
        Path("operator_token_selection_packet_073b/latest_operator_token_selection_status_073b.json"),
        Path("operator_token_selection_packet_073b/operator_token_selection_packet_073b_result.json"),
        Path("operator_token_selection_packet_073b/operator_token_selection_packet_073b.json"),
    ),
    "selected_candidate_artifact_075d": (
        Path("selected_candidate_artifact_075d/latest_selected_candidate_artifact_075d.json"),
        Path("selected_candidate_artifact_075d/selected_candidate_artifact_075d.json"),
        Path("selected_candidate_artifact_075d/selected_candidate_artifact_075d_result.json"),
    ),
    "selected_token_verification_bridge_076a": (
        Path("selected_token_verification_bridge_076a/latest_selected_token_verification_076a_status.json"),
        Path("selected_token_verification_bridge_076a/selected_token_verification_076a_result.json"),
        Path("selected_token_verification_bridge_076a/selected_token_verification_076a_evidence.json"),
    ),
    "signer_diagnostic_evidence_bridge_076c": (
        Path("signer_diagnostic_evidence_bridge_076c/latest_signer_diagnostic_evidence_bridge_076c_status.json"),
        Path("signer_diagnostic_evidence_bridge_076c/latest_signer_diagnostic_evidence_076c_status.json"),
        Path("signer_diagnostic_evidence_bridge_076c/signer_diagnostic_evidence_bridge_076c_result.json"),
        Path("signer_diagnostic_evidence_bridge_076c/signer_diagnostic_evidence_076c_result.json"),
    ),
    "guarded_signer_diagnostic_smoke_069a": (
        Path("guarded_signer_diagnostic_smoke_069a/latest_guarded_signer_diagnostic_status_069a.json"),
        Path("guarded_signer_diagnostic_smoke_069a/guarded_signer_diagnostic_smoke_069a_result.json"),
    ),
    "selected_token_payload_readiness_gate_073c": (
        Path("selected_token_payload_readiness_gate_073c/latest_selected_token_payload_readiness_status_073c.json"),
        Path("selected_token_payload_readiness_gate_073c/selected_token_payload_readiness_gate_073c_result.json"),
    ),
    "signed_order_payload_dry_run_070a": (
        Path("signed_order_payload_dry_run_070a/latest_signed_order_payload_dry_run_status_070a.json"),
        Path("signed_order_payload_dry_run_070a/signed_order_payload_dry_run_070a_result.json"),
    ),
    "signed_payload_diagnostic_adapter_072e": (
        Path("signed_payload_diagnostic_adapter_072e/latest_signed_payload_diagnostic_adapter_status_072e.json"),
        Path("signed_payload_diagnostic_adapter_072e/signed_payload_diagnostic_adapter_072e_result.json"),
    ),
    "order_prep_packet_072a": (
        Path("order_prep_packet_072a/latest_order_prep_packet_status_072a.json"),
        Path("order_prep_packet_072a/order_prep_packet_072a_result.json"),
    ),
    "risk_engine_v2_074d": (
        Path("risk_engine_v2_074d/latest_risk_engine_v2_074d_status.json"),
        Path("risk_engine_v2_074d/risk_engine_v2_074d_result.json"),
    ),
    "first_live_order_final_blocker_reducer_072d": (
        Path("first_live_order_final_blocker_reducer_072d/latest_first_live_order_final_blockers_072d.json"),
        Path("first_live_order_final_blocker_reducer_072d/first_live_order_final_blocker_reducer_072d_result.json"),
    ),
    "static_safety_invariant_report_060q": (
        Path("static_safety_invariant_report_060q/latest_static_safety_invariant_report_status_060q.json"),
        Path("static_safety_invariant_report_060q/static_safety_invariant_report_060q_result.json"),
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

UNSAFE_TRUE_FIELDS = (
    "allowed_for_live",
    "live_ready",
    "submit_ready",
    "order_submission_enabled",
    "order_submission_performed",
    "order_cancellation_enabled",
    "order_cancellation_performed",
    "signing_by_default",
    "signing_enabled",
    "signing_performed",
    "signer_instantiated_by_default",
    "wallet_connected",
    "wallet_connection_enabled",
    "full_signed_payload_output",
    "full_signed_order_output",
    "raw_signed_payload_emitted",
    "raw_signed_order_emitted",
    "real_order_submitted",
    "real_order_cancelled",
    "live_trading_enabled",
    "background_worker_added",
    "scheduler_or_daemon_added",
    "autonomous_live_trading_added",
    "fake_balances_emitted",
    "fake_orders_emitted",
    "fake_fills_emitted",
    "fake_pnl_emitted",
)


def payload_dry_run_readiness_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "payload_dry_run_readiness_076d_result.json",
        "latest_status": root / "latest_payload_dry_run_readiness_076d_status.json",
        "blockers": root / "payload_dry_run_readiness_076d_blockers.json",
        "operator_md": root / "payload_dry_run_readiness_076d_operator_summary.md",
    }


def run_payload_dry_run_readiness_review(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    local_real_check_bundle_path: str | Path | None = None,
    local_real_check_snapshot_path: str | Path | None = None,
    operator_token_selection_packet_path: str | Path | None = None,
    selected_candidate_artifact_path: str | Path | None = None,
    selected_token_verification_bridge_path: str | Path | None = None,
    signer_diagnostic_evidence_bridge_path: str | Path | None = None,
    selected_token_payload_readiness_gate_path: str | Path | None = None,
    signed_order_payload_dry_run_path: str | Path | None = None,
    signed_payload_diagnostic_adapter_path: str | Path | None = None,
    order_prep_packet_path: str | Path | None = None,
    risk_engine_v2_path: str | Path | None = None,
    final_blocker_reducer_path: str | Path | None = None,
    static_safety_report_path: str | Path | None = None,
    generated_at: str = GENERATED_AT,
    head_before: str = "",
    head_after: str = "",
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("payload dry-run readiness review requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    source_root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = payload_dry_run_readiness_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    explicit_paths = {
        "local_real_check_bundle_072c": local_real_check_bundle_path,
        "local_real_check_snapshot_073a": local_real_check_snapshot_path,
        "operator_token_selection_packet_073b": operator_token_selection_packet_path,
        "selected_candidate_artifact_075d": selected_candidate_artifact_path,
        "selected_token_verification_bridge_076a": selected_token_verification_bridge_path,
        "signer_diagnostic_evidence_bridge_076c": signer_diagnostic_evidence_bridge_path,
        "selected_token_payload_readiness_gate_073c": selected_token_payload_readiness_gate_path,
        "signed_order_payload_dry_run_070a": signed_order_payload_dry_run_path,
        "signed_payload_diagnostic_adapter_072e": signed_payload_diagnostic_adapter_path,
        "order_prep_packet_072a": order_prep_packet_path,
        "risk_engine_v2_074d": risk_engine_v2_path,
        "first_live_order_final_blocker_reducer_072d": final_blocker_reducer_path,
        "static_safety_invariant_report_060q": static_safety_report_path,
    }
    source_artifacts = {
        source_id: _load_source_artifact(
            _select_source_path(source_root, SOURCE_CANDIDATES[source_id], explicit_paths.get(source_id)),
            source_id,
        )
        for source_id in SOURCE_CANDIDATES
    }

    selected_candidate = _summarize_selected_candidate(
        source_artifacts["selected_candidate_artifact_075d"],
        market_symbol=market_symbol,
        strategy_name=strategy_name,
    )
    selected_verification = _summarize_selected_token_verification(
        source_artifacts["selected_token_verification_bridge_076a"],
        selected_candidate=selected_candidate,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
    )
    signer_diagnostic = _summarize_signer_diagnostic_evidence(
        source_artifacts["signer_diagnostic_evidence_bridge_076c"],
        legacy_guarded_source=source_artifacts["guarded_signer_diagnostic_smoke_069a"],
    )
    payload_dry_run = _summarize_payload_dry_run(
        selected_token_payload_source=source_artifacts["selected_token_payload_readiness_gate_073c"],
        signed_order_payload_source=source_artifacts["signed_order_payload_dry_run_070a"],
        signed_payload_adapter_source=source_artifacts["signed_payload_diagnostic_adapter_072e"],
        order_prep_source=source_artifacts["order_prep_packet_072a"],
    )
    risk_engine = _summarize_risk_engine(
        risk_source=source_artifacts["risk_engine_v2_074d"],
        final_reducer_source=source_artifacts["first_live_order_final_blocker_reducer_072d"],
        static_safety_source=source_artifacts["static_safety_invariant_report_060q"],
    )

    component_statuses = {
        "selected_candidate": selected_candidate,
        "selected_token_verification": selected_verification,
        "signer_diagnostic_evidence": signer_diagnostic,
        "payload_dry_run": payload_dry_run,
        "risk_engine": risk_engine,
    }
    blockers = _build_blockers(component_statuses, generated_at=generated_at)
    status = _status_for_components(component_statuses)
    current_top_blocker = blockers[0]["blocker_id"] if blockers else ""
    final_blockers = [clean_text(row.get("blocker_id")) for row in blockers if clean_text(row.get("blocker_id"))]
    next_command = _next_recommended_safe_command(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        signer_bridge_present=signer_diagnostic.get("bridge_present") is True,
    )
    operator_summary = _operator_summary(status)

    blockers_artifact = {
        "contract_version": PAYLOAD_DRY_RUN_READINESS_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "current_top_blocker": current_top_blocker,
        "final_blockers": final_blockers,
        "generated_at": generated_at,
        **payload_dry_run_readiness_safety_flags(),
    }
    latest_status = _build_latest_status(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        component_statuses=component_statuses,
        blockers=blockers,
        artifact_paths=path_refs,
        next_recommended_safe_command=next_command,
        operator_summary=operator_summary,
        generated_at=generated_at,
    )
    config = PayloadDryRunReadinessConfig(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        artifact_root=normalize_path(source_root),
        generated_at=generated_at,
    ).to_dict()
    result: dict[str, Any] = {
        "contract_version": PAYLOAD_DRY_RUN_READINESS_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "config": config,
        "component_statuses": component_statuses,
        "source_artifacts": {
            source_id: _source_artifact_summary(row) for source_id, row in source_artifacts.items()
        },
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "final_blockers": final_blockers,
        "current_top_blocker": current_top_blocker,
        "next_recommended_safe_command": next_command,
        "operator_summary": operator_summary,
        "head_before": clean_text(head_before),
        "head_after": clean_text(head_after),
        "generated_at": generated_at,
        "artifact_paths": path_refs,
        **payload_dry_run_readiness_safety_flags(),
    }
    result["latest_status"] = latest_status
    result["blockers_artifact"] = blockers_artifact
    result["validation"] = validate_payload_dry_run_readiness_result(result)

    write_json(paths["blockers"], blockers_artifact)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_payload_dry_run_readiness_markdown(result))
    return result


def render_payload_dry_run_readiness_cli_summary(result_or_status: Mapping[str, Any]) -> str:
    status = dict(result_or_status.get("latest_status", result_or_status))
    blockers = status.get("final_blockers")
    blocker_lines = ", ".join(clean_text(row) for row in blockers if clean_text(row)) if isinstance(blockers, list) else ""
    return "\n".join(
        [
            "PMBOT payload dry-run readiness 076D",
            f"status: {clean_text(status.get('status'))}",
            f"market: {clean_text(status.get('market_symbol') or status.get('market'))}",
            f"strategy: {clean_text(status.get('strategy_name') or status.get('strategy'))}",
            f"selected candidate status: {clean_text(status.get('selected_candidate_status'))}",
            f"selected token verification status: {clean_text(status.get('selected_token_verification_status'))}",
            f"signer diagnostic status: {clean_text(status.get('signer_diagnostic_status'))}",
            f"payload dry-run status: {clean_text(status.get('payload_dry_run_status'))}",
            f"risk status: {clean_text(status.get('risk_status'))}",
            f"final blocker reducer status: {clean_text(status.get('final_blocker_reducer_status'))}",
            f"final blockers: {blocker_lines or 'none'}",
            f"next recommended safe command: {clean_text(status.get('next_recommended_safe_command'))}",
            f"operator summary: {clean_text(status.get('operator_summary'))}",
        ]
    )


def render_payload_dry_run_readiness_markdown(result: Mapping[str, Any]) -> str:
    status = dict(result.get("latest_status", {}))
    component_statuses = dict(result.get("component_statuses", {}))
    blockers = [dict(row) for row in result.get("blockers", []) if isinstance(row, Mapping)]
    source_artifacts = dict(result.get("source_artifacts", {}))
    component_lines = []
    for key in (
        "selected_candidate",
        "selected_token_verification",
        "signer_diagnostic_evidence",
        "payload_dry_run",
        "risk_engine",
    ):
        row = component_statuses.get(key)
        if isinstance(row, Mapping):
            component_lines.append(f"`{key}` status=`{clean_text(row.get('status'))}` ready={row.get('ready') is True}")
    source_lines = []
    for key, row in source_artifacts.items():
        if isinstance(row, Mapping):
            source_lines.append(
                f"`{key}` available={row.get('available') is True} status=`{clean_text(row.get('status'))}` path=`{clean_text(row.get('path'))}`"
            )
    blocker_lines = [
        f"`{clean_text(row.get('blocker_id'))}` - {clean_text(row.get('reason'))}" for row in blockers
    ]
    return "\n".join(
        [
            "# Payload Dry-Run Readiness 076D",
            "",
            f"- status: `{clean_text(status.get('status'))}`",
            f"- market: `{clean_text(status.get('market_symbol'))}`",
            f"- strategy: `{clean_text(status.get('strategy_name'))}`",
            f"- current top blocker: `{clean_text(status.get('current_top_blocker')) or 'none'}`",
            f"- next recommended safe command: `{clean_text(status.get('next_recommended_safe_command'))}`",
            f"- operator summary: {clean_text(status.get('operator_summary'))}",
            "",
            "## Component Statuses",
            "",
            *bullet_lines(component_lines),
            "",
            "## Final Blockers",
            "",
            *bullet_lines(blocker_lines),
            "",
            "## Source Artifacts",
            "",
            *bullet_lines(source_lines),
            "",
            "## Safety Invariants",
            "",
            "- submit_ready=false",
            "- live_ready=false",
            "- allowed_for_live=false",
            "- order_submission_enabled=false",
            "- signing_by_default=false",
            "- no full signed payload output is emitted",
            "",
        ]
    )


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(arg).lower() for arg in argv}
    forbidden = [flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered]
    if forbidden:
        raise SystemExit(
            "payload dry-run readiness review is no-live/no-submit and rejects forbidden flag(s): "
            + ", ".join(forbidden)
        )


def _build_latest_status(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    component_statuses: Mapping[str, Mapping[str, Any]],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    next_recommended_safe_command: str,
    operator_summary: str,
    generated_at: str,
) -> dict[str, Any]:
    selected_candidate = component_statuses["selected_candidate"]
    selected_verification = component_statuses["selected_token_verification"]
    signer = component_statuses["signer_diagnostic_evidence"]
    payload = component_statuses["payload_dry_run"]
    risk = component_statuses["risk_engine"]
    final_blockers = [clean_text(row.get("blocker_id")) for row in blockers if clean_text(row.get("blocker_id"))]
    value = {
        "contract_version": PAYLOAD_DRY_RUN_READINESS_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "selected_candidate_status": clean_text(selected_candidate.get("status")),
        "selected_candidate_ready": selected_candidate.get("ready") is True,
        "selected_token_verification_status": clean_text(selected_verification.get("status")),
        "selected_token_verified": selected_verification.get("verified") is True,
        "signer_diagnostic_status": clean_text(signer.get("status")),
        "signer_diagnostic_ok": signer.get("diagnostic_ok") is True,
        "signer_diagnostic_bridge_present": signer.get("bridge_present") is True,
        "payload_dry_run_status": clean_text(payload.get("status")),
        "payload_dry_run_ready": payload.get("ready") is True,
        "order_prep_status": clean_text(payload.get("order_prep_status")),
        "risk_status": clean_text(risk.get("status")),
        "risk_engine_v2_status": clean_text(risk.get("risk_engine_v2_status")),
        "risk_engine_v2_ready": risk.get("risk_engine_v2_ready") is True,
        "final_blocker_reducer_status": clean_text(risk.get("final_blocker_reducer_status")),
        "final_blocker_reducer_clear": risk.get("final_blocker_reducer_clear") is True,
        "static_safety_report_status": clean_text(risk.get("static_safety_report_status")),
        "static_safety_report_ok": risk.get("static_safety_report_ok") is True,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "final_blockers": final_blockers,
        "current_top_blocker": final_blockers[0] if final_blockers else "",
        "next_recommended_safe_command": next_recommended_safe_command,
        "operator_summary": operator_summary,
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "blockers_path": clean_text(artifact_paths.get("blockers")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "generated_at": generated_at,
        **payload_dry_run_readiness_safety_flags(),
    }
    return value


def _select_source_path(root: Path, candidates: Sequence[Path], explicit_path: str | Path | None) -> Path:
    if explicit_path:
        return Path(explicit_path)
    for candidate in candidates:
        path = root / candidate
        if path.exists():
            return path
    return root / candidates[0]


def _load_source_artifact(path: Path, source_id: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "source_id": source_id,
            "path": normalize_path(path),
            "available": False,
            "parsed": False,
            "status": "missing",
            "contract_version": "",
            "payload": {},
            "error": "artifact missing",
        }
    try:
        payload = load_json_object(path, label=source_id)
    except Exception as exc:  # pragma: no cover - defensive parse summary
        return {
            "source_id": source_id,
            "path": normalize_path(path),
            "available": True,
            "parsed": False,
            "status": "unreadable",
            "contract_version": "",
            "payload": {},
            "error": clean_text(exc),
        }
    return {
        "source_id": source_id,
        "path": normalize_path(path),
        "available": True,
        "parsed": True,
        "status": clean_text(payload.get("status")) or "unknown",
        "contract_version": clean_text(payload.get("contract_version")),
        "payload": payload,
        "error": "",
    }


def _source_artifact_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": clean_text(source.get("source_id")),
        "path": clean_text(source.get("path")),
        "available": source.get("available") is True,
        "parsed": source.get("parsed") is True,
        "status": clean_text(source.get("status")),
        "contract_version": clean_text(source.get("contract_version")),
        "error": clean_text(source.get("error")),
    }


def _summarize_selected_candidate(
    source: Mapping[str, Any],
    *,
    market_symbol: str,
    strategy_name: str,
) -> dict[str, Any]:
    payload = _payload(source)
    status = clean_text(payload.get("status") or source.get("status"))
    scope_matches = _scope_matches(payload, market_symbol, strategy_name)
    recorded = status == STATUS_SELECTED_CANDIDATE_ARTIFACT_RECORDED or payload.get("selected_candidate_artifact_recorded") is True
    source_backed = payload.get("source_backed") is True or payload.get("token_id_source_backed") is True
    selected_by_operator = payload.get("selected_by_operator") is True
    safety_flags_ok = _source_false_flags_ok(payload, UNSAFE_TRUE_FIELDS)
    ready = source.get("available") is True and recorded and source_backed and selected_by_operator and scope_matches and safety_flags_ok
    return {
        "status": status if source.get("available") is True else "missing",
        "available": source.get("available") is True,
        "ready": ready,
        "recorded": recorded,
        "source_backed": source_backed,
        "selected_by_operator": selected_by_operator,
        "scope_matches": scope_matches,
        "safety_flags_ok": safety_flags_ok,
        "candidate_index": _safe_int(payload.get("candidate_index")),
        "selected_token_fingerprint_sha256": clean_text(payload.get("token_id_hash") or payload.get("selected_token_fingerprint_sha256")),
        "token_id_short": clean_text(payload.get("token_id_short")),
        "source_path": clean_text(source.get("path")),
    }


def _summarize_selected_token_verification(
    source: Mapping[str, Any],
    *,
    selected_candidate: Mapping[str, Any],
    market_symbol: str,
    strategy_name: str,
) -> dict[str, Any]:
    payload = _payload(source)
    status = clean_text(payload.get("status") or source.get("status"))
    scope_matches = _scope_matches(payload, market_symbol, strategy_name)
    safety_flags_ok = _source_false_flags_ok(payload, UNSAFE_TRUE_FIELDS)
    verified = (
        source.get("available") is True
        and selected_candidate.get("ready") is True
        and status == STATUS_SELECTED_TOKEN_VERIFIED_FOR_PAYLOAD_DRY_RUN
        and payload.get("selected_token_verified_for_payload_dry_run") is True
        and scope_matches
        and safety_flags_ok
    )
    return {
        "status": status if source.get("available") is True else "missing",
        "available": source.get("available") is True,
        "ready": verified,
        "verified": verified,
        "scope_matches": scope_matches,
        "safety_flags_ok": safety_flags_ok,
        "selected_token_fingerprint_sha256": clean_text(
            payload.get("token_id_hash") or payload.get("selected_token_fingerprint_sha256")
        ),
        "source_path": clean_text(source.get("path")),
    }


def _summarize_signer_diagnostic_evidence(
    source: Mapping[str, Any],
    *,
    legacy_guarded_source: Mapping[str, Any],
) -> dict[str, Any]:
    payload = _payload(source)
    status = clean_text(payload.get("status") or source.get("status"))
    module_available = _module_available(
        "pm_bot.trading_core.signer_diagnostic_evidence_bridge",
        "pm_bot.operator_runner.signer_diagnostic_evidence_bridge",
    )
    bridge_present = source.get("available") is True or module_available
    safety_flags_ok = source.get("available") is True and _source_false_flags_ok(payload, UNSAFE_TRUE_FIELDS)
    diagnostic_ok = (
        source.get("available") is True
        and safety_flags_ok
        and (
            payload.get("signer_diagnostic_evidence_ok") is True
            or payload.get("diagnostic_ok") is True
            or status in {"diagnostic_ok", "signer_diagnostic_evidence_ok", "signer_diagnostic_evidence_bridge_ok"}
        )
    )
    if source.get("available") is not True:
        status = "missing_signer_diagnostic_evidence_bridge_076c"
    return {
        "status": status,
        "available": source.get("available") is True,
        "ready": diagnostic_ok,
        "diagnostic_ok": diagnostic_ok,
        "bridge_present": bridge_present,
        "module_available": module_available,
        "safety_flags_ok": safety_flags_ok,
        "source_path": clean_text(source.get("path")),
        "legacy_guarded_signer_status": clean_text(legacy_guarded_source.get("status")),
        "legacy_guarded_signer_available": legacy_guarded_source.get("available") is True,
    }


def _summarize_payload_dry_run(
    *,
    selected_token_payload_source: Mapping[str, Any],
    signed_order_payload_source: Mapping[str, Any],
    signed_payload_adapter_source: Mapping[str, Any],
    order_prep_source: Mapping[str, Any],
) -> dict[str, Any]:
    selected_payload = _payload(selected_token_payload_source)
    signed_order = _payload(signed_order_payload_source)
    adapter = _payload(signed_payload_adapter_source)
    order_prep = _payload(order_prep_source)

    selected_payload_status = clean_text(selected_payload.get("status") or selected_token_payload_source.get("status"))
    signed_order_status = clean_text(signed_order.get("status") or signed_order_payload_source.get("status"))
    adapter_status = clean_text(adapter.get("status") or signed_payload_adapter_source.get("status"))
    order_prep_status = clean_text(order_prep.get("status") or order_prep_source.get("status"))

    selected_payload_ready = (
        selected_token_payload_source.get("available") is True
        and selected_payload_status == STATUS_SELECTED_TOKEN_PAYLOAD_READY
        and selected_payload.get("ready_for_signed_payload_diagnostic") is True
        and _source_false_flags_ok(selected_payload, UNSAFE_TRUE_FIELDS)
    )
    signed_order_scaffold_ready = (
        signed_order_payload_source.get("available") is True
        and bool(clean_text(signed_order.get("payload_contract_fingerprint_sha256")))
        and _source_false_flags_ok(signed_order, UNSAFE_TRUE_FIELDS)
    )
    adapter_ready = (
        signed_payload_adapter_source.get("available") is True
        and adapter_status == STATUS_SIGNED_PAYLOAD_ADAPTER_READY
        and adapter.get("unsigned_readiness_only") is True
        and _source_false_flags_ok(adapter, UNSAFE_TRUE_FIELDS)
    )
    order_prep_ready = (
        order_prep_source.get("available") is True
        and order_prep_status == STATUS_ORDER_PREP_READY
        and _source_false_flags_ok(order_prep, UNSAFE_TRUE_FIELDS)
    )
    ready = selected_payload_ready and signed_order_scaffold_ready and adapter_ready and order_prep_ready
    return {
        "status": "ready" if ready else _payload_dry_run_block_status(
            selected_payload_ready=selected_payload_ready,
            signed_order_scaffold_ready=signed_order_scaffold_ready,
            adapter_ready=adapter_ready,
            order_prep_ready=order_prep_ready,
            selected_payload_status=selected_payload_status,
            signed_order_status=signed_order_status,
            adapter_status=adapter_status,
            order_prep_status=order_prep_status,
        ),
        "available": any(
            row.get("available") is True
            for row in (
                selected_token_payload_source,
                signed_order_payload_source,
                signed_payload_adapter_source,
                order_prep_source,
            )
        ),
        "ready": ready,
        "selected_token_payload_readiness_status": selected_payload_status,
        "selected_token_payload_readiness_ready": selected_payload_ready,
        "signed_order_payload_dry_run_status": signed_order_status,
        "signed_order_payload_scaffold_ready": signed_order_scaffold_ready,
        "signed_payload_diagnostic_adapter_status": adapter_status,
        "signed_payload_diagnostic_adapter_ready": adapter_ready,
        "order_prep_status": order_prep_status,
        "order_prep_ready": order_prep_ready,
    }


def _summarize_risk_engine(
    *,
    risk_source: Mapping[str, Any],
    final_reducer_source: Mapping[str, Any],
    static_safety_source: Mapping[str, Any],
) -> dict[str, Any]:
    risk = _payload(risk_source)
    final_reducer = _payload(final_reducer_source)
    static_safety = _payload(static_safety_source)
    risk_status = clean_text(risk.get("status") or risk_source.get("status"))
    final_status = clean_text(final_reducer.get("status") or final_reducer_source.get("status"))
    static_status = clean_text(static_safety.get("status") or static_safety_source.get("status"))
    risk_ready = (
        risk_source.get("available") is True
        and risk_status == STATUS_RISK_ENGINE_PASSED
        and _safe_int(risk.get("remaining_blocker_count")) == 0
        and _source_false_flags_ok(risk, UNSAFE_TRUE_FIELDS)
    )
    final_clear = (
        final_reducer_source.get("available") is True
        and _safe_int(final_reducer.get("remaining_blocker_count")) == 0
        and _source_false_flags_ok(final_reducer, UNSAFE_TRUE_FIELDS)
    )
    static_ok = (
        static_safety_source.get("available") is True
        and static_status in STATUS_STATIC_SAFETY_PASSED
        and static_safety.get("safety_ok") is True
        and _safe_int(static_safety.get("critical_count")) == 0
        and _source_false_flags_ok(static_safety, UNSAFE_TRUE_FIELDS)
    )
    ready = risk_ready and final_clear and static_ok
    return {
        "status": "ready" if ready else "blocked_risk_engine_or_final_reducer",
        "available": risk_source.get("available") is True,
        "ready": ready,
        "risk_engine_v2_status": risk_status,
        "risk_engine_v2_ready": risk_ready,
        "risk_engine_v2_blocker_count": _safe_int(risk.get("remaining_blocker_count") or risk.get("blocker_count")),
        "final_blocker_reducer_status": final_status,
        "final_blocker_reducer_clear": final_clear,
        "final_blocker_reducer_remaining_count": _safe_int(final_reducer.get("remaining_blocker_count")),
        "static_safety_report_status": static_status,
        "static_safety_report_ok": static_ok,
        "static_safety_warning_count": _safe_int(static_safety.get("warning_count")),
    }


def _build_blockers(
    component_statuses: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    selected_candidate = component_statuses["selected_candidate"]
    selected_verification = component_statuses["selected_token_verification"]
    signer = component_statuses["signer_diagnostic_evidence"]
    payload = component_statuses["payload_dry_run"]
    risk = component_statuses["risk_engine"]

    if selected_candidate.get("ready") is not True:
        blockers.append(
            _blocker(
                "blocked_missing_selected_candidate",
                "selected_candidate",
                "A source-backed operator-selected candidate artifact is missing or not ready.",
                generated_at=generated_at,
            )
        )
    if selected_candidate.get("ready") is True and selected_verification.get("verified") is not True:
        blockers.append(
            _blocker(
                "blocked_unverified_selected_token",
                "selected_token_verification",
                "Selected token verification bridge is missing, mismatched, or not verified for payload dry-run.",
                generated_at=generated_at,
            )
        )
    if selected_candidate.get("ready") is True and selected_verification.get("verified") is True and signer.get("diagnostic_ok") is not True:
        blockers.append(
            _blocker(
                "blocked_signer_diagnostic_not_ok",
                "signer_diagnostic_evidence",
                "076C signer diagnostic evidence bridge is missing or not diagnostic_ok; legacy 069A evidence is not treated as the 076C bridge.",
                generated_at=generated_at,
            )
        )
    if (
        selected_candidate.get("ready") is True
        and selected_verification.get("verified") is True
        and signer.get("diagnostic_ok") is True
        and payload.get("ready") is not True
    ):
        blockers.append(
            _blocker(
                "blocked_signed_payload_dry_run_not_ready",
                "payload_dry_run",
                "Selected token payload readiness, signed payload dry-run scaffold, adapter, or order prep packet is not ready.",
                generated_at=generated_at,
            )
        )
    if (
        selected_candidate.get("ready") is True
        and selected_verification.get("verified") is True
        and signer.get("diagnostic_ok") is True
        and payload.get("ready") is True
        and risk.get("ready") is not True
    ):
        blockers.append(
            _blocker(
                "blocked_risk_engine_review",
                "risk_engine",
                "Risk Engine v2, final blocker reducer, or static safety review still reports blocking evidence.",
                generated_at=generated_at,
            )
        )
    return blockers


def _status_for_components(component_statuses: Mapping[str, Mapping[str, Any]]) -> str:
    selected_candidate = component_statuses["selected_candidate"]
    selected_verification = component_statuses["selected_token_verification"]
    signer = component_statuses["signer_diagnostic_evidence"]
    payload = component_statuses["payload_dry_run"]
    risk = component_statuses["risk_engine"]
    if selected_candidate.get("ready") is not True:
        return STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE
    if selected_verification.get("verified") is not True:
        return STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN
    if signer.get("diagnostic_ok") is not True:
        return STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK
    if payload.get("ready") is not True:
        return STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY
    if risk.get("ready") is not True:
        return STATUS_BLOCKED_RISK_ENGINE_REVIEW
    return STATUS_READY_FOR_OPERATOR_REVIEW


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = {
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_payload_dry_run_operator_review": True,
        "blocks_live_execution": True,
        "generated_at": generated_at,
    }
    value.update(payload_dry_run_readiness_safety_flags())
    return value


def _payload_dry_run_block_status(
    *,
    selected_payload_ready: bool,
    signed_order_scaffold_ready: bool,
    adapter_ready: bool,
    order_prep_ready: bool,
    selected_payload_status: str,
    signed_order_status: str,
    adapter_status: str,
    order_prep_status: str,
) -> str:
    if not selected_payload_ready:
        return f"selected_token_payload_readiness_not_ready:{selected_payload_status or 'missing'}"
    if not signed_order_scaffold_ready:
        return f"signed_order_payload_dry_run_not_ready:{signed_order_status or 'missing'}"
    if not adapter_ready:
        return f"signed_payload_diagnostic_adapter_not_ready:{adapter_status or 'missing'}"
    if not order_prep_ready:
        return f"order_prep_packet_not_ready:{order_prep_status or 'missing'}"
    return "payload_dry_run_not_ready"


def _next_recommended_safe_command(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    signer_bridge_present: bool,
) -> str:
    suffix = f"--market {market_symbol} --strategy {strategy_name} --dry-run"
    if status == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE:
        return f"python -m pm_bot.operator_runner.selected_candidate_artifact {suffix} --candidate-index 0"
    if status == STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN:
        return f"python -m pm_bot.operator_runner.selected_token_verification_bridge {suffix}"
    if status == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK:
        if signer_bridge_present:
            return f"python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge {suffix}"
        return "N/A - 076C signer diagnostic evidence bridge is not present in this branch"
    if status == STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY:
        return f"python -m pm_bot.operator_runner.selected_token_payload_readiness_gate {suffix}"
    if status == STATUS_BLOCKED_RISK_ENGINE_REVIEW:
        return f"python -m pm_bot.operator_runner.risk_engine_v2_review {suffix}"
    return f"python -m pm_bot.operator_runner.payload_dry_run_readiness_review {suffix} --json"


def _operator_summary(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE:
        return "Payload dry-run readiness is blocked because no source-backed selected candidate is ready."
    if status == STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN:
        return "Payload dry-run readiness is blocked because the selected token is not verified by the 076A bridge."
    if status == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK:
        return "Payload dry-run readiness is blocked because 076C signer diagnostic evidence is missing or not diagnostic_ok."
    if status == STATUS_BLOCKED_SIGNED_PAYLOAD_DRY_RUN_NOT_READY:
        return "Payload dry-run readiness is blocked because payload readiness, adapter, or order prep evidence is not ready."
    if status == STATUS_BLOCKED_RISK_ENGINE_REVIEW:
        return "Payload dry-run readiness is blocked because Risk Engine v2, final blocker reducer, or static safety evidence still blocks review."
    return (
        "Payload dry-run readiness is ready for operator review only. Submit, live execution, signing by default, "
        "wallet connection, and full signed payload output remain disabled."
    )


def _module_available(*module_names: str) -> bool:
    for module_name in module_names:
        try:
            if importlib.util.find_spec(module_name) is not None:
                return True
        except ModuleNotFoundError:
            continue
    return False


def _payload(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = source.get("payload")
    return dict(payload) if isinstance(payload, Mapping) else {}


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


def _source_false_flags_ok(payload: Mapping[str, Any], fields: Sequence[str]) -> bool:
    if not payload:
        return False
    for field in fields:
        if field in payload and payload.get(field) is not False:
            return False
    return True


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
