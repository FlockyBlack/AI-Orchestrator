from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.market_queue import load_market_queue, summarize_market_queue
from pm_bot.practical.one_market_analysis import run_one_market_analysis
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, normalize_path, optional_existing_path, safe_summary, slug_id, write_json, write_text

BATCH_ANALYSIS_CONTRACT_VERSION = "pmbot_batch_local_analysis_summary.v1"


def run_batch_local_analysis(
    *,
    queue_path: str | Path,
    out_dir: str | Path,
    out_summary_json_path: str | Path | None = None,
    out_summary_md_path: str | Path | None = None,
    out_queue_path: str | Path | None = None,
) -> dict[str, Any]:
    queue = load_market_queue(queue_path)
    queue_summary = summarize_market_queue(queue_path)
    base_dir = Path(queue_path).parent
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    processed: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    updated_queue = deepcopy(queue)
    item_by_id = {item.get("queue_item_id"): item for item in updated_queue.get("items", []) if isinstance(item, dict)}

    for item in queue_summary["items"]:
        if item["status"] != "queued":
            skipped.append({"queue_item_id": item["queue_item_id"], "reason": f"status is {item['status']}"})
            continue
        if item["computed_blockers"]:
            skipped.append({"queue_item_id": item["queue_item_id"], "reason": "blocked by missing local artifacts"})
            continue
        input_path = optional_existing_path(item["local_input_path"], base_dir=base_dir)
        if input_path is None:
            skipped.append({"queue_item_id": item["queue_item_id"], "reason": "local input path missing"})
            continue
        stem = slug_id(item["market_id"])
        out_json = output_dir / f"{stem}.analysis.result.json"
        out_md = output_dir / f"{stem}.analysis.md"
        result = run_one_market_analysis(input_path=input_path, out_json_path=out_json, out_md_path=out_md)
        processed.append(
            {
                "queue_item_id": item["queue_item_id"],
                "market_id": item["market_id"],
                "analysis_id": result["analysis_id"],
                "analysis_result_path": normalize_path(out_json),
                "analysis_markdown_path": normalize_path(out_md),
                "paper_hypothesis_id": result["paper_hypothesis"]["hypothesis_id"],
            }
        )
        queue_item = item_by_id.get(item["queue_item_id"])
        if queue_item is not None:
            queue_item["status"] = "analysis_ready"
            queue_item["analysis_result_path"] = normalize_path(out_json)
            queue_item["analysis_markdown_path"] = normalize_path(out_md)
            queue_item["paper_hypothesis_id"] = result["paper_hypothesis"]["hypothesis_id"]
            queue_item["updated_at"] = GENERATED_AT
            queue_item["next_operator_action"] = "Inspect the analysis card and decide whether to track the paper-only hypothesis."

    summary = {
        "contract_version": BATCH_ANALYSIS_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "queue_path": normalize_path(queue_path),
        "out_dir": normalize_path(out_dir),
        "processed_count": len(processed),
        "skipped_count": len(skipped),
        "processed_items": processed,
        "skipped_items": skipped,
        "original_queue_mutated": False,
        "out_queue_path": normalize_path(out_queue_path) if out_queue_path else None,
        "safety_summary": safe_summary(),
    }
    if out_queue_path is not None:
        write_json(out_queue_path, updated_queue)
    if out_summary_json_path is not None:
        write_json(out_summary_json_path, summary)
    if out_summary_md_path is not None:
        write_text(out_summary_md_path, render_batch_local_analysis_markdown(summary))
    return summary


def render_batch_local_analysis_markdown(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Batch Local Analysis",
            "",
            f"- Generated at: `{summary['generated_at']}`",
            f"- Processed: {summary['processed_count']}",
            f"- Skipped: {summary['skipped_count']}",
            "",
            "## Processed markets",
            "",
            *bullet_lines(
                f"`{row['market_id']}` -> `{row['analysis_result_path']}`" for row in summary["processed_items"]
            ),
            "",
            "## Skipped items",
            "",
            *bullet_lines(f"`{row['queue_item_id']}`: {row['reason']}" for row in summary["skipped_items"]),
            "",
            "## Safety boundary",
            "",
            "- Finite local queue processing only.",
            "- The original queue file is not modified unless an explicit output queue path is provided.",
            "- No live fetch, external API, wallet, order, or trading action is used.",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local one-market analysis over queued local PMBOT inputs.")
    parser.add_argument("--queue", required=True, help="Local market queue JSON.")
    parser.add_argument("--out-dir", required=True, help="Directory for per-market analysis artifacts.")
    parser.add_argument("--out-summary-json", required=True, help="Output batch summary JSON.")
    parser.add_argument("--out-summary-md", required=True, help="Output batch summary Markdown.")
    parser.add_argument("--out-queue", required=False, help="Optional updated queue JSON path.")
    args = parser.parse_args(argv)

    run_batch_local_analysis(
        queue_path=args.queue,
        out_dir=args.out_dir,
        out_summary_json_path=args.out_summary_json,
        out_summary_md_path=args.out_summary_md,
        out_queue_path=args.out_queue,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
