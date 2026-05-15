from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.pre_live_tiny_order_gate_models import (
    MODE,
    STATUS_BLOCKED,
    STATUS_MISSING,
    STATUS_PRESENT,
    STATUS_UNAVAILABLE,
    TASK_ID,
    LatestPreLiveTinyOrderGateStatus,
    PreLiveTinyOrderBlocker,
    PreLiveTinyOrderChecklist,
    PreLiveTinyOrderGateConfig,
    PreLiveTinyOrderGateResult,
    PreLiveTinyOrderReadinessSummary,
    build_pre_live_tiny_order_blockers_report,
    pre_live_tiny_order_gate_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/pre_live_tiny_order_gate_062p")
DEFAULT_TINY_SCAFFOLD_LATEST_STATUS_061_PATH = Path(
    "pm_bot/trading_core/artifacts/tiny_order_scaffold_061/latest_tiny_order_scaffold_status_061.json"
)
DEFAULT_TINY_SCAFFOLD_RESULT_061_PATH = Path(
    "pm_bot/trading_core/artifacts/tiny_order_scaffold_061/tiny_order_scaffold_061_result.json"
)
DEFAULT_SIGNER_BOUNDARY_LATEST_STATUS_060_PATH = Path(
    "pm_bot/trading_core/artifacts/signer_boundary_preflight_060/latest_signer_boundary_preflight_status_060.json"
)
DEFAULT_SIGNER_BOUNDARY_RESULT_060_PATH = Path(
    "pm_bot/trading_core/artifacts/signer_boundary_preflight_060/signer_boundary_preflight_060_result.json"
)
DEFAULT_AUTH_PREFLIGHT_LATEST_STATUS_059_PATH = Path(
    "pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/latest_no_order_auth_get_preflight_status_059.json"
)
DEFAULT_AUTH_PREFLIGHT_RESULT_059_PATH = Path(
    "pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/no_order_auth_get_preflight_059_result.json"
)
DEFAULT_AUTH_PREFLIGHT_LATEST_STATUS_057_PATH = Path(
    "pm_bot/trading_core/artifacts/authenticated_clob_preflight_057/latest_authenticated_clob_preflight_status_057.json"
)
DEFAULT_SAFETY_SCAN_LATEST_STATUS_060Q_PATH = Path(
    "pm_bot/trading_core/artifacts/static_safety_invariant_report_060q/latest_static_safety_invariant_report_status_060q.json"
)
DEFAULT_SAFETY_SCAN_RESULT_060Q_PATH = Path(
    "pm_bot/trading_core/artifacts/static_safety_invariant_report_060q/static_safety_invariant_report_060q_result.json"
)

DEFAULT_MAX_NOTIONAL = 1.0
DEFAULT_MARKET_WHITELIST = ("BTC",)
NEXT_OPERATOR_ACTION = "review blockers before any future live-enabling task"

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
)


def pre_live_tiny_order_gate_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "pre_live_tiny_order_gate_062p_result.json",
        "operator_md": root / "pre_live_tiny_order_gate_062p_operator.md",
        "latest_status": root / "latest_pre_live_tiny_order_gate_status_062p.json",
        "checklist": root / "pre_live_tiny_order_checklist_062p.json",
        "blockers": root / "pre_live_tiny_order_blockers_062p.json",
        "readiness_summary": root / "pre_live_tiny_order_readiness_summary_062p.json",
    }


def run_pre_live_tiny_order_gate(
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    dry_run: bool = True,
    from_latest_tiny_scaffold: bool = True,
    require_operator_approval: bool = False,
    max_notional: float = DEFAULT_MAX_NOTIONAL,
    market_whitelist: Sequence[str] | str = DEFAULT_MARKET_WHITELIST,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("pre-live tiny order gate requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    strategy_name = clean_text(strategy) or "tiny-momentum"
    whitelist = _normalize_market_whitelist(market_whitelist)
    max_notional_value = _positive_float(max_notional, DEFAULT_MAX_NOTIONAL)
    paths = pre_live_tiny_order_gate_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    tiny_source = _load_latest_source(
        (
            DEFAULT_TINY_SCAFFOLD_LATEST_STATUS_061_PATH,
            DEFAULT_TINY_SCAFFOLD_RESULT_061_PATH,
        )
        if from_latest_tiny_scaffold
        else (DEFAULT_TINY_SCAFFOLD_LATEST_STATUS_061_PATH,),
        market=market_symbol,
        strategy=strategy_name,
    )
    signer_source = _load_latest_source(
        (
            DEFAULT_SIGNER_BOUNDARY_LATEST_STATUS_060_PATH,
            DEFAULT_SIGNER_BOUNDARY_RESULT_060_PATH,
        ),
        market=market_symbol,
        strategy=strategy_name,
    )
    auth_source = _load_latest_source(
        (
            DEFAULT_AUTH_PREFLIGHT_LATEST_STATUS_059_PATH,
            DEFAULT_AUTH_PREFLIGHT_RESULT_059_PATH,
            DEFAULT_AUTH_PREFLIGHT_LATEST_STATUS_057_PATH,
        ),
        market=market_symbol,
        strategy="",
    )
    safety_source = _load_latest_source(
        (
            DEFAULT_SAFETY_SCAN_LATEST_STATUS_060Q_PATH,
            DEFAULT_SAFETY_SCAN_RESULT_060Q_PATH,
        ),
        market="",
        strategy="",
    )

    tiny_status = dict(tiny_source.get("value") or {})
    signer_status = dict(signer_source.get("value") or {})
    auth_status = dict(auth_source.get("value") or {})
    safety_status = dict(safety_source.get("value") or {})

    source_tiny_scaffold_path = clean_text(tiny_source.get("path"))
    source_signer_boundary_path = clean_text(signer_source.get("path"))
    source_auth_preflight_path = clean_text(auth_source.get("path"))
    source_safety_scan_path = clean_text(safety_source.get("path"))

    tiny_candidate_present = _tiny_candidate_present(tiny_status)
    approval_packet_present = _approval_packet_present(tiny_status)
    source_hard_limits_passed = tiny_status.get("hard_limits_passed") is True
    candidate_notional = _number_or_none(tiny_status.get("candidate_notional"))
    hard_limits_passed = bool(
        source_tiny_scaffold_path
        and source_hard_limits_passed
        and (candidate_notional is None or candidate_notional <= max_notional_value)
    )
    market_whitelisted = market_symbol in whitelist
    signer_boundary_present = bool(source_signer_boundary_path)
    auth_preflight_present = bool(source_auth_preflight_path)
    safety_scan_present = bool(source_safety_scan_path)

    blockers = _build_blockers(
        tiny_scaffold_present=bool(source_tiny_scaffold_path),
        signer_boundary_present=signer_boundary_present,
        auth_preflight_present=auth_preflight_present,
        safety_scan_present=safety_scan_present,
        tiny_candidate_present=tiny_candidate_present,
        approval_packet_present=approval_packet_present,
        hard_limits_passed=hard_limits_passed,
        market_whitelisted=market_whitelisted,
        generated_at=generated_at,
    )
    status = _overall_status(blockers)
    common_kwargs = {
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "source_tiny_scaffold_path": source_tiny_scaffold_path,
        "source_signer_boundary_path": source_signer_boundary_path,
        "source_auth_preflight_path": source_auth_preflight_path,
        "source_safety_scan_path": source_safety_scan_path,
        "tiny_candidate_present": tiny_candidate_present,
        "approval_packet_present": approval_packet_present,
        "operator_approved": False,
        "candidate_is_executable": False,
        "hard_limits_passed": hard_limits_passed,
        "market_whitelisted": market_whitelisted,
        "signer_boundary_present": signer_boundary_present,
        "auth_preflight_present": auth_preflight_present,
        "safety_scan_present": safety_scan_present,
        "signing_available": False,
        "signed_payload_available": False,
        "order_submission_available": False,
        "wallet_available": False,
        "cancel_plan_present": False,
        "failure_plan_present": False,
        "live_execution_approved": False,
        "ready_for_future_live_enablement": False,
        "allowed_for_live": False,
        "generated_at": generated_at,
    }
    config = PreLiveTinyOrderGateConfig(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        source_tiny_scaffold_path=source_tiny_scaffold_path,
        source_signer_boundary_path=source_signer_boundary_path,
        source_auth_preflight_path=source_auth_preflight_path,
        source_safety_scan_path=source_safety_scan_path,
        max_notional=max_notional_value,
        market_whitelist=tuple(whitelist),
        from_latest_tiny_scaffold=from_latest_tiny_scaffold is True,
        require_operator_approval=require_operator_approval is True,
        artifacts_dir=normalize_path(paths["root"]),
        generated_at=generated_at,
    ).to_dict()
    checklist = PreLiveTinyOrderChecklist(blockers=tuple(blockers), **common_kwargs).to_dict()
    readiness_summary = PreLiveTinyOrderReadinessSummary(
        blocker_count=len(blockers),
        blockers=tuple(blockers),
        next_operator_action=NEXT_OPERATOR_ACTION,
        **common_kwargs,
    ).to_dict()
    blockers_report = build_pre_live_tiny_order_blockers_report(blockers, generated_at=generated_at)
    latest_status = LatestPreLiveTinyOrderGateStatus(
        status=status,
        blocker_count=len(blockers),
        blockers=tuple(blockers),
        next_operator_action=NEXT_OPERATOR_ACTION,
        artifact_path=path_refs["result"],
        latest_status_path=path_refs["latest_status"],
        operator_markdown_path=path_refs["operator_md"],
        checklist_path=path_refs["checklist"],
        blockers_path=path_refs["blockers"],
        readiness_summary_path=path_refs["readiness_summary"],
        **common_kwargs,
    ).to_dict()
    result = PreLiveTinyOrderGateResult(
        status=status,
        config=config,
        checklist=checklist,
        readiness_summary=readiness_summary,
        latest_status=latest_status,
        blockers=tuple(blockers),
        artifact_paths=path_refs,
        operator_summary=_operator_summary(
            source_tiny_scaffold_path=source_tiny_scaffold_path,
            source_signer_boundary_path=source_signer_boundary_path,
            source_auth_preflight_path=source_auth_preflight_path,
            source_safety_scan_path=source_safety_scan_path,
        ),
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["checklist"], checklist)
    write_json(paths["blockers"], blockers_report)
    write_json(paths["readiness_summary"], readiness_summary)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_pre_live_tiny_order_gate_markdown(result))
    return result


def render_pre_live_tiny_order_gate_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Pre-live tiny order gate completed.",
            f"Market: {clean_text(value.get('market') or value.get('market_symbol'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Mode: {MODE}",
            f"Tiny scaffold: {clean_text(value.get('tiny_scaffold') or STATUS_MISSING)}",
            "Operator approved: false",
            "Candidate executable: false",
            "Signing: blocked",
            "Order submission: blocked",
            "Wallet: blocked",
            "Live execution: blocked",
            "Ready for future live enablement: false",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_pre_live_tiny_order_gate_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    checklist = dict(value.get("checklist", {}))
    summary = dict(value.get("readiness_summary", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    rows = [
        _markdown_check_row("Tiny scaffold source", checklist.get("source_tiny_scaffold_path") or "missing"),
        _markdown_check_row("Tiny candidate present", _bool_text(checklist.get("tiny_candidate_present"))),
        _markdown_check_row("Approval packet present", _bool_text(checklist.get("approval_packet_present"))),
        _markdown_check_row("Operator approved", "false"),
        _markdown_check_row("Candidate executable", "false"),
        _markdown_check_row("Hard limits passed", _bool_text(checklist.get("hard_limits_passed"))),
        _markdown_check_row("Market whitelisted", _bool_text(checklist.get("market_whitelisted"))),
        _markdown_check_row("Signer boundary source", checklist.get("source_signer_boundary_path") or "missing"),
        _markdown_check_row("Auth preflight source", checklist.get("source_auth_preflight_path") or "missing"),
        _markdown_check_row("Safety scan source", checklist.get("source_safety_scan_path") or "missing"),
        _markdown_check_row("Signing", "blocked"),
        _markdown_check_row("Signed payload generation", "blocked"),
        _markdown_check_row("Order submission", "blocked"),
        _markdown_check_row("Wallet", "blocked"),
        _markdown_check_row("Live execution", "blocked"),
        _markdown_check_row("Ready for future live enablement", "false"),
    ]
    lines = [
        "# PMBOT Pre-Live Tiny Order Gate 062P",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `preflight / review-only`",
        "- execution_mode: `preflight`",
        "- review_only: `true`",
        "- preflight_only: `true`",
        "- gate_only: `true`",
        "",
        "## Source Artifacts",
        "",
        f"- Tiny scaffold 061: `{value.get('source_tiny_scaffold_path') or 'missing'}`",
        f"- Signer boundary 060: `{value.get('source_signer_boundary_path') or 'missing'}`",
        f"- No-order auth preflight 059: `{value.get('source_auth_preflight_path') or 'missing'}`",
        f"- Static safety scan 060Q: `{value.get('source_safety_scan_path') or 'missing'}`",
        "",
        "## Checklist",
        "",
        "| Check | Status |",
        "| --- | --- |",
        *rows,
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
        "",
        "## Guarantees",
        "",
        "- operator_approved=false",
        "- candidate_is_executable=false",
        "- signing blocked",
        "- signed payload generation blocked",
        "- order submission blocked",
        "- order cancellation blocked",
        "- wallet blocked",
        "- live execution blocked",
        "- ready_for_future_live_enablement=false",
        "- allowed_for_live=false",
        "- resolved_blocker_count=0",
        "",
        "## Next Operator Action",
        "",
        f"- {summary.get('next_operator_action') or NEXT_OPERATOR_ACTION}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "pre-live tiny order gate is review-only; unsupported live/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


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
    if market:
        source_market = clean_text(value.get("market_symbol") or value.get("market")).upper()
        if source_market and source_market != clean_text(market).upper():
            return False
    if strategy:
        source_strategy = clean_text(value.get("strategy_name"))
        if source_strategy and source_strategy != clean_text(strategy):
            return False
    return True


def _tiny_candidate_present(value: Mapping[str, Any]) -> bool:
    if clean_text(value.get("tiny_candidate")) == "created":
        return True
    if value.get("tiny_candidate_present") is True:
        return True
    nested = value.get("tiny_order_candidate")
    return isinstance(nested, Mapping) and clean_text(nested.get("status")) == "created"


def _approval_packet_present(value: Mapping[str, Any]) -> bool:
    if clean_text(value.get("approval_packet")) == "created":
        return True
    if value.get("approval_packet_present") is True or value.get("approval_packet_created") is True:
        return True
    nested = value.get("manual_tiny_order_approval_packet")
    return isinstance(nested, Mapping) and clean_text(nested.get("status")) == "created"


def _build_blockers(
    *,
    tiny_scaffold_present: bool,
    signer_boundary_present: bool,
    auth_preflight_present: bool,
    safety_scan_present: bool,
    tiny_candidate_present: bool,
    approval_packet_present: bool,
    hard_limits_passed: bool,
    market_whitelisted: bool,
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if not tiny_scaffold_present:
        blockers.append(
            _blocker(
                "missing_tiny_scaffold",
                "source_artifact",
                "Latest 061 tiny order scaffold artifact is missing.",
                generated_at=generated_at,
            )
        )
    if not signer_boundary_present:
        blockers.append(
            _blocker(
                "missing_signer_boundary",
                "source_artifact",
                "Latest 060 signer boundary artifact is missing.",
                generated_at=generated_at,
            )
        )
    if not auth_preflight_present:
        blockers.append(
            _blocker(
                "missing_auth_preflight",
                "source_artifact",
                "Latest 059 no-order authenticated preflight artifact is missing.",
                generated_at=generated_at,
            )
        )
    if not safety_scan_present:
        blockers.append(
            _blocker(
                "missing_safety_scan",
                "source_artifact",
                "Latest 060Q static safety scan artifact is missing.",
                generated_at=generated_at,
            )
        )
    if tiny_scaffold_present and not tiny_candidate_present:
        blockers.append(
            _blocker(
                "tiny_candidate_missing",
                "tiny_scaffold",
                "Tiny candidate is missing from the latest scaffold artifact.",
                generated_at=generated_at,
            )
        )
    if tiny_scaffold_present and not approval_packet_present:
        blockers.append(
            _blocker(
                "approval_packet_missing",
                "manual_approval",
                "Manual approval packet is missing from the latest scaffold artifact.",
                generated_at=generated_at,
            )
        )
    if not hard_limits_passed:
        blockers.append(
            _blocker(
                "hard_limits_not_passed",
                "hard_limits",
                "Tiny order hard limits are not confirmed for the pre-live gate.",
                generated_at=generated_at,
            )
        )
    if not market_whitelisted:
        blockers.append(
            _blocker(
                "market_not_whitelisted",
                "market_whitelist",
                "Market is not included in the configured pre-live whitelist.",
                generated_at=generated_at,
            )
        )
    blockers.extend(
        [
            _blocker(
                "operator_approved_false",
                "manual_approval",
                "operator_approved remains false; this gate cannot approve live execution.",
                generated_at=generated_at,
            ),
            _blocker(
                "candidate_non_executable",
                "tiny_candidate",
                "candidate_is_executable remains false; the candidate is for review only.",
                generated_at=generated_at,
            ),
            _blocker(
                "signing_unavailable",
                "signing_boundary",
                "Signing is unavailable and blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "signed_payload_unavailable",
                "signed_payload_generation",
                "Signed payload generation is unavailable and blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "order_submission_unavailable",
                "order_submission",
                "Order submission and cancellation are unavailable and blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "wallet_unavailable",
                "wallet_boundary",
                "Wallet connection and wallet signing are unavailable and blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "live_execution_not_approved",
                "live_execution",
                "Live execution approval is false and allowed_for_live remains false.",
                generated_at=generated_at,
            ),
            _blocker(
                "cancel_plan_missing",
                "operator_checklist",
                "Rollback/cancel planning remains checklist-only and is not present as an executable plan.",
                generated_at=generated_at,
            ),
            _blocker(
                "failure_plan_missing",
                "operator_checklist",
                "Failure handling planning remains checklist-only and is not present as an executable plan.",
                generated_at=generated_at,
            ),
            _blocker(
                "live_enablement_task_not_present",
                "future_live_enablement",
                "A separate operator-approved live-enabling task is required before any first tiny live order.",
                generated_at=generated_at,
            ),
        ]
    )
    return blockers


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    return PreLiveTinyOrderBlocker(
        blocker_id=clean_text(blocker_id),
        blocker_category=clean_text(category),
        reason=clean_text(reason),
        generated_at=generated_at,
    ).to_dict()


def _overall_status(blockers: Sequence[Mapping[str, Any]]) -> str:
    source_missing = {
        "missing_tiny_scaffold",
        "missing_signer_boundary",
        "missing_auth_preflight",
        "missing_safety_scan",
    }
    blocker_ids = {clean_text(row.get("blocker_id")) for row in blockers if isinstance(row, Mapping)}
    if blocker_ids & source_missing:
        return "pre_live_tiny_order_gate_incomplete_missing_source_live_blocked"
    return "pre_live_tiny_order_gate_completed_live_blocked"


def _operator_summary(
    *,
    source_tiny_scaffold_path: str,
    source_signer_boundary_path: str,
    source_auth_preflight_path: str,
    source_safety_scan_path: str,
) -> str:
    return (
        "Pre-live tiny order gate completed as review-only. Source tiny scaffold="
        + (clean_text(source_tiny_scaffold_path) or "missing")
        + "; source signer boundary="
        + (clean_text(source_signer_boundary_path) or "missing")
        + "; source auth preflight="
        + (clean_text(source_auth_preflight_path) or "missing")
        + "; source safety scan="
        + (clean_text(source_safety_scan_path) or "missing")
        + "; operator_approved=false; candidate_is_executable=false; signing, signed payload generation, "
        "order submission, cancellation, wallet use, account runtime reads, live execution, and autonomous "
        "trading are blocked."
    )


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _number_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _positive_float(value: Any, fallback: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


def _normalize_market_whitelist(value: Sequence[str] | str) -> list[str]:
    if isinstance(value, str):
        rows = [row.strip() for row in value.split(",")]
    else:
        rows = [clean_text(row) for row in value]
    normalized = [row.upper() for row in rows if row]
    return normalized or list(DEFAULT_MARKET_WHITELIST)


def _markdown_check_row(name: str, status: Any) -> str:
    return f"| {clean_text(name)} | `{clean_text(status)}` |"


def _bool_text(value: Any) -> str:
    return "true" if value is True else "false"
