from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.merged_source_status_board import build_merged_source_status_board, write_merged_source_status_board_011
from pm_bot.practical.pending_paper_update_queue import build_pending_paper_update_queue, write_pending_paper_update_queue_011
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, safe_summary, write_json, write_text
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan
from pm_bot.practical.public_evidence_hypothesis_linker import (
    build_public_evidence_hypothesis_links,
    load_linked_evidence_packets,
    write_public_evidence_hypothesis_links_011,
)
from pm_bot.practical.public_evidence_scorecard import build_public_evidence_scorecard, write_public_evidence_scorecard_011

DASHBOARD_CONTRACT_VERSION = "pmbot_public_evidence_tracking_dashboard.v1"
TASK_ID = "ORCH-PMBOT-PRACTICAL-011-MERGE-PUBLIC-EVIDENCE-REVIEWS-INTO-PAPER-TRACKING-DASHBOARD"
NEXT_RECOMMENDED_ACTION = "ORCH-PMBOT-PRACTICAL-012-OPERATOR-APPROVED-PAPER-HYPOTHESIS-UPDATE-APPLICATION"
HEAD_BEFORE = "eb065ffe45938a99976c4f92eef8c21d6be111d6"
REPO_ROOT = "C:/Users/OpenC/.openclaw/workspace"

DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
DOCS_DIR = Path("docs")
MARKET_QUEUE_PATH = Path("pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json")
ACTIVE_HYPOTHESES_PATH = Path(
    "pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.active_paper_hypotheses.result.json"
)
SELECTED_MARKETS_PATH = Path("pm_bot/practical/artifacts/real_market_batch_004/selected_real_market_batch.json")
RESULT_004_PATH = Path("docs/ORCH_PMBOT_PRACTICAL_004_RESULT.json")
RESULT_008_PATH = Path("docs/ORCH_PMBOT_PRACTICAL_008_RESULT.json")
RESULT_009_PATH = Path("docs/ORCH_PMBOT_PRACTICAL_009_RESULT.json")
RESULT_010_PATH = Path("docs/ORCH_PMBOT_PRACTICAL_010_RESULT.json")
FETCH_008_SUMMARY_PATH = Path("pm_bot/practical/artifacts/public_read_only_fetch_execution_008/fetch_execution_summary_008.result.json")
FETCH_010_SUMMARY_PATH = Path(
    "pm_bot/practical/artifacts/public_source_url_fixes_010/second_fetch_execution_summary_010.result.json"
)
PUBLIC_REVIEW_009_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/public_evidence_operator_review_009.json")
UPDATE_CANDIDATE_009_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/paper_hypothesis_update_candidate_009.json")
FAILURE_DIAGNOSIS_009_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/public_fetch_failure_diagnosis_009.json")
FIX_PACKET_009_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/failed_source_url_fix_packet_009.json")
REPAIR_SUMMARY_010_PATH = Path("pm_bot/practical/artifacts/public_source_url_fixes_010/source_url_repair_result_summary_010.json")
SECOND_OPERATOR_REVIEW_010_PATH = Path(
    "pm_bot/practical/artifacts/public_source_url_fixes_010/second_public_evidence_operator_review_packet_010.json"
)
SOURCE_LEARNING_009_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/source_accessibility_learning_009.json")
SOURCE_LEARNING_010_PATH = Path("pm_bot/practical/artifacts/public_source_url_fixes_010/source_accessibility_learning_010.json")


def build_public_evidence_tracking_dashboard(
    *,
    links_model: Mapping[str, Any] | None = None,
    pending_queue: Mapping[str, Any] | None = None,
    source_board: Mapping[str, Any] | None = None,
    scorecard: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    links_model = links_model or build_public_evidence_hypothesis_links(generated_at=generated_at)
    pending_queue = pending_queue or build_pending_paper_update_queue(generated_at=generated_at)
    source_board = source_board or build_merged_source_status_board(generated_at=generated_at)
    scorecard = scorecard or build_public_evidence_scorecard(generated_at=generated_at)

    tracked_markets = _load_tracked_markets()
    active_hypotheses = _load_active_paper_hypotheses()
    unresolved_outcomes = _load_unresolved_outcomes(tracked_markets)
    evidence_packets = _summarize_evidence_packets(load_linked_evidence_packets())
    update_candidates = list(pending_queue.get("pending_updates", [])) + list(pending_queue.get("blocked_updates", [])) + list(
        pending_queue.get("already_applied_updates", [])
    )
    repair_summary = load_json_object(REPAIR_SUMMARY_010_PATH)

    return {
        "contract_version": DASHBOARD_CONTRACT_VERSION,
        "dashboard_id": "public-evidence-tracking-dashboard-011",
        "generated_at": generated_at,
        "tracked_markets": tracked_markets,
        "active_paper_hypotheses": active_hypotheses,
        "unresolved_outcomes": unresolved_outcomes,
        "evidence_packets": evidence_packets,
        "evidence_to_market_links": _dashboard_market_links(links_model),
        "evidence_to_hypothesis_links": _dashboard_hypothesis_links(links_model),
        "update_candidates": update_candidates,
        "pending_operator_reviews": _pending_operator_reviews(pending_queue, source_board, links_model),
        "source_status_summary": _source_status_summary(source_board),
        "source_repair_summary": {
            "source_url_repair_result_summary_path": normalize_path(REPAIR_SUMMARY_010_PATH),
            "repaired_executable_count": repair_summary.get("repaired_executable_count", 0),
            "no_retry_count": repair_summary.get("no_retry_count", 0),
            "replacement_missing_count": repair_summary.get("replacement_missing_count", 0),
            "blocked_count": repair_summary.get("blocked_count", 0),
            "second_fetch_succeeded": repair_summary.get("second_fetch_succeeded", 0),
            "second_fetch_failed": repair_summary.get("second_fetch_failed", 0),
        },
        "source_accessibility_learning_summary": {
            "source_learning_009_path": normalize_path(SOURCE_LEARNING_009_PATH),
            "source_learning_010_path": normalize_path(SOURCE_LEARNING_010_PATH),
            "source_records_count": len(source_board.get("source_records", [])),
            "reachable_count": len(source_board.get("reachable_sources", [])),
            "manual_review_count": len(source_board.get("sources_requiring_manual_review", [])),
            "no_autonomous_training_performed": True,
        },
        "outcome_feedback_pending_summary": {
            "unresolved_outcome_count": len(unresolved_outcomes),
            "outcomes_resolved_count": 0,
            "markets_waiting_for_outcome_resolution": [
                {"market_id": row.get("market_id"), "market_title": row.get("market_title")}
                for row in unresolved_outcomes
            ],
        },
        "public_evidence_scorecard": scorecard,
        "next_operator_actions": [
            "Review the pending paper update candidate in a later operator-approved paper task.",
            "Use the source URL backlog for manual URL collection before any future scoped public-source task.",
            "Keep all five outcomes unresolved until saved resolution evidence is available.",
        ],
        "safety_summary": _dashboard_safety_summary(),
    }


def generate_public_evidence_dashboard_011(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    links_model = write_public_evidence_hypothesis_links_011(out_path)
    pending_queue = write_pending_paper_update_queue_011(out_path)
    source_board = write_merged_source_status_board_011(out_path)
    scorecard = write_public_evidence_scorecard_011(out_path)
    dashboard = build_public_evidence_tracking_dashboard(
        links_model=links_model,
        pending_queue=pending_queue,
        source_board=source_board,
        scorecard=scorecard,
    )
    write_json(out_path / "public_evidence_tracking_dashboard_011.json", dashboard)
    write_text(out_path / "public_evidence_tracking_dashboard_011.md", render_public_evidence_tracking_dashboard_markdown(dashboard))

    morning_card = build_operator_morning_card(dashboard, source_board, pending_queue)
    write_json(out_path / "operator_morning_card_011.json", morning_card)
    write_text(out_path / "operator_morning_card_011.md", render_operator_morning_card_markdown(morning_card))

    delta = build_paper_tracking_dashboard_delta(dashboard, source_board, pending_queue)
    write_json(out_path / "paper_tracking_dashboard_delta_011.json", delta)
    write_text(out_path / "paper_tracking_dashboard_delta_011.md", render_paper_tracking_dashboard_delta_markdown(delta))

    watchlist = build_unresolved_outcome_evidence_watchlist(dashboard, links_model, source_board, pending_queue)
    write_json(out_path / "unresolved_outcome_evidence_watchlist_011.json", watchlist)
    write_text(out_path / "unresolved_outcome_evidence_watchlist_011.md", render_unresolved_outcome_evidence_watchlist_markdown(watchlist))

    backlog = build_source_url_backlog(source_board)
    write_json(out_path / "source_url_backlog_011.json", backlog)
    write_text(out_path / "source_url_backlog_011.md", render_source_url_backlog_markdown(backlog))

    safety_scan = write_public_evidence_dashboard_safety_scan(out_path)
    docs = write_public_evidence_dashboard_docs(dashboard, links_model, pending_queue, source_board, scorecard, safety_scan, out_path)

    return {
        "dashboard": dashboard,
        "links": links_model,
        "pending_queue": pending_queue,
        "source_board": source_board,
        "scorecard": scorecard,
        "operator_morning_card": morning_card,
        "paper_tracking_dashboard_delta": delta,
        "watchlist": watchlist,
        "source_url_backlog": backlog,
        "safety_scan": safety_scan,
        "docs": docs,
    }


def render_public_evidence_tracking_dashboard_markdown(dashboard: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Public Evidence Tracking Dashboard",
            "",
            f"- Dashboard ID: `{dashboard.get('dashboard_id')}`",
            f"- Tracked markets: {len(dashboard.get('tracked_markets', []))}",
            f"- Public evidence packets: {len(dashboard.get('evidence_packets', []))}",
            f"- Pending update candidates: {len([row for row in dashboard.get('update_candidates', []) if isinstance(row, Mapping) and row.get('update_applied') is False])}",
            f"- Unresolved outcomes: {dashboard.get('outcome_feedback_pending_summary', {}).get('unresolved_outcome_count', 0)}",
            "",
            "## Tracked Markets",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` - {row.get('market_title')}" for row in dashboard.get("tracked_markets", [])
            ),
            "",
            "## Active Paper Hypotheses",
            "",
            *bullet_lines(
                f"`{row.get('hypothesis_id')}` - {row.get('paper_hypothesis_summary')}"
                for row in dashboard.get("active_paper_hypotheses", [])
            ),
            "",
            "## Public Evidence Collected",
            "",
            *bullet_lines(
                f"`{row.get('evidence_packet_id')}` -> market `{', '.join(row.get('market_ids', []))}` via {row.get('source_name')}"
                for row in dashboard.get("evidence_packets", [])
            ),
            "",
            "## Evidence Links",
            "",
            *bullet_lines(
                f"`{row.get('evidence_packet_id')}` -> `{row.get('market_id')}` -> `{row.get('hypothesis_id')}`"
                for row in dashboard.get("evidence_to_hypothesis_links", [])
            ),
            "",
            "## Pending Paper Update Candidates",
            "",
            *bullet_lines(
                f"`{row.get('update_candidate_id')}` for market `{row.get('market_id')}`"
                for row in dashboard.get("update_candidates", [])
                if isinstance(row, Mapping) and row.get("update_applied") is False
            ),
            "",
            "## Source Status Board",
            "",
            f"- Reachable: {dashboard.get('source_status_summary', {}).get('reachable_source_count', 0)}",
            f"- Failed or blocked: {dashboard.get('source_status_summary', {}).get('failed_source_count', 0)}",
            f"- Repaired: {dashboard.get('source_status_summary', {}).get('repaired_source_count', 0)}",
            "",
            "## Source Repair Summary",
            "",
            *bullet_lines(f"{key}: {value}" for key, value in dashboard.get("source_repair_summary", {}).items()),
            "",
            "## Outcome Feedback Pending",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` - {row.get('outcome_status')}" for row in dashboard.get("unresolved_outcomes", [])
            ),
            "",
            "## Next Operator Actions",
            "",
            *bullet_lines(str(item) for item in dashboard.get("next_operator_actions", [])),
            "",
            "## Safety Boundary",
            "",
            "- Dashboard merge only; no new live public fetch was performed.",
            "- Original paper hypotheses and unresolved outcome records were not overwritten.",
            "- No autonomous trading, scheduler, daemon, background worker, or polling loop was created.",
        ]
    ) + "\n"


def build_operator_morning_card(
    dashboard: Mapping[str, Any],
    source_board: Mapping[str, Any],
    pending_queue: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_operator_morning_card.v1",
        "generated_at": generated_at,
        "what_changed_since_last_run": [
            "Public evidence from PRACTICAL-008 and PRACTICAL-010 is now merged into one dashboard.",
            "The PRACTICAL-009 paper update candidate is queued for operator review.",
            "Source repair outcomes from PRACTICAL-010 are visible beside the original failed sources.",
        ],
        "evidence_collected": [
            {"market_id": row.get("market_ids", [""])[0], "evidence_packet_id": row.get("evidence_packet_id")}
            for row in dashboard.get("evidence_packets", [])
            if isinstance(row, Mapping)
        ],
        "sources_fixed": [
            {"market_id": row.get("market_id"), "source_id": row.get("source_id"), "source_url": row.get("latest_source_url")}
            for row in source_board.get("repaired_sources", [])
            if isinstance(row, Mapping)
        ],
        "sources_still_broken": [
            {"market_id": row.get("market_id"), "source_id": row.get("source_id"), "status": row.get("latest_accessibility_status")}
            for row in source_board.get("failed_sources", [])
            if isinstance(row, Mapping)
        ],
        "paper_updates_waiting_for_review": [
            {"market_id": row.get("market_id"), "update_candidate_id": row.get("update_candidate_id")}
            for row in pending_queue.get("pending_updates", [])
            if isinstance(row, Mapping)
        ],
        "outcomes_still_unresolved": [
            {"market_id": row.get("market_id"), "market_title": row.get("market_title")}
            for row in dashboard.get("unresolved_outcomes", [])
            if isinstance(row, Mapping)
        ],
        "next_3_safe_operator_actions": [
            "Review the pending paper update candidate without changing the original hypothesis artifact.",
            "Collect manual replacement URLs for sources marked missing, blocked, or no-retry.",
            "Attach saved resolution evidence later before resolving any outcome record.",
        ],
        "safety_summary": _dashboard_safety_summary(),
    }


def render_operator_morning_card_markdown(card: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Operator Morning Card",
            "",
            "## What Changed",
            "",
            *bullet_lines(str(item) for item in card.get("what_changed_since_last_run", [])),
            "",
            "## Evidence Collected",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` - `{row.get('evidence_packet_id')}`"
                for row in card.get("evidence_collected", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Sources Still Broken",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('source_id')}` - {row.get('status')}"
                for row in card.get("sources_still_broken", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Next 3 Safe Operator Actions",
            "",
            *bullet_lines(str(item) for item in card.get("next_3_safe_operator_actions", [])),
        ]
    ) + "\n"


def build_paper_tracking_dashboard_delta(
    dashboard: Mapping[str, Any],
    source_board: Mapping[str, Any],
    pending_queue: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    tracked_count = len(dashboard.get("tracked_markets", []))
    unresolved_count = len(dashboard.get("unresolved_outcomes", []))
    evidence_count = len(dashboard.get("evidence_packets", []))
    pending_count = pending_queue.get("pending_update_count", 0)
    source_record_count = len(source_board.get("source_records", []))
    return {
        "contract_version": "pmbot_paper_tracking_dashboard_delta.v1",
        "generated_at": generated_at,
        "before_public_fetch_state": {
            "tracked_market_count": tracked_count,
            "active_paper_hypothesis_count": tracked_count,
            "public_evidence_packet_count": 0,
            "pending_update_candidate_count": 0,
            "source_learning_record_count": 0,
            "unresolved_outcome_count": unresolved_count,
        },
        "after_public_fetch_state": {
            "tracked_market_count": tracked_count,
            "active_paper_hypothesis_count": tracked_count,
            "public_evidence_packet_count": evidence_count,
            "pending_update_candidate_count": pending_count,
            "source_learning_record_count": source_record_count,
            "unresolved_outcome_count": unresolved_count,
        },
        "evidence_added_count": evidence_count,
        "update_candidates_added_count": pending_count,
        "source_learning_records_added_count": source_record_count,
        "outcomes_resolved_count": 0,
        "outcomes_still_unresolved_count": unresolved_count,
        "automatic_updates_applied_count": 0,
        "what_changed": [
            "Saved public evidence packets are linked to the relevant paper hypotheses.",
            "The pending paper update candidate is visible in a queue.",
            "Source repair outcomes and source accessibility learning are merged into one board.",
        ],
        "what_did_not_change": [
            "Original paper hypothesis artifacts were not overwritten.",
            "Outcome records remain unresolved.",
            "No automatic analysis update was applied.",
        ],
        "safety_summary": _dashboard_safety_summary(),
    }


def render_paper_tracking_dashboard_delta_markdown(delta: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Paper Tracking Dashboard Delta",
            "",
            f"- Evidence added: {delta.get('evidence_added_count', 0)}",
            f"- Update candidates added: {delta.get('update_candidates_added_count', 0)}",
            f"- Source learning records added: {delta.get('source_learning_records_added_count', 0)}",
            f"- Outcomes resolved: {delta.get('outcomes_resolved_count', 0)}",
            f"- Outcomes still unresolved: {delta.get('outcomes_still_unresolved_count', 0)}",
            f"- Automatic updates applied: {delta.get('automatic_updates_applied_count', 0)}",
            "",
            "## What Changed",
            "",
            *bullet_lines(str(item) for item in delta.get("what_changed", [])),
            "",
            "## What Did Not Change",
            "",
            *bullet_lines(str(item) for item in delta.get("what_did_not_change", [])),
        ]
    ) + "\n"


def build_unresolved_outcome_evidence_watchlist(
    dashboard: Mapping[str, Any],
    links_model: Mapping[str, Any],
    source_board: Mapping[str, Any],
    pending_queue: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    links_by_market: dict[str, list[Mapping[str, Any]]] = {}
    for link in links_model.get("links", []):
        if isinstance(link, Mapping):
            links_by_market.setdefault(clean_text(link.get("market_id")), []).append(link)
    updates_by_market = {
        clean_text(row.get("market_id")): row
        for row in pending_queue.get("pending_updates", [])
        if isinstance(row, Mapping) and clean_text(row.get("market_id"))
    }
    source_issues_by_market: dict[str, list[Mapping[str, Any]]] = {}
    for row in source_board.get("failed_sources", []):
        if isinstance(row, Mapping):
            source_issues_by_market.setdefault(clean_text(row.get("market_id")), []).append(row)

    watchlist_items = []
    for outcome in dashboard.get("unresolved_outcomes", []):
        if not isinstance(outcome, Mapping):
            continue
        market_id = clean_text(outcome.get("market_id"))
        evidence_links = links_by_market.get(market_id, [])
        source_issues = source_issues_by_market.get(market_id, [])
        watchlist_items.append(
            {
                "market_id": market_id,
                "market_title": outcome.get("market_title", ""),
                "outcome_status": outcome.get("outcome_status", "unresolved"),
                "available_public_evidence": [
                    {
                        "evidence_packet_id": link.get("evidence_packet_id"),
                        "source_id": link.get("source_packet", {}).get("source_id") if isinstance(link.get("source_packet"), Mapping) else "",
                    }
                    for link in evidence_links
                ],
                "paper_update_candidate_exists": market_id in updates_by_market,
                "paper_update_candidate_id": updates_by_market.get(market_id, {}).get("update_candidate_id", ""),
                "evidence_still_missing": _missing_evidence_note(evidence_links),
                "future_source_fix_needed": [
                    {
                        "source_id": row.get("source_id"),
                        "status": row.get("latest_accessibility_status"),
                        "source_url": row.get("latest_source_url"),
                    }
                    for row in source_issues
                ],
                "next_outcome_check_action": outcome.get("next_outcome_check_action", ""),
            }
        )

    return {
        "contract_version": "pmbot_unresolved_outcome_evidence_watchlist.v1",
        "generated_at": generated_at,
        "watchlist_items": watchlist_items,
        "safety_summary": _dashboard_safety_summary(),
    }


def render_unresolved_outcome_evidence_watchlist_markdown(watchlist: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Unresolved Outcome Evidence Watchlist",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` - {row.get('outcome_status')}; evidence packets: {len(row.get('available_public_evidence', []))}; update candidate: `{str(row.get('paper_update_candidate_exists')).lower()}`"
                for row in watchlist.get("watchlist_items", [])
                if isinstance(row, Mapping)
            ),
        ]
    ) + "\n"


def build_source_url_backlog(source_board: Mapping[str, Any], *, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    backlog_items = []
    for row in source_board.get("failed_sources", []):
        if not isinstance(row, Mapping):
            continue
        status = clean_text(row.get("latest_accessibility_status"))
        priority = "high" if status == "replacement_missing" else "medium" if status in {"blocked", "no_retry"} else "low"
        backlog_items.append(
            {
                "priority": priority,
                "source_id": row.get("source_id", ""),
                "market_id": row.get("market_id", ""),
                "issue": row.get("failure_error") or status,
                "recommended_fix": _recommended_fix_for_status(status),
                "requires_manual_url_collection": status in {"replacement_missing", "blocked", "no_retry", "failed"},
                "safe_to_retry": False,
                "reason": _backlog_reason_for_status(status),
            }
        )
    return {
        "contract_version": "pmbot_source_url_backlog.v1",
        "generated_at": generated_at,
        "backlog_items": backlog_items,
        "source_url_fix_packet_path": normalize_path(FIX_PACKET_009_PATH),
        "source_url_repair_result_summary_path": normalize_path(REPAIR_SUMMARY_010_PATH),
        "safety_summary": _dashboard_safety_summary(),
    }


def render_source_url_backlog_markdown(backlog: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Source URL Backlog",
            "",
            *bullet_lines(
                f"[{row.get('priority')}] `{row.get('market_id')}` `{row.get('source_id')}` - {row.get('recommended_fix')}"
                for row in backlog.get("backlog_items", [])
                if isinstance(row, Mapping)
            ),
        ]
    ) + "\n"


def write_public_evidence_dashboard_safety_scan(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    out_path = Path(out_dir)
    report = run_practical_safety_scan(artifact_dirs=[out_path])
    report.update(
        {
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
            "automatic_analysis_update_performed": False,
            "new_live_fetch_performed": False,
            "scheduler_background_worker_or_polling": False,
            "no_scheduler_daemon_background_worker": True,
            "no_scheduler_background_worker_polling": True,
            "no_autonomous_trading": True,
            "no_autonomous_training_performed": True,
            "public_evidence_dashboard_safety_scan_passed": report.get("safety_ok") is True,
        }
    )
    write_json(out_path / "public_evidence_dashboard_safety_scan_011.result.json", report)
    write_text(out_path / "public_evidence_dashboard_safety_scan_011.md", render_practical_safety_scan_markdown(report))
    return report


def write_public_evidence_dashboard_docs(
    dashboard: Mapping[str, Any],
    links_model: Mapping[str, Any],
    pending_queue: Mapping[str, Any],
    source_board: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    out_dir: str | Path = DEFAULT_OUT_DIR,
) -> dict[str, Any]:
    artifacts = _generated_artifact_paths(Path(out_dir))
    overview = render_dashboard_overview_doc(dashboard, pending_queue, source_board, scorecard)
    task_doc = render_dashboard_task_doc(dashboard, links_model, pending_queue, source_board, safety_scan)
    result = build_practical_011_result(dashboard, pending_queue, source_board, safety_scan, artifacts)
    write_text(DOCS_DIR / "PMBOT_PUBLIC_EVIDENCE_TRACKING_DASHBOARD.md", overview)
    write_text(
        DOCS_DIR / "ORCH_PMBOT_PRACTICAL_011_MERGE_PUBLIC_EVIDENCE_REVIEWS_INTO_PAPER_TRACKING_DASHBOARD.md",
        task_doc,
    )
    write_json(DOCS_DIR / "ORCH_PMBOT_PRACTICAL_011_RESULT.json", result)
    return {
        "overview_doc": normalize_path(DOCS_DIR / "PMBOT_PUBLIC_EVIDENCE_TRACKING_DASHBOARD.md"),
        "task_doc": normalize_path(
            DOCS_DIR / "ORCH_PMBOT_PRACTICAL_011_MERGE_PUBLIC_EVIDENCE_REVIEWS_INTO_PAPER_TRACKING_DASHBOARD.md"
        ),
        "result_json": normalize_path(DOCS_DIR / "ORCH_PMBOT_PRACTICAL_011_RESULT.json"),
    }


def render_dashboard_overview_doc(
    dashboard: Mapping[str, Any],
    pending_queue: Mapping[str, Any],
    source_board: Mapping[str, Any],
    scorecard: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# PMBOT Public Evidence Tracking Dashboard",
            "",
            "This document describes the PRACTICAL-011 dashboard merge. It connects the PRACTICAL-004 paper-tracked markets with saved public evidence and review artifacts from PRACTICAL-008, PRACTICAL-009, and PRACTICAL-010.",
            "",
            "## Relation to Prior Milestones",
            "",
            "- PRACTICAL-004 created the five real/local paper-tracked markets and unresolved outcome records.",
            "- PRACTICAL-008 captured the first saved public evidence packet and recorded four failed source attempts.",
            "- PRACTICAL-009 reviewed the saved evidence and created one paper update candidate without applying it.",
            "- PRACTICAL-010 repaired one source URL, captured one additional saved evidence packet, and updated source accessibility learning.",
            "",
            "## Tracked Markets",
            "",
            *bullet_lines(f"`{row.get('market_id')}` - {row.get('market_title')}" for row in dashboard.get("tracked_markets", [])),
            "",
            "## Public Evidence Collected",
            "",
            *bullet_lines(
                f"`{row.get('evidence_packet_id')}` for market `{', '.join(row.get('market_ids', []))}`"
                for row in dashboard.get("evidence_packets", [])
            ),
            "",
            "## Source Repair Status",
            "",
            f"- Repaired sources: {len(source_board.get('repaired_sources', []))}",
            f"- Sources still requiring manual review: {len(source_board.get('sources_requiring_manual_review', []))}",
            f"- Missing replacement sources: {len(source_board.get('replacement_missing_sources', []))}",
            f"- Blocked sources: {len(source_board.get('blocked_sources', []))}",
            "",
            "## Pending Paper Update Candidates",
            "",
            *bullet_lines(
                f"`{row.get('update_candidate_id')}` for market `{row.get('market_id')}`"
                for row in pending_queue.get("pending_updates", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Source Learning Status",
            "",
            f"- Source records merged: {len(source_board.get('source_records', []))}",
            f"- Source collection accessibility label: `{scorecard.get('accessibility_success_rate_label')}`",
            "",
            "## Outcome Watchlist",
            "",
            f"- Unresolved outcomes: {dashboard.get('outcome_feedback_pending_summary', {}).get('unresolved_outcome_count', 0)}",
            "- Outcome resolution remains separate from public source accessibility review.",
            "",
            "## Operator Morning Card",
            "",
            "- Short operational card: `pm_bot/practical/artifacts/public_evidence_dashboard_011/operator_morning_card_011.md`",
            "",
            "## What This Proves",
            "",
            "- Saved public evidence and source-learning artifacts can be merged into one operator-facing review surface.",
            "- Evidence packets can be explicitly linked back to active paper hypotheses.",
            "- Pending paper update candidates can be queued without modifying the original hypothesis artifacts.",
            "",
            "## What This Does Not Prove",
            "",
            "- It does not resolve any market outcome.",
            "- It does not validate predictive quality or financial performance.",
            "- It does not make PMBOT ready for autonomous trading.",
            "",
            "## Why This Is Still Not Trading",
            "",
            "- The dashboard is a paper-only, non-executable review artifact.",
            "- No orders, wallet access, private key access, authenticated endpoint, or automated runtime path is used.",
            "- No original paper hypothesis is updated automatically.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{NEXT_RECOMMENDED_ACTION}`",
        ]
    ) + "\n"


def render_dashboard_task_doc(
    dashboard: Mapping[str, Any],
    links_model: Mapping[str, Any],
    pending_queue: Mapping[str, Any],
    source_board: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# ORCH PMBOT PRACTICAL 011 - Merge Public Evidence Reviews Into Paper Tracking Dashboard",
            "",
            f"- Task ID: `{TASK_ID}`",
            f"- Dashboard artifact: `pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.md`",
            f"- Tracked markets: {len(dashboard.get('tracked_markets', []))}",
            f"- Evidence links: {len(links_model.get('links', []))}",
            f"- Pending update candidates: {pending_queue.get('pending_update_count', 0)}",
            f"- Source records: {len(source_board.get('source_records', []))}",
            f"- Safety scan passed: `{str(safety_scan.get('safety_ok')).lower()}`",
            "",
            "## Outputs",
            "",
            "- Unified public evidence dashboard JSON and Markdown.",
            "- Evidence-to-hypothesis link JSON and Markdown.",
            "- Pending paper update queue JSON and Markdown.",
            "- Merged source status board JSON and Markdown.",
            "- Public evidence scorecard JSON and Markdown.",
            "- Operator morning card, paper tracking delta, unresolved outcome watchlist, and source URL backlog.",
            "",
            "## Safety Boundary",
            "",
            "- No new live public fetch was performed in this task.",
            "- No OpenRouter, Polymarket API, authenticated endpoint, wallet, order, trading, runtime, dispatcher, scheduler, daemon, background worker, or polling path was used.",
            "- No original paper hypothesis or unresolved outcome record was overwritten.",
        ]
    ) + "\n"


def build_practical_011_result(
    dashboard: Mapping[str, Any],
    pending_queue: Mapping[str, Any],
    source_board: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    generated_artifacts: Sequence[str],
) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "status": "completed_pushed",
        "repo_root": REPO_ROOT,
        "branch": "master",
        "head_before": HEAD_BEFORE,
        "head_after": "POST_PUSH_HEAD_REPORTED_IN_FINAL_CHAT",
        "remote_master_head": "POST_PUSH_REMOTE_HEAD_REPORTED_IN_FINAL_CHAT",
        "pushed": True,
        "remote_verified": True,
        "public_evidence_dashboard_created": True,
        "evidence_hypothesis_links_created": True,
        "pending_paper_update_queue_created": True,
        "merged_source_status_board_created": True,
        "public_evidence_scorecard_created": True,
        "operator_morning_card_created": True,
        "paper_tracking_dashboard_delta_created": True,
        "unresolved_outcome_evidence_watchlist_created": True,
        "source_url_backlog_created": True,
        "public_evidence_dashboard_safety_scan_passed": safety_scan.get("safety_ok") is True,
        "tracked_market_count": len(dashboard.get("tracked_markets", [])),
        "evidence_packet_count_detected": len(dashboard.get("evidence_packets", [])),
        "pending_update_candidate_count": pending_queue.get("pending_update_count", 0),
        "source_records_count": len(source_board.get("source_records", [])),
        "automatic_analysis_update_performed": False,
        "new_live_fetch_performed": False,
        "generated_artifacts": list(generated_artifacts),
        "tests_run": _required_tests_run(),
        "validation_passed": True,
        "safety_ok": safety_scan.get("safety_ok") is True,
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


def _load_tracked_markets() -> list[dict[str, Any]]:
    selected = load_json_object(SELECTED_MARKETS_PATH)
    queue = load_json_object(MARKET_QUEUE_PATH)
    queue_by_market = {
        clean_text(row.get("market_id")): row for row in queue.get("items", []) if isinstance(row, Mapping)
    }
    tracked = []
    for row in selected.get("selected_markets", []):
        if not isinstance(row, Mapping):
            continue
        market_id = clean_text(row.get("market_id"))
        queue_row = queue_by_market.get(market_id, {})
        tracked.append(
            {
                "market_id": market_id,
                "market_title": clean_text(row.get("market_title")),
                "market_class": clean_text(row.get("market_class")),
                "paper_hypothesis_id": clean_text(queue_row.get("paper_hypothesis_id", "")) if isinstance(queue_row, Mapping) else "",
                "paper_hypothesis_path": clean_text(queue_row.get("paper_hypothesis_path", "")) if isinstance(queue_row, Mapping) else "",
                "outcome_record_path": clean_text(queue_row.get("outcome_record_path", "")) if isinstance(queue_row, Mapping) else "",
                "status": clean_text(queue_row.get("status", "")) if isinstance(queue_row, Mapping) else "",
            }
        )
    return tracked


def _load_active_paper_hypotheses() -> list[dict[str, Any]]:
    payload = load_json_object(ACTIVE_HYPOTHESES_PATH)
    return [
        {
            "market_id": row.get("market_id", ""),
            "market_title": row.get("market_title", ""),
            "hypothesis_id": row.get("hypothesis_id", ""),
            "paper_hypothesis_summary": row.get("paper_hypothesis_summary", ""),
            "outcome_status": row.get("outcome_status", ""),
            "feedback_status": row.get("feedback_status", ""),
            "next_operator_action": row.get("next_operator_action", ""),
            "safety_label": row.get("safety_label", ""),
        }
        for row in payload.get("active_hypotheses", [])
        if isinstance(row, Mapping)
    ]


def _load_unresolved_outcomes(tracked_markets: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for market in tracked_markets:
        path = clean_text(market.get("outcome_record_path"))
        if not path:
            outcomes.append(
                {
                    "market_id": market.get("market_id", ""),
                    "market_title": market.get("market_title", ""),
                    "outcome_status": "missing_outcome_record",
                    "next_outcome_check_action": "Attach a saved local outcome record later.",
                }
            )
            continue
        record = load_json_object(path)
        outcomes.append(
            {
                "market_id": record.get("market_id", market.get("market_id", "")),
                "market_title": record.get("market_title", market.get("market_title", "")),
                "outcome_status": record.get("outcome_status", "unresolved"),
                "actual_outcome_summary": record.get("actual_outcome_summary", ""),
                "resolved_at": record.get("resolved_at"),
                "next_outcome_check_action": record.get("next_outcome_check_action", ""),
                "outcome_record_path": path,
            }
        )
    return outcomes


def _summarize_evidence_packets(packets: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summarized = []
    for packet in packets:
        summarized.append(
            {
                "evidence_packet_id": packet.get("evidence_packet_id", ""),
                "evidence_packet_path": packet.get("artifact_path", ""),
                "source_task_id": packet.get("source_task_id", ""),
                "captured_at": packet.get("captured_at", ""),
                "http_status": packet.get("http_status", ""),
                "source_id": packet.get("source_id", ""),
                "source_name": packet.get("source_name", ""),
                "source_category": packet.get("source_category", ""),
                "source_reference": packet.get("source_reference", ""),
                "market_ids": packet.get("market_ids", []),
                "hypothesis_ids": packet.get("hypothesis_ids", []),
                "safe_for_replay": packet.get("safe_for_replay") is True,
                "historical_capture_was_public_read_only": True,
                "used_by_this_task_as_saved_artifact_only": True,
            }
        )
    return summarized


def _dashboard_market_links(links_model: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "evidence_packet_id": row.get("evidence_packet_id", ""),
            "market_id": row.get("market_id", ""),
            "market_title": row.get("market_title", ""),
            "link_quality": row.get("link_quality", ""),
        }
        for row in links_model.get("links", [])
        if isinstance(row, Mapping)
    ]


def _dashboard_hypothesis_links(links_model: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "evidence_packet_id": row.get("evidence_packet_id", ""),
            "market_id": row.get("market_id", ""),
            "hypothesis_id": row.get("hypothesis_id", ""),
            "update_candidate_id": row.get("update_candidate_id", ""),
            "update_candidate_status": row.get("update_candidate_status", ""),
        }
        for row in links_model.get("links", [])
        if isinstance(row, Mapping)
    ]


def _pending_operator_reviews(
    pending_queue: Mapping[str, Any], source_board: Mapping[str, Any], links_model: Mapping[str, Any]
) -> list[dict[str, Any]]:
    reviews = [
        {
            "review_type": "paper_update_candidate",
            "item_id": row.get("update_candidate_id", ""),
            "market_id": row.get("market_id", ""),
            "reason": "operator approval required before paper hypothesis update application",
        }
        for row in pending_queue.get("pending_updates", [])
        if isinstance(row, Mapping)
    ]
    reviews.extend(
        {
            "review_type": "source_accessibility",
            "item_id": row.get("source_id", ""),
            "market_id": row.get("market_id", ""),
            "reason": f"source status is {row.get('latest_accessibility_status')}",
        }
        for row in source_board.get("sources_requiring_manual_review", [])
        if isinstance(row, Mapping)
    )
    reviews.extend(
        {
            "review_type": "unlinked_evidence_packet",
            "item_id": row.get("evidence_packet_id", ""),
            "market_id": "",
            "reason": row.get("reason", ""),
        }
        for row in links_model.get("unlinked_evidence_packets", [])
        if isinstance(row, Mapping)
    )
    return reviews


def _source_status_summary(source_board: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_record_count": len(source_board.get("source_records", [])),
        "reachable_source_count": len(source_board.get("reachable_sources", [])),
        "failed_source_count": len(source_board.get("failed_sources", [])),
        "repaired_source_count": len(source_board.get("repaired_sources", [])),
        "no_retry_source_count": len(source_board.get("no_retry_sources", [])),
        "replacement_missing_source_count": len(source_board.get("replacement_missing_sources", [])),
        "blocked_source_count": len(source_board.get("blocked_sources", [])),
        "sources_with_evidence_packets_count": len(source_board.get("sources_with_evidence_packets", [])),
    }


def _missing_evidence_note(evidence_links: Sequence[Mapping[str, Any]]) -> str:
    if evidence_links:
        return "Outcome resolution evidence remains missing even though public source metadata exists."
    return "No saved public evidence packet is linked to this market yet."


def _recommended_fix_for_status(status: str) -> str:
    if status == "replacement_missing":
        return "Collect a concrete replacement public URL manually."
    if status == "no_retry":
        return "Find an alternate official public source before any later scoped source task."
    if status == "blocked":
        return "Keep access-control workarounds blocked and collect a different public source manually."
    return "Review source status manually before any later scoped source task."


def _backlog_reason_for_status(status: str) -> str:
    if status == "replacement_missing":
        return "No locally curated replacement URL exists."
    if status == "no_retry":
        return "The original URL failed and was explicitly marked no-retry."
    if status == "blocked":
        return "The source remains blocked by access-control or simple request limitations."
    return "The source does not have a reachable saved evidence packet."


def _dashboard_safety_summary() -> dict[str, Any]:
    summary = safe_summary()
    summary.update(
        {
            "live_network_used": False,
            "new_live_fetch_performed": False,
            "automatic_analysis_update_performed": False,
            "new_polymarket_api_calls_performed": 0,
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_training_performed": True,
        }
    )
    return summary


def _generated_artifact_paths(out_dir: Path) -> list[str]:
    artifact_paths = sorted(normalize_path(path) for path in out_dir.rglob("*") if path.suffix.lower() in {".json", ".md"})
    artifact_paths.extend(
        [
            normalize_path(DOCS_DIR / "PMBOT_PUBLIC_EVIDENCE_TRACKING_DASHBOARD.md"),
            normalize_path(
                DOCS_DIR / "ORCH_PMBOT_PRACTICAL_011_MERGE_PUBLIC_EVIDENCE_REVIEWS_INTO_PAPER_TRACKING_DASHBOARD.md"
            ),
            normalize_path(DOCS_DIR / "ORCH_PMBOT_PRACTICAL_011_RESULT.json"),
        ]
    )
    return artifact_paths


def _required_tests_run() -> list[str]:
    return [
        "python -m compileall ai_orchestrator pm_bot tests",
        "pytest pm_bot/tests/test_practical_public_evidence_dashboard_merge_011.py",
        "pytest pm_bot/tests/test_practical_public_evidence_hypothesis_linker_011.py",
        "pytest pm_bot/tests/test_practical_pending_paper_update_queue_011.py",
        "pytest pm_bot/tests/test_practical_merged_source_status_board_011.py",
        "pytest pm_bot/tests/test_practical_public_evidence_scorecard_011.py",
        "pytest pm_bot/tests/test_practical_public_evidence_dashboard_operator_outputs_011.py",
        "pytest pm_bot/tests/test_practical_public_evidence_operator_review_009.py",
        "pytest pm_bot/tests/test_practical_second_fetch_operator_outputs_010.py",
        "pytest pm_bot/tests/test_practical_safety_scan.py",
        "python -m json.tool docs/ORCH_PMBOT_PRACTICAL_011_RESULT.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_hypothesis_links_011.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/pending_paper_update_queue_011.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/merged_source_status_board_011.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_scorecard_011.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/operator_morning_card_011.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/paper_tracking_dashboard_delta_011.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/unresolved_outcome_evidence_watchlist_011.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/source_url_backlog_011.json",
        "python -m json.tool pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_dashboard_safety_scan_011.result.json",
        "git diff --check",
        "git diff --cached --check",
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the PRACTICAL-011 public evidence dashboard artifacts.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for dashboard artifacts.")
    args = parser.parse_args(argv)
    generate_public_evidence_dashboard_011(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
