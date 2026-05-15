from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text
from pm_bot.trading_core.tiny_order_scaffold_models import (
    MODE,
    STATUS_BLOCKED,
    STATUS_CREATED,
    STATUS_MISSING_SOURCE,
    STATUS_UNAVAILABLE,
    TASK_ID,
    LatestTinyOrderScaffoldStatus,
    ManualTinyOrderApprovalPacket,
    TinyOrderCandidate,
    TinyOrderHardLimits,
    TinyOrderScaffoldBlocker,
    TinyOrderScaffoldResult,
    TinyOrderScaffoldRiskSummary,
    TinyOrderSubmissionAvailability,
    build_tiny_order_scaffold_blockers_report,
    tiny_order_scaffold_safety_flags,
)

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/tiny_order_scaffold_061")
DEFAULT_SIGNER_BOUNDARY_LATEST_STATUS_060_PATH = Path(
    "pm_bot/trading_core/artifacts/signer_boundary_preflight_060/latest_signer_boundary_preflight_status_060.json"
)
DEFAULT_SIGNER_BOUNDARY_RESULT_060_PATH = Path(
    "pm_bot/trading_core/artifacts/signer_boundary_preflight_060/signer_boundary_preflight_060_result.json"
)
DEFAULT_SIGNER_BOUNDARY_CANDIDATE_060_PATH = Path(
    "pm_bot/trading_core/artifacts/signer_boundary_preflight_060/live_candidate_order_intent_060.json"
)
DEFAULT_PAPER_INTENT_053_PATH = Path(
    "pm_bot/trading_core/artifacts/paper_trading_loop_053/paper_trading_order_intent_053.json"
)
DEFAULT_PAPER_RESULT_053_PATH = Path(
    "pm_bot/trading_core/artifacts/paper_trading_loop_053/paper_trading_loop_053_result.json"
)
DEFAULT_PUBLIC_MARKET_INTENT_054_PATH = Path(
    "pm_bot/trading_core/artifacts/public_market_paper_loop_054/public_market_order_intent_054.json"
)
DEFAULT_PUBLIC_MARKET_RESULT_054_PATH = Path(
    "pm_bot/trading_core/artifacts/public_market_paper_loop_054/public_market_paper_loop_054_result.json"
)

DEFAULT_MAX_NOTIONAL = 1.0
DEFAULT_MAX_SIZE = 1.0
DEFAULT_MAX_PRICE = 0.99

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
)


def tiny_order_scaffold_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "tiny_order_scaffold_061_result.json",
        "operator_md": root / "tiny_order_scaffold_061_operator.md",
        "latest_status": root / "latest_tiny_order_scaffold_status_061.json",
        "tiny_order_candidate": root / "tiny_order_candidate_061.json",
        "tiny_order_hard_limits": root / "tiny_order_hard_limits_061.json",
        "manual_tiny_order_approval_packet": root / "manual_tiny_order_approval_packet_061.json",
        "tiny_order_scaffold_risk_summary": root / "tiny_order_scaffold_risk_summary_061.json",
        "tiny_order_submission_availability": root / "tiny_order_submission_availability_061.json",
        "blockers": root / "tiny_order_scaffold_blockers_061.json",
    }


def run_tiny_order_scaffold(
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    dry_run: bool = True,
    from_latest_signer_boundary: bool = False,
    from_latest_paper_intent: bool = False,
    max_notional: float = DEFAULT_MAX_NOTIONAL,
    max_size: float = DEFAULT_MAX_SIZE,
    max_price: float = DEFAULT_MAX_PRICE,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("tiny order scaffold requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    strategy_name = clean_text(strategy) or "tiny-momentum"
    max_notional_value = _positive_float(max_notional, DEFAULT_MAX_NOTIONAL)
    max_size_value = _positive_float(max_size, DEFAULT_MAX_SIZE)
    max_price_value = _positive_float(max_price, DEFAULT_MAX_PRICE)
    paths = tiny_order_scaffold_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    source = _load_latest_source(
        market=market_symbol,
        strategy=strategy_name,
        from_latest_signer_boundary=from_latest_signer_boundary,
        from_latest_paper_intent=from_latest_paper_intent,
    )
    source_intent = dict(source.get("intent") or {})
    source_intent_path = clean_text(source.get("source_intent_path"))
    source_signer_boundary_path = clean_text(source.get("source_signer_boundary_path"))
    source_available = bool(source_intent)

    candidate_outcome = clean_text(source_intent.get("outcome") or source_intent.get("candidate_outcome"))
    candidate_side = clean_text(source_intent.get("side") or source_intent.get("candidate_side"))
    candidate_limit_price = _number_or_none(
        source_intent.get("limit_price"),
        source_intent.get("candidate_limit_price"),
    )
    candidate_size = _number_or_none(source_intent.get("size"), source_intent.get("candidate_size"))
    candidate_notional = _number_or_none(source_intent.get("notional"), source_intent.get("candidate_notional"))

    hard_limits_passed = source_available and _hard_limits_passed(
        candidate_limit_price=candidate_limit_price,
        candidate_size=candidate_size,
        candidate_notional=candidate_notional,
        max_notional=max_notional_value,
        max_size=max_size_value,
        max_price=max_price_value,
    )
    approval_packet_created = source_available
    status = _overall_status(source_available=source_available, hard_limits_passed=hard_limits_passed)
    candidate_status = STATUS_MISSING_SOURCE if not source_available else STATUS_CREATED
    hard_limits_status = STATUS_CREATED if hard_limits_passed else STATUS_BLOCKED
    approval_packet_status = STATUS_CREATED if approval_packet_created else STATUS_BLOCKED
    blockers = _build_blockers(
        source_available=source_available,
        hard_limits_passed=hard_limits_passed,
        approval_packet_created=approval_packet_created,
        generated_at=generated_at,
    )
    common_kwargs = {
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "source_intent_path": source_intent_path,
        "source_signer_boundary_path": source_signer_boundary_path,
        "candidate_outcome": candidate_outcome,
        "candidate_side": candidate_side,
        "candidate_limit_price": candidate_limit_price,
        "candidate_size": candidate_size,
        "candidate_notional": candidate_notional,
        "max_notional": max_notional_value,
        "max_size": max_size_value,
        "max_price": max_price_value,
        "hard_limits_passed": hard_limits_passed,
        "approval_packet_created": approval_packet_created,
        "blockers": tuple(blockers),
        "generated_at": generated_at,
    }

    candidate = TinyOrderCandidate(status=candidate_status, **common_kwargs).to_dict()
    hard_limits = TinyOrderHardLimits(status=hard_limits_status, **common_kwargs).to_dict()
    approval_packet = ManualTinyOrderApprovalPacket(status=approval_packet_status, **common_kwargs).to_dict()
    risk_summary = TinyOrderScaffoldRiskSummary(status=status, **common_kwargs).to_dict()
    submission_availability = TinyOrderSubmissionAvailability(status=STATUS_BLOCKED, **common_kwargs).to_dict()
    blockers_report = build_tiny_order_scaffold_blockers_report(blockers, generated_at=generated_at)
    latest_status = LatestTinyOrderScaffoldStatus(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        source_intent_path=source_intent_path,
        source_signer_boundary_path=source_signer_boundary_path,
        candidate_outcome=candidate_outcome,
        candidate_side=candidate_side,
        candidate_limit_price=candidate_limit_price,
        candidate_size=candidate_size,
        candidate_notional=candidate_notional,
        max_notional=max_notional_value,
        max_size=max_size_value,
        max_price=max_price_value,
        hard_limits_passed=hard_limits_passed,
        approval_packet_created=approval_packet_created,
        blocker_count=len(blockers),
        blockers=tuple(blockers),
        artifact_path=path_refs["result"],
        latest_status_path=path_refs["latest_status"],
        operator_markdown_path=path_refs["operator_md"],
        tiny_order_candidate_path=path_refs["tiny_order_candidate"],
        tiny_order_hard_limits_path=path_refs["tiny_order_hard_limits"],
        manual_tiny_order_approval_packet_path=path_refs["manual_tiny_order_approval_packet"],
        tiny_order_scaffold_risk_summary_path=path_refs["tiny_order_scaffold_risk_summary"],
        tiny_order_submission_availability_path=path_refs["tiny_order_submission_availability"],
        blockers_path=path_refs["blockers"],
        generated_at=generated_at,
    ).to_dict()
    result = TinyOrderScaffoldResult(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        source_intent_path=source_intent_path,
        source_signer_boundary_path=source_signer_boundary_path,
        candidate_outcome=candidate_outcome,
        candidate_side=candidate_side,
        candidate_limit_price=candidate_limit_price,
        candidate_size=candidate_size,
        candidate_notional=candidate_notional,
        max_notional=max_notional_value,
        max_size=max_size_value,
        max_price=max_price_value,
        hard_limits_passed=hard_limits_passed,
        approval_packet_created=approval_packet_created,
        tiny_order_candidate=candidate,
        tiny_order_hard_limits=hard_limits,
        manual_tiny_order_approval_packet=approval_packet,
        tiny_order_scaffold_risk_summary=risk_summary,
        tiny_order_submission_availability=submission_availability,
        latest_status=latest_status,
        blockers=tuple(blockers),
        artifact_paths=path_refs,
        operator_summary=_operator_summary(latest_status),
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["tiny_order_candidate"], candidate)
    write_json(paths["tiny_order_hard_limits"], hard_limits)
    write_json(paths["manual_tiny_order_approval_packet"], approval_packet)
    write_json(paths["tiny_order_scaffold_risk_summary"], risk_summary)
    write_json(paths["tiny_order_submission_availability"], submission_availability)
    write_json(paths["blockers"], blockers_report)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_tiny_order_scaffold_markdown(result))
    return result


def render_tiny_order_scaffold_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Tiny order scaffold completed.",
            f"Market: {clean_text(value.get('market') or value.get('market_symbol'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Mode: {MODE}",
            f"Tiny candidate: {clean_text(value.get('tiny_candidate') or STATUS_MISSING_SOURCE)}",
            f"Approval packet: {clean_text(value.get('approval_packet') or STATUS_BLOCKED)}",
            "Operator approved: false",
            "Signing: blocked",
            "Order submission: blocked",
            "Live execution: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_tiny_order_scaffold_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    candidate = dict(value.get("tiny_order_candidate", {}))
    hard_limits = dict(value.get("tiny_order_hard_limits", {}))
    approval = dict(value.get("manual_tiny_order_approval_packet", {}))
    submission = dict(value.get("tiny_order_submission_availability", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Tiny Order Scaffold 061",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `preflight / review-only`",
        "- execution_mode: `preflight`",
        "- review_only: `true`",
        "- preflight_only: `true`",
        "- scaffold_only: `true`",
        "",
        "## Source",
        "",
        f"- Source intent path: `{value.get('source_intent_path') or 'missing'}`",
        f"- Source signer boundary path: `{value.get('source_signer_boundary_path') or 'missing'}`",
        "",
        "## Tiny Candidate",
        "",
        f"- Tiny candidate status: `{candidate.get('status')}`",
        f"- Candidate outcome: `{candidate.get('candidate_outcome')}`",
        f"- Candidate side: `{candidate.get('candidate_side')}`",
        f"- Candidate limit price: `{candidate.get('candidate_limit_price')}`",
        f"- Candidate size: `{candidate.get('candidate_size')}`",
        f"- Candidate notional: `{candidate.get('candidate_notional')}`",
        "- candidate executable=false",
        "",
        "## Hard Limits",
        "",
        f"- max_notional: `{hard_limits.get('max_notional')}`",
        f"- max_size: `{hard_limits.get('max_size')}`",
        f"- max_price: `{hard_limits.get('max_price')}`",
        f"- hard_limits_passed: `{str(hard_limits.get('hard_limits_passed') is True).lower()}`",
        "",
        "## Manual Approval Packet",
        "",
        f"- approval required: `{str(approval.get('approval_required') is True).lower()}`",
        "- operator approved=false",
        f"- approval packet created: `{str(approval.get('approval_packet_created') is True).lower()}`",
        "- candidate executable=false",
        "",
        "## Submission Availability",
        "",
        "- signing blocked",
        f"- signed payload unavailable: `{str(submission.get('signed_payload_unavailable') is True).lower()}`",
        "- order submission blocked",
        "- order cancellation blocked",
        "- wallet blocked",
        "- balance reads blocked",
        "- position reads blocked",
        "- fill reads blocked",
        "- live execution blocked",
        "- signed_payload_available: `false`",
        "- order_submission_available: `false`",
        "- live_execution_approved: `false`",
        "- allowed_for_live: `false`",
        "- resolved_blocker_count: `0`",
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
        "",
        "## Next Operator Action",
        "",
        "- review packet only; no live order available",
        f"- Latest status path: `{latest.get('latest_status_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "tiny order scaffold is review-only; unsupported live/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _load_latest_source(
    *,
    market: str,
    strategy: str,
    from_latest_signer_boundary: bool,
    from_latest_paper_intent: bool,
) -> dict[str, Any]:
    if from_latest_signer_boundary and not from_latest_paper_intent:
        return _load_latest_signer_boundary_source(market=market, strategy=strategy)
    if from_latest_paper_intent and not from_latest_signer_boundary:
        return _load_latest_paper_intent_source(market=market, strategy=strategy)

    signer_source = _load_latest_signer_boundary_source(market=market, strategy=strategy)
    if signer_source.get("intent"):
        return signer_source
    return _load_latest_paper_intent_source(market=market, strategy=strategy)


def _load_latest_signer_boundary_source(*, market: str, strategy: str) -> dict[str, Any]:
    candidates = (
        DEFAULT_SIGNER_BOUNDARY_LATEST_STATUS_060_PATH,
        DEFAULT_SIGNER_BOUNDARY_RESULT_060_PATH,
        DEFAULT_SIGNER_BOUNDARY_CANDIDATE_060_PATH,
    )
    for path in candidates:
        if not path.exists():
            continue
        loaded = _load_json_object(path)
        intent = _extract_intent_from_signer_boundary(loaded)
        if not intent:
            continue
        if not _intent_matches(intent, market=market, strategy=strategy):
            continue
        source_intent_path = clean_text(
            loaded.get("source_intent_path")
            or loaded.get("source_paper_intent_path")
            or intent.get("source_intent_path")
            or intent.get("source_paper_intent_path")
        )
        return {
            "source_kind": "signer_boundary_preflight_060",
            "source_signer_boundary_path": normalize_path(path),
            "source_intent_path": source_intent_path,
            "intent": intent,
        }
    return {
        "source_kind": "missing_signer_boundary",
        "source_signer_boundary_path": "",
        "source_intent_path": "",
        "intent": {},
    }


def _load_latest_paper_intent_source(*, market: str, strategy: str) -> dict[str, Any]:
    candidates = (
        DEFAULT_PAPER_INTENT_053_PATH,
        DEFAULT_PAPER_RESULT_053_PATH,
        DEFAULT_PUBLIC_MARKET_INTENT_054_PATH,
        DEFAULT_PUBLIC_MARKET_RESULT_054_PATH,
    )
    for path in candidates:
        if not path.exists():
            continue
        loaded = _load_json_object(path)
        intent = _extract_intent_from_paper_source(loaded)
        if not intent:
            continue
        if not _intent_matches(intent, market=market, strategy=strategy):
            continue
        return {
            "source_kind": "paper_intent",
            "source_signer_boundary_path": "",
            "source_intent_path": normalize_path(path),
            "intent": intent,
        }
    return {
        "source_kind": "missing_paper_intent",
        "source_signer_boundary_path": "",
        "source_intent_path": "",
        "intent": {},
    }


def _extract_intent_from_signer_boundary(value: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(value or {})
    nested = row.get("latest_status")
    if isinstance(nested, Mapping) and nested:
        nested_intent = _extract_intent_from_signer_boundary(nested)
        if nested_intent:
            return nested_intent
    nested = row.get("live_candidate_order_intent") or row.get("tiny_order_candidate")
    if isinstance(nested, Mapping) and nested:
        nested_row = dict(nested)
        if _has_candidate_values(nested_row):
            return nested_row
    if _has_candidate_values(row):
        return row
    return {}


def _extract_intent_from_paper_source(value: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(value or {})
    if clean_text(row.get("paper_intent_status")) and row.get("paper_intent_status") != "no_paper_intent":
        return row
    nested = row.get("paper_order_intent")
    if isinstance(nested, Mapping) and nested:
        return dict(nested)
    paper_loop = row.get("paper_loop_result")
    if isinstance(paper_loop, Mapping):
        nested = paper_loop.get("paper_order_intent")
        if isinstance(nested, Mapping) and nested:
            return dict(nested)
    return {}


def _intent_matches(intent: Mapping[str, Any], *, market: str, strategy: str) -> bool:
    intent_market = clean_text(intent.get("market_symbol") or intent.get("market")).upper()
    intent_strategy = clean_text(intent.get("strategy_name"))
    if intent_market and intent_market != clean_text(market).upper():
        return False
    if intent_strategy and intent_strategy != clean_text(strategy):
        return False
    return True


def _has_candidate_values(value: Mapping[str, Any]) -> bool:
    return bool(
        clean_text(value.get("candidate_outcome") or value.get("outcome"))
        and clean_text(value.get("candidate_side") or value.get("side"))
        and _number_or_none(value.get("candidate_limit_price"), value.get("limit_price")) is not None
        and _number_or_none(value.get("candidate_size"), value.get("size")) is not None
        and _number_or_none(value.get("candidate_notional"), value.get("notional")) is not None
    )


def _hard_limits_passed(
    *,
    candidate_limit_price: float | None,
    candidate_size: float | None,
    candidate_notional: float | None,
    max_notional: float,
    max_size: float,
    max_price: float,
) -> bool:
    if not _positive(candidate_limit_price) or not _positive(candidate_size) or not _positive(candidate_notional):
        return False
    return (
        float(candidate_limit_price or 0) <= max_price
        and float(candidate_size or 0) <= max_size
        and float(candidate_notional or 0) <= max_notional
    )


def _build_blockers(
    *,
    source_available: bool,
    hard_limits_passed: bool,
    approval_packet_created: bool,
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if not source_available:
        blockers.append(
            _blocker(
                "missing_source",
                "source",
                "No latest signer boundary or paper intent artifact was available for tiny order scaffold review.",
                generated_at=generated_at,
            )
        )
    if not hard_limits_passed:
        blockers.append(
            _blocker(
                "hard_limits_not_passed",
                "hard_limits",
                "Tiny order hard limits did not pass or no source candidate was available.",
                generated_at=generated_at,
            )
        )
    if not approval_packet_created:
        blockers.append(
            _blocker(
                "approval_packet_not_created",
                "manual_approval_packet",
                "Manual approval packet was not created because the source candidate is missing.",
                generated_at=generated_at,
            )
        )
    blockers.extend(
        [
            _blocker(
                "manual_operator_approval_required",
                "manual_approval",
                "Manual operator approval is required and operator_approved remains false.",
                generated_at=generated_at,
            ),
            _blocker(
                "signing_blocked",
                "signing_boundary",
                "Signing remains blocked; no signer is configured or instantiated.",
                generated_at=generated_at,
            ),
            _blocker(
                "signed_payload_unavailable",
                "signed_payload_generation",
                "Signed payload generation is unavailable and blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "order_submission_blocked",
                "order_submission",
                "Order submission and cancellation are blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "wallet_blocked",
                "wallet_boundary",
                "Wallet connection and wallet signing remain blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "account_reads_blocked",
                "account_runtime",
                "Balance, position, fill, and PnL reads remain blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "live_execution_not_approved",
                "live_execution",
                "Live execution approval is false; no live action is available.",
                generated_at=generated_at,
            ),
        ]
    )
    return blockers


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = TinyOrderScaffoldBlocker(
        blocker_id=clean_text(blocker_id),
        blocker_category=clean_text(category),
        reason=clean_text(reason),
    ).to_dict()
    value["generated_at"] = generated_at
    return value


def _overall_status(*, source_available: bool, hard_limits_passed: bool) -> str:
    if not source_available:
        return "tiny_order_scaffold_incomplete_missing_source_live_blocked"
    if hard_limits_passed:
        return "tiny_order_scaffold_completed_live_blocked"
    return "tiny_order_scaffold_blocked_by_hard_limits_live_blocked"


def _operator_summary(status: Mapping[str, Any]) -> str:
    return (
        "Tiny order scaffold completed as review-only. Source intent="
        + (clean_text(status.get("source_intent_path")) or "missing")
        + "; source signer boundary="
        + (clean_text(status.get("source_signer_boundary_path")) or "missing")
        + "; candidate="
        + clean_text(status.get("tiny_candidate"))
        + "; approval packet="
        + clean_text(status.get("approval_packet"))
        + "; operator_approved=false; signing, signed payload generation, order submission, cancellation, "
        "wallet use, balances, positions, fills, PnL, and live execution are blocked."
    )


def _load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return dict(value) if isinstance(value, Mapping) else {}


def _number_or_none(*values: Any) -> float | None:
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _positive(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _positive_float(value: Any, fallback: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback
