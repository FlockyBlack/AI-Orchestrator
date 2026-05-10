from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.active_paper_hypotheses import build_active_paper_hypotheses
from pm_bot.practical.market_queue import summarize_market_queue
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, load_json_object, optional_existing_path, safe_summary, write_json, write_text

CONSOLE_CONTRACT_VERSION = "pmbot_practical_operator_console.v1"


def build_operator_console(queue_path: str | Path) -> dict[str, Any]:
    queue_summary = summarize_market_queue(queue_path)
    active_summary = build_active_paper_hypotheses(queue_path)
    base_dir = Path(queue_path).parent
    feedback_complete = [item for item in queue_summary["items"] if item["status"] == "feedback_complete"]
    source_learning_summary = _source_learning_summary(queue_summary["items"], base_dir=base_dir)
    console = {
        "contract_version": CONSOLE_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "queue_status_counts": queue_summary["status_counts"],
        "markets_queued": [item for item in queue_summary["items"] if item["status"] == "queued"],
        "markets_analyzed": [
            item
            for item in queue_summary["items"]
            if item["analysis_result_path"] and item["status"] != "queued"
        ],
        "active_paper_hypotheses_count": len(active_summary["active_hypotheses"]),
        "unresolved_outcomes_count": active_summary["unresolved_count"],
        "feedback_pending_count": active_summary["feedback_pending_count"],
        "feedback_complete_count": len(feedback_complete),
        "source_learning_summary": source_learning_summary,
        "blocked_items": queue_summary["blocked_items"],
        "next_operator_actions": queue_summary["next_operator_actions"],
        "safety_summary": safe_summary(),
        "generated_artifacts": {
            "market_queue_summary": queue_summary.get("queue_path"),
            "active_paper_hypotheses": "generated_inline",
            "operator_console": "generated_inline",
        },
    }
    return console


def write_operator_console(
    *,
    queue_path: str | Path,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    console = build_operator_console(queue_path)
    if out_json_path is not None:
        console["generated_artifacts"]["operator_console_json"] = str(out_json_path).replace("\\", "/")
    if out_md_path is not None:
        console["generated_artifacts"]["operator_console_markdown"] = str(out_md_path).replace("\\", "/")
    if out_json_path is not None:
        write_json(out_json_path, console)
    if out_md_path is not None:
        write_text(out_md_path, render_operator_console_markdown(console))
    return console


def render_operator_console_markdown(console: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Practical Operator Console",
        "",
        "## Queue summary",
        "",
        *bullet_lines(f"`{status}`: {count}" for status, count in console["queue_status_counts"].items()),
        "",
        "## Active paper hypotheses",
        "",
        f"- Active paper hypotheses: {console['active_paper_hypotheses_count']}",
        f"- Unresolved outcomes: {console['unresolved_outcomes_count']}",
        "",
        "## Outcome checks",
        "",
        f"- Feedback pending: {console['feedback_pending_count']}",
        "",
        "## Feedback pending",
        "",
        *bullet_lines(
            f"`{row['market_id']}` - {row['next_operator_action']}"
            for row in console["next_operator_actions"]
            if "feedback" in row["next_operator_action"].lower()
        ),
        "",
        "## Source learning summary",
        "",
        *bullet_lines(
            f"`{label}`: {count}" for label, count in console["source_learning_summary"].get("source_usefulness_summary", {}).items()
        ),
        "",
        "## Blockers",
        "",
        *bullet_lines(
            f"`{row['queue_item_id']}`: {'; '.join(row['blockers'])}" for row in console["blocked_items"]
        ),
        "",
        "## Next practical actions",
        "",
        *bullet_lines(
            f"`{row['market_id']}` - {row['next_operator_action']}" for row in console["next_operator_actions"][:8]
        ),
        "",
        "## Safety boundary",
        "",
        "- Local artifacts only.",
        "- Paper-only analysis-quality tracking.",
        "- No live fetch, real trade decision, wallet access, order, or trading action is used.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the PMBOT practical operator console from a local queue.")
    parser.add_argument("--queue", required=True, help="Local market queue JSON.")
    parser.add_argument("--out-json", required=True, help="Output operator console JSON.")
    parser.add_argument("--out-md", required=True, help="Output operator console Markdown.")
    args = parser.parse_args(argv)
    write_operator_console(queue_path=args.queue, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


def _source_learning_summary(items: Sequence[Mapping[str, Any]], *, base_dir: Path) -> dict[str, Any]:
    summary: dict[str, int] = {}
    ledgers = []
    for item in items:
        path = optional_existing_path(item.get("source_learning_ledger_path"), base_dir=base_dir)
        if path is None:
            continue
        payload = load_json_object(path, label="source learning ledger")
        ledgers.append(str(path).replace("\\", "/"))
        for label, count in payload.get("source_usefulness_summary", {}).items():
            summary[label] = summary.get(label, 0) + int(count)
    return {
        "ledger_count": len(ledgers),
        "source_usefulness_summary": {key: summary[key] for key in sorted(summary)},
        "ledger_paths": ledgers,
    }


if __name__ == "__main__":
    raise SystemExit(main())
