from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.market_queue import summarize_market_queue
from pm_bot.practical.paper_feedback import FEEDBACK_RESULT_CONTRACT_VERSION
from pm_bot.practical.practical_io import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    optional_existing_path,
    safe_summary,
    write_json,
    write_text,
)

ACTIVE_CONTRACT_VERSION = "pmbot_active_paper_hypotheses.v1"


def build_active_paper_hypotheses(queue_path: str | Path) -> dict[str, Any]:
    queue_summary = summarize_market_queue(queue_path)
    base_dir = Path(queue_path).parent
    hypotheses = []
    for item in queue_summary["items"]:
        analysis_path = optional_existing_path(item.get("analysis_result_path"), base_dir=base_dir)
        if analysis_path is None:
            continue
        analysis = load_json_object(analysis_path, label="analysis result")
        paper_hypothesis = analysis.get("paper_hypothesis", {})
        if not isinstance(paper_hypothesis, Mapping):
            continue
        outcome = _load_optional(item.get("outcome_record_path"), base_dir=base_dir)
        feedback = _load_optional(item.get("feedback_result_path"), base_dir=base_dir)
        outcome_status = _outcome_status(outcome)
        outcome_due_status = _outcome_due_status(item, outcome_status)
        feedback_status = _feedback_status(feedback, outcome_status)
        hypotheses.append(
            {
                "hypothesis_id": clean_text(paper_hypothesis.get("hypothesis_id") or item.get("paper_hypothesis_id")),
                "analysis_id": clean_text(analysis.get("analysis_id")),
                "market_id": clean_text(analysis.get("market_id") or item.get("market_id")),
                "market_title": clean_text(analysis.get("market_title") or item.get("market_title")),
                "paper_hypothesis_summary": clean_text(paper_hypothesis.get("tracked_claim", "")),
                "safety_label": clean_text(
                    paper_hypothesis.get("safety_label") or analysis.get("paper_hypothesis_safety_label")
                ),
                "no_real_trade_decision": True,
                "outcome_status": outcome_status,
                "outcome_due_status": outcome_due_status,
                "linked_sources": _linked_sources(analysis),
                "feedback_status": feedback_status,
                "next_operator_action": _next_operator_action(outcome_due_status, feedback_status),
            }
        )
    unresolved = [row for row in hypotheses if row["outcome_status"] in {"unresolved", "unknown"}]
    resolved = [row for row in hypotheses if row["outcome_status"] in {"resolved", "void", "ambiguous"}]
    feedback_pending = [row for row in hypotheses if row["feedback_status"] == "feedback_pending"]
    stale = [row for row in hypotheses if row["outcome_due_status"] == "overdue"]
    blocked = [row for row in queue_summary["items"] if row["computed_blockers"]]
    return {
        "contract_version": ACTIVE_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "active_hypotheses": sorted(hypotheses, key=lambda row: row["hypothesis_id"]),
        "unresolved_count": len(unresolved),
        "resolved_count": len(resolved),
        "feedback_pending_count": len(feedback_pending),
        "stale_outcome_check_count": len(stale),
        "blocked_count": len(blocked),
        "next_outcome_checks": [
            {
                "hypothesis_id": row["hypothesis_id"],
                "market_id": row["market_id"],
                "outcome_due_status": row["outcome_due_status"],
                "next_operator_action": row["next_operator_action"],
            }
            for row in hypotheses
            if row["outcome_due_status"] in {"due_now", "overdue", "unknown"}
        ],
        "safety_summary": safe_summary(),
    }


def write_active_paper_hypotheses(
    *,
    queue_path: str | Path,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    summary = build_active_paper_hypotheses(queue_path)
    if out_json_path is not None:
        write_json(out_json_path, summary)
    if out_md_path is not None:
        write_text(out_md_path, render_active_hypotheses_markdown(summary))
    return summary


def render_active_hypotheses_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Active Paper Hypotheses",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Unresolved: {summary['unresolved_count']}",
        f"- Resolved or closed: {summary['resolved_count']}",
        f"- Feedback pending: {summary['feedback_pending_count']}",
        f"- Stale outcome checks: {summary['stale_outcome_check_count']}",
        "",
        "## Hypotheses",
        "",
    ]
    for row in summary["active_hypotheses"]:
        lines.extend(
            [
                f"- `{row['hypothesis_id']}` - {row['market_title']}",
                f"  Outcome: `{row['outcome_status']}` / `{row['outcome_due_status']}`",
                f"  Feedback: `{row['feedback_status']}`",
                f"  Next: {row['next_operator_action']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Next outcome checks",
            "",
            *bullet_lines(
                f"`{row['hypothesis_id']}` `{row['outcome_due_status']}` - {row['next_operator_action']}"
                for row in summary["next_outcome_checks"]
            ),
            "",
            "## Safety boundary",
            "",
            "- Paper-only, non-executable analysis tracking.",
            "- No real trade decision or market instruction is produced.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List active paper-only PMBOT hypotheses from a local queue.")
    parser.add_argument("--queue", required=True, help="Local market queue JSON.")
    parser.add_argument("--out-json", required=True, help="Output active hypotheses JSON.")
    parser.add_argument("--out-md", required=True, help="Output active hypotheses Markdown.")
    args = parser.parse_args(argv)

    write_active_paper_hypotheses(queue_path=args.queue, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


def _load_optional(path: Any, *, base_dir: Path) -> dict[str, Any] | None:
    existing = optional_existing_path(path, base_dir=base_dir)
    if existing is None:
        return None
    return load_json_object(existing, label="linked artifact")


def _outcome_status(outcome: Mapping[str, Any] | None) -> str:
    if outcome is None:
        return "unknown"
    return clean_text(outcome.get("outcome_status") or "unknown")


def _outcome_due_status(item: Mapping[str, Any], outcome_status: str) -> str:
    if outcome_status in {"resolved", "void", "ambiguous"}:
        return "resolved"
    if item["status"] == "outcome_pending" and item.get("updated_at", "") <= "2026-05-08T00:00:00Z":
        return "overdue"
    if item["status"] in {"hypothesis_active", "outcome_pending"}:
        return "due_now"
    if outcome_status == "unresolved":
        return "due_now"
    return "unknown"


def _feedback_status(feedback: Mapping[str, Any] | None, outcome_status: str) -> str:
    if feedback is not None and feedback.get("contract_version") == FEEDBACK_RESULT_CONTRACT_VERSION:
        return clean_text(feedback.get("analysis_quality_label") or "feedback_complete")
    if outcome_status in {"resolved", "void", "ambiguous"}:
        return "feedback_pending"
    return "outcome_pending"


def _linked_sources(analysis: Mapping[str, Any]) -> list[dict[str, str]]:
    sources = analysis.get("sources_used") or analysis.get("source_attribution") or []
    linked = []
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        linked.append(
            {
                "source_id": clean_text(source.get("source_id")),
                "source_name": clean_text(source.get("source_name")),
                "freshness_status": clean_text(source.get("freshness_status")),
            }
        )
    return linked


def _next_operator_action(outcome_due_status: str, feedback_status: str) -> str:
    if outcome_due_status == "overdue":
        return "Add or confirm the local outcome record before judging analysis quality."
    if outcome_due_status in {"due_now", "unknown"}:
        return "Check whether a local outcome record is available."
    if feedback_status == "feedback_pending":
        return "Run local paper feedback for the resolved outcome."
    return "Review source-learning lessons from completed feedback."


if __name__ == "__main__":
    raise SystemExit(main())
