from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    mapping_rows,
    trading_core_safety_summary,
)

PAPER_OUTCOME_RECHECK_QUEUE_CONTRACT = "pmbot_paper_outcome_recheck_queue.v1"
PAPER_FEEDBACK_READINESS_CONTRACT = "pmbot_paper_feedback_readiness_summary.v1"

RESOLUTION_STATUSES = {"resolved", "ambiguous", "void"}


def build_paper_outcome_recheck_queue(
    *,
    tracked_markets: Sequence[Mapping[str, Any]],
    outcome_inputs: Sequence[Mapping[str, Any]],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    outcomes_by_market = {clean_text(row.get("market_id")): row for row in outcome_inputs}
    items = []
    for market in tracked_markets:
        market_id = clean_text(market.get("market_id"))
        outcome = dict(outcomes_by_market.get(market_id, {}))
        status = _outcome_status(outcome, market)
        feedback_ready = _feedback_ready(status, outcome)
        local_resolution_evidence_present = status in RESOLUTION_STATUSES and _has_resolution_evidence(outcome)
        items.append(
            {
                "market_id": market_id,
                "market_title": clean_text(market.get("market_title")),
                "outcome_status": status,
                "outcome_record_path": clean_text(
                    outcome.get("outcome_record_path") or market.get("outcome_record_path")
                ),
                "needs_future_outcome_check": status not in RESOLUTION_STATUSES,
                "local_resolution_evidence_present": local_resolution_evidence_present,
                "feedback_ready": feedback_ready,
                "feedback_blocked_reason": "" if feedback_ready else _feedback_blocked_reason(status, outcome),
                "next_operator_action": _next_outcome_action(status, feedback_ready),
            }
        )
    status_counts = _status_counts(items)
    return {
        "contract_version": PAPER_OUTCOME_RECHECK_QUEUE_CONTRACT,
        "queue_id": "paper-outcome-recheck-023",
        "generated_at": generated_at,
        "tracked_market_count": len(items),
        "unresolved_count": status_counts["unresolved"],
        "resolved_count": status_counts["resolved"] + status_counts["ambiguous"] + status_counts["void"],
        "ambiguous_count": status_counts["ambiguous"],
        "void_count": status_counts["void"],
        "feedback_ready_count": len([row for row in items if row["feedback_ready"] is True]),
        "needs_future_outcome_check_count": len([row for row in items if row["needs_future_outcome_check"] is True]),
        "recheck_items": items,
        "next_recheck_actions": [
            "Keep unresolved markets in the future outcome-check queue.",
            "Use only saved local outcome artifacts when changing a market to feedback-ready.",
            "Leave feedback blocked when local resolution evidence is absent.",
        ],
        "safety_summary": _feedback_safety_summary(),
    }


def build_feedback_readiness_summary(
    *,
    tracked_markets: Sequence[Mapping[str, Any]],
    outcome_inputs: Sequence[Mapping[str, Any]],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    queue = build_paper_outcome_recheck_queue(
        tracked_markets=tracked_markets,
        outcome_inputs=outcome_inputs,
        generated_at=generated_at,
    )
    ready_items = []
    blocked_items = []
    future_feedback_records = []
    for item in mapping_rows(queue.get("recheck_items")):
        record = {
            "market_id": item.get("market_id"),
            "market_title": item.get("market_title"),
            "outcome_status": item.get("outcome_status"),
            "feedback_ready": item.get("feedback_ready") is True,
            "paper_feedback_result_label": "pending",
            "source_learning_status": "blocked_until_local_outcome_resolution",
            "scoring_status": "blocked",
            "feedback_blocked_reason": item.get("feedback_blocked_reason"),
            "outcome_record_path": item.get("outcome_record_path"),
        }
        if item.get("feedback_ready") is True:
            ready_items.append(item)
            record["source_learning_status"] = "ready_for_manual_feedback_review"
            record["scoring_status"] = "ready_for_manual_scoring"
        else:
            blocked_items.append(
                {
                    "market_id": item.get("market_id"),
                    "market_title": item.get("market_title"),
                    "outcome_status": item.get("outcome_status"),
                    "feedback_blocked_reason": item.get("feedback_blocked_reason"),
                    "next_operator_action": item.get("next_operator_action"),
                }
            )
        future_feedback_records.append(record)

    unresolved_count = int(queue.get("unresolved_count", 0) or 0)
    resolved_count = int(queue.get("resolved_count", 0) or 0)
    return {
        "contract_version": PAPER_FEEDBACK_READINESS_CONTRACT,
        "summary_id": "paper-feedback-readiness-023",
        "generated_at": generated_at,
        "total_tracked_markets": int(queue.get("tracked_market_count", 0) or 0),
        "unresolved_count": unresolved_count,
        "resolved_count": resolved_count,
        "feedback_ready_count": len(ready_items),
        "blocked_feedback_count": len(blocked_items),
        "ready_items": ready_items,
        "blocked_items": blocked_items,
        "future_feedback_records": future_feedback_records,
        "next_feedback_actions": [
            "Recheck markets in the outcome queue after local resolution artifacts are saved.",
            "Create feedback records only for markets with explicit local resolution evidence.",
            "Keep unresolved markets out of source scoring and paper feedback result labels.",
        ],
        "outcome_resolution_invented": False,
        "safety_summary": _feedback_safety_summary(),
    }


def render_paper_outcome_recheck_queue_markdown(queue: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Outcome Recheck Queue",
        "",
        f"- Tracked markets: {queue.get('tracked_market_count')}",
        f"- Unresolved markets: {queue.get('unresolved_count')}",
        f"- Resolved local outcomes: {queue.get('resolved_count')}",
        f"- Feedback ready: {queue.get('feedback_ready_count')}",
        f"- Future outcome checks: {queue.get('needs_future_outcome_check_count')}",
        "",
        "## Recheck Items",
        "",
    ]
    for item in mapping_rows(queue.get("recheck_items")):
        lines.extend(
            [
                f"- `{item.get('market_id')}` `{item.get('outcome_status')}` - {item.get('market_title')}",
                f"  Next: {item.get('next_operator_action')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Next Recheck Actions",
            "",
            *bullet_lines(str(item) for item in queue.get("next_recheck_actions", [])),
            "",
            "## Safety",
            "",
            "- Local paper-only artifacts are used.",
            "- No live outcome lookup is performed.",
            "- No outcome is invented.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_feedback_readiness_summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Feedback Readiness",
        "",
        f"- Total tracked markets: {summary.get('total_tracked_markets')}",
        f"- Unresolved markets: {summary.get('unresolved_count')}",
        f"- Resolved local outcomes: {summary.get('resolved_count')}",
        f"- Feedback ready: {summary.get('feedback_ready_count')}",
        f"- Blocked feedback items: {summary.get('blocked_feedback_count')}",
        "",
        "## Blocked Items",
        "",
    ]
    lines.extend(
        bullet_lines(
            f"`{row.get('market_id')}` - {row.get('feedback_blocked_reason')}"
            for row in mapping_rows(summary.get("blocked_items"))
        )
    )
    lines.extend(
        [
            "",
            "## Future Feedback Records",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('scoring_status')}`"
                for row in mapping_rows(summary.get("future_feedback_records"))
            ),
            "",
            "## Next Feedback Actions",
            "",
            *bullet_lines(str(item) for item in summary.get("next_feedback_actions", [])),
            "",
            "## Safety",
            "",
            "- Feedback readiness is false for unresolved markets.",
            "- Source scoring stays blocked until saved local resolution evidence exists.",
            "- No market outcome was fabricated.",
        ]
    )
    return "\n".join(lines) + "\n"


def _outcome_status(outcome: Mapping[str, Any], market: Mapping[str, Any]) -> str:
    direct = clean_text(outcome.get("outcome_status") or outcome.get("status")).lower()
    if direct in {"unresolved", "resolved", "ambiguous", "void"}:
        return direct
    fallback = clean_text(market.get("outcome_status") or market.get("status")).lower()
    if fallback in {"unresolved", "resolved", "ambiguous", "void"}:
        return fallback
    return "unknown"


def _feedback_ready(status: str, outcome: Mapping[str, Any]) -> bool:
    return status in RESOLUTION_STATUSES and _has_resolution_evidence(outcome)


def _feedback_blocked_reason(status: str, outcome: Mapping[str, Any]) -> str:
    if status == "unresolved":
        return "local outcome status is unresolved"
    if status in RESOLUTION_STATUSES and not _has_resolution_evidence(outcome):
        return "local resolution status lacks explicit saved evidence"
    if status == "unknown":
        return "local outcome record is missing or has unknown status"
    return "feedback is blocked until a valid local outcome resolution record exists"


def _next_outcome_action(status: str, feedback_ready: bool) -> str:
    if feedback_ready:
        return "Review the saved local resolution artifact before preparing paper feedback."
    if status == "unresolved":
        return "Recheck later and keep feedback blocked until saved local resolution evidence exists."
    return "Inspect the local outcome record and keep feedback blocked until status and evidence are clear."


def _has_resolution_evidence(outcome: Mapping[str, Any]) -> bool:
    for field in (
        "resolution_evidence_path",
        "resolution_evidence_artifact",
        "resolution_source_artifact",
        "resolution_evidence_summary",
    ):
        if clean_text(outcome.get(field)):
            return True
    evidence_rows = outcome.get("source_evidence_used_for_resolution")
    if isinstance(evidence_rows, list) and evidence_rows:
        return True
    reference = clean_text(outcome.get("resolution_source_reference"))
    if reference and not reference.lower().startswith("stub summary only"):
        return True
    evidence_path = clean_text(outcome.get("resolution_evidence_path"))
    return bool(evidence_path and Path(evidence_path).exists())


def _status_counts(items: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {"unresolved": 0, "resolved": 0, "ambiguous": 0, "void": 0, "unknown": 0}
    for item in items:
        status = clean_text(item.get("outcome_status")) or "unknown"
        counts[status if status in counts else "unknown"] += 1
    return counts


def _feedback_safety_summary() -> dict[str, Any]:
    summary = trading_core_safety_summary()
    summary.update(
        {
            "outcome_resolution_invented": False,
            "new_live_fetch_performed": False,
            "new_polymarket_api_calls_performed": 0,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "no_autonomous_training_performed": True,
            "no_real_trade_decision": True,
        }
    )
    return summary
