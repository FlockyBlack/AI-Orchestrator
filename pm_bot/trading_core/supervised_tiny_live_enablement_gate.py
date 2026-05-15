from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text
from pm_bot.trading_core.supervised_tiny_live_enablement_models import (
    MODE,
    REQUIRED_UNRESOLVED_BLOCKER_IDS,
    STATUS_BLOCKED,
    STATUS_MISSING,
    STATUS_PRESENT,
    TASK_ID,
    LATEST_SUPERVISED_TINY_LIVE_ENABLEMENT_STATUS_CONTRACT,
    SupervisedTinyLiveBlocker,
    SupervisedTinyLiveBlockerMatrix,
    SupervisedTinyLiveCancelPlan,
    SupervisedTinyLiveEnablementGate,
    SupervisedTinyLiveEnvReadiness,
    SupervisedTinyLiveFailurePlan,
    SupervisedTinyLiveKillSwitchPlan,
    SupervisedTinyLiveManualApprovalPacket,
    SupervisedTinyLiveOperatorChecklist,
    SupervisedTinyLiveReadinessSummary,
    SupervisedTinyLiveRiskLimits,
    supervised_tiny_live_enablement_safety_flags,
)

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063")
DEFAULT_PRE_LIVE_TINY_ORDER_GATE_062P_LATEST_STATUS_PATH = Path(
    "pm_bot/trading_core/artifacts/pre_live_tiny_order_gate_062p/latest_pre_live_tiny_order_gate_status_062p.json"
)
DEFAULT_PRE_LIVE_TINY_ORDER_GATE_062P_RESULT_PATH = Path(
    "pm_bot/trading_core/artifacts/pre_live_tiny_order_gate_062p/pre_live_tiny_order_gate_062p_result.json"
)
DEFAULT_TINY_ORDER_SCAFFOLD_061_LATEST_STATUS_PATH = Path(
    "pm_bot/trading_core/artifacts/tiny_order_scaffold_061/latest_tiny_order_scaffold_status_061.json"
)
DEFAULT_TINY_ORDER_SCAFFOLD_061_RESULT_PATH = Path(
    "pm_bot/trading_core/artifacts/tiny_order_scaffold_061/tiny_order_scaffold_061_result.json"
)

DEFAULT_MAX_ORDER_NOTIONAL_USD = 1.0
DEFAULT_MAX_DAILY_NOTIONAL_USD = 1.0
DEFAULT_MAX_ORDERS_PER_DAY = 1
DEFAULT_MAX_MARKET_COUNT = 1
DEFAULT_ALLOWED_MARKET = "BTC"
DEFAULT_ALLOWED_STRATEGY = "tiny-momentum"

DEFAULT_READINESS_MARKERS = (
    "PMBOT_TINY_LIVE_OPERATOR_APPROVAL_RECORD_PRESENT",
    "PMBOT_TINY_LIVE_RISK_LIMITS_REVIEWED",
    "PMBOT_TINY_LIVE_KILL_SWITCH_REVIEWED",
    "PMBOT_TINY_LIVE_CANCEL_PLAN_REVIEWED",
    "PMBOT_TINY_LIVE_FAILURE_PLAN_REVIEWED",
    "PMBOT_TINY_LIVE_AUTH_BOUNDARY_REVIEWED",
    "PMBOT_TINY_LIVE_SIGNER_BOUNDARY_REVIEWED",
    "PMBOT_TINY_LIVE_WALLET_BOUNDARY_REVIEWED",
)

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--signing",
    "--sign",
    "--submit",
    "--cancel",
    "--approve-live",
    "--private-key",
    "--wallet-connect",
    "--balances",
    "--positions",
    "--fills",
    "--pnl",
    "--order-id",
    "--tx-hash",
)


def supervised_tiny_live_enablement_gate_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "supervised_tiny_live_enablement_gate_063_result.json",
        "operator_md": root / "supervised_tiny_live_enablement_gate_063_operator.md",
        "latest_status": root / "latest_supervised_tiny_live_enablement_status_063.json",
        "operator_checklist": root / "supervised_tiny_live_operator_checklist_063.json",
        "blockers": root / "supervised_tiny_live_blockers_063.json",
        "risk_limits": root / "supervised_tiny_live_risk_limits_063.json",
        "kill_switch_plan": root / "supervised_tiny_live_kill_switch_plan_063.json",
        "cancel_plan": root / "supervised_tiny_live_cancel_plan_063.json",
        "failure_plan": root / "supervised_tiny_live_failure_plan_063.json",
        "env_readiness": root / "supervised_tiny_live_env_readiness_063.json",
        "manual_approval_packet": root / "supervised_tiny_live_manual_approval_packet_063.json",
    }


def run_supervised_tiny_live_enablement_gate(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    readiness_markers: Sequence[str] = DEFAULT_READINESS_MARKERS,
    readiness_marker_presence: Mapping[str, bool] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("supervised tiny live enablement gate requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = supervised_tiny_live_enablement_gate_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    source_pre_live_gate = _load_latest_source(
        (
            DEFAULT_PRE_LIVE_TINY_ORDER_GATE_062P_LATEST_STATUS_PATH,
            DEFAULT_PRE_LIVE_TINY_ORDER_GATE_062P_RESULT_PATH,
        ),
        market=market_symbol,
        strategy=strategy_name,
    )
    source_tiny_scaffold = _load_latest_source(
        (
            DEFAULT_TINY_ORDER_SCAFFOLD_061_LATEST_STATUS_PATH,
            DEFAULT_TINY_ORDER_SCAFFOLD_061_RESULT_PATH,
        ),
        market=market_symbol,
        strategy=strategy_name,
    )
    source_pre_live_gate_path = clean_text(source_pre_live_gate.get("path"))
    source_tiny_scaffold_path = clean_text(source_tiny_scaffold.get("path"))

    marker_checks = _build_marker_checks(
        markers=readiness_markers,
        readiness_marker_presence=readiness_marker_presence,
    )
    env_readiness = SupervisedTinyLiveEnvReadiness(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        marker_checks=tuple(marker_checks),
        generated_at=generated_at,
    ).to_dict()
    risk_limits = SupervisedTinyLiveRiskLimits(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        max_order_notional_usd=DEFAULT_MAX_ORDER_NOTIONAL_USD,
        max_daily_notional_usd=DEFAULT_MAX_DAILY_NOTIONAL_USD,
        max_orders_per_day=DEFAULT_MAX_ORDERS_PER_DAY,
        max_market_count=DEFAULT_MAX_MARKET_COUNT,
        allowed_market=DEFAULT_ALLOWED_MARKET,
        allowed_strategy=DEFAULT_ALLOWED_STRATEGY,
        operator_approval_required_for_later_live_task=True,
        generated_at=generated_at,
    ).to_dict()
    kill_switch_plan = SupervisedTinyLiveKillSwitchPlan(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        stop_future_live_enablement_steps=(
            "Operator declines or withholds approval in the later live-enabling task.",
            "Keep operator_approved=false, allowed_for_live=false, and all execution flags false.",
            "Do not provide wallet, signer, authenticated trading, submission, or cancellation capability.",
            "Close the later task as blocked if any approval, limit, environment, or safety evidence is missing.",
        ),
        operator_confirmation_required=True,
        generated_at=generated_at,
    ).to_dict()
    cancel_plan = SupervisedTinyLiveCancelPlan(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        required_before_any_real_order=(
            "A later operator-approved task must document a verified cancellation path before any real order.",
            "The later task must define exact operator ownership, escalation, and stop conditions.",
            "The later task must prove cancellation readiness without this preparation package submitting or cancelling.",
            "If cancellation readiness is absent, the later task remains blocked.",
        ),
        operator_confirmation_required=True,
        generated_at=generated_at,
    ).to_dict()
    failure_plan = SupervisedTinyLiveFailurePlan(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        later_task_failure_steps=(
            "If placement, API, auth, network, wallet, signer, or cancellation readiness fails in a later task, stop.",
            "Record the failure as an operator artifact and keep all execution flags false.",
            "Do not retry autonomously, do not create background workers, and do not continue without operator review.",
            "Require a separate fix task and a separate approval task before any future live attempt.",
        ),
        operator_confirmation_required=True,
        generated_at=generated_at,
    ).to_dict()
    manual_approval_packet = SupervisedTinyLiveManualApprovalPacket(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        approval_required=True,
        approval_scope="first_tiny_live_order_preparation_only",
        later_live_enabling_task_required=True,
        generated_at=generated_at,
    ).to_dict()
    blockers = _build_blockers(generated_at=generated_at)
    blocker_matrix = SupervisedTinyLiveBlockerMatrix(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        blockers=tuple(blockers),
        generated_at=generated_at,
    ).to_dict()
    operator_checklist = SupervisedTinyLiveOperatorChecklist(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        source_pre_live_gate_path=source_pre_live_gate_path,
        source_tiny_scaffold_path=source_tiny_scaffold_path,
        risk_limits=risk_limits,
        kill_switch_plan=kill_switch_plan,
        cancel_plan=cancel_plan,
        failure_plan=failure_plan,
        env_readiness=env_readiness,
        manual_approval_packet=manual_approval_packet,
        blocker_matrix=blocker_matrix,
        generated_at=generated_at,
    ).to_dict()
    readiness_summary = SupervisedTinyLiveReadinessSummary(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        source_pre_live_gate_path=source_pre_live_gate_path,
        source_tiny_scaffold_path=source_tiny_scaffold_path,
        risk_limits_path=path_refs["risk_limits"],
        kill_switch_plan_path=path_refs["kill_switch_plan"],
        cancel_plan_path=path_refs["cancel_plan"],
        failure_plan_path=path_refs["failure_plan"],
        env_readiness_path=path_refs["env_readiness"],
        manual_approval_packet_path=path_refs["manual_approval_packet"],
        blocker_matrix_path=path_refs["blockers"],
        blocker_matrix=blocker_matrix,
        env_readiness=env_readiness,
        generated_at=generated_at,
    ).to_dict()
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        source_pre_live_gate_path=source_pre_live_gate_path,
        source_tiny_scaffold_path=source_tiny_scaffold_path,
        readiness_summary=readiness_summary,
        blocker_matrix=blocker_matrix,
        path_refs=path_refs,
        generated_at=generated_at,
    )
    result = SupervisedTinyLiveEnablementGate(
        status="supervised_tiny_live_enablement_prepared_live_blocked",
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        source_pre_live_gate_path=source_pre_live_gate_path,
        source_tiny_scaffold_path=source_tiny_scaffold_path,
        readiness_summary=readiness_summary,
        operator_checklist=operator_checklist,
        blocker_matrix=blocker_matrix,
        risk_limits=risk_limits,
        kill_switch_plan=kill_switch_plan,
        cancel_plan=cancel_plan,
        failure_plan=failure_plan,
        env_readiness=env_readiness,
        manual_approval_packet=manual_approval_packet,
        latest_status=latest_status,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["risk_limits"], risk_limits)
    write_json(paths["kill_switch_plan"], kill_switch_plan)
    write_json(paths["cancel_plan"], cancel_plan)
    write_json(paths["failure_plan"], failure_plan)
    write_json(paths["env_readiness"], env_readiness)
    write_json(paths["manual_approval_packet"], manual_approval_packet)
    write_json(paths["blockers"], blocker_matrix)
    write_json(paths["operator_checklist"], operator_checklist)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_supervised_tiny_live_enablement_gate_markdown(result))
    return result


def render_supervised_tiny_live_enablement_gate_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Supervised tiny live enablement gate completed.",
            f"Market: {clean_text(value.get('market') or value.get('market_symbol'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Mode: {MODE}",
            f"Pre-live source: {clean_text(value.get('source_pre_live_gate') or STATUS_MISSING)}",
            "Operator approved: false",
            "Candidate executable: false",
            "Live execution: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Signing: blocked",
            "Wallet: blocked",
            f"Resolved blockers: {int(value.get('resolved_blocker_count', 0) or 0)}",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_supervised_tiny_live_enablement_gate_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    risk_limits = dict(value.get("risk_limits", {}))
    env_readiness = dict(value.get("env_readiness", {}))
    manual_packet = dict(value.get("manual_approval_packet", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Supervised Tiny Live Enablement Gate 063",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `supervised tiny live enablement preparation / review-only`",
        "- execution_mode: `preflight`",
        "- preparation_only: `true`",
        "- non_executable: `true`",
        "",
        "## Source Artifacts",
        "",
        f"- Pre-live tiny order gate 062P: `{value.get('source_pre_live_gate_path') or 'missing'}`",
        f"- Tiny order scaffold 061: `{value.get('source_tiny_scaffold_path') or 'missing'}`",
        "",
        "## Tiny Limits",
        "",
        f"- max_order_notional_usd: `{risk_limits.get('max_order_notional_usd')}`",
        f"- max_daily_notional_usd: `{risk_limits.get('max_daily_notional_usd')}`",
        f"- max_orders_per_day: `{risk_limits.get('max_orders_per_day')}`",
        f"- max_market_count: `{risk_limits.get('max_market_count')}`",
        f"- allowed_market: `{risk_limits.get('allowed_market')}`",
        f"- allowed_strategy: `{risk_limits.get('allowed_strategy')}`",
        "- preparation constraints only; not executable",
        "",
        "## Manual Approval Packet",
        "",
        f"- approval_required: `{str(manual_packet.get('approval_required') is True).lower()}`",
        f"- approval_scope: `{manual_packet.get('approval_scope')}`",
        "- operator_approved=false",
        "- this packet is not executable",
        "- a later explicit live-enabling task is required",
        "- no order can be submitted from this packet",
        "",
        "## Environment Readiness",
        "",
        f"- marker_count: `{env_readiness.get('marker_count')}`",
        f"- missing_marker_count: `{env_readiness.get('missing_marker_count')}`",
        "- presence_only=true",
        "- values_redacted=true",
        "- raw_values_emitted=false",
        "",
        "## Descriptive Plans",
        "",
        "- kill switch plan exists and is not executable",
        "- cancellation prerequisites exist and are not executable",
        "- failure plan exists and is not executable",
        "",
        "## Blockers",
        "",
        *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
        "",
        "## Required False Flags",
        "",
        "- live_execution_approved=false",
        "- canary_executable_now=false",
        "- real_execution_available=false",
        "- order_submission_enabled=false",
        "- order_cancel_enabled=false",
        "- wallet_signing_enabled=false",
        "- signing_enabled=false",
        "- signed_payload_generation_enabled=false",
        "- signed_order_generation_enabled=false",
        "- authenticated_polymarket_enabled=false",
        "- live_connector_enabled=false",
        "- allowed_for_live=false",
        "- operator_approved=false",
        "- candidate_is_executable=false",
        "- resolved_blocker_count=0",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "supervised tiny live enablement gate is preparation-only; unsupported live/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    source_pre_live_gate_path: str,
    source_tiny_scaffold_path: str,
    readiness_summary: Mapping[str, Any],
    blocker_matrix: Mapping[str, Any],
    path_refs: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    blockers = [dict(row) for row in dict(blocker_matrix).get("blockers", []) if isinstance(row, Mapping)]
    value = {
        "contract_version": LATEST_SUPERVISED_TINY_LIVE_ENABLEMENT_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": "supervised_tiny_live_enablement_prepared_live_blocked",
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "readiness_status": STATUS_BLOCKED,
        "source_pre_live_gate": STATUS_PRESENT if source_pre_live_gate_path else STATUS_MISSING,
        "source_pre_live_gate_path": source_pre_live_gate_path,
        "source_tiny_scaffold": STATUS_PRESENT if source_tiny_scaffold_path else STATUS_MISSING,
        "source_tiny_scaffold_path": source_tiny_scaffold_path,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "required_unresolved_blocker_ids": list(REQUIRED_UNRESOLVED_BLOCKER_IDS),
        "unresolved_blocker_ids": [clean_text(row.get("blocker_id")) for row in blockers],
        "missing_env_marker_count": int(dict(readiness_summary).get("missing_env_marker_count", 0) or 0),
        "artifact_path": clean_text(path_refs.get("result")),
        "latest_status_path": clean_text(path_refs.get("latest_status")),
        "operator_markdown_path": clean_text(path_refs.get("operator_md")),
        "operator_checklist_path": clean_text(path_refs.get("operator_checklist")),
        "blockers_path": clean_text(path_refs.get("blockers")),
        "risk_limits_path": clean_text(path_refs.get("risk_limits")),
        "kill_switch_plan_path": clean_text(path_refs.get("kill_switch_plan")),
        "cancel_plan_path": clean_text(path_refs.get("cancel_plan")),
        "failure_plan_path": clean_text(path_refs.get("failure_plan")),
        "env_readiness_path": clean_text(path_refs.get("env_readiness")),
        "manual_approval_packet_path": clean_text(path_refs.get("manual_approval_packet")),
        "operator_summary": (
            "Preparation package generated; operator_approved=false, candidate_is_executable=false, live execution, "
            "submission, cancellation, signing, wallet, authenticated trading, and account runtime reads are blocked."
        ),
        "generated_at": generated_at,
    }
    value.update(supervised_tiny_live_enablement_safety_flags())
    return value


def _build_marker_checks(
    *,
    markers: Sequence[str],
    readiness_marker_presence: Mapping[str, bool] | None,
) -> list[dict[str, Any]]:
    explicit_presence = dict(readiness_marker_presence or {})
    checks: list[dict[str, Any]] = []
    for marker in markers:
        label = clean_text(marker)
        present = explicit_presence.get(label) is True if readiness_marker_presence is not None else label in os.environ
        checks.append(
            {
                "marker_label": label,
                "present": present,
                "required": True,
                "value_redacted": True,
                "raw_value_emitted": False,
            }
        )
    return checks


def _build_blockers(*, generated_at: str) -> list[dict[str, Any]]:
    rows = [
        (
            "operator_approved_false",
            "manual_approval",
            "operator_approved remains false; this preparation gate cannot approve live execution.",
        ),
        (
            "live_enablement_task_not_present",
            "future_live_enablement",
            "A separate explicit live-enabling task is required before any first tiny live order.",
        ),
        (
            "private_key_unavailable_and_not_read",
            "credential_boundary",
            "Private key material is unavailable and was not read.",
        ),
        ("wallet_unavailable", "wallet_boundary", "Wallet connection and wallet signing are unavailable."),
        ("signer_unavailable", "signing_boundary", "Signer runtime is unavailable and not instantiated."),
        ("signing_unavailable", "signing_boundary", "Signing is unavailable and blocked."),
        (
            "signed_payload_generation_unavailable",
            "signed_payload_generation",
            "Signed payload generation is unavailable and blocked.",
        ),
        ("order_submission_unavailable", "order_submission", "Order submission is unavailable and blocked."),
        ("order_cancel_unavailable", "order_cancellation", "Order cancellation is unavailable and blocked."),
        (
            "authenticated_trading_unavailable",
            "authenticated_trading",
            "Authenticated trading calls are unavailable and blocked.",
        ),
        (
            "balances_positions_fills_pnl_unavailable",
            "account_runtime",
            "Balance, position, fill, and PnL runtime reads are unavailable and blocked.",
        ),
        (
            "live_execution_not_approved",
            "live_execution",
            "Live execution approval is false and allowed_for_live remains false.",
        ),
        (
            "candidate_non_executable",
            "candidate_boundary",
            "candidate_is_executable remains false; any candidate is preparation-only.",
        ),
    ]
    return [
        SupervisedTinyLiveBlocker(
            blocker_id=blocker_id,
            blocker_category=category,
            reason=reason,
            generated_at=generated_at,
        ).to_dict()
        for blocker_id, category, reason in rows
    ]


def _load_latest_source(
    candidates: Sequence[Path],
    *,
    market: str,
    strategy: str,
) -> dict[str, Any]:
    for path in candidates:
        if not path.exists():
            continue
        loaded = _load_json_object(path)
        if not loaded:
            continue
        if not _source_matches(loaded, market=market, strategy=strategy):
            continue
        return {"path": normalize_path(path), "value": loaded}
    return {"path": "", "value": {}}


def _source_matches(value: Mapping[str, Any], *, market: str, strategy: str) -> bool:
    source_market = clean_text(value.get("market_symbol") or value.get("market")).upper()
    source_strategy = clean_text(value.get("strategy_name"))
    if source_market and source_market != clean_text(market).upper():
        return False
    if source_strategy and source_strategy != clean_text(strategy):
        return False
    return True


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}
