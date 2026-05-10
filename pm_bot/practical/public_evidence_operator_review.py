from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

PUBLIC_EVIDENCE_OPERATOR_REVIEW_CONTRACT_VERSION = "pmbot_public_evidence_operator_review.v1"
SOURCE_TASK_ID = "ORCH-PMBOT-PRACTICAL-008-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-WITH-CONCRETE-URL-MANIFEST"


def build_public_evidence_operator_review(
    *,
    execution_summary: Mapping[str, Any],
    evidence_packets: Sequence[Mapping[str, Any]],
    replay_artifacts: Sequence[Mapping[str, Any]],
    replay_artifact_paths: Sequence[str],
    review_id: str = "public-evidence-review-009",
    source_task_id: str = SOURCE_TASK_ID,
) -> dict[str, Any]:
    affected_market_ids = sorted({market_id for packet in evidence_packets for market_id in packet.get("market_ids", [])})
    affected_hypothesis_ids = sorted(
        {hypothesis_id for packet in evidence_packets for hypothesis_id in packet.get("hypothesis_ids", [])}
    )
    normalized_summary = _normalized_evidence_summary(evidence_packets, execution_summary)
    limitations = _review_limitations(evidence_packets)
    review = {
        "contract_version": PUBLIC_EVIDENCE_OPERATOR_REVIEW_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "review_id": review_id,
        "source_task_id": source_task_id,
        "evidence_packet_count": len(evidence_packets),
        "evidence_packets_reviewed": [_reviewed_packet(packet) for packet in evidence_packets],
        "replay_artifacts_used": [
            _reviewed_replay_artifact(path, artifact) for path, artifact in zip(replay_artifact_paths, replay_artifacts)
        ],
        "affected_market_ids": affected_market_ids,
        "affected_hypothesis_ids": affected_hypothesis_ids,
        "normalized_evidence_summary": normalized_summary,
        "evidence_relevance": _evidence_relevance(evidence_packets),
        "contradiction_notes": _contradiction_notes(evidence_packets),
        "staleness_notes": _staleness_notes(evidence_packets),
        "limitations": limitations,
        "operator_review_required": True,
        "operator_review_checklist": [
            "Confirm the saved evidence packet matches the approved PRACTICAL-008 request intent.",
            "Confirm the replay artifact preserves source identity, freshness, and limitations.",
            "Confirm the successful source is relevant to the paper hypothesis before approving any separate paper update.",
            "Confirm failed requests are handled through a later URL/source correction task before another controlled fetch.",
            "Confirm outcome resolution remains separate from source accessibility review.",
        ],
        "no_real_trade_decision": True,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "automatic_analysis_update_performed": False,
        "no_live_fetch_performed_in_this_task": True,
        "safety_summary": safe_summary(),
    }
    if int(execution_summary.get("evidence_packets_created_count") or 0) > 0 and not evidence_packets:
        review["review_status"] = "blocked_evidence_packet_count_mismatch"
        review["limitations"].append("PRACTICAL-008 reported evidence packets, but no saved packet was loaded.")
    else:
        review["review_status"] = "operator_review_candidate_created"
    return review


def write_public_evidence_operator_review(
    *,
    execution_summary_path: str | Path,
    evidence_packet_paths: Sequence[str | Path],
    replay_artifact_paths: Sequence[str | Path],
    out_json_path: str | Path,
    out_md_path: str | Path,
    review_id: str = "public-evidence-review-009",
) -> dict[str, Any]:
    summary = load_json_object(execution_summary_path, label="PRACTICAL-008 execution summary")
    evidence_packets = [load_json_object(path, label="saved evidence packet") for path in evidence_packet_paths]
    replay_artifacts = [load_json_object(path, label="replay artifact") for path in replay_artifact_paths]
    review = build_public_evidence_operator_review(
        execution_summary=summary,
        evidence_packets=evidence_packets,
        replay_artifacts=replay_artifacts,
        replay_artifact_paths=[str(path).replace("\\", "/") for path in replay_artifact_paths],
        review_id=review_id,
    )
    write_json(out_json_path, review)
    write_text(out_md_path, render_public_evidence_operator_review_markdown(review))
    return review


def render_public_evidence_operator_review_markdown(review: Mapping[str, Any]) -> str:
    lines = [
        "# Public evidence review",
        "",
        f"- Review ID: `{review.get('review_id')}`",
        f"- Source task: `{review.get('source_task_id')}`",
        f"- Evidence packets reviewed: {review.get('evidence_packet_count')}",
        f"- Review status: `{review.get('review_status')}`",
        "",
        "## Evidence packet summary",
        "",
    ]
    for packet in review.get("evidence_packets_reviewed", []):
        lines.extend(
            [
                f"- `{packet.get('evidence_packet_id')}`",
                f"  Source: `{packet.get('source_name')}`",
                f"  Reference: `{packet.get('source_reference')}`",
                f"  HTTP status: `{packet.get('http_status')}`",
                f"  Freshness: `{packet.get('freshness_status')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Affected markets/hypotheses",
            "",
            *bullet_lines(f"Market `{market_id}`" for market_id in review.get("affected_market_ids", [])),
            *bullet_lines(f"Hypothesis `{hypothesis_id}`" for hypothesis_id in review.get("affected_hypothesis_ids", [])),
            "",
            "## What the evidence says",
            "",
            *bullet_lines(review.get("normalized_evidence_summary", [])),
            "",
            "## Relevance to paper hypothesis",
            "",
            f"- `{review.get('evidence_relevance')}`",
            "",
            "## Contradictions/staleness",
            "",
            *bullet_lines(review.get("contradiction_notes", [])),
            *bullet_lines(review.get("staleness_notes", [])),
            "",
            "## Limitations",
            "",
            *bullet_lines(review.get("limitations", [])),
            "",
            "## Operator checklist",
            "",
            *bullet_lines(review.get("operator_review_checklist", [])),
            "",
            "## Safety boundary",
            "",
            "- Local saved evidence replay only in PRACTICAL-009.",
            "- No live source request, OpenRouter call, authenticated endpoint, wallet path, order path, runtime path, scheduler, or autonomous execution was used.",
            "- No real trade decision or executable market output was generated.",
            "- No prior market analysis was automatically changed.",
        ]
    )
    return "\n".join(lines) + "\n"


def _reviewed_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "evidence_packet_id": clean_text(packet.get("evidence_packet_id")),
        "source_id": clean_text(packet.get("source_id")),
        "source_name": clean_text(packet.get("source_name")),
        "source_category": clean_text(packet.get("source_category")),
        "source_reference": clean_text(packet.get("source_reference")),
        "market_ids": list(packet.get("market_ids", [])),
        "hypothesis_ids": list(packet.get("hypothesis_ids", [])),
        "captured_at": clean_text(packet.get("captured_at")),
        "http_status": packet.get("http_status"),
        "content_type": clean_text(packet.get("content_type")),
        "body_sha256": clean_text(packet.get("body_sha256")),
        "freshness_status": clean_text(packet.get("freshness_status")),
        "normalized_claims": list(packet.get("normalized_claims", [])),
        "limitations": list(packet.get("limitations", [])),
        "safe_for_replay": packet.get("safe_for_replay") is True,
    }


def _reviewed_replay_artifact(path: str, artifact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "path": path,
        "contract_version": clean_text(artifact.get("contract_version")),
        "replay_status": clean_text(artifact.get("replay_status")),
        "replay_performed": artifact.get("replay_performed") is True,
        "source_packet_count": len(artifact.get("source_packets", [])),
        "live_network_used": False,
    }


def _normalized_evidence_summary(
    evidence_packets: Sequence[Mapping[str, Any]],
    execution_summary: Mapping[str, Any],
) -> list[str]:
    if not evidence_packets:
        return ["No saved public evidence packet was available for review."]
    summary = []
    for packet in evidence_packets:
        source = clean_text(packet.get("source_name")) or clean_text(packet.get("source_id"))
        reference = clean_text(packet.get("source_reference"))
        status = packet.get("http_status")
        summary.append(f"{source} returned HTTP {status} for `{reference}` and was saved as replay-safe metadata.")
        summary.extend(clean_text(claim) for claim in packet.get("normalized_claims", []) if clean_text(claim))
    failed_count = int(execution_summary.get("request_count_failed") or 0)
    if failed_count:
        summary.append(f"{failed_count} approved PRACTICAL-008 source requests did not produce saved evidence packets.")
    summary.append("The saved evidence supports source-accessibility tracking, not outcome resolution.")
    return summary


def _evidence_relevance(evidence_packets: Sequence[Mapping[str, Any]]) -> str:
    if not evidence_packets:
        return "insufficient"
    if any(packet.get("contradiction_candidates") for packet in evidence_packets):
        return "contradicts_tracking_assumption"
    return "supports_tracking_assumption"


def _contradiction_notes(evidence_packets: Sequence[Mapping[str, Any]]) -> list[str]:
    notes = []
    for packet in evidence_packets:
        for item in packet.get("contradiction_candidates", []):
            notes.append(f"{packet.get('evidence_packet_id')}: {item}")
    return notes or ["No contradiction candidates were present in the saved evidence packet metadata."]


def _staleness_notes(evidence_packets: Sequence[Mapping[str, Any]]) -> list[str]:
    if not evidence_packets:
        return ["No evidence freshness could be reviewed."]
    return [
        f"{packet.get('evidence_packet_id')}: freshness `{packet.get('freshness_status')}` captured at `{packet.get('captured_at')}`."
        for packet in evidence_packets
    ]


def _review_limitations(evidence_packets: Sequence[Mapping[str, Any]]) -> list[str]:
    limitations = sorted(
        {
            clean_text(item)
            for packet in evidence_packets
            for item in packet.get("limitations", [])
            if clean_text(item)
        }
    )
    limitations.extend(
        [
            "The original response body is not embedded in the review artifact.",
            "The review does not resolve the market outcome.",
            "The successful source still needs operator review for exact market relevance.",
            "Failed PRACTICAL-008 requests require URL/source handling before a later controlled fetch.",
        ]
    )
    return limitations


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a PMBOT public evidence operator review from saved artifacts.")
    parser.add_argument("--execution-summary", required=True)
    parser.add_argument("--evidence-packet", action="append", default=[])
    parser.add_argument("--replay-artifact", action="append", default=[])
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    write_public_evidence_operator_review(
        execution_summary_path=args.execution_summary,
        evidence_packet_paths=args.evidence_packet,
        replay_artifact_paths=args.replay_artifact,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
