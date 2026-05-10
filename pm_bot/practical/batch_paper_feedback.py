from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.market_queue import summarize_market_queue
from pm_bot.practical.paper_feedback import run_paper_feedback
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, normalize_path, optional_existing_path, safe_summary, slug_id, write_json, write_text

BATCH_FEEDBACK_CONTRACT_VERSION = "pmbot_batch_paper_feedback_summary.v1"


def run_batch_paper_feedback(
    *,
    queue_path: str | Path,
    out_dir: str | Path,
    out_summary_json_path: str | Path | None = None,
    out_summary_md_path: str | Path | None = None,
) -> dict[str, Any]:
    queue_summary = summarize_market_queue(queue_path)
    base_dir = Path(queue_path).parent
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for item in queue_summary["items"]:
        analysis_path = optional_existing_path(item.get("analysis_result_path"), base_dir=base_dir)
        outcome_path = optional_existing_path(item.get("outcome_record_path"), base_dir=base_dir)
        if analysis_path is None or outcome_path is None:
            skipped.append({"queue_item_id": item["queue_item_id"], "reason": "analysis or outcome artifact missing"})
            continue
        stem = slug_id(f"{item['queue_item_id']}-{item['market_id']}")
        out_json = output_dir / f"{stem}.feedback.result.json"
        out_md = output_dir / f"{stem}.feedback.md"
        feedback = run_paper_feedback(
            analysis_path=analysis_path,
            outcome_path=outcome_path,
            out_json_path=out_json,
            out_md_path=out_md,
        )
        generated.append(
            {
                "queue_item_id": item["queue_item_id"],
                "market_id": item["market_id"],
                "feedback_id": feedback["feedback_id"],
                "analysis_quality_label": feedback["analysis_quality_label"],
                "outcome_status": feedback["outcome_status"],
                "feedback_result_path": normalize_path(out_json),
                "feedback_markdown_path": normalize_path(out_md),
            }
        )
    summary = {
        "contract_version": BATCH_FEEDBACK_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "generated_count": len(generated),
        "skipped_count": len(skipped),
        "generated_feedback": generated,
        "skipped_items": skipped,
        "safety_summary": safe_summary(),
    }
    if out_summary_json_path is not None:
        write_json(out_summary_json_path, summary)
    if out_summary_md_path is not None:
        write_text(out_summary_md_path, render_batch_paper_feedback_markdown(summary))
    return summary


def render_batch_paper_feedback_markdown(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Batch Paper Feedback",
            "",
            f"- Generated feedback: {summary['generated_count']}",
            f"- Skipped items: {summary['skipped_count']}",
            "",
            "## Feedback generated",
            "",
            *bullet_lines(
                f"`{row['market_id']}` `{row['analysis_quality_label']}` -> `{row['feedback_result_path']}`"
                for row in summary["generated_feedback"]
            ),
            "",
            "## Skipped items",
            "",
            *bullet_lines(f"`{row['queue_item_id']}`: {row['reason']}" for row in summary["skipped_items"]),
            "",
            "## Safety boundary",
            "",
            "- Local analysis/outcome pairs only.",
            "- No recommendations, orders, wallet access, or live fetches are produced.",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local PMBOT paper feedback over queue analysis/outcome pairs.")
    parser.add_argument("--queue", required=True, help="Local market queue JSON.")
    parser.add_argument("--out-dir", required=True, help="Directory for per-market feedback artifacts.")
    parser.add_argument("--out-summary-json", required=True, help="Output batch feedback summary JSON.")
    parser.add_argument("--out-summary-md", required=True, help="Output batch feedback summary Markdown.")
    args = parser.parse_args(argv)
    run_batch_paper_feedback(
        queue_path=args.queue,
        out_dir=args.out_dir,
        out_summary_json_path=args.out_summary_json,
        out_summary_md_path=args.out_summary_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
