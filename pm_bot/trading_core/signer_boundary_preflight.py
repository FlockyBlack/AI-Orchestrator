from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text
from pm_bot.trading_core.signer_boundary_models import (
    MODE,
    ORDER_SUBMISSION_AVAILABILITY_CONTRACT,
    SIGNED_PAYLOAD_AVAILABILITY_CONTRACT,
    SIGNER_BOUNDARY_PREFLIGHT_RESULT_CONTRACT,
    STATUS_BLOCKED,
    STATUS_CREATED,
    STATUS_MISSING_SOURCE,
    STATUS_UNAVAILABLE,
    TASK_ID,
    UNSIGNED_PLAN_STATUS,
    LatestSignerBoundaryPreflightStatus,
    LiveCandidateOrderIntent,
    OrderSubmissionAvailability,
    SignedPayloadAvailability,
    SignerBoundaryBlocker,
    SignerBoundaryPreflightResult,
    SigningBoundaryStatus,
    UnsignedOrderPayloadPlan,
    build_signer_boundary_blockers_report,
    signer_boundary_safety_flags,
)

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/signer_boundary_preflight_060")
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
)


def signer_boundary_preflight_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "signer_boundary_preflight_060_result.json",
        "operator_md": root / "signer_boundary_preflight_060_operator.md",
        "latest_status": root / "latest_signer_boundary_preflight_status_060.json",
        "live_candidate_order_intent": root / "live_candidate_order_intent_060.json",
        "unsigned_order_payload_plan": root / "unsigned_order_payload_plan_060.json",
        "signing_boundary_status": root / "signing_boundary_status_060.json",
        "signed_payload_availability": root / "signed_payload_availability_060.json",
        "order_submission_availability": root / "order_submission_availability_060.json",
        "blockers": root / "signer_boundary_blockers_060.json",
    }


def run_signer_boundary_preflight(
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    dry_run: bool = True,
    from_latest_paper_intent: bool = True,
    from_latest_public_market_loop: bool = False,
    mock_unsigned_plan: bool = False,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("signer boundary preflight requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    strategy_name = clean_text(strategy) or "tiny-momentum"
    paths = signer_boundary_preflight_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    source = _load_latest_source_paper_intent(
        market=market_symbol,
        strategy=strategy_name,
        from_latest_paper_intent=from_latest_paper_intent,
        from_latest_public_market_loop=from_latest_public_market_loop,
    )
    source_intent = dict(source.get("intent") or {})
    source_path = clean_text(source.get("path"))
    source_available = bool(source_intent)
    candidate_status = STATUS_CREATED if source_available else STATUS_MISSING_SOURCE

    candidate_outcome = clean_text(source_intent.get("outcome") or source_intent.get("candidate_outcome"))
    candidate_side = clean_text(source_intent.get("side") or source_intent.get("candidate_side"))
    candidate_limit_price = _number_or_none(
        source_intent.get("limit_price"),
        source_intent.get("candidate_limit_price"),
    )
    candidate_size = _number_or_none(source_intent.get("size"), source_intent.get("candidate_size"))
    candidate_notional = _number_or_none(source_intent.get("notional"), source_intent.get("candidate_notional"))

    live_candidate = LiveCandidateOrderIntent(
        status=candidate_status,
        source_paper_intent_path=source_path,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        candidate_outcome=candidate_outcome,
        candidate_side=candidate_side,
        candidate_limit_price=candidate_limit_price,
        candidate_size=candidate_size,
        candidate_notional=candidate_notional,
        source_contract_version=clean_text(source_intent.get("contract_version")),
        source_paper_intent_status=clean_text(source_intent.get("paper_intent_status")),
        generated_at=generated_at,
    ).to_dict()
    unsigned_plan = UnsignedOrderPayloadPlan(
        status=UNSIGNED_PLAN_STATUS,
        source_paper_intent_path=source_path,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        candidate_outcome=candidate_outcome,
        candidate_side=candidate_side,
        candidate_limit_price=candidate_limit_price,
        candidate_size=candidate_size,
        candidate_notional=candidate_notional,
        unsigned_plan_created=source_available or mock_unsigned_plan or True,
        generated_at=generated_at,
    ).to_dict()
    signing_status = SigningBoundaryStatus(generated_at=generated_at).to_dict()
    signed_payload_availability = SignedPayloadAvailability(generated_at=generated_at).to_dict()
    order_submission_availability = OrderSubmissionAvailability(generated_at=generated_at).to_dict()
    blockers = _build_blockers(source_available=source_available, generated_at=generated_at)
    blockers_report = build_signer_boundary_blockers_report(blockers, generated_at=generated_at)
    status = (
        "signer_boundary_preflight_completed_live_blocked"
        if source_available
        else "signer_boundary_preflight_incomplete_missing_source_live_blocked"
    )
    latest_status = LatestSignerBoundaryPreflightStatus(
        status=status,
        source_paper_intent_path=source_path,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        candidate_outcome=candidate_outcome,
        candidate_side=candidate_side,
        candidate_limit_price=candidate_limit_price,
        candidate_size=candidate_size,
        candidate_notional=candidate_notional,
        live_candidate_intent_status=candidate_status,
        unsigned_plan_status=UNSIGNED_PLAN_STATUS,
        signer_status=STATUS_BLOCKED,
        signed_payload_status=STATUS_UNAVAILABLE,
        order_submission_status=STATUS_BLOCKED,
        unsigned_plan_created=unsigned_plan.get("unsigned_plan_created") is True,
        blocker_count=len(blockers),
        blockers=tuple(blockers),
        artifact_path=path_refs["result"],
        latest_status_path=path_refs["latest_status"],
        operator_markdown_path=path_refs["operator_md"],
        live_candidate_order_intent_path=path_refs["live_candidate_order_intent"],
        unsigned_order_payload_plan_path=path_refs["unsigned_order_payload_plan"],
        signing_boundary_status_path=path_refs["signing_boundary_status"],
        signed_payload_availability_path=path_refs["signed_payload_availability"],
        order_submission_availability_path=path_refs["order_submission_availability"],
        blockers_path=path_refs["blockers"],
        generated_at=generated_at,
    ).to_dict()
    result = SignerBoundaryPreflightResult(
        status=status,
        source_paper_intent_path=source_path,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        candidate_outcome=candidate_outcome,
        candidate_side=candidate_side,
        candidate_limit_price=candidate_limit_price,
        candidate_size=candidate_size,
        candidate_notional=candidate_notional,
        live_candidate_order_intent=live_candidate,
        unsigned_order_payload_plan=unsigned_plan,
        signing_boundary_status=signing_status,
        signed_payload_availability=signed_payload_availability,
        order_submission_availability=order_submission_availability,
        latest_status=latest_status,
        blockers=tuple(blockers),
        artifact_paths=path_refs,
        operator_summary=_operator_summary(latest_status),
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["live_candidate_order_intent"], live_candidate)
    write_json(paths["unsigned_order_payload_plan"], unsigned_plan)
    write_json(paths["signing_boundary_status"], signing_status)
    write_json(paths["signed_payload_availability"], signed_payload_availability)
    write_json(paths["order_submission_availability"], order_submission_availability)
    write_json(paths["blockers"], blockers_report)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_signer_boundary_preflight_markdown(result))
    return result


def render_signer_boundary_preflight_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Signer boundary preflight completed.",
            f"Market: {clean_text(value.get('market') or value.get('market_symbol'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Mode: {MODE}",
            f"Live candidate intent: {clean_text(value.get('live_candidate_intent_status') or STATUS_MISSING_SOURCE)}",
            f"Unsigned payload plan: {clean_text(value.get('unsigned_plan_status') or UNSIGNED_PLAN_STATUS)}",
            "Signer: blocked",
            "Signed payload: unavailable",
            "Order submission: blocked",
            "Live execution: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_signer_boundary_preflight_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    candidate = dict(value.get("live_candidate_order_intent", {}))
    unsigned_plan = dict(value.get("unsigned_order_payload_plan", {}))
    signing = dict(value.get("signing_boundary_status", {}))
    signed_payload = dict(value.get("signed_payload_availability", {}))
    order_submission = dict(value.get("order_submission_availability", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Signer Boundary Preflight 060",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `preflight / review-only`",
        "- execution_mode: `preflight`",
        "- review_only: `true`",
        "- preflight_only: `true`",
        "",
        "## Source Intent",
        "",
        f"- Source intent path: `{value.get('source_paper_intent_path') or 'missing'}`",
        f"- Live candidate intent status: `{candidate.get('status')}`",
        f"- Candidate outcome: `{candidate.get('candidate_outcome')}`",
        f"- Candidate side: `{candidate.get('candidate_side')}`",
        f"- Candidate limit price: `{candidate.get('candidate_limit_price')}`",
        f"- Candidate size: `{candidate.get('candidate_size')}`",
        f"- Candidate notional: `{candidate.get('candidate_notional')}`",
        "- Candidate intent is non-executable: `true`",
        "",
        "## Unsigned Plan",
        "",
        f"- Unsigned plan status: `{unsigned_plan.get('status')}`",
        f"- unsigned_plan_created: `{str(unsigned_plan.get('unsigned_plan_created') is True).lower()}`",
        "- unsigned_plan_is_executable=false",
        "- Schema-only plan: `true`",
        "- Real CLOB payload materialized: `false`",
        "- Ready for signing: `false`",
        "",
        "## Boundary Status",
        "",
        f"- Signer blocked: `{str(signing.get('signer_blocked') is True).lower()}`",
        f"- Signed payload unavailable: `{str(signed_payload.get('signed_payload_unavailable') is True).lower()}`",
        f"- Order submission blocked: `{str(order_submission.get('order_submission_blocked') is True).lower()}`",
        "- Wallet blocked: `true`",
        "- Live execution blocked: `true`",
        "- private_key_read: `false`",
        "- seed_phrase_read: `false`",
        "- mnemonic_read: `false`",
        "- wallet_connection_attempted: `false`",
        "- signer_instantiated: `false`",
        "- signing_attempted: `false`",
        "- signed_payload_generated: `false`",
        "- order_submission_attempted: `false`",
        "- order_cancellation_attempted: `false`",
        "- balance_read_attempted: `false`",
        "- position_read_attempted: `false`",
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
        "- review signer boundary only, no live order available",
        f"- Latest status path: `{latest.get('latest_status_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "signer boundary preflight is review-only; unsupported live/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _load_latest_source_paper_intent(
    *,
    market: str,
    strategy: str,
    from_latest_paper_intent: bool,
    from_latest_public_market_loop: bool,
) -> dict[str, Any]:
    candidates: list[tuple[Path, str]] = []
    if from_latest_public_market_loop:
        candidates.extend(
            [
                (DEFAULT_PUBLIC_MARKET_INTENT_054_PATH, "public_market_loop_054_intent"),
                (DEFAULT_PUBLIC_MARKET_RESULT_054_PATH, "public_market_loop_054_result"),
            ]
        )
    if from_latest_paper_intent or not candidates:
        candidates.extend(
            [
                (DEFAULT_PAPER_INTENT_053_PATH, "paper_trading_loop_053_intent"),
                (DEFAULT_PAPER_RESULT_053_PATH, "paper_trading_loop_053_result"),
            ]
        )
    if not from_latest_public_market_loop:
        candidates.extend(
            [
                (DEFAULT_PUBLIC_MARKET_INTENT_054_PATH, "public_market_loop_054_intent"),
                (DEFAULT_PUBLIC_MARKET_RESULT_054_PATH, "public_market_loop_054_result"),
            ]
        )

    for path, source_kind in candidates:
        if not path.exists():
            continue
        loaded = _load_json_object(path)
        intent = _extract_intent_from_source(loaded)
        if not intent:
            continue
        if not _intent_matches(intent, market=market, strategy=strategy):
            continue
        return {"path": normalize_path(path), "source_kind": source_kind, "intent": intent}
    return {"path": "", "source_kind": "missing", "intent": {}}


def _extract_intent_from_source(value: Mapping[str, Any]) -> dict[str, Any]:
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


def _build_blockers(*, source_available: bool, generated_at: str) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if not source_available:
        blockers.append(
            _blocker(
                "missing_source_paper_intent",
                "source_paper_intent",
                "No latest paper intent artifact was available for signer boundary review.",
                generated_at=generated_at,
            )
        )
    blockers.extend(
        [
            _blocker(
                "signer_unavailable_blocked",
                "signing_boundary",
                "Signer is unavailable and blocked; no signer is configured or instantiated.",
                generated_at=generated_at,
            ),
            _blocker(
                "signed_payload_unavailable_blocked",
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
                "live_execution_not_approved",
                "live_execution",
                "Live execution approval is false; no live action is available.",
                generated_at=generated_at,
            ),
        ]
    )
    return blockers


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = SignerBoundaryBlocker(
        blocker_id=clean_text(blocker_id),
        blocker_category=clean_text(category),
        reason=clean_text(reason),
    ).to_dict()
    value["generated_at"] = generated_at
    return value


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


def _operator_summary(status: Mapping[str, Any]) -> str:
    return (
        "Signer boundary preflight completed as review-only. Source intent="
        + (clean_text(status.get("source_paper_intent_path")) or "missing")
        + "; live candidate intent="
        + clean_text(status.get("live_candidate_intent_status"))
        + "; unsigned plan is schema-only and non-executable; signer, signed payload generation, "
        "order submission, wallet use, balances, positions, and live execution are blocked."
    )
