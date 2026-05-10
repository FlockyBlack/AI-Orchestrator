from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.paper_update_approval import current_utc_timestamp
from pm_bot.practical.practical_io import bullet_lines, clean_text, safe_summary, write_json, write_text

SOURCE_ACCURACY_FEEDBACK_CONTRACT_VERSION = "pmbot_source_accuracy_feedback.v1"

SOURCE_ACCURACY_LABELS = {"pending", "useful", "insufficient", "misleading", "contradicted", "unknown"}


class SourceAccuracyFeedbackError(ValueError):
    pass


def build_source_accuracy_feedback(
    *,
    paper_hypothesis_feedback: Mapping[str, Any],
    source_records: Sequence[Mapping[str, Any]] | None = None,
    manual_outcome_packet: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or current_utc_timestamp()
    market_id = clean_text(paper_hypothesis_feedback.get("market_id"))
    hypothesis_id = clean_text(paper_hypothesis_feedback.get("hypothesis_id"))
    outcome_status = clean_text(paper_hypothesis_feedback.get("outcome_status"))
    evidence_label = clean_text(paper_hypothesis_feedback.get("evidence_usefulness_label"))
    records = _source_records(source_records, manual_outcome_packet)
    labeled_records = [_label_source_record(row, outcome_status, evidence_label) for row in records]
    source_accuracy_labels = {
        clean_text(row.get("source_id") or row.get("source_reference") or f"source-{index + 1}"): row["source_accuracy_label"]
        for index, row in enumerate(labeled_records)
    }

    feedback = {
        "contract_version": SOURCE_ACCURACY_FEEDBACK_CONTRACT_VERSION,
        "source_feedback_id": f"source-accuracy-feedback-014-{market_id}-{outcome_status}",
        "created_at": generated_at,
        "market_id": market_id,
        "hypothesis_id": hypothesis_id,
        "input_feedback_id": clean_text(paper_hypothesis_feedback.get("feedback_id")),
        "outcome_status": outcome_status,
        "source_records": labeled_records,
        "source_accuracy_labels": source_accuracy_labels,
        "source_role_in_analysis": _source_role_in_analysis(labeled_records),
        "source_role_in_resolution": _source_role_in_resolution(labeled_records, manual_outcome_packet),
        "source_lessons": _source_lessons(paper_hypothesis_feedback, outcome_status),
        "recommended_future_source_handling": _recommended_future_source_handling(labeled_records, outcome_status),
        "requires_more_outcomes": _requires_more_outcomes(outcome_status, source_accuracy_labels),
        "no_autonomous_training_performed": True,
        "no_real_trade_decision": True,
        "safety_summary": _source_accuracy_safety_summary(),
    }
    _assert_source_accuracy_feedback_safe(feedback)
    return feedback


def write_source_accuracy_feedback(
    feedback: Mapping[str, Any],
    *,
    out_json_path: str | Path,
    out_md_path: str | Path,
) -> None:
    write_json(out_json_path, dict(feedback))
    write_text(out_md_path, render_source_accuracy_feedback_markdown(feedback))


def render_source_accuracy_feedback_markdown(feedback: Mapping[str, Any]) -> str:
    lines = [
        "# Source Accuracy Feedback",
        "",
        f"- Source feedback ID: `{feedback.get('source_feedback_id')}`",
        f"- Market: `{feedback.get('market_id')}`",
        f"- Outcome status: `{feedback.get('outcome_status')}`",
        f"- Requires more outcomes: `{str(feedback.get('requires_more_outcomes')).lower()}`",
        "",
        "## Source Labels",
        "",
    ]
    labels = feedback.get("source_accuracy_labels", {})
    if isinstance(labels, Mapping) and labels:
        lines.extend(f"- `{source_id}`: `{label}`" for source_id, label in sorted(labels.items()))
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Lessons",
            "",
            *bullet_lines(str(item) for item in feedback.get("source_lessons", [])),
            "",
            "## Future Source Handling",
            "",
            *bullet_lines(
                f"`{row.get('source_id')}` - {row.get('handling')}"
                for row in feedback.get("recommended_future_source_handling", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Safety",
            "",
            "- no_autonomous_training_performed: `true`",
            "- no_real_trade_decision: `true`",
        ]
    )
    return "\n".join(lines) + "\n"


def _source_records(
    source_records: Sequence[Mapping[str, Any]] | None,
    manual_outcome_packet: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    records = [dict(row) for row in source_records or []]
    if records:
        return records
    if not manual_outcome_packet:
        return []
    resolution_sources = manual_outcome_packet.get("source_evidence_used_for_resolution", [])
    if not isinstance(resolution_sources, list):
        return []
    projected = []
    for index, row in enumerate(resolution_sources):
        if not isinstance(row, Mapping):
            continue
        projected.append(
            {
                "source_id": clean_text(row.get("source_id") or row.get("source_reference") or f"resolution-source-{index + 1}"),
                "source_name": clean_text(row.get("source_name") or row.get("source_reference")),
                "source_role": "manual_resolution_source",
                "source_reference": clean_text(row.get("source_reference") or row.get("source_url") or row.get("url")),
            }
        )
    return projected


def _label_source_record(row: Mapping[str, Any], outcome_status: str, evidence_label: str) -> dict[str, Any]:
    record = dict(row)
    if outcome_status == "unresolved":
        label = "pending"
    elif evidence_label in SOURCE_ACCURACY_LABELS:
        label = evidence_label
    else:
        label = "unknown"
    if outcome_status in {"ambiguous", "void"}:
        label = "unknown"
    record["source_accuracy_label"] = label
    record["accuracy_limit"] = _accuracy_limit(outcome_status, label)
    return record


def _accuracy_limit(outcome_status: str, label: str) -> str:
    if outcome_status == "unresolved":
        return "Outcome unresolved; source accuracy is not claimed."
    if label == "unknown":
        return "Local packet does not support a source accuracy claim."
    return "Label is based only on the approved local manual outcome packet."


def _source_role_in_analysis(records: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    roles = []
    for row in records:
        roles.append(
            {
                "source_id": clean_text(row.get("source_id") or row.get("source_reference")),
                "role": clean_text(row.get("source_usefulness_label") or row.get("source_role") or "analysis_context"),
            }
        )
    return roles


def _source_role_in_resolution(
    records: Sequence[Mapping[str, Any]],
    manual_outcome_packet: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    resolution_sources = manual_outcome_packet.get("source_evidence_used_for_resolution", []) if manual_outcome_packet else []
    resolution_ids = {
        clean_text(row.get("source_id") or row.get("source_reference"))
        for row in resolution_sources
        if isinstance(row, Mapping)
    }
    roles = []
    for row in records:
        source_id = clean_text(row.get("source_id") or row.get("source_reference"))
        roles.append(
            {
                "source_id": source_id,
                "role": "used_for_manual_resolution" if source_id in resolution_ids else "analysis_context_only",
            }
        )
    return roles


def _source_lessons(feedback: Mapping[str, Any], outcome_status: str) -> list[str]:
    if outcome_status == "unresolved":
        return []
    lessons = feedback.get("source_quality_lessons", [])
    if not isinstance(lessons, list):
        return []
    return [clean_text(item) for item in lessons if isinstance(item, str) and clean_text(item)]


def _recommended_future_source_handling(records: Sequence[Mapping[str, Any]], outcome_status: str) -> list[dict[str, str]]:
    handling = []
    for row in records:
        source_id = clean_text(row.get("source_id") or row.get("source_reference"))
        label = clean_text(row.get("source_accuracy_label"))
        if outcome_status == "unresolved":
            action = "Keep pending until an approved local outcome packet exists."
        elif label == "useful":
            action = "Keep as a useful local review source for this market class."
        elif label == "insufficient":
            action = "Add a note that this source was not enough for outcome resolution review."
        elif label in {"misleading", "contradicted"}:
            action = "Require explicit operator review before reusing this source pattern."
        else:
            action = "Keep the source label unknown until more resolved local outcomes exist."
        handling.append({"source_id": source_id, "source_accuracy_label": label, "handling": action})
    return handling


def _requires_more_outcomes(outcome_status: str, labels: Mapping[str, str]) -> bool:
    if outcome_status == "unresolved":
        return True
    if not labels:
        return True
    return any(label in {"pending", "unknown"} for label in labels.values())


def _assert_source_accuracy_feedback_safe(feedback: Mapping[str, Any]) -> None:
    labels = feedback.get("source_accuracy_labels", {})
    if not isinstance(labels, Mapping):
        raise SourceAccuracyFeedbackError("source_accuracy_labels must be an object")
    invalid = [label for label in labels.values() if label not in SOURCE_ACCURACY_LABELS]
    if invalid:
        raise SourceAccuracyFeedbackError(f"invalid source accuracy labels: {invalid}")
    if feedback.get("no_autonomous_training_performed") is not True:
        raise SourceAccuracyFeedbackError("no_autonomous_training_performed must be true")
    if feedback.get("no_real_trade_decision") is not True:
        raise SourceAccuracyFeedbackError("no_real_trade_decision must be true")


def _source_accuracy_safety_summary() -> dict[str, Any]:
    summary = safe_summary()
    summary.update(
        {
            "new_live_fetch_performed": False,
            "openrouter_calls_performed": 0,
            "new_polymarket_api_calls_performed": 0,
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "outcome_resolution_invented": False,
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_trading": True,
        }
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build source accuracy feedback from paper hypothesis feedback.")
    parser.add_argument("feedback", help="Local paper hypothesis feedback JSON path.")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    feedback = json.loads(Path(args.feedback).read_text(encoding="utf-8"))
    source_feedback = build_source_accuracy_feedback(paper_hypothesis_feedback=feedback)
    write_source_accuracy_feedback(source_feedback, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
