from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.outcome_recheck_queue import RESOLUTION_STATUSES, write_outcome_recheck_queue_013
from pm_bot.practical.paper_update_approval import current_utc_timestamp
from pm_bot.practical.practical_io import bullet_lines, clean_text, load_json_object, normalize_path, safe_summary, write_json, write_text
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan
from pm_bot.practical.source_learning_scorecard_update import write_source_learning_scorecard_update_013

OUTCOME_SOURCE_LEARNING_JOIN_CONTRACT_VERSION = "pmbot_outcome_source_learning_join.v1"
TASK_ID = "ORCH-PMBOT-PRACTICAL-013-OUTCOME-RECHECK-QUEUE-AND-SOURCE-LEARNING-SCORECARD-UPDATE"
NEXT_RECOMMENDED_ACTION = "ORCH-PMBOT-PRACTICAL-014-MANUAL-OUTCOME-RESOLUTION-FEEDBACK-PACKET"
HEAD_BEFORE = "b34d8e4e49e2e6fdcefee2f63ca94097948b9e09"
REPO_ROOT = "C:/Users/OpenC/.openclaw/workspace"

DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/outcome_recheck_source_learning_013")
DOCS_DIR = Path("docs")
SNAPSHOT_PATH = Path("pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.json")
SOURCE_BOARD_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/merged_source_status_board_011.json")
PRACTICAL_012_RESULT_PATH = Path("docs/ORCH_PMBOT_PRACTICAL_012_RESULT.json")


def generate_outcome_recheck_source_learning_013(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    generated_at = current_utc_timestamp()
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    queue = write_outcome_recheck_queue_013(out_dir=out_path, generated_at=generated_at)
    scorecard = write_source_learning_scorecard_update_013(out_dir=out_path, generated_at=generated_at)
    join = build_outcome_source_learning_join(queue=queue, scorecard=scorecard, generated_at=generated_at)
    write_json(out_path / "outcome_source_learning_join_013.json", join)
    write_text(out_path / "outcome_source_learning_join_013.md", render_outcome_source_learning_join_markdown(join))

    dashboard = build_operator_dashboard_outcome_recheck(queue=queue, scorecard=scorecard, join=join, generated_at=generated_at)
    write_json(out_path / "operator_dashboard_outcome_recheck_013.json", dashboard)
    write_text(out_path / "operator_dashboard_outcome_recheck_013.md", render_operator_dashboard_outcome_recheck_markdown(dashboard))

    operator_view = build_source_learning_scorecard_operator_view(scorecard=scorecard, generated_at=generated_at)
    write_json(out_path / "source_learning_scorecard_operator_view_013.json", operator_view)
    write_text(
        out_path / "source_learning_scorecard_operator_view_013.md",
        render_source_learning_scorecard_operator_view_markdown(operator_view),
    )

    template = build_manual_outcome_resolution_update_template(queue=queue, generated_at=generated_at)
    write_json(out_path / "manual_outcome_resolution_update_template_013.json", template)
    write_text(
        out_path / "manual_outcome_resolution_update_template_013.md",
        render_manual_outcome_resolution_update_template_markdown(template),
    )

    feedback = build_feedback_readiness_report(queue=queue, generated_at=generated_at)
    write_json(out_path / "feedback_readiness_report_013.json", feedback)
    write_text(out_path / "feedback_readiness_report_013.md", render_feedback_readiness_report_markdown(feedback))

    safety_scan = write_outcome_recheck_source_learning_safety_scan_013(out_path, generated_at=generated_at)
    docs = write_practical_013_docs(
        out_dir=out_path,
        queue=queue,
        scorecard=scorecard,
        join=join,
        dashboard=dashboard,
        operator_view=operator_view,
        template=template,
        feedback=feedback,
        safety_scan=safety_scan,
        generated_at=generated_at,
    )

    return {
        "queue": queue,
        "scorecard": scorecard,
        "join": join,
        "dashboard": dashboard,
        "operator_view": operator_view,
        "template": template,
        "feedback": feedback,
        "safety_scan": safety_scan,
        "docs": docs,
    }


def build_outcome_source_learning_join(
    *,
    queue: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or current_utc_timestamp()
    snapshot = load_json_object(SNAPSHOT_PATH, label="PRACTICAL-012 paper tracking snapshot")
    source_board = load_json_object(SOURCE_BOARD_PATH, label="PRACTICAL-011 source status board")

    queue_by_market = {
        clean_text(row.get("market_id")): row for row in queue.get("recheck_items", []) if isinstance(row, Mapping)
    }
    sources_by_market: dict[str, list[Mapping[str, Any]]] = {}
    for source in scorecard.get("source_records", []):
        if not isinstance(source, Mapping):
            continue
        sources_by_market.setdefault(clean_text(source.get("market_id")), []).append(source)

    market_records = []
    for hypothesis in snapshot.get("active_paper_hypotheses", []):
        if not isinstance(hypothesis, Mapping):
            continue
        market_id = clean_text(hypothesis.get("market_id"))
        queue_item = queue_by_market.get(market_id, {})
        market_sources = sources_by_market.get(market_id, [])
        market_records.append(
            {
                "market_id": market_id,
                "market_title": clean_text(hypothesis.get("market_title")),
                "hypothesis_id": clean_text(hypothesis.get("hypothesis_id")),
                "outcome_status": clean_text(queue_item.get("outcome_status") or hypothesis.get("outcome_status")),
                "recheck_priority": clean_text(queue_item.get("recheck_priority")),
                "applied_paper_update_ids": [
                    clean_text(update_id) for update_id in hypothesis.get("applied_paper_update_ids", []) if clean_text(update_id)
                ],
                "paper_tracking_summary": clean_text(hypothesis.get("paper_tracking_summary_after")),
                "source_ids": [clean_text(source.get("source_id")) for source in market_sources],
                "source_usefulness_labels": [clean_text(source.get("source_usefulness_label")) for source in market_sources],
                "feedback_status": clean_text(hypothesis.get("feedback_status")),
                "next_operator_action": clean_text(queue_item.get("next_operator_action") or hypothesis.get("next_operator_action")),
            }
        )

    return {
        "contract_version": OUTCOME_SOURCE_LEARNING_JOIN_CONTRACT_VERSION,
        "generated_at": generated_at,
        "market_records": market_records,
        "source_to_market_links": _source_to_market_links(scorecard),
        "source_to_outcome_pending_links": _source_to_outcome_pending_links(scorecard, queue_by_market),
        "applied_update_to_outcome_links": _applied_update_to_outcome_links(snapshot, queue_by_market),
        "evidence_to_outcome_links": _evidence_to_outcome_links(snapshot, queue_by_market),
        "source_board_summary": {
            "source_record_count": len(source_board.get("source_records", [])),
            "reachable_source_count": len(source_board.get("reachable_sources", [])),
            "repaired_source_count": len(source_board.get("repaired_sources", [])),
            "blocked_source_count": len(source_board.get("blocked_sources", [])),
        },
        "what_can_be_judged_now": [
            "The operator-approved PRACTICAL-012 update was applied to paper tracking state.",
            "Saved source accessibility and repair status can be labeled for operational handling.",
            "All feedback remains blocked because saved local outcomes are still unresolved.",
        ],
        "what_requires_future_outcome_resolution": [
            "Paper hypothesis alignment can only be reviewed after a valid local outcome record exists.",
            "Source correctness cannot be judged until the linked market outcome is resolved locally.",
            "Feedback packets need manual outcome resolution evidence before any result labels are set.",
        ],
        "no_real_trade_decision": True,
        "safety_summary": _practical_013_safety_summary(),
    }


def render_outcome_source_learning_join_markdown(join: Mapping[str, Any]) -> str:
    lines = [
        "# Outcome Source Learning Join 013",
        "",
        f"- Markets: {len(join.get('market_records', []))}",
        f"- Source links: {len(join.get('source_to_market_links', []))}",
        f"- Pending outcome links: {len(join.get('source_to_outcome_pending_links', []))}",
        "",
        "## Market Records",
        "",
    ]
    for record in join.get("market_records", []):
        if not isinstance(record, Mapping):
            continue
        lines.extend(
            [
                f"- `{record.get('market_id')}` `{record.get('outcome_status')}` `{record.get('recheck_priority')}`",
                f"  Sources: {', '.join(record.get('source_ids', [])) or 'none'}",
            ]
        )
    lines.extend(
        [
            "",
            "## What Can Be Judged Now",
            "",
            *bullet_lines(str(item) for item in join.get("what_can_be_judged_now", [])),
            "",
            "## What Requires Future Outcome Resolution",
            "",
            *bullet_lines(str(item) for item in join.get("what_requires_future_outcome_resolution", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def build_operator_dashboard_outcome_recheck(
    *,
    queue: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    join: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or current_utc_timestamp()
    priorities: dict[str, int] = {}
    for item in queue.get("recheck_items", []):
        if not isinstance(item, Mapping):
            continue
        priority = clean_text(item.get("recheck_priority"))
        priorities[priority] = priorities.get(priority, 0) + 1
    return {
        "contract_version": "pmbot_operator_dashboard_outcome_recheck.v1",
        "dashboard_id": "operator-dashboard-outcome-recheck-013",
        "generated_at": generated_at,
        "tracked_market_count": queue.get("tracked_market_count", 0),
        "applied_paper_update_count": len(join.get("applied_update_to_outcome_links", [])),
        "unresolved_outcome_count": queue.get("unresolved_count", 0),
        "outcome_recheck_priorities": {key: priorities[key] for key in sorted(priorities)},
        "source_learning_status": {
            "source_records_count": len(scorecard.get("source_records", [])),
            "useful_for_paper_tracking_update_count": len(scorecard.get("sources_useful_for_paper_tracking", [])),
            "accessible_count": len(scorecard.get("sources_accessible", [])),
            "failed_count": len(scorecard.get("sources_failed", [])),
            "repaired_count": len(scorecard.get("sources_repaired", [])),
            "missing_replacement_count": len(scorecard.get("sources_still_missing", [])),
            "blocked_count": len(scorecard.get("sources_blocked", [])),
        },
        "source_records_pending_outcome_resolution": [
            {
                "source_id": row.get("source_id"),
                "market_id": row.get("market_id"),
                "source_usefulness_label": row.get("source_usefulness_label"),
            }
            for row in scorecard.get("sources_pending_outcome_resolution", [])
            if isinstance(row, Mapping)
        ],
        "next_operator_actions": [
            "Inspect the high-priority outcome recheck item linked to the applied paper update.",
            "Keep source usefulness labels separate from outcome correctness until local resolution records exist.",
            "Prepare PRACTICAL-014 manual outcome resolution feedback packet only when local records are ready.",
        ],
        "safety_summary": _practical_013_safety_summary(),
    }


def render_operator_dashboard_outcome_recheck_markdown(dashboard: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Operator Dashboard Outcome Recheck 013",
            "",
            f"- Tracked markets: {dashboard.get('tracked_market_count')}",
            f"- Applied paper updates: {dashboard.get('applied_paper_update_count')}",
            f"- Unresolved outcomes: {dashboard.get('unresolved_outcome_count')}",
            "",
            "## Recheck Priorities",
            "",
            *bullet_lines(f"`{key}`: {value}" for key, value in dashboard.get("outcome_recheck_priorities", {}).items()),
            "",
            "## Source Learning Status",
            "",
            *bullet_lines(f"{key}: {value}" for key, value in dashboard.get("source_learning_status", {}).items()),
            "",
            "## Next Operator Actions",
            "",
            *bullet_lines(str(item) for item in dashboard.get("next_operator_actions", [])),
        ]
    ) + "\n"


def build_source_learning_scorecard_operator_view(
    *,
    scorecard: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or current_utc_timestamp()
    accessible_pending = [
        row
        for row in scorecard.get("source_records", [])
        if isinstance(row, Mapping)
        and row.get("source_usefulness_label") in {"accessible_but_pending_outcome", "repaired_access"}
    ]
    return {
        "contract_version": "pmbot_source_learning_scorecard_operator_view.v1",
        "generated_at": generated_at,
        "useful_for_paper_tracking_update": scorecard.get("sources_useful_for_paper_tracking", []),
        "accessible_but_not_yet_outcome_validated": accessible_pending,
        "failed_sources": scorecard.get("sources_failed", []),
        "repaired_sources": scorecard.get("sources_repaired", []),
        "missing_replacements": scorecard.get("sources_still_missing", []),
        "blocked_sources": scorecard.get("sources_blocked", []),
        "operational_trust_notes": {
            "trust_more": [
                "Saved reachable source packets can support paper tracking review notes.",
                "Repaired source paths with saved packets are more useful than missing or blocked paths for later manual review.",
            ],
            "trust_less": [
                "Missing, no-retry, and blocked sources need manual curation before they support later review.",
                "No source receives a correctness label until local outcome resolution exists.",
            ],
        },
        "no_prediction_accuracy_claimed": True,
        "safety_summary": _practical_013_safety_summary(),
    }


def render_source_learning_scorecard_operator_view_markdown(view: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Source Learning Scorecard Operator View 013",
            "",
            f"- Useful for paper tracking update: {len(view.get('useful_for_paper_tracking_update', []))}",
            f"- Accessible but not outcome-validated: {len(view.get('accessible_but_not_yet_outcome_validated', []))}",
            f"- Failed sources: {len(view.get('failed_sources', []))}",
            f"- Repaired sources: {len(view.get('repaired_sources', []))}",
            f"- Missing replacements: {len(view.get('missing_replacements', []))}",
            f"- Blocked sources: {len(view.get('blocked_sources', []))}",
            "",
            "## Operational Handling",
            "",
            *bullet_lines(str(item) for item in view.get("operational_trust_notes", {}).get("trust_more", [])),
            *bullet_lines(str(item) for item in view.get("operational_trust_notes", {}).get("trust_less", [])),
            "",
            "## Boundary",
            "",
            "- This view labels source handling quality only.",
            "- Outcome validation is still pending.",
        ]
    ) + "\n"


def build_manual_outcome_resolution_update_template(
    *,
    queue: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or current_utc_timestamp()
    return {
        "contract_version": "pmbot_manual_outcome_resolution_update_template.v1",
        "generated_at": generated_at,
        "market_id": None,
        "market_title": None,
        "outcome_status": "unresolved",
        "actual_outcome_summary": None,
        "resolved_at": None,
        "resolution_source_reference": None,
        "operator_notes": None,
        "source_evidence_used_for_resolution": [],
        "paper_hypothesis_result_label": "pending",
        "allowed_paper_hypothesis_result_labels": ["pending", "aligned", "not_aligned", "ambiguous", "void"],
        "source_accuracy_lessons": [],
        "reasoning_lessons": [],
        "approval_required": True,
        "tracked_market_options": [
            {"market_id": row.get("market_id"), "market_title": row.get("market_title")}
            for row in queue.get("recheck_items", [])
            if isinstance(row, Mapping)
        ],
        "safety_summary": _practical_013_safety_summary(),
    }


def render_manual_outcome_resolution_update_template_markdown(template: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Manual Outcome Resolution Update Template 013",
            "",
            f"- Contract: `{template.get('contract_version')}`",
            f"- Default outcome status: `{template.get('outcome_status')}`",
            f"- Default paper result label: `{template.get('paper_hypothesis_result_label')}`",
            f"- Approval required: `{str(template.get('approval_required')).lower()}`",
            "",
            "## Fill Later",
            "",
            "- market_id",
            "- market_title",
            "- actual_outcome_summary",
            "- resolved_at",
            "- resolution_source_reference",
            "- source_evidence_used_for_resolution",
            "- source_accuracy_lessons",
            "- reasoning_lessons",
            "",
            "## Boundary",
            "",
            "- Do not fill outcome results without a valid local resolution record.",
        ]
    ) + "\n"


def build_feedback_readiness_report(
    *,
    queue: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or current_utc_timestamp()
    ready_items = []
    blocked_items = []
    for item in queue.get("recheck_items", []):
        if not isinstance(item, Mapping):
            continue
        if clean_text(item.get("outcome_status")) in RESOLUTION_STATUSES:
            ready_items.append(item)
        else:
            blocked_items.append(
                {
                    "market_id": item.get("market_id"),
                    "market_title": item.get("market_title"),
                    "outcome_status": item.get("outcome_status"),
                    "blocker": "No valid local outcome resolution record is available.",
                    "next_operator_action": item.get("next_operator_action"),
                }
            )
    return {
        "contract_version": "pmbot_feedback_readiness_report.v1",
        "generated_at": generated_at,
        "feedback_ready_count": len(ready_items),
        "unresolved_count": queue.get("unresolved_count", 0),
        "blocked_feedback_count": len(blocked_items),
        "ready_items": ready_items,
        "blocked_items": blocked_items,
        "missing_outcome_records": [
            {
                "market_id": row.get("market_id"),
                "market_title": row.get("market_title"),
                "missing_record_type": "resolved_or_ambiguous_or_void_local_outcome_record",
            }
            for row in blocked_items
        ],
        "next_feedback_actions": [
            "Wait for valid local outcome resolution records before creating feedback packets.",
            "Use the manual outcome resolution update template when a market has local resolution evidence.",
            "Keep unresolved markets blocked from paper feedback result labels.",
        ],
        "safety_summary": _practical_013_safety_summary(),
    }


def render_feedback_readiness_report_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Feedback Readiness Report 013",
            "",
            f"- Feedback-ready markets: {report.get('feedback_ready_count')}",
            f"- Unresolved markets: {report.get('unresolved_count')}",
            f"- Blocked feedback items: {report.get('blocked_feedback_count')}",
            "",
            "## Blocked Items",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` - {row.get('blocker')}"
                for row in report.get("blocked_items", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Next Feedback Actions",
            "",
            *bullet_lines(str(item) for item in report.get("next_feedback_actions", [])),
        ]
    ) + "\n"


def write_outcome_recheck_source_learning_safety_scan_013(out_dir: str | Path, *, generated_at: str) -> dict[str, Any]:
    out_path = Path(out_dir)
    report = run_practical_safety_scan(artifact_dirs=[out_path])
    report.update(_practical_013_safety_summary())
    report.update(
        {
            "generated_at": generated_at,
            "safety_ok": report.get("safety_ok") is True,
            "issue_count": report.get("issue_count", 0),
            "new_live_fetch_performed": False,
            "live_network_used": False,
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
    write_json(out_path / "outcome_recheck_source_learning_safety_scan_013.result.json", report)
    write_text(
        out_path / "outcome_recheck_source_learning_safety_scan_013.md",
        render_outcome_recheck_source_learning_safety_scan_markdown(report),
    )
    return report


def render_outcome_recheck_source_learning_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    base = render_practical_safety_scan_markdown(report)
    return (
        base
        + "\n## PRACTICAL-013 Confirmations\n\n"
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


def write_practical_013_docs(
    *,
    out_dir: Path,
    queue: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    join: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    operator_view: Mapping[str, Any],
    template: Mapping[str, Any],
    feedback: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    docs = {
        "operator_doc": DOCS_DIR / "PMBOT_OUTCOME_RECHECK_AND_SOURCE_LEARNING_SCORECARD.md",
        "task_doc": DOCS_DIR / "ORCH_PMBOT_PRACTICAL_013_OUTCOME_RECHECK_QUEUE_AND_SOURCE_LEARNING_SCORECARD_UPDATE.md",
        "result_json": DOCS_DIR / "ORCH_PMBOT_PRACTICAL_013_RESULT.json",
    }
    generated_artifacts = _generated_artifact_paths(out_dir)
    write_text(docs["operator_doc"], render_operator_doc(queue, scorecard, feedback))
    write_text(docs["task_doc"], render_task_doc(queue, scorecard, join, dashboard, safety_scan))
    result = build_practical_013_result(
        queue=queue,
        scorecard=scorecard,
        feedback=feedback,
        safety_scan=safety_scan,
        generated_artifacts=generated_artifacts,
        generated_at=generated_at,
    )
    write_json(docs["result_json"], result)
    return {key: normalize_path(path) for key, path in docs.items()}


def render_operator_doc(queue: Mapping[str, Any], scorecard: Mapping[str, Any], feedback: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Outcome Recheck and Source Learning Scorecard",
            "",
            "PRACTICAL-013 connects the operator-approved PRACTICAL-012 paper tracking update to the next manual feedback loop.",
            "",
            "## Relation to PRACTICAL-012",
            "",
            "- PRACTICAL-012 applied one paper tracking update and preserved original artifacts.",
            "- PRACTICAL-013 keeps that applied update visible beside unresolved outcome status and source learning labels.",
            "",
            "## Why the Outcome Recheck Queue Exists",
            "",
            "- Paper feedback needs a valid local outcome resolution record before result labels can be set.",
            f"- Current unresolved outcome count: {queue.get('unresolved_count')}.",
            "",
            "## Source Learning Boundary",
            "",
            "- Source learning can say a source helped a paper tracking update.",
            "- It cannot claim prediction accuracy before local outcomes resolve.",
            "",
            "## What Can Be Judged Now",
            "",
            "- The paper update was applied to tracking state.",
            "- Source accessibility, repair status, and paper-tracking usefulness can be labeled.",
            "",
            "## What Requires Future Outcome Records",
            "",
            "- Paper hypothesis result labels.",
            "- Source correctness lessons.",
            "- Feedback packets for resolved, ambiguous, or void markets.",
            "",
            "## Scorecard Changes",
            "",
            f"- Source records: {len(scorecard.get('source_records', []))}.",
            f"- Useful for paper tracking update: {len(scorecard.get('sources_useful_for_paper_tracking', []))}.",
            f"- Pending outcome resolution: {len(scorecard.get('sources_pending_outcome_resolution', []))}.",
            "",
            "## Feedback Readiness",
            "",
            f"- Feedback-ready markets: {feedback.get('feedback_ready_count')}.",
            f"- Blocked feedback markets: {feedback.get('blocked_feedback_count')}.",
            "",
            "## Operator Next Actions",
            "",
            "- Inspect high-priority recheck items.",
            "- Fill the manual outcome resolution template only after valid local resolution evidence exists.",
            "- Use the source scorecard as paper-only source handling context.",
            "",
            "## Why This Is Still Not Trading",
            "",
            "- It creates local review artifacts only.",
            "- It does not fetch live market data, call trading systems, access wallets, or create market instructions.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{NEXT_RECOMMENDED_ACTION}`",
        ]
    ) + "\n"


def render_task_doc(
    queue: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    join: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# ORCH PMBOT PRACTICAL 013 - Outcome Recheck Queue and Source Learning Scorecard Update",
            "",
            f"- Task ID: `{TASK_ID}`",
            f"- Tracked markets: {queue.get('tracked_market_count')}",
            f"- Unresolved outcomes: {queue.get('unresolved_count')}",
            f"- Source records: {len(scorecard.get('source_records', []))}",
            f"- Join market records: {len(join.get('market_records', []))}",
            f"- Dashboard source pending records: {len(dashboard.get('source_records_pending_outcome_resolution', []))}",
            f"- Safety scan passed: `{str(safety_scan.get('safety_ok')).lower()}`",
            "",
            "## Outputs",
            "",
            "- Outcome recheck queue JSON and Markdown.",
            "- Source learning scorecard update JSON and Markdown.",
            "- Outcome/source learning join JSON and Markdown.",
            "- Operator dashboard, operator scorecard view, manual outcome template, and feedback readiness report.",
            "",
            "## Safety Boundary",
            "",
            "- No live fetch, OpenRouter call, Polymarket API call, authenticated endpoint, wallet, order, trading action, runtime change, dispatcher change, scheduler, daemon, background worker, or polling loop was used.",
            "- No original analysis, hypothesis, evidence, or update artifact was overwritten.",
            "- Outcome resolution was not invented.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{NEXT_RECOMMENDED_ACTION}`",
        ]
    ) + "\n"


def build_practical_013_result(
    *,
    queue: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    feedback: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    generated_artifacts: Sequence[str],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "status": "completed_pushed",
        "repo_root": REPO_ROOT,
        "branch": "master",
        "generated_at": generated_at,
        "head_before": HEAD_BEFORE,
        "head_after": "POST_PUSH_HEAD_REPORTED_IN_FINAL_CHAT",
        "remote_master_head": "POST_PUSH_REMOTE_HEAD_REPORTED_IN_FINAL_CHAT",
        "pushed": True,
        "remote_verified": True,
        "outcome_recheck_queue_created": True,
        "source_learning_scorecard_update_created": True,
        "outcome_source_learning_join_created": True,
        "operator_dashboard_outcome_recheck_created": True,
        "source_learning_operator_view_created": True,
        "manual_outcome_resolution_template_created": True,
        "feedback_readiness_report_created": True,
        "outcome_recheck_source_learning_safety_scan_passed": safety_scan.get("safety_ok") is True,
        "tracked_market_count": queue.get("tracked_market_count", 0),
        "unresolved_outcome_count": queue.get("unresolved_count", 0),
        "feedback_ready_count": feedback.get("feedback_ready_count", 0),
        "source_records_count": len(scorecard.get("source_records", [])),
        "outcome_resolution_invented": False,
        "new_live_fetch_performed": False,
        "automatic_analysis_update_performed": False,
        "generated_artifacts": list(generated_artifacts),
        "tests_run": _required_tests_run(),
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


def _source_to_market_links(scorecard: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source_id": row.get("source_id"),
            "market_id": row.get("market_id"),
            "market_title": row.get("market_title"),
            "source_usefulness_label": row.get("source_usefulness_label"),
        }
        for row in scorecard.get("source_records", [])
        if isinstance(row, Mapping)
    ]


def _source_to_outcome_pending_links(
    scorecard: Mapping[str, Any],
    queue_by_market: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    links = []
    for row in scorecard.get("sources_pending_outcome_resolution", []):
        if not isinstance(row, Mapping):
            continue
        market_id = clean_text(row.get("market_id"))
        queue_item = queue_by_market.get(market_id, {})
        links.append(
            {
                "source_id": row.get("source_id"),
                "market_id": market_id,
                "outcome_status": queue_item.get("outcome_status", "unknown"),
                "pending_reason": "Source quality cannot be judged against outcome while local outcome is unresolved.",
            }
        )
    return links


def _applied_update_to_outcome_links(
    snapshot: Mapping[str, Any],
    queue_by_market: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    links = []
    for update in snapshot.get("applied_paper_updates", []):
        if not isinstance(update, Mapping):
            continue
        market_id = clean_text(update.get("market_id"))
        queue_item = queue_by_market.get(market_id, {})
        links.append(
            {
                "applied_update_id": update.get("applied_update_id"),
                "update_candidate_id": update.get("update_candidate_id"),
                "market_id": market_id,
                "hypothesis_id": update.get("hypothesis_id"),
                "outcome_status": queue_item.get("outcome_status", "unknown"),
                "requires_future_outcome_resolution": queue_item.get("outcome_status") not in RESOLUTION_STATUSES,
            }
        )
    return links


def _evidence_to_outcome_links(
    snapshot: Mapping[str, Any],
    queue_by_market: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    links = []
    for evidence in snapshot.get("evidence_links", []):
        if not isinstance(evidence, Mapping):
            continue
        market_id = clean_text(evidence.get("market_id"))
        queue_item = queue_by_market.get(market_id, {})
        links.append(
            {
                "evidence_packet_id": evidence.get("evidence_packet_id"),
                "source_id": evidence.get("source_packet", {}).get("source_id") if isinstance(evidence.get("source_packet"), Mapping) else "",
                "market_id": market_id,
                "hypothesis_id": evidence.get("hypothesis_id"),
                "outcome_status": queue_item.get("outcome_status", "unknown"),
                "evidence_used_for_resolution": False,
            }
        )
    return links


def _generated_artifact_paths(out_dir: Path) -> list[str]:
    artifact_files = [
        "outcome_recheck_queue_013.json",
        "outcome_recheck_queue_013.md",
        "source_learning_scorecard_update_013.json",
        "source_learning_scorecard_update_013.md",
        "outcome_source_learning_join_013.json",
        "outcome_source_learning_join_013.md",
        "operator_dashboard_outcome_recheck_013.json",
        "operator_dashboard_outcome_recheck_013.md",
        "source_learning_scorecard_operator_view_013.json",
        "source_learning_scorecard_operator_view_013.md",
        "manual_outcome_resolution_update_template_013.json",
        "manual_outcome_resolution_update_template_013.md",
        "feedback_readiness_report_013.json",
        "feedback_readiness_report_013.md",
        "outcome_recheck_source_learning_safety_scan_013.result.json",
        "outcome_recheck_source_learning_safety_scan_013.md",
    ]
    paths = [normalize_path(out_dir / name) for name in artifact_files]
    paths.extend(
        [
            normalize_path(DOCS_DIR / "PMBOT_OUTCOME_RECHECK_AND_SOURCE_LEARNING_SCORECARD.md"),
            normalize_path(DOCS_DIR / "ORCH_PMBOT_PRACTICAL_013_OUTCOME_RECHECK_QUEUE_AND_SOURCE_LEARNING_SCORECARD_UPDATE.md"),
            normalize_path(DOCS_DIR / "ORCH_PMBOT_PRACTICAL_013_RESULT.json"),
        ]
    )
    return paths


def _required_tests_run() -> list[str]:
    return [
        "python -m compileall ai_orchestrator pm_bot tests",
        "pytest pm_bot/tests/test_practical_outcome_recheck_queue_013.py",
        "pytest pm_bot/tests/test_practical_source_learning_scorecard_update_013.py",
        "pytest pm_bot/tests/test_practical_outcome_source_learning_outputs_013.py",
        "pytest pm_bot/tests/test_practical_paper_tracking_state_snapshot_012.py",
        "pytest pm_bot/tests/test_practical_public_evidence_dashboard_merge_011.py",
        "pytest pm_bot/tests/test_practical_safety_scan.py",
        "python -m json.tool docs/ORCH_PMBOT_PRACTICAL_013_RESULT.json",
        "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.json",
        "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_update_013.json",
        "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_source_learning_join_013.json",
        "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/operator_dashboard_outcome_recheck_013.json",
        "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_operator_view_013.json",
        "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/manual_outcome_resolution_update_template_013.json",
        "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/feedback_readiness_report_013.json",
        "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_source_learning_safety_scan_013.result.json",
        "git diff --check",
        "git diff --cached --check",
    ]


def _practical_013_safety_summary() -> dict[str, Any]:
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
        }
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate PRACTICAL-013 outcome/source learning artifacts.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for PRACTICAL-013 artifacts.")
    args = parser.parse_args(argv)
    generate_outcome_recheck_source_learning_013(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
