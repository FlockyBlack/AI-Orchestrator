from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

PAPER_HYPOTHESIS_UPDATE_CANDIDATE_CONTRACT_VERSION = "pmbot_paper_hypothesis_update_candidate.v1"


def build_paper_hypothesis_update_candidate(
    *,
    public_evidence_review: Mapping[str, Any],
    existing_paper_hypothesis: Mapping[str, Any],
    update_candidate_id: str = "paper-hypothesis-update-candidate-009",
) -> dict[str, Any]:
    market_id = clean_text(existing_paper_hypothesis.get("market_id")) or _single_or_multiple(
        public_evidence_review.get("affected_market_ids", [])
    )
    hypothesis_id = clean_text(existing_paper_hypothesis.get("hypothesis_id")) or _single_or_multiple(
        public_evidence_review.get("affected_hypothesis_ids", [])
    )
    candidate = {
        "contract_version": PAPER_HYPOTHESIS_UPDATE_CANDIDATE_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "update_candidate_id": update_candidate_id,
        "source_review_id": clean_text(public_evidence_review.get("review_id")),
        "market_id": market_id,
        "hypothesis_id": hypothesis_id,
        "existing_paper_hypothesis_summary": _existing_hypothesis_summary(existing_paper_hypothesis),
        "evidence_summary": list(public_evidence_review.get("normalized_evidence_summary", [])),
        "proposed_paper_tracking_update": [
            "Record that PRACTICAL-008 captured and replayed a public SCOTUS docket source for this paper hypothesis.",
            "Treat the evidence as source-accessibility support only until an operator confirms exact case relevance.",
            "Keep final outcome resolution as a separate unresolved follow-up.",
        ],
        "update_reason": _update_reason(public_evidence_review),
        "operator_approval_required": True,
        "update_applied": False,
        "no_real_trade_decision": True,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "orders_or_trading_actions": False,
        "wallet_or_private_key_access": False,
        "automatic_analysis_update_performed": False,
        "original_hypothesis_changed": False,
        "safety_summary": safe_summary(),
    }
    return candidate


def write_paper_hypothesis_update_candidate(
    *,
    public_evidence_review_path: str | Path,
    existing_paper_hypothesis_path: str | Path,
    out_json_path: str | Path,
    out_md_path: str | Path,
    update_candidate_id: str = "paper-hypothesis-update-candidate-009",
) -> dict[str, Any]:
    review = load_json_object(public_evidence_review_path, label="public evidence review")
    hypothesis = load_json_object(existing_paper_hypothesis_path, label="existing paper hypothesis")
    candidate = build_paper_hypothesis_update_candidate(
        public_evidence_review=review,
        existing_paper_hypothesis=hypothesis,
        update_candidate_id=update_candidate_id,
    )
    candidate["existing_paper_hypothesis_artifact_path"] = str(existing_paper_hypothesis_path).replace("\\", "/")
    write_json(out_json_path, candidate)
    write_text(out_md_path, render_paper_hypothesis_update_candidate_markdown(candidate))
    return candidate


def render_paper_hypothesis_update_candidate_markdown(candidate: Mapping[str, Any]) -> str:
    lines = [
        "# Paper hypothesis update candidate",
        "",
        f"- Candidate ID: `{candidate.get('update_candidate_id')}`",
        f"- Source review: `{candidate.get('source_review_id')}`",
        f"- Market: `{candidate.get('market_id')}`",
        f"- Hypothesis: `{candidate.get('hypothesis_id')}`",
        f"- Update applied: `{str(candidate.get('update_applied')).lower()}`",
        "",
        "## Existing paper hypothesis",
        "",
        *bullet_lines(_summary_lines(candidate.get("existing_paper_hypothesis_summary", {}))),
        "",
        "## New evidence",
        "",
        *bullet_lines(candidate.get("evidence_summary", [])),
        "",
        "## Proposed tracking update",
        "",
        *bullet_lines(candidate.get("proposed_paper_tracking_update", [])),
        "",
        "## Why update is or is not useful",
        "",
        f"- Update reason: `{candidate.get('update_reason')}`",
        "- Useful for paper tracking because it records a saved public source and replay outcome.",
        "- Not sufficient for outcome resolution because the operator still needs exact source relevance and final outcome review.",
        "",
        "## Operator approval required",
        "",
        f"- `{str(candidate.get('operator_approval_required')).lower()}`",
        "",
        "## Safety boundary",
        "",
        "- Candidate artifact only; the original hypothesis file is unchanged.",
        "- No real trade decision, order path, wallet path, or executable market output is created.",
        "- No automatic analysis update is performed.",
    ]
    return "\n".join(lines) + "\n"


def _existing_hypothesis_summary(hypothesis: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "analysis_id": clean_text(hypothesis.get("analysis_id")),
        "market_id": clean_text(hypothesis.get("market_id")),
        "market_title": clean_text(hypothesis.get("market_title")),
        "hypothesis_id": clean_text(hypothesis.get("hypothesis_id")),
        "paper_hypothesis_summary": clean_text(hypothesis.get("paper_hypothesis_summary")),
        "outcome_check_needed": clean_text(hypothesis.get("outcome_check_needed")),
        "safety_label": clean_text(hypothesis.get("safety_label")),
        "source_dependency_count": len(hypothesis.get("source_dependencies", [])),
    }


def _summary_lines(summary: Any) -> list[str]:
    if not isinstance(summary, Mapping):
        return []
    return [f"{key}: `{value}`" for key, value in summary.items()]


def _single_or_multiple(values: Any) -> str:
    if isinstance(values, list) and len(values) == 1:
        return clean_text(values[0])
    if isinstance(values, list) and values:
        return "multiple"
    return "unknown"


def _update_reason(review: Mapping[str, Any]) -> str:
    if int(review.get("evidence_packet_count") or 0) <= 0:
        return "insufficient_evidence"
    if review.get("evidence_relevance") == "contradicts_tracking_assumption":
        return "contradiction_update"
    return "new_public_evidence"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a paper-only hypothesis update candidate.")
    parser.add_argument("--review", required=True)
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    write_paper_hypothesis_update_candidate(
        public_evidence_review_path=args.review,
        existing_paper_hypothesis_path=args.hypothesis,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
