from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.risk_engine_v2_models import (
    BLOCKING_EVIDENCE_STATUSES,
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    EXECUTION_MODE,
    FORCED_FALSE_EXECUTION_FIELDS,
    MODE,
    REQUIRED_GATE_IDS,
    RISK_ENGINE_V2_BLOCKERS_CONTRACT,
    RISK_ENGINE_V2_GATE_EVALUATION_CONTRACT,
    RISK_ENGINE_V2_LATEST_STATUS_CONTRACT,
    STATUS_BLOCKED,
    STATUS_MISSING,
    STATUS_PASSED_REVIEW_CHECK,
    STATUS_REVIEW_REQUIRED,
    STATUS_UNKNOWN,
    TASK_ID,
    RiskEngineV2Blocker,
    RiskEngineV2ReviewResult,
    RiskEngineV2SafetySnapshot,
    risk_engine_v2_blocker_id_for_gate,
    risk_engine_v2_category_for_gate,
    risk_engine_v2_gate_label,
    risk_engine_v2_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/risk_engine_v2_074d")

FRESH_DATA_STATUSES = {"fresh", "fresh_enough", "review_fresh"}
STRONG_LIQUIDITY_STATUSES = {"strong", "sufficient", "source_backed", "review_ready"}
TOKEN_CANDIDATE_STATUSES = {"present", "source_backed", "verified", "review_ready"}
ACCOUNT_READONLY_STATUSES = {"present", "read_only_ok", "readonly_ok", "account_state_probe_succeeded_live_blocked"}
SIGNER_DIAGNOSTIC_STATUSES = {"present", "diagnostic_ok"}
SELECTED_TOKEN_PAYLOAD_STATUSES = {"ready_for_signed_payload_diagnostic", "review_ready"}
APPROVED_OPERATOR_STATUSES = {"operator_approved", "operator_approved_review_only"}

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
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
    "--env-dump",
)


def risk_engine_v2_review_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "risk_engine_v2_074d_result.json",
        "latest_status": root / "latest_risk_engine_v2_074d_status.json",
        "blockers": root / "risk_engine_v2_074d_blockers.json",
        "gate_evaluations": root / "risk_engine_v2_074d_gate_evaluations.json",
        "safety_snapshot": root / "risk_engine_v2_074d_safety_snapshot.json",
        "operator_summary_md": root / "risk_engine_v2_074d_operator_summary.md",
    }


def run_risk_engine_v2_review(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    evidence: Mapping[str, Mapping[str, Any]] | None = None,
    risk_state: Mapping[str, Any] | None = None,
    risk_limits: Mapping[str, Any] | None = None,
    review_controls: Mapping[str, Any] | None = None,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("Risk Engine v2 review requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    evidence_rows = {clean_text(key): dict(value) for key, value in dict(evidence or {}).items() if isinstance(value, Mapping)}
    state = dict(risk_state or {})
    limits = dict(risk_limits or _default_risk_limits())
    controls = dict(review_controls or {})

    gate_evaluations: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    def add_gate(
        gate_id: str,
        passed: bool,
        evidence_status: str,
        reason: str,
        *,
        source_keys: Sequence[str] = (),
        detail: str = "",
    ) -> None:
        evaluation = _gate_evaluation(
            gate_id=gate_id,
            passed=passed,
            evidence_status=evidence_status,
            reason=reason,
            source_keys=source_keys,
            detail=detail,
            generated_at=generated_at,
        )
        gate_evaluations.append(evaluation)
        if not passed:
            blockers.append(
                _blocker_for_gate(
                    gate_id=gate_id,
                    reason=reason,
                    evidence_status=evidence_status,
                    source_keys=source_keys,
                    generated_at=generated_at,
                )
            )

    _add_evidence_gate(
        add_gate,
        evidence_rows,
        gate_id="stale_data",
        evidence_key="data_freshness",
        allowed_statuses=FRESH_DATA_STATUSES,
        missing_reason="Data freshness evidence is missing; stale or unknown data blocks the review.",
        rejected_reason="Data freshness evidence is stale or not review-ready.",
    )
    _add_evidence_gate(
        add_gate,
        evidence_rows,
        gate_id="liquidity_evidence",
        evidence_key="liquidity",
        allowed_statuses=STRONG_LIQUIDITY_STATUSES,
        missing_reason="Liquidity evidence is missing; weak or unknown liquidity blocks the review.",
        rejected_reason="Liquidity evidence is weak or not source-backed enough for review.",
    )
    _add_evidence_gate(
        add_gate,
        evidence_rows,
        gate_id="source_backed_token_candidate",
        evidence_key="source_backed_token_candidate",
        allowed_statuses=TOKEN_CANDIDATE_STATUSES,
        missing_reason="A source-backed token candidate is missing; the engine must not invent one.",
        rejected_reason="Token candidate evidence is present but not source-backed and verified.",
    )
    _add_evidence_gate(
        add_gate,
        evidence_rows,
        gate_id="account_readonly_evidence",
        evidence_key="account_readonly",
        allowed_statuses=ACCOUNT_READONLY_STATUSES,
        missing_reason="Read-only account evidence is missing; account readiness remains unknown.",
        rejected_reason="Read-only account evidence is not review-ready.",
    )
    _add_evidence_gate(
        add_gate,
        evidence_rows,
        gate_id="signer_diagnostic_evidence",
        evidence_key="signer_diagnostic",
        allowed_statuses=SIGNER_DIAGNOSTIC_STATUSES,
        missing_reason="Signer diagnostic evidence is missing; signer readiness remains unknown.",
        rejected_reason="Signer diagnostic evidence is present but not diagnostic_ok.",
    )
    _add_evidence_gate(
        add_gate,
        evidence_rows,
        gate_id="selected_token_payload_readiness",
        evidence_key="selected_token_payload_readiness",
        allowed_statuses=SELECTED_TOKEN_PAYLOAD_STATUSES,
        missing_reason="Selected-token payload readiness evidence is missing.",
        rejected_reason="Selected-token payload readiness is not review-ready.",
    )

    _add_cap_gate(
        add_gate,
        gate_id="exposure_cap",
        state=state,
        limits=limits,
        current_key="current_total_exposure_usd",
        limit_key="max_total_exposure_usd",
        source_key="exposure_state",
        label="total exposure",
    )
    _add_cap_gate(
        add_gate,
        gate_id="per_market_cap",
        state=state,
        limits=limits,
        current_key="current_market_exposure_usd",
        limit_key="max_market_exposure_usd",
        source_key="per_market_exposure_state",
        label="per-market exposure",
    )
    _add_daily_loss_gate(add_gate, state=state, limits=limits)
    _add_duplicate_attempt_gate(add_gate, state=state)
    _add_halt_state_gate(add_gate, state=state)

    unknown_gate_ids = [
        clean_text(row.get("gate_id"))
        for row in gate_evaluations
        if row.get("passed") is not True and clean_text(row.get("evidence_status")) in {STATUS_UNKNOWN, STATUS_MISSING}
    ]
    if unknown_gate_ids:
        add_gate(
            "unknown_means_block",
            False,
            STATUS_UNKNOWN,
            "One or more readiness gates are unknown; unknown means block.",
            source_keys=tuple(unknown_gate_ids),
        )
    else:
        add_gate(
            "unknown_means_block",
            True,
            STATUS_PASSED_REVIEW_CHECK,
            "No unknown evidence gates remain in the supplied local review context.",
        )

    operator_status = clean_text(controls.get("operator_approval_status")).lower()
    operator_acknowledged = controls.get("operator_approval_required_acknowledged") is True
    if operator_status in APPROVED_OPERATOR_STATUSES and operator_acknowledged:
        add_gate(
            "operator_approval_required",
            True,
            STATUS_PASSED_REVIEW_CHECK,
            "Operator approval requirement is acknowledged for review only; it still does not authorize live execution.",
            source_keys=("review_controls",),
        )
    else:
        add_gate(
            "operator_approval_required",
            False,
            STATUS_REVIEW_REQUIRED,
            "A separate operator approval record is required before any future live action.",
            source_keys=("review_controls",),
        )

    add_gate(
        "explicit_live_authorization_missing",
        False,
        "authorization_missing",
        "Explicit live authorization is missing and cannot be consumed by this no-live scaffold.",
        source_keys=("review_controls",),
    )

    path_refs = {key: normalize_path(path) for key, path in risk_engine_v2_review_artifact_paths(artifact_dir).items() if key != "root"}
    safety_snapshot = RiskEngineV2SafetySnapshot(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    blockers_artifact = _build_blockers_artifact(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        blockers=blockers,
        generated_at=generated_at,
    )
    gate_evaluations_artifact = _build_gate_evaluations_artifact(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        gate_evaluations=gate_evaluations,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        gate_evaluations=gate_evaluations,
        blockers=blockers,
        path_refs=path_refs,
        generated_at=generated_at,
    )
    result = RiskEngineV2ReviewResult(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        gate_evaluations=tuple(gate_evaluations),
        blockers=tuple(blockers),
        safety_snapshot=safety_snapshot,
        latest_status=latest_status,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()

    paths = risk_engine_v2_review_artifact_paths(artifact_dir)
    write_json(paths["blockers"], blockers_artifact)
    write_json(paths["gate_evaluations"], gate_evaluations_artifact)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_summary_md"], render_risk_engine_v2_review_markdown(result))
    return result


def render_risk_engine_v2_review_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Risk Engine v2 review 074D completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Gate count: {int(value.get('gate_count', 0) or 0)}",
            f"Blockers: {int(value.get('remaining_blocker_count', 0) or 0)}",
            f"Unknown blockers: {int(value.get('unknown_blocker_count', 0) or 0)}",
            "Allowed for live: false",
            "Risk Engine v2 executable for live: false",
            "First supervised tiny order blocked: true",
            "Live authorization: blocked",
            "Operator approval: required",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_risk_engine_v2_review_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    paths = dict(value.get("artifact_paths", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    gates = [dict(row) for row in value.get("gate_evaluations", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Risk Engine v2 Review 074D",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        f"- execution_mode: `{EXECUTION_MODE}`",
        "- allowed_for_live: `false`",
        "- risk_engine_v2_executable_for_live: `false`",
        "- first_supervised_tiny_order_blocked: `true`",
        "- unknown evidence blocks",
        "- no submit, no cancel, no signing, no wallet, no network",
        "",
        "## Gates",
        "",
        *bullet_lines(
            f"`{row.get('gate_id')}` passed={str(row.get('passed') is True).lower()} "
            f"status=`{row.get('evidence_status')}`"
            for row in gates
        ),
        "",
        "## Blockers",
        "",
        *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"`{path}`" for path in paths.values()),
        "",
        "## Safety Statement",
        "",
        "074D is a local review scaffold only. It does not read private material, instantiate signers, prepare "
        "executable payloads, submit or cancel orders, call Polymarket APIs, create schedulers, create daemons, "
        "or run background workers.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "Risk Engine v2 review is no-live/no-submit/no-cancel/no-signing; unsupported flag(s): "
            + ", ".join(requested)
        )


def _add_evidence_gate(
    add_gate,
    evidence_rows: Mapping[str, Mapping[str, Any]],
    *,
    gate_id: str,
    evidence_key: str,
    allowed_statuses: set[str],
    missing_reason: str,
    rejected_reason: str,
) -> None:
    evidence = dict(evidence_rows.get(evidence_key, {}))
    source_safe = _source_safety_ok(evidence)
    status = _evidence_status(evidence)
    if not evidence:
        add_gate(gate_id, False, STATUS_MISSING, missing_reason, source_keys=(evidence_key,))
        return
    if not source_safe:
        add_gate(
            gate_id,
            False,
            "unsafe_source_flag",
            "Source evidence contains an activation flag that is not safely false.",
            source_keys=(evidence_key,),
        )
        return
    if status in allowed_statuses:
        add_gate(
            gate_id,
            True,
            STATUS_PASSED_REVIEW_CHECK,
            f"{risk_engine_v2_gate_label(gate_id)} evidence is present for review only.",
            source_keys=(evidence_key,),
        )
        return
    evidence_status = STATUS_UNKNOWN if status in {"", "unknown"} else status
    add_gate(gate_id, False, evidence_status, rejected_reason, source_keys=(evidence_key,))


def _add_cap_gate(
    add_gate,
    *,
    gate_id: str,
    state: Mapping[str, Any],
    limits: Mapping[str, Any],
    current_key: str,
    limit_key: str,
    source_key: str,
    label: str,
) -> None:
    requested = _number_or_none(state.get("requested_notional_usd"))
    current = _number_or_none(state.get(current_key))
    limit = _number_or_none(limits.get(limit_key))
    if requested is None or current is None or limit is None:
        add_gate(
            gate_id,
            False,
            STATUS_UNKNOWN,
            f"{label} cannot be evaluated because requested/current/limit values are missing.",
            source_keys=(source_key, "risk_limits"),
        )
        return
    projected = round(current + requested, 2)
    if projected > limit:
        add_gate(
            gate_id,
            False,
            "cap_exceeded",
            f"{label} cap would be exceeded by the review context.",
            source_keys=(source_key, "risk_limits"),
            detail=f"projected={projected}; limit={limit}",
        )
        return
    add_gate(
        gate_id,
        True,
        STATUS_PASSED_REVIEW_CHECK,
        f"{label} cap is within the supplied review limits.",
        source_keys=(source_key, "risk_limits"),
    )


def _add_daily_loss_gate(add_gate, *, state: Mapping[str, Any], limits: Mapping[str, Any]) -> None:
    daily_loss = _number_or_none(state.get("realized_daily_loss_usd"))
    limit = _number_or_none(limits.get("max_daily_loss_usd"))
    if daily_loss is None or limit is None:
        add_gate(
            "daily_loss_cap",
            False,
            STATUS_UNKNOWN,
            "Daily loss cap cannot be evaluated because local review values are missing.",
            source_keys=("daily_loss_state", "risk_limits"),
        )
        return
    if daily_loss >= limit:
        add_gate(
            "daily_loss_cap",
            False,
            "cap_exceeded",
            "Daily loss cap is reached or exceeded in the supplied review state.",
            source_keys=("daily_loss_state", "risk_limits"),
            detail=f"daily_loss={daily_loss}; limit={limit}",
        )
        return
    add_gate(
        "daily_loss_cap",
        True,
        STATUS_PASSED_REVIEW_CHECK,
        "Daily loss cap is within the supplied review limits.",
        source_keys=("daily_loss_state", "risk_limits"),
    )


def _add_duplicate_attempt_gate(add_gate, *, state: Mapping[str, Any]) -> None:
    attempt_key = clean_text(state.get("attempt_key"))
    prior = state.get("prior_attempt_keys")
    if not attempt_key or not isinstance(prior, list):
        add_gate(
            "duplicate_attempt_guard",
            False,
            STATUS_UNKNOWN,
            "Duplicate attempt guard cannot be evaluated because the attempt key or prior-attempt list is missing.",
            source_keys=("attempt_guard_state",),
        )
        return
    prior_keys = {clean_text(item) for item in prior if clean_text(item)}
    if attempt_key in prior_keys:
        add_gate(
            "duplicate_attempt_guard",
            False,
            "duplicate_detected",
            "Duplicate attempt guard detected a prior matching attempt key.",
            source_keys=("attempt_guard_state",),
        )
        return
    add_gate(
        "duplicate_attempt_guard",
        True,
        STATUS_PASSED_REVIEW_CHECK,
        "Duplicate attempt guard found no matching prior attempt key.",
        source_keys=("attempt_guard_state",),
    )


def _add_halt_state_gate(add_gate, *, state: Mapping[str, Any]) -> None:
    halt_state_known = state.get("halt_state_known") is True
    active_halts = state.get("active_halt_states")
    if not halt_state_known or not isinstance(active_halts, list):
        add_gate(
            "halt_states",
            False,
            STATUS_UNKNOWN,
            "Halt state is unknown; unknown halt state blocks the review.",
            source_keys=("halt_state",),
        )
        return
    active = [clean_text(item) for item in active_halts if clean_text(item)]
    if active:
        add_gate(
            "halt_states",
            False,
            "halt_active",
            "One or more halt states are active.",
            source_keys=("halt_state",),
            detail=", ".join(active),
        )
        return
    add_gate(
        "halt_states",
        True,
        STATUS_PASSED_REVIEW_CHECK,
        "No halt states are active in the supplied local review state.",
        source_keys=("halt_state",),
    )


def _gate_evaluation(
    *,
    gate_id: str,
    passed: bool,
    evidence_status: str,
    reason: str,
    source_keys: Sequence[str],
    detail: str,
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": RISK_ENGINE_V2_GATE_EVALUATION_CONTRACT,
        "task_id": TASK_ID,
        "gate_id": clean_text(gate_id),
        "gate_label": risk_engine_v2_gate_label(gate_id),
        "category": risk_engine_v2_category_for_gate(gate_id),
        "passed": passed is True,
        "evidence_status": clean_text(evidence_status) or STATUS_UNKNOWN,
        "reason": clean_text(reason),
        "detail": clean_text(detail),
        "source_keys": [clean_text(item) for item in source_keys if clean_text(item)],
        "blocks_live_execution": passed is not True,
        "generated_at": generated_at,
    }
    value.update(risk_engine_v2_safety_flags())
    return value


def _blocker_for_gate(
    *,
    gate_id: str,
    reason: str,
    evidence_status: str,
    source_keys: Sequence[str],
    generated_at: str,
) -> dict[str, Any]:
    return RiskEngineV2Blocker(
        blocker_id=risk_engine_v2_blocker_id_for_gate(gate_id),
        gate_id=gate_id,
        category=risk_engine_v2_category_for_gate(gate_id),
        reason=reason,
        evidence_status=evidence_status,
        source_keys=tuple(source_keys),
        generated_at=generated_at,
    ).to_dict()


def _build_blockers_artifact(
    *,
    market_symbol: str,
    strategy_name: str,
    blockers: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    rows = [dict(row) for row in blockers]
    value = {
        "contract_version": RISK_ENGINE_V2_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "blockers": rows,
        "blocker_ids": [clean_text(row.get("blocker_id")) for row in rows],
        "blocker_count": len(rows),
        "remaining_blocker_count": len(rows),
        "resolved_blocker_count": 0,
        "generated_at": generated_at,
    }
    value.update(risk_engine_v2_safety_flags())
    return value


def _build_gate_evaluations_artifact(
    *,
    market_symbol: str,
    strategy_name: str,
    gate_evaluations: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    rows = [dict(row) for row in gate_evaluations]
    value = {
        "contract_version": RISK_ENGINE_V2_GATE_EVALUATION_CONTRACT + ".list",
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "gate_evaluations": rows,
        "gate_count": len(rows),
        "required_gate_ids": list(REQUIRED_GATE_IDS),
        "passed_gate_count": len([row for row in rows if row.get("passed") is True]),
        "blocked_gate_count": len([row for row in rows if row.get("passed") is not True]),
        "generated_at": generated_at,
    }
    value.update(risk_engine_v2_safety_flags())
    return value


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    gate_evaluations: Sequence[Mapping[str, Any]],
    blockers: Sequence[Mapping[str, Any]],
    path_refs: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    gates = [dict(row) for row in gate_evaluations]
    rows = [dict(row) for row in blockers]
    unknown_blockers = [
        clean_text(row.get("blocker_id"))
        for row in rows
        if clean_text(row.get("evidence_status")) in {STATUS_UNKNOWN, STATUS_MISSING}
    ]
    value = {
        "contract_version": RISK_ENGINE_V2_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "gate_count": len(gates),
        "passed_gate_count": len([row for row in gates if row.get("passed") is True]),
        "blocked_gate_count": len([row for row in gates if row.get("passed") is not True]),
        "remaining_blocker_count": len(rows),
        "resolved_blocker_count": 0,
        "blocker_ids": [clean_text(row.get("blocker_id")) for row in rows],
        "unknown_blocker_ids": unknown_blockers,
        "unknown_blocker_count": len(unknown_blockers),
        "allowed_for_live": False,
        "risk_engine_v2_executable_for_live": False,
        "first_supervised_tiny_order_blocked": True,
        "live_authorization": "blocked",
        "operator_approval": "required",
        "artifact_path": clean_text(path_refs.get("result")),
        "latest_status_path": clean_text(path_refs.get("latest_status")),
        "blockers_path": clean_text(path_refs.get("blockers")),
        "gate_evaluations_path": clean_text(path_refs.get("gate_evaluations")),
        "safety_snapshot_path": clean_text(path_refs.get("safety_snapshot")),
        "operator_summary_path": clean_text(path_refs.get("operator_summary_md")),
        "generated_at": generated_at,
    }
    value.update(risk_engine_v2_safety_flags())
    return value


def _default_risk_limits() -> dict[str, Any]:
    return {
        "max_total_exposure_usd": 10.0,
        "max_market_exposure_usd": 5.0,
        "max_daily_loss_usd": 5.0,
    }


def _evidence_status(evidence: Mapping[str, Any]) -> str:
    status = clean_text(evidence.get("status") or evidence.get("evidence_status")).lower()
    if not status:
        return STATUS_UNKNOWN
    return status


def _source_safety_ok(evidence: Mapping[str, Any]) -> bool:
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if field in evidence and evidence.get(field) is not False:
            return False
    return True


def _number_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _blocking_evidence_statuses() -> set[str]:
    return set(BLOCKING_EVIDENCE_STATUSES)
