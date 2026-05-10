from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.market_queue import summarize_market_queue
from pm_bot.practical.paper_feedback import FEEDBACK_RESULT_CONTRACT_VERSION
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, optional_existing_path, safe_summary, write_json, write_text
from pm_bot.practical.source_learning import build_source_learning_ledger, render_source_learning_markdown

SOURCE_LEARNING_BATCH_CONTRACT_VERSION = "pmbot_source_learning_batch_ledger.v1"


def build_source_learning_batch(
    *,
    queue_path: str | Path | None = None,
    feedback_paths: Sequence[str | Path] = (),
    generated_artifact_paths: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    paths: list[Path] = []
    if queue_path is not None:
        queue_summary = summarize_market_queue(queue_path)
        base_dir = Path(queue_path).parent
        for item in queue_summary["items"]:
            existing = optional_existing_path(item.get("feedback_result_path"), base_dir=base_dir)
            if existing is not None:
                paths.append(existing)
    for path in feedback_paths:
        existing = optional_existing_path(path)
        if existing is not None:
            paths.append(existing)
    unique_paths = sorted({normalize_path(path): path for path in paths}.values(), key=normalize_path)
    feedback_results = [load_json_object(path, label="feedback result") for path in unique_paths]
    feedback_results = [result for result in feedback_results if result.get("contract_version") == FEEDBACK_RESULT_CONTRACT_VERSION]
    if feedback_results:
        ledger = build_source_learning_ledger(feedback_results, generated_artifact_paths=generated_artifact_paths)
    else:
        ledger = _empty_ledger(generated_artifact_paths=generated_artifact_paths)
    observations = _source_observations(feedback_results)
    records = _aggregate_records(observations, ledger.get("source_records", []))
    ledger["contract_version"] = SOURCE_LEARNING_BATCH_CONTRACT_VERSION
    ledger["generated_at"] = GENERATED_AT
    ledger["source_observations"] = observations
    ledger["source_records"] = records
    ledger["source_usefulness_summary"] = dict(sorted(Counter(row["usefulness_label"] for row in observations).items()))
    ledger["source_failure_patterns"] = _failure_patterns(ledger["source_usefulness_summary"])
    ledger["recommended_source_handling_updates"] = _recommended_updates(records)
    ledger["no_autonomous_training_performed"] = True
    ledger["no_real_trade_decision"] = True
    return ledger


def run_source_learning_batch(
    *,
    queue_path: str | Path | None = None,
    feedback_paths: Sequence[str | Path] = (),
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    artifacts = {}
    if out_json_path is not None:
        artifacts["source_learning_ledger_json"] = normalize_path(out_json_path)
    if out_md_path is not None:
        artifacts["source_learning_ledger_markdown"] = normalize_path(out_md_path)
    ledger = build_source_learning_batch(
        queue_path=queue_path,
        feedback_paths=feedback_paths,
        generated_artifact_paths=artifacts,
    )
    if out_json_path is not None:
        write_json(out_json_path, ledger)
    if out_md_path is not None:
        write_text(out_md_path, render_source_learning_batch_markdown(ledger))
    return ledger


def render_source_learning_batch_markdown(ledger: Mapping[str, Any]) -> str:
    base = render_source_learning_markdown({**ledger, "contract_version": "pmbot_source_learning_ledger.v1"})
    extra = [
        "",
        "## Batch source observations",
        "",
        *bullet_lines(
            f"`{row['source_id']}` `{row['usefulness_label']}` from `{row['feedback_id']}`"
            for row in ledger.get("source_observations", [])
        ),
        "",
        "## Batch safety note",
        "",
        "- Source learning is a transparent ledger aggregation only.",
        "- No autonomous training was performed.",
    ]
    return base + "\n".join(extra) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate local PMBOT feedback into a source learning batch ledger.")
    parser.add_argument("--queue", required=False, help="Local market queue JSON.")
    parser.add_argument("--feedback", action="append", default=[], help="Optional feedback JSON path; repeatable.")
    parser.add_argument("--out-json", required=True, help="Output source learning ledger JSON.")
    parser.add_argument("--out-md", required=True, help="Output source learning ledger Markdown.")
    args = parser.parse_args(argv)
    if not args.queue and not args.feedback:
        parser.error("--queue or --feedback is required")
    run_source_learning_batch(
        queue_path=args.queue,
        feedback_paths=args.feedback,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


def _source_observations(feedback_results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for feedback in feedback_results:
        for row in feedback.get("source_contribution_review", []):
            if not isinstance(row, Mapping):
                continue
            rows.append(
                {
                    "feedback_id": clean_text(feedback.get("feedback_id")),
                    "market_id": clean_text(feedback.get("market_id")),
                    "source_id": clean_text(row.get("source_id")),
                    "source_name": clean_text(row.get("source_name")),
                    "usefulness_label": clean_text(row.get("usefulness_label") or "unknown"),
                    "observed_issue": clean_text(row.get("observed_issue", "")),
                    "suggested_future_handling": clean_text(row.get("suggested_future_handling", "")),
                }
            )
    return sorted(rows, key=lambda row: (row["source_id"], row["feedback_id"]))


def _aggregate_records(observations: Sequence[Mapping[str, Any]], existing_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in observations:
        grouped[row["source_id"]].append(row)
    existing_by_id = {clean_text(row.get("source_id")): row for row in existing_records if isinstance(row, Mapping)}
    records = []
    for source_id, rows in sorted(grouped.items()):
        counts = Counter(row["usefulness_label"] for row in rows)
        existing = existing_by_id.get(source_id, {})
        dominant = clean_text(existing.get("usefulness_label") or _dominant_label(counts))
        records.append(
            {
                "source_id": source_id,
                "source_name": clean_text(rows[0].get("source_name")),
                "markets_used": sorted({clean_text(row.get("market_id")) for row in rows}),
                "usefulness_label": dominant,
                "source_label_counts": dict(sorted(counts.items())),
                "observed_issue": _join_unique(row.get("observed_issue") for row in rows),
                "suggested_future_handling": _join_unique(row.get("suggested_future_handling") for row in rows),
            }
        )
    return records


def _dominant_label(counts: Counter[str]) -> str:
    for label in ("misleading", "contradictory", "stale", "insufficient", "useful", "unused", "unknown"):
        if counts.get(label):
            return label
    return "unknown"


def _failure_patterns(summary: Mapping[str, int]) -> list[str]:
    return [f"{count} source observation(s) labeled {label}." for label, count in sorted(summary.items()) if label != "useful"]


def _recommended_updates(records: Sequence[Mapping[str, Any]]) -> list[str]:
    labels = {label for record in records for label in record.get("source_label_counts", {})}
    updates = []
    if "stale" in labels:
        updates.append("Require freshness review for stale local source packets.")
    if "misleading" in labels:
        updates.append("Separate source claim capture from reasoning review for misleading observations.")
    if "contradictory" in labels:
        updates.append("Keep contradiction notes visible before feedback review.")
    if "insufficient" in labels:
        updates.append("Pair insufficient sources with explicit missing-evidence capture.")
    if not updates:
        updates.append("Keep source attribution and limitations visible in future analysis cards.")
    return updates


def _join_unique(values: Sequence[Any]) -> str:
    return "; ".join(sorted({clean_text(value) for value in values if clean_text(value)}))


def _empty_ledger(*, generated_artifact_paths: Mapping[str, str] | None = None) -> dict[str, Any]:
    return {
        "analysis_prompt_improvement_notes": [],
        "contract_version": SOURCE_LEARNING_BATCH_CONTRACT_VERSION,
        "generated_artifacts": dict(generated_artifact_paths or {}),
        "generated_at": GENERATED_AT,
        "input_feedback_ids": [],
        "ledger_id": "source_learning_batch.empty",
        "market_ids": [],
        "no_autonomous_training_performed": True,
        "no_real_trade_decision": True,
        "recommended_source_handling_updates": [],
        "source_failure_patterns": [],
        "source_records": [],
        "source_usefulness_summary": {},
    }


if __name__ == "__main__":
    raise SystemExit(main())
