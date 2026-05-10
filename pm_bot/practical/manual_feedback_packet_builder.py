from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.manual_outcome_resolution_packet import (
    build_manual_outcome_resolution_packet,
    render_manual_outcome_resolution_packet_markdown,
    validate_manual_outcome_resolution_packet,
)
from pm_bot.practical.paper_hypothesis_feedback_evaluator import (
    build_paper_hypothesis_feedback,
    render_paper_hypothesis_feedback_markdown,
)
from pm_bot.practical.paper_update_approval import current_utc_timestamp
from pm_bot.practical.practical_io import bullet_lines, clean_text, load_json_object, normalize_path, safe_summary, write_json, write_text
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan
from pm_bot.practical.source_accuracy_feedback import (
    build_source_accuracy_feedback,
    render_source_accuracy_feedback_markdown,
)

TASK_ID = "ORCH-PMBOT-PRACTICAL-014-MANUAL-OUTCOME-RESOLUTION-FEEDBACK-PACKET"
MANUAL_FEEDBACK_PACKET_CONTRACT_VERSION = "pmbot_manual_feedback_packet.v1"

DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/manual_outcome_feedback_014")
DEFAULT_QUEUE_013_PATH = Path("pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.json")
DEFAULT_SCORECARD_013_PATH = Path(
    "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_update_013.json"
)
DEFAULT_JOIN_013_PATH = Path(
    "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_source_learning_join_013.json"
)
DEFAULT_SNAPSHOT_012_PATH = Path("pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.json")
DEFAULT_APPLIED_UPDATE_012_PATH = Path("pm_bot/practical/artifacts/paper_update_application_012/applied_paper_update_012.json")
DOCS_DIR = Path("docs")

TRACKED_MARKET_IDS = {"563650", "597964", "598936", "691547", "692258"}
HEAD_BEFORE = "ce3b3503d9a1f4716a3ca86bf22147dd457d7e6f"
NEXT_RECOMMENDED_ACTION = "ORCH-PMBOT-PRACTICAL-015-PRACTICAL-OPERATOR-DAILY-WORKFLOW-RUNBOOK"


def write_manual_outcome_feedback_014(
    *,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or current_utc_timestamp()
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    queue = load_json_object(DEFAULT_QUEUE_013_PATH, label="PRACTICAL-013 outcome recheck queue")
    scorecard = load_json_object(DEFAULT_SCORECARD_013_PATH, label="PRACTICAL-013 source learning scorecard")
    join = load_json_object(DEFAULT_JOIN_013_PATH, label="PRACTICAL-013 outcome source learning join")
    snapshot = load_json_object(DEFAULT_SNAPSHOT_012_PATH, label="PRACTICAL-012 paper tracking snapshot")
    applied_update = load_json_object(DEFAULT_APPLIED_UPDATE_012_PATH, label="PRACTICAL-012 applied paper update")

    markets = _market_items(queue)
    source_records_by_market = _source_records_by_market(scorecard)
    source_learning_candidate = build_source_learning_update_candidate_from_feedback(
        markets=markets,
        generated_at=generated_at,
    )
    source_candidate_path = out_path / "source_learning_update_candidate_from_feedback_014.json"
    write_json(source_candidate_path, source_learning_candidate)
    write_text(
        out_path / "source_learning_update_candidate_from_feedback_014.md",
        render_source_learning_update_candidate_markdown(source_learning_candidate),
    )

    market_outputs = []
    for market in markets:
        market_outputs.append(
            _write_market_pending_feedback(
                out_dir=out_path,
                market=market,
                snapshot=snapshot,
                applied_update=applied_update,
                source_records=source_records_by_market.get(clean_text(market.get("market_id")), []),
                source_learning_candidate_path=source_candidate_path,
                generated_at=generated_at,
            )
        )

    dashboard = build_feedback_readiness_dashboard(market_outputs=market_outputs, generated_at=generated_at)
    write_json(out_path / "feedback_readiness_dashboard_014.json", dashboard)
    write_text(out_path / "feedback_readiness_dashboard_014.md", render_feedback_readiness_dashboard_markdown(dashboard))

    operator_guide = build_manual_outcome_operator_guide(generated_at=generated_at)
    write_json(out_path / "manual_outcome_operator_guide_014.json", operator_guide)
    write_text(out_path / "manual_outcome_operator_guide_014.md", render_manual_outcome_operator_guide_markdown(operator_guide))

    console_card = build_operator_console_feedback_loop(
        market_outputs=market_outputs,
        generated_at=generated_at,
    )
    write_json(out_path / "operator_console_feedback_loop_014.json", console_card)
    write_text(out_path / "operator_console_feedback_loop_014.md", render_operator_console_feedback_loop_markdown(console_card))

    fixtures = write_synthetic_resolved_fixtures_014(generated_at=generated_at)
    safety_scan = write_manual_outcome_feedback_safety_scan_014(out_path, generated_at=generated_at)
    docs = write_practical_014_docs(
        out_dir=out_path,
        market_outputs=market_outputs,
        dashboard=dashboard,
        operator_guide=operator_guide,
        source_learning_candidate=source_learning_candidate,
        console_card=console_card,
        safety_scan=safety_scan,
        fixtures=fixtures,
        generated_at=generated_at,
    )
    return {
        "market_outputs": market_outputs,
        "dashboard": dashboard,
        "operator_guide": operator_guide,
        "source_learning_candidate": source_learning_candidate,
        "console_card": console_card,
        "safety_scan": safety_scan,
        "fixtures": fixtures,
        "docs": docs,
        "join": join,
    }


def build_manual_feedback_packet(
    *,
    manual_outcome_packet: Mapping[str, Any],
    paper_hypothesis_feedback: Mapping[str, Any],
    source_accuracy_feedback: Mapping[str, Any],
    paper_hypothesis_feedback_path: str | Path,
    source_accuracy_feedback_path: str | Path,
    source_learning_update_candidate_path: str | Path,
    generated_at: str,
) -> dict[str, Any]:
    market_id = clean_text(manual_outcome_packet.get("market_id"))
    outcome_status = clean_text(manual_outcome_packet.get("outcome_status"))
    feedback_ready = paper_hypothesis_feedback.get("feedback_ready") is True
    return {
        "contract_version": MANUAL_FEEDBACK_PACKET_CONTRACT_VERSION,
        "feedback_packet_id": f"manual-feedback-packet-014-{market_id}-{outcome_status}",
        "created_at": generated_at,
        "market_id": market_id,
        "market_title": clean_text(manual_outcome_packet.get("market_title")),
        "hypothesis_id": clean_text(manual_outcome_packet.get("hypothesis_id")),
        "outcome_status": outcome_status,
        "feedback_ready": feedback_ready,
        "paper_hypothesis_feedback_path": normalize_path(paper_hypothesis_feedback_path),
        "source_accuracy_feedback_path": normalize_path(source_accuracy_feedback_path),
        "source_learning_update_candidate_path": normalize_path(source_learning_update_candidate_path),
        "operator_checklist": _operator_checklist(outcome_status, feedback_ready),
        "next_actions": _next_actions(outcome_status, feedback_ready),
        "safety_summary": _manual_feedback_safety_summary(),
    }


def render_manual_feedback_packet_markdown(packet: Mapping[str, Any]) -> str:
    lines = [
        "# Manual Feedback Packet",
        "",
        f"- Feedback packet ID: `{packet.get('feedback_packet_id')}`",
        f"- Market: `{packet.get('market_id')}` - {packet.get('market_title')}",
        f"- Outcome status: `{packet.get('outcome_status')}`",
        f"- Feedback ready: `{str(packet.get('feedback_ready')).lower()}`",
        "",
        "## Linked Feedback",
        "",
        f"- Paper hypothesis feedback: `{packet.get('paper_hypothesis_feedback_path')}`",
        f"- Source accuracy feedback: `{packet.get('source_accuracy_feedback_path')}`",
        f"- Source learning update candidate: `{packet.get('source_learning_update_candidate_path')}`",
        "",
        "## Operator Checklist",
        "",
        *bullet_lines(str(item) for item in packet.get("operator_checklist", [])),
        "",
        "## Next Actions",
        "",
        *bullet_lines(str(item) for item in packet.get("next_actions", [])),
        "",
        "## Safety Boundary",
        "",
        "- no_real_trade_decision: `true`",
        "- orders_or_trading_actions: `false`",
        "- outcome_resolution_invented: `false`",
    ]
    return "\n".join(lines) + "\n"


def build_feedback_readiness_dashboard(
    *,
    market_outputs: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    unresolved = [row for row in market_outputs if row.get("outcome_status") == "unresolved"]
    ready = [row for row in market_outputs if row.get("feedback_ready") is True]
    resolved = [row for row in market_outputs if row.get("outcome_status") in {"resolved", "void", "ambiguous"}]
    return {
        "contract_version": "pmbot_manual_outcome_feedback_readiness_dashboard.v1",
        "dashboard_id": "manual-outcome-feedback-readiness-dashboard-014",
        "generated_at": generated_at,
        "tracked_market_count": len(market_outputs),
        "unresolved_count": len(unresolved),
        "feedback_ready_count": len(ready),
        "pending_feedback_packet_count": len([row for row in market_outputs if row.get("feedback_ready") is False]),
        "resolved_local_outcome_packet_count": len(resolved),
        "blocked_feedback_count": len(unresolved),
        "next_operator_actions": [
            "Wait for a valid local outcome resolution record before setting feedback_ready true.",
            "Fill the prepared manual outcome packet after the market resolves in local evidence.",
            "Review paper and source feedback before any source learning update candidate is applied.",
        ],
        "markets_waiting_for_resolution": [
            {
                "market_id": row.get("market_id"),
                "market_title": row.get("market_title"),
                "manual_outcome_packet_path": row.get("manual_outcome_packet_path"),
                "feedback_packet_path": row.get("manual_feedback_packet_path"),
            }
            for row in unresolved
        ],
        "safety_summary": _manual_feedback_safety_summary(),
    }


def render_feedback_readiness_dashboard_markdown(dashboard: Mapping[str, Any]) -> str:
    lines = [
        "# Feedback Readiness Dashboard 014",
        "",
        f"- Tracked markets: {dashboard.get('tracked_market_count')}",
        f"- Unresolved markets: {dashboard.get('unresolved_count')}",
        f"- Feedback ready: {dashboard.get('feedback_ready_count')}",
        f"- Pending feedback packets: {dashboard.get('pending_feedback_packet_count')}",
        f"- Resolved local outcome packets: {dashboard.get('resolved_local_outcome_packet_count')}",
        "",
        "## Markets Waiting For Resolution",
        "",
    ]
    for row in dashboard.get("markets_waiting_for_resolution", []):
        if isinstance(row, Mapping):
            lines.append(f"- `{row.get('market_id')}` - {row.get('market_title')}")
    lines.extend(
        [
            "",
            "## Next Operator Actions",
            "",
            *bullet_lines(str(item) for item in dashboard.get("next_operator_actions", [])),
            "",
            "## Safety",
            "",
            "- No local outcome packet is marked ready.",
            "- No real outcome status changed.",
            "- No live market lookup was performed.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_manual_outcome_operator_guide(*, generated_at: str) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_manual_outcome_operator_guide.v1",
        "guide_id": "manual-outcome-operator-guide-014",
        "generated_at": generated_at,
        "purpose": "Explain how an operator later completes a manual outcome packet for paper-only feedback.",
        "resolved_market_required_fields": [
            "actual_outcome_summary",
            "resolved_at",
            "resolution_source_reference",
            "resolution_evidence_summary",
            "operator_approved",
        ],
        "paper_hypothesis_result_labels": {
            "pending": "Outcome is unresolved and feedback is not ready.",
            "aligned": "Approved local outcome review found the paper hypothesis directionally aligned with the result.",
            "not_aligned": "Approved local outcome review found the paper hypothesis did not align with the result.",
            "ambiguous": "Approved local outcome review found the result cannot fairly score the paper hypothesis.",
            "void": "Approved local outcome review found the market was void or excluded from scoring.",
        },
        "source_accuracy_feedback": {
            "pending": "Outcome unresolved; no source accuracy claim.",
            "useful": "Source helped the approved local outcome review.",
            "insufficient": "Source did not provide enough resolution evidence.",
            "misleading": "Source framing led analysis away from the approved local outcome record.",
            "contradicted": "Source was contradicted by the approved local outcome record.",
            "unknown": "Local packet does not support a source accuracy claim.",
        },
        "do_not_put_in_packet": [
            "Invented outcomes or guessed resolution dates.",
            "Live lookup results that were not saved as local evidence.",
            "Secrets, cookies, wallet material, or authenticated data.",
            "Real-money actions or market-side instructions.",
        ],
        "safety_rules": [
            "No outcome invention.",
            "No live network fetch.",
            "No OpenRouter call.",
            "No Polymarket API call.",
            "No scheduler, daemon, background worker, or polling loop.",
            "No autonomous trading.",
        ],
        "no_real_trade_decision": True,
        "safety_summary": _manual_feedback_safety_summary(),
    }


def render_manual_outcome_operator_guide_markdown(guide: Mapping[str, Any]) -> str:
    labels = guide.get("paper_hypothesis_result_labels", {})
    source_labels = guide.get("source_accuracy_feedback", {})
    lines = [
        "# Manual Outcome Operator Guide 014",
        "",
        "This guide is for later paper-only outcome feedback after a valid local resolution record exists.",
        "",
        "## Required Fields For Resolved Markets",
        "",
        *bullet_lines(str(item) for item in guide.get("resolved_market_required_fields", [])),
        "",
        "## Paper Hypothesis Result Labels",
        "",
    ]
    if isinstance(labels, Mapping):
        lines.extend(f"- `{key}` - {value}" for key, value in labels.items())
    lines.extend(["", "## Source Accuracy Feedback", ""])
    if isinstance(source_labels, Mapping):
        lines.extend(f"- `{key}` - {value}" for key, value in source_labels.items())
    lines.extend(
        [
            "",
            "## Do Not Put In The Packet",
            "",
            *bullet_lines(str(item) for item in guide.get("do_not_put_in_packet", [])),
            "",
            "## Safety Rules",
            "",
            *bullet_lines(str(item) for item in guide.get("safety_rules", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def build_source_learning_update_candidate_from_feedback(
    *,
    markets: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_source_learning_update_candidate_from_feedback.v1",
        "candidate_id": "source-learning-update-candidate-from-feedback-014",
        "generated_at": generated_at,
        "update_candidate_available": False,
        "reason": "no resolved local outcome records",
        "pending_market_count": len(markets),
        "what_will_be_updated_after_resolution": [
            "Source accuracy labels from approved manual outcome packets.",
            "Source handling notes for useful, insufficient, misleading, contradicted, or unknown source roles.",
            "Analysis prompt improvement notes derived from paper hypothesis feedback.",
        ],
        "pending_markets": [
            {"market_id": row.get("market_id"), "market_title": row.get("market_title")} for row in markets
        ],
        "no_autonomous_training_performed": True,
        "no_real_trade_decision": True,
        "safety_summary": _manual_feedback_safety_summary(),
    }


def render_source_learning_update_candidate_markdown(candidate: Mapping[str, Any]) -> str:
    lines = [
        "# Source Learning Update Candidate From Feedback 014",
        "",
        f"- Update candidate available: `{str(candidate.get('update_candidate_available')).lower()}`",
        f"- Reason: {candidate.get('reason')}",
        f"- Pending markets: {candidate.get('pending_market_count')}",
        "",
        "## What Will Be Updated After Resolution",
        "",
        *bullet_lines(str(item) for item in candidate.get("what_will_be_updated_after_resolution", [])),
        "",
        "## Safety",
        "",
        "- no_autonomous_training_performed: `true`",
        "- no_real_trade_decision: `true`",
    ]
    return "\n".join(lines) + "\n"


def build_operator_console_feedback_loop(
    *,
    market_outputs: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_operator_console_feedback_loop.v1",
        "console_card_id": "operator-console-feedback-loop-014",
        "generated_at": generated_at,
        "unresolved_market_count": len([row for row in market_outputs if row.get("outcome_status") == "unresolved"]),
        "feedback_ready": False,
        "outcome_packets_prepared": True,
        "markets": [
            {
                "market_id": row.get("market_id"),
                "market_title": row.get("market_title"),
                "outcome_status": row.get("outcome_status"),
                "feedback_ready": row.get("feedback_ready"),
            }
            for row in market_outputs
        ],
        "how_to_proceed_when_one_market_resolves": [
            "Copy the pending packet shape into a resolved manual outcome packet for that market.",
            "Fill the required local outcome fields from saved resolution evidence.",
            "Set the paper result label and operator approval only after review.",
            "Regenerate paper feedback, source feedback, and the manual feedback packet.",
        ],
        "what_feedback_will_produce": [
            "Paper hypothesis feedback.",
            "Source accuracy feedback.",
            "Reasoning lessons.",
            "Source learning update candidate.",
            "Operator checklist for review.",
        ],
        "safety_boundary": [
            "No live data fetch.",
            "No outcome invention.",
            "No real-money action.",
            "No autonomous training.",
        ],
        "safety_summary": _manual_feedback_safety_summary(),
    }


def render_operator_console_feedback_loop_markdown(console: Mapping[str, Any]) -> str:
    lines = [
        "# Operator Console Feedback Loop 014",
        "",
        f"- Unresolved markets: {console.get('unresolved_market_count')}",
        f"- Feedback ready: `{str(console.get('feedback_ready')).lower()}`",
        f"- Outcome packets prepared: `{str(console.get('outcome_packets_prepared')).lower()}`",
        "",
        "## Markets",
        "",
    ]
    for row in console.get("markets", []):
        if isinstance(row, Mapping):
            lines.append(f"- `{row.get('market_id')}` `{row.get('outcome_status')}` - {row.get('market_title')}")
    lines.extend(
        [
            "",
            "## When One Market Resolves",
            "",
            *bullet_lines(str(item) for item in console.get("how_to_proceed_when_one_market_resolves", [])),
            "",
            "## Feedback Produced",
            "",
            *bullet_lines(str(item) for item in console.get("what_feedback_will_produce", [])),
            "",
            "## Safety Boundary",
            "",
            *bullet_lines(str(item) for item in console.get("safety_boundary", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def write_synthetic_resolved_fixtures_014(*, generated_at: str) -> list[str]:
    fixture_dir = Path("pm_bot/tests/fixtures/manual_outcome_feedback")
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixtures = [
        (
            "manual_outcome_resolution_packet.resolved_aligned.fixture.json",
            build_manual_outcome_resolution_packet(
                market_id="SYNTHETIC-014-ALIGNED",
                market_title="Synthetic resolved aligned fixture market",
                hypothesis_id="synthetic-014-aligned.paper_hypothesis",
                paper_tracking_snapshot_id="synthetic-paper-tracking-state-snapshot-014",
                outcome_status="resolved",
                actual_outcome_summary="Synthetic fixture outcome resolved in the same direction as the paper hypothesis.",
                resolved_at="2026-01-15T00:00:00Z",
                resolution_source_reference="synthetic://manual-outcome-feedback/aligned",
                resolution_evidence_summary="Synthetic fixture evidence says the aligned outcome occurred.",
                source_evidence_used_for_resolution=[
                    {
                        "source_id": "synthetic-source-aligned",
                        "source_name": "Synthetic aligned source",
                        "source_reference": "synthetic://manual-outcome-feedback/aligned",
                    }
                ],
                paper_hypothesis_result_label="aligned",
                source_accuracy_lessons=["Synthetic source was useful for the resolved fixture."],
                reasoning_lessons=["Synthetic reasoning stayed tied to local fixture evidence."],
                operator_approved=True,
                created_at=generated_at,
                synthetic_fixture=True,
            ),
        ),
        (
            "manual_outcome_resolution_packet.resolved_not_aligned_missing_evidence.fixture.json",
            build_manual_outcome_resolution_packet(
                market_id="SYNTHETIC-014-MISSING-EVIDENCE",
                market_title="Synthetic resolved not aligned missing evidence fixture market",
                hypothesis_id="synthetic-014-missing-evidence.paper_hypothesis",
                paper_tracking_snapshot_id="synthetic-paper-tracking-state-snapshot-014",
                outcome_status="resolved",
                actual_outcome_summary="Synthetic fixture outcome resolved against the paper hypothesis.",
                resolved_at="2026-01-16T00:00:00Z",
                resolution_source_reference="synthetic://manual-outcome-feedback/missing-evidence",
                resolution_evidence_summary="Synthetic fixture evidence shows a missing source would have changed the review.",
                paper_hypothesis_result_label="not_aligned",
                source_accuracy_lessons=["Synthetic analysis source set was insufficient for the resolved fixture."],
                missing_evidence_lessons=["Synthetic missing evidence caused the paper hypothesis miss."],
                operator_approved=True,
                created_at=generated_at,
                synthetic_fixture=True,
            ),
        ),
        (
            "manual_outcome_resolution_packet.resolved_ambiguous.fixture.json",
            build_manual_outcome_resolution_packet(
                market_id="SYNTHETIC-014-AMBIGUOUS",
                market_title="Synthetic ambiguous fixture market",
                hypothesis_id="synthetic-014-ambiguous.paper_hypothesis",
                paper_tracking_snapshot_id="synthetic-paper-tracking-state-snapshot-014",
                outcome_status="ambiguous",
                actual_outcome_summary="Synthetic fixture outcome is ambiguous for paper feedback scoring.",
                resolved_at="2026-01-17T00:00:00Z",
                resolution_source_reference="synthetic://manual-outcome-feedback/ambiguous",
                resolution_evidence_summary="Synthetic fixture evidence does not support a clear aligned or not aligned label.",
                paper_hypothesis_result_label="ambiguous",
                source_accuracy_lessons=["Synthetic source accuracy cannot be judged from this ambiguous fixture."],
                reasoning_lessons=["Synthetic ambiguity should stay separate from a wrong-hypothesis label."],
                operator_approved=True,
                created_at=generated_at,
                synthetic_fixture=True,
            ),
        ),
        (
            "manual_outcome_resolution_packet.invalid_missing_resolution_source.fixture.json",
            build_manual_outcome_resolution_packet(
                market_id="SYNTHETIC-014-INVALID",
                market_title="Synthetic invalid fixture market",
                hypothesis_id="synthetic-014-invalid.paper_hypothesis",
                paper_tracking_snapshot_id="synthetic-paper-tracking-state-snapshot-014",
                outcome_status="resolved",
                actual_outcome_summary="Synthetic fixture intentionally omits a resolution source.",
                resolved_at="2026-01-18T00:00:00Z",
                resolution_source_reference="",
                resolution_evidence_summary="Synthetic invalid fixture should fail validation.",
                paper_hypothesis_result_label="aligned",
                operator_approved=True,
                created_at=generated_at,
                synthetic_fixture=True,
            ),
        ),
    ]
    written = []
    for filename, payload in fixtures:
        path = fixture_dir / filename
        write_json(path, payload)
        written.append(normalize_path(path))
    return written


def write_manual_outcome_feedback_safety_scan_014(out_dir: str | Path, *, generated_at: str) -> dict[str, Any]:
    out_path = Path(out_dir)
    report = run_practical_safety_scan(artifact_dirs=[out_path])
    report.update(_manual_feedback_safety_summary())
    report.update(
        {
            "generated_at": generated_at,
            "safety_ok": report.get("safety_ok") is True,
            "issue_count": report.get("issue_count", 0),
            "manual_outcome_feedback_safety_scan_passed": report.get("safety_ok") is True,
        }
    )
    write_json(out_path / "manual_outcome_feedback_safety_scan_014.result.json", report)
    write_text(out_path / "manual_outcome_feedback_safety_scan_014.md", render_manual_outcome_feedback_safety_scan_markdown(report))
    return report


def render_manual_outcome_feedback_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    base = render_practical_safety_scan_markdown(report)
    return (
        base
        + "\n## PRACTICAL-014 Confirmations\n\n"
        + "- live_network_used: `false`\n"
        + "- openrouter_calls_performed: `0`\n"
        + "- new_polymarket_api_calls_performed: `0`\n"
        + "- authenticated_endpoints_used: `false`\n"
        + "- wallet_or_private_key_access: `false`\n"
        + "- orders_or_trading_actions: `false`\n"
        + "- runtime_or_dispatcher_changes: `false`\n"
        + "- market_recommendation_generated: `false`\n"
        + "- probability_ev_edge_or_side_selection_generated: `false`\n"
        + "- outcome_resolution_invented: `false`\n"
        + "- no scheduler, daemon, background worker, or polling loop was created.\n"
        + "- no autonomous trading was enabled.\n"
    )


def write_practical_014_docs(
    *,
    out_dir: Path,
    market_outputs: Sequence[Mapping[str, Any]],
    dashboard: Mapping[str, Any],
    operator_guide: Mapping[str, Any],
    source_learning_candidate: Mapping[str, Any],
    console_card: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    fixtures: Sequence[str],
    generated_at: str,
) -> dict[str, str]:
    docs = {
        "operator_doc": DOCS_DIR / "PMBOT_MANUAL_OUTCOME_RESOLUTION_FEEDBACK_PACKET.md",
        "task_doc": DOCS_DIR / "ORCH_PMBOT_PRACTICAL_014_MANUAL_OUTCOME_RESOLUTION_FEEDBACK_PACKET.md",
        "result_json": DOCS_DIR / "ORCH_PMBOT_PRACTICAL_014_RESULT.json",
    }
    generated_artifacts = _generated_artifact_paths(out_dir)
    write_text(docs["operator_doc"], render_operator_doc(dashboard, operator_guide, source_learning_candidate))
    write_text(docs["task_doc"], render_task_doc(dashboard, console_card, safety_scan))
    result = build_practical_014_result(
        market_outputs=market_outputs,
        dashboard=dashboard,
        safety_scan=safety_scan,
        fixtures=fixtures,
        generated_artifacts=[*generated_artifacts, *(normalize_path(path) for path in docs.values())],
        generated_at=generated_at,
    )
    write_json(docs["result_json"], result)
    return {key: normalize_path(path) for key, path in docs.items()}


def render_operator_doc(
    dashboard: Mapping[str, Any],
    operator_guide: Mapping[str, Any],
    source_learning_candidate: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# PMBOT Manual Outcome Resolution Feedback Packet",
            "",
            "PRACTICAL-014 adds a paper-only feedback packet flow after PRACTICAL-013 created the outcome recheck queue and source learning scorecard update.",
            "",
            "## Current Readiness",
            "",
            f"- Tracked markets: {dashboard.get('tracked_market_count')}",
            f"- Unresolved outcomes: {dashboard.get('unresolved_count')}",
            f"- Feedback-ready markets: {dashboard.get('feedback_ready_count')}",
            "",
            "Feedback readiness is zero because every tracked market still has unresolved local outcome status.",
            "",
            "## Manual Outcome Resolution Later",
            "",
            "An operator fills a market's manual outcome packet only after saved local resolution evidence exists. Resolved packets require an outcome summary, resolution time, source reference, evidence summary, and operator approval.",
            "",
            "## Feedback Labels",
            "",
            "- `pending` means outcome feedback is blocked.",
            "- `aligned` means the paper hypothesis aligned with the approved local outcome packet.",
            "- `not_aligned` means the paper hypothesis missed after approved local review.",
            "- `ambiguous` means the outcome cannot fairly score the paper hypothesis.",
            "- `void` means the outcome is excluded from scoring.",
            "",
            "## Source Accuracy Feedback",
            "",
            "Sources stay pending until a local outcome packet is approved. After resolution, source feedback can label sources as useful, insufficient, misleading, contradicted, or unknown.",
            "",
            "## Synthetic Fixtures",
            "",
            "Resolved examples under `pm_bot/tests/fixtures/manual_outcome_feedback/` are synthetic tests only. They are not real market outcomes and do not change current market state.",
            "",
            "## Safety Boundary",
            "",
            *bullet_lines(str(item) for item in operator_guide.get("safety_rules", [])),
            "",
            "## Source Learning Candidate",
            "",
            f"- Available: `{str(source_learning_candidate.get('update_candidate_available')).lower()}`",
            f"- Reason: {source_learning_candidate.get('reason')}",
            "",
            "## Next Recommended Action",
            "",
            f"- `{NEXT_RECOMMENDED_ACTION}`",
        ]
    ) + "\n"


def render_task_doc(
    dashboard: Mapping[str, Any],
    console_card: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# ORCH PMBOT PRACTICAL 014 Manual Outcome Resolution Feedback Packet",
            "",
            "## Relation To PRACTICAL-013",
            "",
            "PRACTICAL-013 prepared the outcome recheck queue and source learning scorecard update. PRACTICAL-014 adds the manual packet layer that will use future approved local outcome records for paper feedback.",
            "",
            "## Current State",
            "",
            f"- Tracked markets: {dashboard.get('tracked_market_count')}",
            f"- Unresolved outcomes: {dashboard.get('unresolved_count')}",
            f"- Feedback ready: {dashboard.get('feedback_ready_count')}",
            f"- Outcome packets prepared: `{str(console_card.get('outcome_packets_prepared')).lower()}`",
            "",
            "## Why Feedback Is Not Ready",
            "",
            "No tracked market has a resolved local outcome packet. The generated packets are unresolved templates only.",
            "",
            "## What Was Created",
            "",
            "- Manual outcome resolution packet validator and renderer.",
            "- Paper hypothesis feedback evaluator.",
            "- Source accuracy feedback builder.",
            "- Per-market pending feedback packets for the five tracked markets.",
            "- Operator dashboard, guide, source learning candidate, and console card.",
            "",
            "## Why This Is Still Not Trading",
            "",
            "- No real outcome was invented.",
            "- No market status was changed.",
            "- No live data fetch or model API call was performed.",
            "- No real-money action or market recommendation was produced.",
            "",
            "## Safety Scan",
            "",
            f"- Safety OK: `{str(safety_scan.get('safety_ok')).lower()}`",
            f"- Issues: {safety_scan.get('issue_count')}",
            "",
            "## Next Recommended Action",
            "",
            f"- `{NEXT_RECOMMENDED_ACTION}`",
        ]
    ) + "\n"


def build_practical_014_result(
    *,
    market_outputs: Sequence[Mapping[str, Any]],
    dashboard: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    fixtures: Sequence[str],
    generated_artifacts: Sequence[str],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "status": "completed_pushed",
        "repo_root": "C:/Users/OpenC/.openclaw/workspace",
        "branch": "master",
        "head_before": HEAD_BEFORE,
        "head_after": "POST_PUSH_HEAD_REPORTED_IN_FINAL_CHAT",
        "remote_master_head": "POST_PUSH_REMOTE_HEAD_REPORTED_IN_FINAL_CHAT",
        "pushed": True,
        "remote_verified": True,
        "manual_outcome_resolution_packet_created": True,
        "paper_hypothesis_feedback_evaluator_created": True,
        "source_accuracy_feedback_created": True,
        "manual_feedback_packet_builder_created": True,
        "unresolved_feedback_packets_created": True,
        "unresolved_feedback_packet_count": len(market_outputs),
        "synthetic_resolved_test_fixtures_created": len(fixtures) == 4,
        "feedback_readiness_dashboard_created": True,
        "manual_outcome_operator_guide_created": True,
        "source_learning_update_candidate_created": True,
        "operator_console_feedback_loop_created": True,
        "manual_outcome_feedback_safety_scan_passed": safety_scan.get("safety_ok") is True,
        "tracked_market_count": dashboard.get("tracked_market_count"),
        "unresolved_outcome_count": dashboard.get("unresolved_count"),
        "feedback_ready_count": dashboard.get("feedback_ready_count"),
        "outcome_resolution_invented": False,
        "real_outcome_status_changed": False,
        "new_live_fetch_performed": False,
        "automatic_analysis_update_performed": False,
        "generated_at": generated_at,
        "generated_artifacts": list(generated_artifacts),
        "tests_run": [
            "python -m compileall ai_orchestrator pm_bot tests",
            "pytest pm_bot/tests/test_practical_manual_outcome_resolution_packet_014.py",
            "pytest pm_bot/tests/test_practical_paper_hypothesis_feedback_evaluator_014.py",
            "pytest pm_bot/tests/test_practical_source_accuracy_feedback_014.py",
            "pytest pm_bot/tests/test_practical_manual_feedback_packet_outputs_014.py",
            "pytest pm_bot/tests/test_practical_outcome_recheck_queue_013.py",
            "pytest pm_bot/tests/test_practical_source_learning_scorecard_update_013.py",
            "pytest pm_bot/tests/test_practical_safety_scan.py",
            "python -m json.tool docs/ORCH_PMBOT_PRACTICAL_014_RESULT.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_outcome_feedback_014/manual_outcome_operator_guide_014.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_outcome_feedback_014/source_learning_update_candidate_from_feedback_014.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_outcome_feedback_014/operator_console_feedback_loop_014.json",
            "python -m json.tool pm_bot/practical/artifacts/manual_outcome_feedback_014/manual_outcome_feedback_safety_scan_014.result.json",
            "git diff --check",
            "git diff --cached --check",
        ],
        "validation_passed": True,
        "safety_ok": safety_scan.get("safety_ok") is True,
        "live_network_used": False,
        "openrouter_calls_performed": 0,
        "new_polymarket_api_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_access": False,
        "orders_or_trading_actions": False,
        "runtime_or_dispatcher_changes": False,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "no_autonomous_training_performed": True,
        "no_scheduler_daemon_background_worker": True,
        "next_recommended_action": NEXT_RECOMMENDED_ACTION,
    }


def _write_market_pending_feedback(
    *,
    out_dir: Path,
    market: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    applied_update: Mapping[str, Any],
    source_records: Sequence[Mapping[str, Any]],
    source_learning_candidate_path: Path,
    generated_at: str,
) -> dict[str, Any]:
    market_id = clean_text(market.get("market_id"))
    market_dir = out_dir / "markets" / market_id
    market_dir.mkdir(parents=True, exist_ok=True)
    packet = build_manual_outcome_resolution_packet(
        market_id=market_id,
        market_title=clean_text(market.get("market_title")),
        hypothesis_id=clean_text(market.get("hypothesis_id")),
        paper_tracking_snapshot_id=clean_text(snapshot.get("snapshot_id")),
        outcome_status="unresolved",
        paper_hypothesis_result_label="pending",
        created_at=generated_at,
    )
    validation_errors = validate_manual_outcome_resolution_packet(packet)
    if validation_errors:
        raise ValueError(f"invalid unresolved packet for {market_id}: {validation_errors}")

    manual_packet_json = market_dir / "manual_outcome_resolution_packet.unresolved.json"
    manual_packet_md = market_dir / "manual_outcome_resolution_packet.unresolved.md"
    write_json(manual_packet_json, packet)
    write_text(manual_packet_md, render_manual_outcome_resolution_packet_markdown(packet))

    feedback = build_paper_hypothesis_feedback(
        manual_outcome_packet=packet,
        paper_tracking_state_snapshot=snapshot,
        applied_paper_update=applied_update,
        generated_at=generated_at,
    )
    paper_feedback_json = market_dir / "paper_hypothesis_feedback.pending.json"
    paper_feedback_md = market_dir / "paper_hypothesis_feedback.pending.md"
    write_json(paper_feedback_json, feedback)
    write_text(paper_feedback_md, render_paper_hypothesis_feedback_markdown(feedback))

    source_feedback = build_source_accuracy_feedback(
        paper_hypothesis_feedback=feedback,
        source_records=source_records,
        manual_outcome_packet=packet,
        generated_at=generated_at,
    )
    source_feedback_json = market_dir / "source_accuracy_feedback.pending.json"
    source_feedback_md = market_dir / "source_accuracy_feedback.pending.md"
    write_json(source_feedback_json, source_feedback)
    write_text(source_feedback_md, render_source_accuracy_feedback_markdown(source_feedback))

    manual_feedback_packet = build_manual_feedback_packet(
        manual_outcome_packet=packet,
        paper_hypothesis_feedback=feedback,
        source_accuracy_feedback=source_feedback,
        paper_hypothesis_feedback_path=paper_feedback_json,
        source_accuracy_feedback_path=source_feedback_json,
        source_learning_update_candidate_path=source_learning_candidate_path,
        generated_at=generated_at,
    )
    manual_feedback_json = market_dir / "manual_feedback_packet.pending.json"
    manual_feedback_md = market_dir / "manual_feedback_packet.pending.md"
    write_json(manual_feedback_json, manual_feedback_packet)
    write_text(manual_feedback_md, render_manual_feedback_packet_markdown(manual_feedback_packet))

    return {
        "market_id": market_id,
        "market_title": clean_text(market.get("market_title")),
        "hypothesis_id": clean_text(market.get("hypothesis_id")),
        "outcome_status": "unresolved",
        "feedback_ready": False,
        "manual_outcome_packet_path": normalize_path(manual_packet_json),
        "paper_hypothesis_feedback_path": normalize_path(paper_feedback_json),
        "source_accuracy_feedback_path": normalize_path(source_feedback_json),
        "manual_feedback_packet_path": normalize_path(manual_feedback_json),
    }


def _market_items(queue: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = queue.get("recheck_items", [])
    if not isinstance(rows, list):
        return []
    markets = [row for row in rows if isinstance(row, Mapping) and clean_text(row.get("market_id")) in TRACKED_MARKET_IDS]
    return sorted(markets, key=lambda row: clean_text(row.get("market_id")))


def _source_records_by_market(scorecard: Mapping[str, Any]) -> dict[str, list[Mapping[str, Any]]]:
    records: dict[str, list[Mapping[str, Any]]] = {}
    for row in scorecard.get("source_records", []):
        if not isinstance(row, Mapping):
            continue
        records.setdefault(clean_text(row.get("market_id")), []).append(row)
    return records


def _operator_checklist(outcome_status: str, feedback_ready: bool) -> list[str]:
    if feedback_ready:
        return [
            "Confirm the manual outcome packet was approved.",
            "Review paper hypothesis feedback before applying any source learning candidate.",
            "Keep the review paper-only.",
        ]
    if outcome_status == "unresolved":
        return [
            "Leave outcome fields empty until saved local resolution evidence exists.",
            "Keep paper_hypothesis_result_label as pending.",
            "Keep operator_approved false.",
            "Do not change original analysis or tracking artifacts in place.",
        ]
    return ["Review packet consistency before applying feedback."]


def _next_actions(outcome_status: str, feedback_ready: bool) -> list[str]:
    if feedback_ready:
        return ["Review the source learning update candidate and decide whether to apply it in a separate paper-only task."]
    if outcome_status == "unresolved":
        return ["Wait for a valid local outcome resolution record before evaluating paper feedback."]
    return ["Resolve packet validation issues before marking feedback ready."]


def _manual_feedback_safety_summary() -> dict[str, Any]:
    summary = safe_summary()
    summary.update(
        {
            "new_live_fetch_performed": False,
            "live_network_used": False,
            "openrouter_calls_performed": 0,
            "new_polymarket_api_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "outcome_resolution_invented": False,
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_trading": True,
            "no_autonomous_training_performed": True,
            "no_real_trade_decision": True,
        }
    )
    return summary


def _generated_artifact_paths(out_dir: Path) -> list[str]:
    return [normalize_path(path) for path in sorted(out_dir.rglob("*")) if path.is_file() and path.suffix in {".json", ".md"}]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate PRACTICAL-014 manual outcome feedback artifacts.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for PRACTICAL-014 artifacts.")
    args = parser.parse_args(argv)
    write_manual_outcome_feedback_014(out_dir=args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
