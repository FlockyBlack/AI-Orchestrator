from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import (
    GENERATED_AT,
    PracticalIOError,
    bullet_lines,
    clean_string_list,
    clean_text,
    load_json_any,
    normalize_path,
    path_exists,
    safe_summary,
    sorted_counter_dict,
    write_json,
    write_text,
)

SUMMARY_CONTRACT_VERSION = "pmbot_market_queue_summary.v1"
ALLOWED_QUEUE_STATUSES = {
    "queued",
    "analysis_ready",
    "hypothesis_active",
    "outcome_pending",
    "feedback_ready",
    "feedback_complete",
    "blocked",
}

QUEUE_ITEM_FIELDS = (
    "queue_item_id",
    "market_id",
    "market_title",
    "market_type",
    "local_input_path",
    "status",
    "created_at",
    "updated_at",
    "analysis_result_path",
    "analysis_markdown_path",
    "paper_hypothesis_id",
    "outcome_record_path",
    "feedback_result_path",
    "source_learning_ledger_path",
    "blockers",
    "next_operator_action",
)

LINKED_ARTIFACT_FIELDS = (
    "local_input_path",
    "analysis_result_path",
    "analysis_markdown_path",
    "outcome_record_path",
    "feedback_result_path",
    "source_learning_ledger_path",
)


class MarketQueueError(ValueError):
    pass


def load_market_queue(path: str | Path) -> dict[str, Any]:
    payload = load_json_any(path, label="market queue")
    if isinstance(payload, list):
        return {"contract_version": "pmbot_market_queue.v1", "items": payload}
    if not isinstance(payload, dict):
        raise MarketQueueError("market queue JSON must be an object or list")
    if "items" not in payload:
        raise MarketQueueError("market queue JSON must contain items")
    if not isinstance(payload["items"], list):
        raise MarketQueueError("market queue items must be a list")
    return payload


def summarize_market_queue(path: str | Path) -> dict[str, Any]:
    queue = load_market_queue(path)
    base_dir = Path(path).parent
    items = [_normalize_queue_item(item, index=index, base_dir=base_dir) for index, item in enumerate(queue["items"])]
    status_counts = Counter(item["status"] for item in items)
    blocked_items = [item for item in items if item["computed_blockers"]]
    missing_artifacts = [
        {
            "queue_item_id": item["queue_item_id"],
            "market_id": item["market_id"],
            "field": missing["field"],
            "path": missing["path"],
        }
        for item in items
        for missing in item["missing_linked_artifacts"]
    ]
    next_actions = [
        {
            "queue_item_id": item["queue_item_id"],
            "market_id": item["market_id"],
            "market_title": item["market_title"],
            "next_operator_action": item["computed_next_operator_action"],
        }
        for item in items
        if item["computed_next_operator_action"]
    ]
    return {
        "contract_version": SUMMARY_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "queue_path": normalize_path(path),
        "total_count": len(items),
        "status_counts": sorted_counter_dict(status_counts),
        "items": items,
        "missing_linked_artifacts": missing_artifacts,
        "blocked_items": [
            {
                "queue_item_id": item["queue_item_id"],
                "market_id": item["market_id"],
                "market_title": item["market_title"],
                "blockers": item["computed_blockers"],
                "next_operator_action": item["computed_next_operator_action"],
            }
            for item in blocked_items
        ],
        "next_operator_actions": next_actions,
        "safety_summary": safe_summary(),
    }


def write_market_queue_summary(
    *,
    queue_path: str | Path,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    summary = summarize_market_queue(queue_path)
    if out_json_path is not None:
        write_json(out_json_path, summary)
    if out_md_path is not None:
        write_text(out_md_path, render_market_queue_markdown(summary))
    return summary


def render_market_queue_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Market Queue Summary",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Queue items: {summary['total_count']}",
        "",
        "## Status counts",
        "",
        *bullet_lines(f"`{status}`: {count}" for status, count in summary["status_counts"].items()),
        "",
        "## Markets",
        "",
    ]
    for item in summary["items"]:
        blockers = item["computed_blockers"]
        blocker_text = "; ".join(blockers) if blockers else "none"
        lines.extend(
            [
                f"- `{item['queue_item_id']}` `{item['status']}` - {item['market_title']}",
                f"  Next: {item['computed_next_operator_action']}",
                f"  Blockers: {blocker_text}",
            ]
        )
    lines.extend(
        [
            "",
            "## Missing linked artifacts",
            "",
            *bullet_lines(
                f"`{row['queue_item_id']}` missing `{row['field']}` at `{row['path']}`"
                for row in summary["missing_linked_artifacts"]
            ),
            "",
            "## Safety boundary",
            "",
            "- Local queue JSON and linked local artifacts only.",
            "- No live fetch, API key, wallet, order, or trading action is used.",
            "- Operator actions are workflow steps, not market instructions.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize a local-only PMBOT practical market queue.")
    parser.add_argument("--queue", required=True, help="Local market queue JSON.")
    parser.add_argument("--out-json", required=True, help="Output queue summary JSON.")
    parser.add_argument("--out-md", required=True, help="Output queue summary Markdown.")
    args = parser.parse_args(argv)

    write_market_queue_summary(queue_path=args.queue, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


def _normalize_queue_item(item: Any, *, index: int, base_dir: Path) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise MarketQueueError(f"queue item {index} must be an object")
    missing_fields = [field for field in QUEUE_ITEM_FIELDS if field not in item]
    if missing_fields:
        raise MarketQueueError(f"queue item {index} missing fields: {', '.join(missing_fields)}")
    normalized = {field: item.get(field) for field in QUEUE_ITEM_FIELDS}
    for field in (
        "queue_item_id",
        "market_id",
        "market_title",
        "market_type",
        "status",
        "created_at",
        "updated_at",
    ):
        normalized[field] = clean_text(normalized[field])
    if normalized["status"] not in ALLOWED_QUEUE_STATUSES:
        raise MarketQueueError(f"queue item {index} status is not allowed: {normalized['status']}")
    normalized["blockers"] = clean_string_list(item.get("blockers"))
    normalized["next_operator_action"] = clean_text(item.get("next_operator_action", ""))
    for field in LINKED_ARTIFACT_FIELDS:
        normalized[field] = clean_text(item.get(field, ""))
    normalized["paper_hypothesis_id"] = clean_text(item.get("paper_hypothesis_id", ""))

    missing_linked_artifacts = _missing_linked_artifacts(normalized, base_dir=base_dir)
    computed_blockers = list(normalized["blockers"])
    computed_blockers.extend(
        f"Missing linked artifact `{row['field']}` at `{row['path']}`" for row in missing_linked_artifacts
    )
    if normalized["status"] == "blocked" and not computed_blockers:
        computed_blockers.append("Queue item is marked blocked without a detailed local blocker.")
    normalized["missing_linked_artifacts"] = missing_linked_artifacts
    normalized["computed_blockers"] = computed_blockers
    normalized["computed_next_operator_action"] = _next_operator_action(normalized, computed_blockers)
    normalized["safety_flags"] = safe_summary()
    return normalized


def _missing_linked_artifacts(item: Mapping[str, Any], *, base_dir: Path) -> list[dict[str, str]]:
    fields = ["local_input_path"]
    if item["status"] in {"analysis_ready", "hypothesis_active", "outcome_pending", "feedback_ready", "feedback_complete"}:
        fields.extend(["analysis_result_path", "analysis_markdown_path"])
    if item["status"] in {"feedback_ready", "feedback_complete"}:
        fields.append("outcome_record_path")
    if item["status"] == "feedback_complete":
        fields.extend(["feedback_result_path", "source_learning_ledger_path"])

    missing: list[dict[str, str]] = []
    for field in fields:
        value = item.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append({"field": field, "path": ""})
            continue
        try:
            exists = path_exists(value, base_dir=base_dir)
        except PracticalIOError:
            exists = False
        if not exists:
            missing.append({"field": field, "path": value})
    return missing


def _next_operator_action(item: Mapping[str, Any], blockers: Sequence[str]) -> str:
    if blockers:
        return "Resolve the local blockers before continuing this queue item."
    status = item["status"]
    if status == "queued":
        return "Run local packet import if needed, then run finite local analysis."
    if status == "analysis_ready":
        return "Inspect the analysis card and decide whether to track the paper-only hypothesis."
    if status == "hypothesis_active":
        return "Wait for a local outcome record or add one when the outcome is known."
    if status == "outcome_pending":
        return "Add a resolved local outcome record when available."
    if status == "feedback_ready":
        return "Run local paper feedback for the analysis and outcome pair."
    if status == "feedback_complete":
        return "Review feedback lessons and update the source learning ledger."
    if status == "blocked":
        return "Resolve the recorded blocker before further practical review."
    return "Review this queue item manually."


if __name__ == "__main__":
    raise SystemExit(main())
