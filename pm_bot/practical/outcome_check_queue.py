from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.active_paper_hypotheses import build_active_paper_hypotheses
from pm_bot.practical.market_queue import summarize_market_queue
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, optional_existing_path, safe_summary, write_json, write_text

OUTCOME_QUEUE_CONTRACT_VERSION = "pmbot_outcome_check_queue.v1"


def build_outcome_check_queue(queue_path: str | Path) -> dict[str, Any]:
    queue_summary = summarize_market_queue(queue_path)
    active_summary = build_active_paper_hypotheses(queue_path)
    base_dir = Path(queue_path).parent
    checks = []
    by_market = {row["market_id"]: row for row in active_summary["active_hypotheses"]}
    for item in queue_summary["items"]:
        hypothesis = by_market.get(item["market_id"])
        outcome_path = optional_existing_path(item.get("outcome_record_path"), base_dir=base_dir)
        outcome = load_json_object(outcome_path, label="outcome record") if outcome_path is not None else None
        status = classify_outcome_check_status(item, outcome)
        checks.append(
            {
                "queue_item_id": item["queue_item_id"],
                "market_id": item["market_id"],
                "market_title": item["market_title"],
                "paper_hypothesis_id": hypothesis["hypothesis_id"] if hypothesis else item.get("paper_hypothesis_id", ""),
                "outcome_record_path": item.get("outcome_record_path", ""),
                "outcome_status": clean_text(outcome.get("outcome_status")) if outcome else "unknown",
                "outcome_check_status": status,
                "next_operator_action": _next_action(status),
            }
        )
    counts: dict[str, int] = {}
    for row in checks:
        counts[row["outcome_check_status"]] = counts.get(row["outcome_check_status"], 0) + 1
    return {
        "contract_version": OUTCOME_QUEUE_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "outcome_checks": checks,
        "status_counts": {key: counts[key] for key in sorted(counts)},
        "safety_summary": safe_summary(),
    }


def classify_outcome_check_status(item: Mapping[str, Any], outcome: Mapping[str, Any] | None) -> str:
    if item.get("computed_blockers"):
        return "unknown"
    if outcome is None:
        if item.get("status") in {"hypothesis_active", "outcome_pending"}:
            return "overdue" if item.get("updated_at", "") <= "2026-05-08T00:00:00Z" else "due_now"
        return "not_due"
    outcome_status = clean_text(outcome.get("outcome_status"))
    if outcome_status in {"resolved", "void"}:
        return "resolved"
    if outcome_status == "ambiguous":
        return "ambiguous"
    if outcome_status == "unresolved":
        return "overdue" if item.get("updated_at", "") <= "2026-05-08T00:00:00Z" else "due_now"
    return "unknown"


def write_outcome_check_queue(
    *,
    queue_path: str | Path,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    summary = build_outcome_check_queue(queue_path)
    if out_json_path is not None:
        write_json(out_json_path, summary)
    if out_md_path is not None:
        write_text(out_md_path, render_outcome_check_queue_markdown(summary))
    return summary


def render_outcome_check_queue_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Outcome Check Queue",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        "",
        "## Status counts",
        "",
        *bullet_lines(f"`{status}`: {count}" for status, count in summary["status_counts"].items()),
        "",
        "## Outcome checks",
        "",
    ]
    for row in summary["outcome_checks"]:
        lines.extend(
            [
                f"- `{row['market_id']}` `{row['outcome_check_status']}` - {row['market_title']}",
                f"  Next: {row['next_operator_action']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety boundary",
            "",
            "- Local outcome records only.",
            "- No live outcome lookup is performed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT outcome check queue.")
    parser.add_argument("--queue", required=True, help="Local market queue JSON.")
    parser.add_argument("--out-json", required=True, help="Output outcome queue JSON.")
    parser.add_argument("--out-md", required=True, help="Output outcome queue Markdown.")
    args = parser.parse_args(argv)
    write_outcome_check_queue(queue_path=args.queue, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


def _next_action(status: str) -> str:
    actions = {
        "not_due": "No local outcome check is needed yet.",
        "due_now": "Look for a local outcome record and attach it to the queue item.",
        "overdue": "Attach or update the local outcome record before feedback review.",
        "resolved": "Run local paper feedback if it has not been generated.",
        "ambiguous": "Record operator notes explaining why outcome review is ambiguous.",
        "unknown": "Resolve queue blockers or inspect the local outcome record path.",
    }
    return actions[status]


if __name__ == "__main__":
    raise SystemExit(main())
