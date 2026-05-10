from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

SOURCE_ACCESSIBILITY_LEARNING_CONTRACT_VERSION = "pmbot_source_accessibility_learning.v1"
SOURCE_TASK_ID = "ORCH-PMBOT-PRACTICAL-008-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-WITH-CONCRETE-URL-MANIFEST"


def build_source_accessibility_learning(
    *,
    execution_summary: Mapping[str, Any],
    replay_artifact: Mapping[str, Any],
    failure_diagnosis: Mapping[str, Any],
    learning_id: str = "source-accessibility-learning-009",
    source_task_id: str = SOURCE_TASK_ID,
) -> dict[str, Any]:
    records = [_accessibility_record(row, replay_artifact, failure_diagnosis) for row in _fetch_results(execution_summary)]
    reachable = [record for record in records if record["accessibility_status"] == "reachable"]
    failed = [record for record in records if record["accessibility_status"] == "failed"]
    replay_usable = [record for record in reachable if record["replay_usable"] is True]
    url_fix = [record for record in failed if record["recommended_handling"] in {"replace_url", "verify_url_manually", "use_alternative_official_source", "retry_later"}]
    manual_review = [
        record
        for record in records
        if record["accessibility_status"] == "failed" or record.get("operator_review_reason")
    ]
    return {
        "contract_version": SOURCE_ACCESSIBILITY_LEARNING_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "learning_id": learning_id,
        "source_task_id": source_task_id,
        "source_accessibility_records": records,
        "reachable_sources": reachable,
        "failed_sources": failed,
        "replay_usable_sources": replay_usable,
        "sources_requiring_url_fix": url_fix,
        "sources_requiring_manual_review": manual_review,
        "recommended_source_handling_updates": _recommended_updates(records),
        "no_autonomous_training_performed": True,
        "no_real_trade_decision": True,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "orders_or_trading_actions": False,
        "wallet_or_private_key_access": False,
        "no_live_fetch_performed_in_this_task": True,
        "safety_summary": safe_summary(),
    }


def write_source_accessibility_learning(
    *,
    execution_summary_path: str | Path,
    replay_artifact_path: str | Path,
    failure_diagnosis_path: str | Path,
    out_json_path: str | Path,
    out_md_path: str | Path,
    learning_id: str = "source-accessibility-learning-009",
) -> dict[str, Any]:
    summary = load_json_object(execution_summary_path, label="PRACTICAL-008 execution summary")
    replay = load_json_object(replay_artifact_path, label="PRACTICAL-008 replay artifact")
    diagnosis = load_json_object(failure_diagnosis_path, label="PRACTICAL-009 failure diagnosis")
    learning = build_source_accessibility_learning(
        execution_summary=summary,
        replay_artifact=replay,
        failure_diagnosis=diagnosis,
        learning_id=learning_id,
    )
    write_json(out_json_path, learning)
    write_text(out_md_path, render_source_accessibility_learning_markdown(learning))
    return learning


def render_source_accessibility_learning_markdown(learning: Mapping[str, Any]) -> str:
    lines = [
        "# Source accessibility learning",
        "",
        f"- Learning ID: `{learning.get('learning_id')}`",
        f"- Reachable sources: {len(learning.get('reachable_sources', []))}",
        f"- Failed sources: {len(learning.get('failed_sources', []))}",
        f"- Replay-usable sources: {len(learning.get('replay_usable_sources', []))}",
        "",
        "## Source records",
        "",
    ]
    for record in learning.get("source_accessibility_records", []):
        lines.extend(
            [
                f"- `{record.get('request_intent_id')}`",
                f"  Status: `{record.get('accessibility_status')}`",
                f"  Handling: `{record.get('recommended_handling')}`",
                f"  Replay usable: `{str(record.get('replay_usable')).lower()}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Recommended handling updates",
            "",
            *bullet_lines(
                f"`{item.get('request_intent_id')}` -> `{item.get('recommended_handling')}`"
                for item in learning.get("recommended_source_handling_updates", [])
            ),
            "",
            "## Safety boundary",
            "",
            "- Source accessibility learning only; no outcome-correctness learning is performed.",
            "- No autonomous training, real trade decision, wallet path, order path, or executable market output is created.",
            "- A later scoped task must handle any corrected URL/source packet.",
        ]
    )
    return "\n".join(lines) + "\n"


def _fetch_results(execution_summary: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = execution_summary.get("fetch_results")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, Mapping)]
    return [
        row
        for row in list(execution_summary.get("succeeded_requests", [])) + list(execution_summary.get("failed_requests", []))
        if isinstance(row, Mapping)
    ]


def _accessibility_record(
    row: Mapping[str, Any],
    replay_artifact: Mapping[str, Any],
    failure_diagnosis: Mapping[str, Any],
) -> dict[str, Any]:
    status = clean_text(row.get("result_status"))
    accessible = status == "succeeded"
    request_intent_id = clean_text(row.get("request_intent_id"))
    failure = _diagnosis_by_request_id(failure_diagnosis, request_intent_id)
    replay_usable = _replay_has_source(replay_artifact, request_intent_id)
    return {
        "request_intent_id": request_intent_id,
        "market_id": clean_text(row.get("market_id")),
        "market_title": clean_text(row.get("market_title")),
        "source_name": clean_text(row.get("source_name")),
        "source_category": clean_text(row.get("source_category")),
        "source_url": clean_text(row.get("source_url") or row.get("final_url") or ""),
        "accessibility_status": "reachable" if accessible else "failed",
        "failure_category": clean_text(failure.get("failure_category")) if failure else "",
        "evidence_packet_id": clean_text(row.get("evidence_packet_id") or ""),
        "evidence_usable": accessible and bool(row.get("evidence_packet_id")),
        "replay_usable": replay_usable,
        "recommended_handling": _recommended_handling(accessible, failure),
        "operator_review_reason": "Confirm exact source relevance to the paper hypothesis." if accessible else "Review failure before any later corrected fetch packet.",
    }


def _diagnosis_by_request_id(diagnosis: Mapping[str, Any], request_intent_id: str) -> Mapping[str, Any]:
    for item in diagnosis.get("per_request_diagnosis", []):
        if isinstance(item, Mapping) and item.get("request_intent_id") == request_intent_id:
            return item
    return {}


def _replay_has_source(replay_artifact: Mapping[str, Any], request_intent_id: str) -> bool:
    for source in replay_artifact.get("source_packets", []):
        if isinstance(source, Mapping) and source.get("source_id") == request_intent_id:
            return source.get("replay_mode") is True
    return False


def _recommended_handling(accessible: bool, failure: Mapping[str, Any]) -> str:
    if accessible:
        return "keep_for_operator_review"
    category = clean_text(failure.get("failure_category"))
    if category == "http_error":
        return "use_alternative_official_source"
    if category == "source_unavailable":
        return "replace_url"
    if category in {"timeout", "dns_error", "url_invalid", "unknown"}:
        return "verify_url_manually"
    return "verify_url_manually"


def _recommended_updates(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "request_intent_id": clean_text(record.get("request_intent_id")),
            "market_id": clean_text(record.get("market_id")),
            "source_url": clean_text(record.get("source_url")),
            "recommended_handling": clean_text(record.get("recommended_handling")),
            "requires_operator_review": True,
        }
        for record in records
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record source accessibility learning from saved PRACTICAL-008 artifacts.")
    parser.add_argument("--execution-summary", required=True)
    parser.add_argument("--replay-artifact", required=True)
    parser.add_argument("--failure-diagnosis", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    write_source_accessibility_learning(
        execution_summary_path=args.execution_summary,
        replay_artifact_path=args.replay_artifact,
        failure_diagnosis_path=args.failure_diagnosis,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
