from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.manual_outcome_resolution_packet import (
    assert_valid_manual_outcome_resolution_packet,
    validate_manual_outcome_resolution_packet,
)
from pm_bot.practical.paper_update_approval import current_utc_timestamp
from pm_bot.practical.practical_io import bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

PAPER_HYPOTHESIS_FEEDBACK_CONTRACT_VERSION = "pmbot_paper_hypothesis_feedback.v1"

ANALYSIS_QUALITY_LABELS = {
    "pending",
    "useful",
    "incomplete",
    "wrong_due_to_missing_evidence",
    "wrong_due_to_bad_reasoning",
    "ambiguous",
    "void",
}
EVIDENCE_USEFULNESS_LABELS = {"pending", "useful", "insufficient", "misleading", "contradicted", "unknown"}


class PaperHypothesisFeedbackError(ValueError):
    pass


def build_paper_hypothesis_feedback(
    *,
    manual_outcome_packet: Mapping[str, Any],
    paper_tracking_state_snapshot: Mapping[str, Any] | None = None,
    applied_paper_update: Mapping[str, Any] | None = None,
    evidence_links: Sequence[Mapping[str, Any]] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    validation_errors = validate_manual_outcome_resolution_packet(manual_outcome_packet)
    if validation_errors:
        raise PaperHypothesisFeedbackError("; ".join(validation_errors))

    generated_at = generated_at or current_utc_timestamp()
    market_id = clean_text(manual_outcome_packet.get("market_id"))
    hypothesis_id = clean_text(manual_outcome_packet.get("hypothesis_id"))
    outcome_status = clean_text(manual_outcome_packet.get("outcome_status"))
    result_label = clean_text(manual_outcome_packet.get("paper_hypothesis_result_label"))
    snapshot = paper_tracking_state_snapshot or {}
    update = applied_paper_update or {}
    links = [dict(row) for row in evidence_links or _evidence_links_for_market(snapshot, market_id)]

    if outcome_status == "unresolved":
        analysis_quality_label = "pending"
        evidence_usefulness_label = "pending"
        feedback_ready = False
    else:
        analysis_quality_label = _analysis_quality_label(manual_outcome_packet)
        evidence_usefulness_label = _evidence_usefulness_label(manual_outcome_packet)
        feedback_ready = manual_outcome_packet.get("operator_approved") is True

    feedback = {
        "contract_version": PAPER_HYPOTHESIS_FEEDBACK_CONTRACT_VERSION,
        "feedback_id": f"paper-hypothesis-feedback-014-{market_id}-{outcome_status}",
        "created_at": generated_at,
        "market_id": market_id,
        "market_title": clean_text(manual_outcome_packet.get("market_title")),
        "hypothesis_id": hypothesis_id,
        "outcome_status": outcome_status,
        "paper_hypothesis_result_label": result_label,
        "analysis_quality_label": analysis_quality_label,
        "evidence_usefulness_label": evidence_usefulness_label,
        "source_contribution_review": _source_contribution_review(
            outcome_status=outcome_status,
            evidence_usefulness_label=evidence_usefulness_label,
            evidence_links=links,
            manual_outcome_packet=manual_outcome_packet,
        ),
        "reasoning_lessons": _pending_or_packet_lessons(outcome_status, manual_outcome_packet, "reasoning_lessons"),
        "missing_evidence_lessons": _pending_or_packet_lessons(
            outcome_status, manual_outcome_packet, "missing_evidence_lessons"
        ),
        "source_quality_lessons": _pending_or_packet_lessons(
            outcome_status, manual_outcome_packet, "source_accuracy_lessons"
        ),
        "analysis_rule_improvement_notes": _analysis_rule_improvement_notes(
            outcome_status=outcome_status,
            analysis_quality_label=analysis_quality_label,
            manual_outcome_packet=manual_outcome_packet,
            applied_paper_update=update,
        ),
        "next_prompt_improvements": _next_prompt_improvements(
            outcome_status=outcome_status,
            analysis_quality_label=analysis_quality_label,
            manual_outcome_packet=manual_outcome_packet,
        ),
        "feedback_ready": feedback_ready,
        "feedback_applied": False,
        "no_real_trade_decision": True,
        "safety_summary": _paper_feedback_safety_summary(),
    }
    _assert_safe_feedback_labels(feedback)
    return feedback


def write_paper_hypothesis_feedback(
    feedback: Mapping[str, Any],
    *,
    out_json_path: str | Path,
    out_md_path: str | Path,
) -> None:
    write_json(out_json_path, dict(feedback))
    write_text(out_md_path, render_paper_hypothesis_feedback_markdown(feedback))


def render_paper_hypothesis_feedback_markdown(feedback: Mapping[str, Any]) -> str:
    lines = [
        "# Paper Hypothesis Feedback",
        "",
        f"- Feedback ID: `{feedback.get('feedback_id')}`",
        f"- Market: `{feedback.get('market_id')}` - {feedback.get('market_title')}",
        f"- Outcome status: `{feedback.get('outcome_status')}`",
        f"- Paper result label: `{feedback.get('paper_hypothesis_result_label')}`",
        f"- Analysis quality label: `{feedback.get('analysis_quality_label')}`",
        f"- Evidence usefulness label: `{feedback.get('evidence_usefulness_label')}`",
        f"- Feedback ready: `{str(feedback.get('feedback_ready')).lower()}`",
        "",
        "## Source Contribution Review",
        "",
        f"- Status: `{feedback.get('source_contribution_review', {}).get('status')}`",
        f"- Summary: {feedback.get('source_contribution_review', {}).get('summary')}",
        "",
        "## Lessons",
        "",
        "### Reasoning",
        "",
        *bullet_lines(str(item) for item in feedback.get("reasoning_lessons", [])),
        "",
        "### Missing Evidence",
        "",
        *bullet_lines(str(item) for item in feedback.get("missing_evidence_lessons", [])),
        "",
        "### Source Quality",
        "",
        *bullet_lines(str(item) for item in feedback.get("source_quality_lessons", [])),
        "",
        "## Analysis Improvements",
        "",
        *bullet_lines(str(item) for item in feedback.get("analysis_rule_improvement_notes", [])),
        "",
        "## Prompt Improvements",
        "",
        *bullet_lines(str(item) for item in feedback.get("next_prompt_improvements", [])),
        "",
        "## Safety",
        "",
        "- feedback_applied: `false`",
        "- no_real_trade_decision: `true`",
    ]
    return "\n".join(lines) + "\n"


def _analysis_quality_label(packet: Mapping[str, Any]) -> str:
    outcome_status = clean_text(packet.get("outcome_status"))
    result_label = clean_text(packet.get("paper_hypothesis_result_label"))
    if outcome_status == "void" or result_label == "void":
        return "void"
    if outcome_status == "ambiguous" or result_label == "ambiguous":
        return "ambiguous"
    if result_label == "aligned":
        return "useful"
    if result_label == "not_aligned":
        if _clean_lessons(packet.get("missing_evidence_lessons")):
            return "wrong_due_to_missing_evidence"
        if _clean_lessons(packet.get("reasoning_lessons")):
            return "wrong_due_to_bad_reasoning"
        return "incomplete"
    return "pending"


def _evidence_usefulness_label(packet: Mapping[str, Any]) -> str:
    outcome_status = clean_text(packet.get("outcome_status"))
    if outcome_status == "unresolved":
        return "pending"
    if outcome_status in {"ambiguous", "void"}:
        return "unknown"
    source_lessons = " ".join(_clean_lessons(packet.get("source_accuracy_lessons"))).lower()
    if "contradict" in source_lessons:
        return "contradicted"
    if "misleading" in source_lessons:
        return "misleading"
    if _clean_lessons(packet.get("missing_evidence_lessons")) and not packet.get("source_evidence_used_for_resolution"):
        return "insufficient"
    if packet.get("source_evidence_used_for_resolution") or _clean_lessons(packet.get("source_accuracy_lessons")):
        return "useful"
    return "unknown"


def _source_contribution_review(
    *,
    outcome_status: str,
    evidence_usefulness_label: str,
    evidence_links: Sequence[Mapping[str, Any]],
    manual_outcome_packet: Mapping[str, Any],
) -> dict[str, Any]:
    if outcome_status == "unresolved":
        return {
            "status": "pending",
            "summary": "Outcome remains unresolved; source contribution cannot be judged yet.",
            "evidence_link_count": len(evidence_links),
            "resolution_source_count": 0,
            "evidence_links": list(evidence_links),
        }
    resolution_sources = [dict(row) for row in manual_outcome_packet.get("source_evidence_used_for_resolution", [])]
    return {
        "status": evidence_usefulness_label,
        "summary": _source_review_summary(evidence_usefulness_label, len(evidence_links), len(resolution_sources)),
        "evidence_link_count": len(evidence_links),
        "resolution_source_count": len(resolution_sources),
        "evidence_links": list(evidence_links),
        "resolution_sources": resolution_sources,
    }


def _source_review_summary(label: str, evidence_link_count: int, resolution_source_count: int) -> str:
    if label == "useful":
        return "Local source evidence contributed to the manual feedback review."
    if label == "insufficient":
        return "Local source evidence did not cover the needed resolution facts."
    if label in {"misleading", "contradicted"}:
        return "Local source evidence needs operator review before reuse."
    return f"Source contribution remains unknown from {evidence_link_count} analysis links and {resolution_source_count} resolution sources."


def _analysis_rule_improvement_notes(
    *,
    outcome_status: str,
    analysis_quality_label: str,
    manual_outcome_packet: Mapping[str, Any],
    applied_paper_update: Mapping[str, Any],
) -> list[str]:
    if outcome_status == "unresolved":
        return []
    if analysis_quality_label == "useful":
        return ["Preserve the local evidence-to-hypothesis link pattern that helped later review."]
    if analysis_quality_label == "wrong_due_to_missing_evidence":
        return [
            "Require explicit missing-evidence notes when a paper hypothesis lacks the source needed for later resolution review."
        ]
    if analysis_quality_label == "wrong_due_to_bad_reasoning":
        return ["Record the reasoning failure as a prompt rule candidate before applying any future analysis update."]
    if analysis_quality_label == "ambiguous":
        return ["Keep ambiguous outcomes separate from wrong-hypothesis labels."]
    if analysis_quality_label == "void":
        return ["Do not score void outcomes as paper hypothesis wins or misses."]
    if clean_text(applied_paper_update.get("applied_update_id")):
        return ["Review the applied paper update after the approved local outcome packet."]
    return []


def _next_prompt_improvements(
    *,
    outcome_status: str,
    analysis_quality_label: str,
    manual_outcome_packet: Mapping[str, Any],
) -> list[str]:
    if outcome_status == "unresolved":
        return []
    if analysis_quality_label == "wrong_due_to_missing_evidence":
        return ["Ask future paper analyses to name the exact resolution source needed before outcome review."]
    if analysis_quality_label == "wrong_due_to_bad_reasoning":
        return ["Ask future paper analyses to separate observed facts from reasoning assumptions."]
    if analysis_quality_label == "useful":
        return ["Keep source relevance and outcome resolution as distinct review steps."]
    if analysis_quality_label == "ambiguous":
        return ["Ask future analyses to state which resolution facts would make the outcome ambiguous."]
    if analysis_quality_label == "void":
        return ["Ask future analyses to keep void outcomes outside performance scoring."]
    return []


def _pending_or_packet_lessons(outcome_status: str, packet: Mapping[str, Any], field: str) -> list[str]:
    if outcome_status == "unresolved":
        return []
    return _clean_lessons(packet.get(field))


def _evidence_links_for_market(snapshot: Mapping[str, Any], market_id: str) -> list[Mapping[str, Any]]:
    rows = snapshot.get("evidence_links", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping) and clean_text(row.get("market_id")) == market_id]


def _clean_lessons(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [clean_text(item) for item in value if isinstance(item, str) and clean_text(item)]


def _assert_safe_feedback_labels(feedback: Mapping[str, Any]) -> None:
    if feedback.get("analysis_quality_label") not in ANALYSIS_QUALITY_LABELS:
        raise PaperHypothesisFeedbackError("invalid analysis_quality_label")
    if feedback.get("evidence_usefulness_label") not in EVIDENCE_USEFULNESS_LABELS:
        raise PaperHypothesisFeedbackError("invalid evidence_usefulness_label")
    if feedback.get("no_real_trade_decision") is not True:
        raise PaperHypothesisFeedbackError("feedback must remain paper-only")


def _paper_feedback_safety_summary() -> dict[str, Any]:
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
    parser = argparse.ArgumentParser(description="Build paper hypothesis feedback from a local manual outcome packet.")
    parser.add_argument("packet", help="Local manual outcome packet JSON path.")
    parser.add_argument("--snapshot", default="", help="Optional paper tracking snapshot JSON path.")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    snapshot = load_json_object(args.snapshot, label="paper tracking snapshot") if args.snapshot else None
    assert_valid_manual_outcome_resolution_packet(packet)
    feedback = build_paper_hypothesis_feedback(manual_outcome_packet=packet, paper_tracking_state_snapshot=snapshot)
    write_paper_hypothesis_feedback(feedback, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
