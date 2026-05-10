from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    normalize_path,
    safe_summary,
    write_json,
    write_text,
)
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan

DAILY_WORKFLOW_SUMMARY_CONTRACT_VERSION = "pmbot_daily_workflow_summary.v1"
OPERATOR_QUICKSTART_CONTRACT_VERSION = "pmbot_operator_quickstart_card.v1"
NEXT_TASK_DECISION_MATRIX_CONTRACT_VERSION = "pmbot_next_task_decision_matrix.v1"
CURRENT_STATUS_SNAPSHOT_CONTRACT_VERSION = "pmbot_current_practical_status_snapshot.v1"
SAFETY_BOUNDARY_REFERENCE_CONTRACT_VERSION = "pmbot_practical_safety_boundary_reference.v1"

TASK_ID_015 = "ORCH-PMBOT-PRACTICAL-015-PRACTICAL-OPERATOR-DAILY-WORKFLOW-RUNBOOK"
NEXT_RECOMMENDED_ACTION = "ORCH-PMBOT-PRACTICAL-016-ADD-NEXT-REAL-MARKET-PACKET-AND-RUN-DAILY-WORKFLOW"

ARTIFACT_DIR_015 = Path("pm_bot/practical/artifacts/daily_workflow_015")
DEFAULT_PUBLIC_DASHBOARD_PATH = Path(
    "pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.json"
)
DEFAULT_SOURCE_URL_BACKLOG_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/source_url_backlog_011.json")
DEFAULT_PAPER_SNAPSHOT_PATH = Path(
    "pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.json"
)
DEFAULT_OUTCOME_RECHECK_PATH = Path(
    "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.json"
)
DEFAULT_SOURCE_LEARNING_SCORECARD_PATH = Path(
    "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_update_013.json"
)
DEFAULT_FEEDBACK_DASHBOARD_PATH = Path(
    "pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.json"
)


def build_daily_workflow_summary(
    *,
    public_dashboard_path: str | Path = DEFAULT_PUBLIC_DASHBOARD_PATH,
    source_url_backlog_path: str | Path = DEFAULT_SOURCE_URL_BACKLOG_PATH,
    paper_snapshot_path: str | Path = DEFAULT_PAPER_SNAPSHOT_PATH,
    outcome_recheck_path: str | Path = DEFAULT_OUTCOME_RECHECK_PATH,
    source_learning_scorecard_path: str | Path = DEFAULT_SOURCE_LEARNING_SCORECARD_PATH,
    feedback_dashboard_path: str | Path = DEFAULT_FEEDBACK_DASHBOARD_PATH,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    public_dashboard = load_json_object(public_dashboard_path, label="PRACTICAL-011 public evidence dashboard")
    source_backlog = load_json_object(source_url_backlog_path, label="PRACTICAL-011 source URL backlog")
    paper_snapshot = load_json_object(paper_snapshot_path, label="PRACTICAL-012 paper tracking snapshot")
    outcome_recheck = load_json_object(outcome_recheck_path, label="PRACTICAL-013 outcome recheck queue")
    source_scorecard = load_json_object(source_learning_scorecard_path, label="PRACTICAL-013 source learning scorecard")
    feedback_dashboard = load_json_object(feedback_dashboard_path, label="PRACTICAL-014 feedback readiness dashboard")

    tracked_markets = _tracked_markets(paper_snapshot, public_dashboard)
    active_hypotheses = _mapping_rows(paper_snapshot.get("active_paper_hypotheses"))
    applied_updates = _mapping_rows(paper_snapshot.get("applied_paper_updates"))
    unresolved_outcomes = _unresolved_outcomes(paper_snapshot, outcome_recheck)
    evidence_packets = _mapping_rows(public_dashboard.get("evidence_packets"))
    source_records = _mapping_rows(source_scorecard.get("source_records"))
    source_backlog_items = _mapping_rows(source_backlog.get("backlog_items"))
    feedback_ready_count = int(feedback_dashboard.get("feedback_ready_count", 0))

    dashboard_files = dashboard_files_to_open()
    summary = {
        "contract_version": DAILY_WORKFLOW_SUMMARY_CONTRACT_VERSION,
        "summary_id": "daily-workflow-summary-015",
        "generated_at": generated_at,
        "tracked_market_count": len(tracked_markets),
        "tracked_markets": tracked_markets,
        "active_paper_hypotheses_count": len(active_hypotheses),
        "applied_paper_update_count": len(applied_updates),
        "unresolved_outcome_count": len(unresolved_outcomes),
        "feedback_ready_count": feedback_ready_count,
        "public_evidence_packet_count": len(evidence_packets),
        "source_records_count": len(source_records),
        "source_url_backlog_count": len(source_backlog_items),
        "blocked_items": _blocked_items(
            unresolved_count=len(unresolved_outcomes),
            feedback_ready_count=feedback_ready_count,
            source_backlog_count=len(source_backlog_items),
        ),
        "next_operator_actions": _next_operator_actions(len(unresolved_outcomes), len(source_backlog_items)),
        "dashboard_files_to_open": dashboard_files,
        "manual_actions_required": _manual_actions_required(source_backlog_items),
        "safe_local_commands": safe_local_commands(),
        "prohibited_actions": prohibited_actions(),
        "safety_summary": daily_workflow_safety_summary(),
        "recent_changes": [
            "PRACTICAL-014 prepared pending manual feedback packets for all five tracked markets.",
            "PRACTICAL-013 created the outcome recheck queue and source learning scorecard update.",
            "PRACTICAL-012 applied one operator-approved paper tracking update to a versioned snapshot.",
            "PRACTICAL-011 merged two saved public evidence packets into the dashboard.",
        ],
        "source_status": {
            "source_records_count": len(source_records),
            "source_url_backlog_count": len(source_backlog_items),
            "sources_with_saved_evidence_count": len([row for row in source_records if row.get("has_evidence_packet") is True]),
            "blocked_source_count": len([row for row in source_records if row.get("source_usefulness_label") == "blocked"]),
        },
        "paper_updates": [
            {
                "applied_update_id": clean_text(row.get("applied_update_id")),
                "market_id": clean_text(row.get("market_id")),
                "outcome_status_after_update": clean_text(row.get("outcome_status_after_update")),
            }
            for row in applied_updates
        ],
    }
    return summary


def run_daily_workflow_summary(
    *,
    out_json_path: str | Path,
    out_md_path: str | Path,
    public_dashboard_path: str | Path = DEFAULT_PUBLIC_DASHBOARD_PATH,
    source_url_backlog_path: str | Path = DEFAULT_SOURCE_URL_BACKLOG_PATH,
    paper_snapshot_path: str | Path = DEFAULT_PAPER_SNAPSHOT_PATH,
    outcome_recheck_path: str | Path = DEFAULT_OUTCOME_RECHECK_PATH,
    source_learning_scorecard_path: str | Path = DEFAULT_SOURCE_LEARNING_SCORECARD_PATH,
    feedback_dashboard_path: str | Path = DEFAULT_FEEDBACK_DASHBOARD_PATH,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    summary = build_daily_workflow_summary(
        public_dashboard_path=public_dashboard_path,
        source_url_backlog_path=source_url_backlog_path,
        paper_snapshot_path=paper_snapshot_path,
        outcome_recheck_path=outcome_recheck_path,
        source_learning_scorecard_path=source_learning_scorecard_path,
        feedback_dashboard_path=feedback_dashboard_path,
        generated_at=generated_at,
    )
    write_json(out_json_path, summary)
    write_text(out_md_path, render_daily_workflow_summary_markdown(summary))
    return summary


def render_daily_workflow_summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Daily Operator Summary",
        "",
        f"- Tracked markets: {summary.get('tracked_market_count')}",
        f"- Unresolved outcomes: {summary.get('unresolved_outcome_count')}",
        f"- Feedback ready: {summary.get('feedback_ready_count')}",
        f"- Public evidence packets: {summary.get('public_evidence_packet_count')}",
        f"- Source URL backlog: {summary.get('source_url_backlog_count')}",
        "",
        "## What changed recently",
        "",
        *bullet_lines(str(item) for item in summary.get("recent_changes", [])),
        "",
        "## Markets being tracked",
        "",
    ]
    for market in _mapping_rows(summary.get("tracked_markets")):
        lines.append(
            f"- `{market.get('market_id')}` `{market.get('market_class')}` - {market.get('market_title')} "
            f"({market.get('status')})"
        )
    lines.extend(
        [
            "",
            "## Evidence and source status",
            "",
            f"- Saved public evidence packets: {summary.get('public_evidence_packet_count')}",
            f"- Source records: {summary.get('source_records_count')}",
            f"- Source URLs needing manual repair: {summary.get('source_url_backlog_count')}",
            "",
            "## Paper updates",
            "",
            f"- Applied paper updates: {summary.get('applied_paper_update_count')}",
            *bullet_lines(
                f"`{row.get('market_id')}` - `{row.get('applied_update_id')}`"
                for row in _mapping_rows(summary.get("paper_updates"))
            ),
            "",
            "## Outcome recheck status",
            "",
            f"- Unresolved outcomes: {summary.get('unresolved_outcome_count')}",
            "- Outcome status stays unresolved until saved local resolution evidence exists.",
            "",
            "## Feedback readiness",
            "",
            f"- Feedback-ready packets: {summary.get('feedback_ready_count')}",
            "- Feedback packets are pending because every tracked outcome remains unresolved.",
            "",
            "## What to open first",
            "",
        ]
    )
    for row in _mapping_rows(summary.get("dashboard_files_to_open")):
        lines.append(f"- `{row.get('path')}` - {row.get('why')}")
    lines.extend(
        [
            "",
            "## Next safe actions",
            "",
            *bullet_lines(str(item) for item in summary.get("next_operator_actions", [])),
            "",
            "## Prohibited actions",
            "",
            *bullet_lines(str(item) for item in summary.get("prohibited_actions", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def dashboard_files_to_open() -> list[dict[str, Any]]:
    rows = [
        (
            1,
            "Operator quickstart",
            ARTIFACT_DIR_015 / "operator_quickstart_card_015.md",
            "One-screen daily entry point.",
        ),
        (
            2,
            "Daily summary",
            ARTIFACT_DIR_015 / "daily_workflow_summary_015.md",
            "Current counts, blockers, and next safe actions.",
        ),
        (
            3,
            "Feedback readiness dashboard",
            "pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.md",
            "Shows which feedback packets are pending or ready.",
        ),
        (
            4,
            "Outcome recheck queue",
            "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.md",
            "Shows unresolved markets and recheck priority.",
        ),
        (
            5,
            "Source learning scorecard",
            "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_operator_view_013.md",
            "Shows reachable, repaired, missing, and blocked source records.",
        ),
        (
            6,
            "Paper tracking snapshot",
            "pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.md",
            "Shows active paper hypotheses and applied paper updates.",
        ),
        (
            7,
            "Public evidence dashboard",
            "pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.md",
            "Shows saved public evidence packets and source status.",
        ),
    ]
    return [
        {
            "priority": priority,
            "label": label,
            "path": normalize_path(path),
            "exists": Path(path).exists(),
            "why": why,
        }
        for priority, label, path, why in rows
    ]


def safe_local_commands() -> list[str]:
    return [
        "python -m pm_bot.practical.daily_workflow_summary --out-json pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.json --out-md pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.md",
        "python -m pm_bot.practical.practical_command_catalog --out-json pm_bot/practical/artifacts/daily_workflow_015/practical_command_catalog_015.json --out-md pm_bot/practical/artifacts/daily_workflow_015/practical_command_catalog_015.md",
        "python -m pm_bot.practical.practical_workflow_index --out-json pm_bot/practical/artifacts/daily_workflow_015/practical_workflow_index_015.json --out-md pm_bot/practical/artifacts/daily_workflow_015/practical_workflow_index_015.md",
        "python -m pm_bot.practical.practical_daily_checklist --out-json pm_bot/practical/artifacts/daily_workflow_015/practical_daily_checklist_015.json --out-md pm_bot/practical/artifacts/daily_workflow_015/practical_daily_checklist_015.md",
        "python -m pm_bot.practical.practical_safety_scan --artifact-dir pm_bot/practical/artifacts/daily_workflow_015 --out-json pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_safety_scan_015.result.json --out-md pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_safety_scan_015.md",
    ]


def prohibited_actions() -> list[str]:
    return [
        "No wallet, private key, signing, or real-money path access.",
        "No order placement, trading endpoint, or authenticated endpoint.",
        "No OpenRouter call unless a separate approved task explicitly allows it.",
        "No Polymarket API call unless a separate approved task explicitly allows it.",
        "No scheduler, daemon, background worker, watcher, polling loop, or unattended automation.",
        "No market recommendation, probability, EV, edge, confidence, or side-selection output.",
        "No invented outcomes and no resolved status for unresolved markets.",
        "No runtime, dispatcher, browser automation, or autonomous execution path changes.",
    ]


def daily_workflow_safety_summary() -> dict[str, Any]:
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
            "paper_only": True,
        }
    )
    return summary


def build_operator_quickstart_card(summary: Mapping[str, Any], *, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": OPERATOR_QUICKSTART_CONTRACT_VERSION,
        "card_id": "operator-quickstart-card-015",
        "generated_at": generated_at,
        "open_this_first": [
            "pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.md",
            "pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.md",
            "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.md",
        ],
        "check_these_3_numbers": [
            {"name": "unresolved_outcome_count", "value": summary.get("unresolved_outcome_count")},
            {"name": "feedback_ready_count", "value": summary.get("feedback_ready_count")},
            {"name": "source_url_backlog_count", "value": summary.get("source_url_backlog_count")},
        ],
        "if_outcome_resolved": [
            "Open that market's manual outcome packet under manual_outcome_feedback_014/markets/<market_id>/.",
            "Fill only from saved local resolution evidence.",
            "Run the feedback evaluator in a separate paper-only task after review.",
        ],
        "if_source_broken": [
            "Open source_url_backlog_011.md.",
            "Collect a replacement public source manually in local notes.",
            "Use a later approved public-source task before any fetch.",
        ],
        "if_new_market_needed": [
            "Prepare a local market packet under pm_bot/llm/manual_packet_batch/.",
            "Run local packet normalization and local analysis only.",
            f"Prefer next task `{NEXT_RECOMMENDED_ACTION}`.",
        ],
        "never_do_this": prohibited_actions(),
        "safety_summary": daily_workflow_safety_summary(),
    }


def render_operator_quickstart_card_markdown(card: Mapping[str, Any]) -> str:
    checks = [
        f"{row.get('name')}: {row.get('value')}"
        for row in _mapping_rows(card.get("check_these_3_numbers"))
    ]
    return "\n".join(
        [
            "# Operator Quickstart Card 015",
            "",
            "## Open this first",
            "",
            *bullet_lines(str(item) for item in card.get("open_this_first", [])),
            "",
            "## Check these 3 numbers",
            "",
            *bullet_lines(checks),
            "",
            "## If outcome resolved, do this",
            "",
            *bullet_lines(str(item) for item in card.get("if_outcome_resolved", [])),
            "",
            "## If source broken, do this",
            "",
            *bullet_lines(str(item) for item in card.get("if_source_broken", [])),
            "",
            "## If new market needed, do this",
            "",
            *bullet_lines(str(item) for item in card.get("if_new_market_needed", [])),
            "",
            "## Never do this",
            "",
            *bullet_lines(str(item) for item in card.get("never_do_this", [])[:6]),
        ]
    ) + "\n"


def build_next_task_decision_matrix(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    rows = [
        {
            "condition": "Need more real markets",
            "recommended_next_task_id": NEXT_RECOMMENDED_ACTION,
            "why": "The current loop tracks five markets; more local packets improve operator coverage without live access.",
            "blocked_until": "A safe local packet exists with title, rules, source placeholders, and unresolved outcome placeholder.",
            "safety_notes": "Local-only packet import and paper tracking only.",
        },
        {
            "condition": "Need outcome resolution feedback",
            "recommended_next_task_id": "ORCH-PMBOT-PRACTICAL-017-PROCESS-FIRST-RESOLVED-OUTCOME-FEEDBACK-PACKET",
            "why": "Feedback is blocked until a saved local resolution record exists for at least one market.",
            "blocked_until": "A real local resolution record is saved and manually reviewed.",
            "safety_notes": "Never invent outcome fields.",
        },
        {
            "condition": "Need source URL repair",
            "recommended_next_task_id": "ORCH-PMBOT-PRACTICAL-018-SOURCE-URL-REPAIR-PACKET-LOCAL-ONLY",
            "why": "Three source records still need manual replacement or alternate official sources.",
            "blocked_until": "Operator provides local replacement candidates.",
            "safety_notes": "No access-control workaround, cookies, profiles, or browser automation.",
        },
        {
            "condition": "Need another controlled public fetch",
            "recommended_next_task_id": "ORCH-PMBOT-PRACTICAL-019-CONTROLLED-PUBLIC-FETCH-PACKET-SEPARATE-APPROVAL",
            "why": "Fetch work is outside the daily runbook and needs explicit separate approval.",
            "blocked_until": "A scoped manifest and approval packet exist.",
            "safety_notes": "Not part of the daily workflow.",
        },
        {
            "condition": "Need practical UI/report polishing",
            "recommended_next_task_id": "ORCH-PMBOT-PRACTICAL-020-LOCAL-REPORT-POLISHING",
            "why": "The operator surface can be refined after this runbook is used.",
            "blocked_until": "Operator identifies which report is confusing.",
            "safety_notes": "Documentation and local artifact rendering only.",
        },
        {
            "condition": "Need risk engine design later",
            "recommended_next_task_id": "ORCH-PMBOT-PRACTICAL-LATER-RISK-ENGINE-DESIGN-PAPER-ONLY",
            "why": "Risk design belongs after reliable source and outcome feedback loops exist.",
            "blocked_until": "Several resolved outcome feedback packets exist.",
            "safety_notes": "Design only; no execution path.",
        },
        {
            "condition": "Need execution mock later",
            "recommended_next_task_id": "ORCH-PMBOT-PRACTICAL-LATER-EXECUTION-MOCK-PAPER-ONLY",
            "why": "A mock can test accounting language after risk design, without real execution.",
            "blocked_until": "Risk design and paper-only accounting constraints are written.",
            "safety_notes": "No wallet, signing, or real-money action.",
        },
        {
            "condition": "Do not start real trading yet",
            "recommended_next_task_id": "BLOCKED-REAL-TRADING-NOT-A-PRACTICAL-015-OUTCOME",
            "why": "The current system has unresolved outcomes and no proven feedback loop.",
            "blocked_until": "Separate explicit approval after many safety and validation milestones.",
            "safety_notes": "Real autonomous trading progress remains 0%.",
        },
    ]
    return {
        "contract_version": NEXT_TASK_DECISION_MATRIX_CONTRACT_VERSION,
        "matrix_id": "next-task-decision-matrix-015",
        "generated_at": generated_at,
        "rows": rows,
        "safety_summary": daily_workflow_safety_summary(),
    }


def render_next_task_decision_matrix_markdown(matrix: Mapping[str, Any]) -> str:
    lines = ["# Next Task Decision Matrix 015", ""]
    for row in _mapping_rows(matrix.get("rows")):
        lines.extend(
            [
                f"## {row.get('condition')}",
                "",
                f"- Next task: `{row.get('recommended_next_task_id')}`",
                f"- Why: {row.get('why')}",
                f"- Blocked until: {row.get('blocked_until')}",
                f"- Safety: {row.get('safety_notes')}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_current_practical_status_snapshot(
    summary: Mapping[str, Any], *, generated_at: str = GENERATED_AT
) -> dict[str, Any]:
    return {
        "contract_version": CURRENT_STATUS_SNAPSHOT_CONTRACT_VERSION,
        "snapshot_id": "current-practical-status-snapshot-015",
        "generated_at": generated_at,
        "practical_analysis_loop_progress_estimate": "40% local paper-analysis loop operating with five tracked markets",
        "source_learning_feedback_loop_progress_estimate": "25% source status tracked; outcome feedback not yet available",
        "controlled_public_read_only_progress_estimate": "20% two saved public evidence packets from earlier approved tasks",
        "real_autonomous_trading_progress_estimate": "0%",
        "tracked_market_count": summary.get("tracked_market_count"),
        "unresolved_outcome_count": summary.get("unresolved_outcome_count"),
        "feedback_ready_count": summary.get("feedback_ready_count"),
        "evidence_packet_count": summary.get("public_evidence_packet_count"),
        "applied_paper_update_count": summary.get("applied_paper_update_count"),
        "source_records_count": summary.get("source_records_count"),
        "next_major_milestone": NEXT_RECOMMENDED_ACTION,
        "blockers_before_real_trading": [
            "Resolved outcome feedback packets are missing.",
            "Source accuracy feedback is not validated against resolved outcomes.",
            "Source URL backlog remains open.",
            "Risk and execution design are not approved.",
            "No wallet, order, or autonomous execution approval exists.",
        ],
        "safety_summary": daily_workflow_safety_summary(),
    }


def render_current_practical_status_snapshot_markdown(snapshot: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Current PMBOT Practical Status Snapshot 015",
            "",
            f"- Practical analysis loop: {snapshot.get('practical_analysis_loop_progress_estimate')}",
            f"- Source learning loop: {snapshot.get('source_learning_feedback_loop_progress_estimate')}",
            f"- Controlled public read-only loop: {snapshot.get('controlled_public_read_only_progress_estimate')}",
            f"- Real autonomous trading: {snapshot.get('real_autonomous_trading_progress_estimate')}",
            f"- Tracked markets: {snapshot.get('tracked_market_count')}",
            f"- Unresolved outcomes: {snapshot.get('unresolved_outcome_count')}",
            f"- Feedback ready: {snapshot.get('feedback_ready_count')}",
            f"- Evidence packets: {snapshot.get('evidence_packet_count')}",
            f"- Applied paper updates: {snapshot.get('applied_paper_update_count')}",
            f"- Source records: {snapshot.get('source_records_count')}",
            "",
            "## Next major milestone",
            "",
            f"- `{snapshot.get('next_major_milestone')}`",
            "",
            "## Blockers before real trading",
            "",
            *bullet_lines(str(item) for item in snapshot.get("blockers_before_real_trading", [])),
        ]
    ) + "\n"


def build_practical_safety_boundary_reference(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    boundaries = [
        "No wallet or private key access.",
        "No order placement.",
        "No trading endpoints.",
        "No real-money action.",
        "No authenticated endpoint.",
        "No OpenRouter call unless separately approved.",
        "No Polymarket API call unless separately approved.",
        "No scheduler, daemon, background worker, watcher, polling loop, or unattended automation.",
        "No market recommendations, probability, EV, edge, confidence, or side-selection output.",
        "Paper-only tracking only.",
    ]
    return {
        "contract_version": SAFETY_BOUNDARY_REFERENCE_CONTRACT_VERSION,
        "reference_id": "practical-safety-boundary-reference-015",
        "generated_at": generated_at,
        "boundaries": boundaries,
        "required_false_flags": {
            "live_network_used": False,
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "outcome_resolution_invented": False,
        },
        "required_zero_counts": {
            "openrouter_calls_performed": 0,
            "new_polymarket_api_calls_performed": 0,
        },
        "required_true_flags": {
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_trading": True,
            "paper_only": True,
        },
        "safety_summary": daily_workflow_safety_summary(),
    }


def render_practical_safety_boundary_reference_markdown(reference: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Practical Safety Boundary Reference 015",
            "",
            "## Boundaries",
            "",
            *bullet_lines(str(item) for item in reference.get("boundaries", [])),
            "",
            "## Required false flags",
            "",
            *bullet_lines(f"`{key}`: `{str(value).lower()}`" for key, value in reference.get("required_false_flags", {}).items()),
            "",
            "## Required zero counts",
            "",
            *bullet_lines(f"`{key}`: `{value}`" for key, value in reference.get("required_zero_counts", {}).items()),
        ]
    ) + "\n"


def write_daily_workflow_support_artifacts_015(
    *, out_dir: str | Path = ARTIFACT_DIR_015, generated_at: str = GENERATED_AT
) -> dict[str, Any]:
    out_path = Path(out_dir)
    summary = build_daily_workflow_summary(generated_at=generated_at)

    quickstart = build_operator_quickstart_card(summary, generated_at=generated_at)
    matrix = build_next_task_decision_matrix(generated_at=generated_at)
    status = build_current_practical_status_snapshot(summary, generated_at=generated_at)
    boundary = build_practical_safety_boundary_reference(generated_at=generated_at)

    write_json(out_path / "operator_quickstart_card_015.json", quickstart)
    write_text(out_path / "operator_quickstart_card_015.md", render_operator_quickstart_card_markdown(quickstart))
    write_json(out_path / "next_task_decision_matrix_015.json", matrix)
    write_text(out_path / "next_task_decision_matrix_015.md", render_next_task_decision_matrix_markdown(matrix))
    write_json(out_path / "current_practical_status_snapshot_015.json", status)
    write_text(out_path / "current_practical_status_snapshot_015.md", render_current_practical_status_snapshot_markdown(status))
    write_json(out_path / "practical_safety_boundary_reference_015.json", boundary)
    write_text(
        out_path / "practical_safety_boundary_reference_015.md",
        render_practical_safety_boundary_reference_markdown(boundary),
    )
    return {
        "summary": summary,
        "quickstart": quickstart,
        "next_task_decision_matrix": matrix,
        "current_practical_status_snapshot": status,
        "safety_boundary_reference": boundary,
    }


def write_daily_workflow_safety_scan_015(
    *, artifact_dir: str | Path = ARTIFACT_DIR_015, generated_at: str = GENERATED_AT
) -> dict[str, Any]:
    artifact_path = Path(artifact_dir)
    report = run_practical_safety_scan(artifact_dirs=[artifact_path])
    report.update(daily_workflow_safety_summary())
    report.update(
        {
            "generated_at": generated_at,
            "safety_ok": report.get("safety_ok") is True,
            "issue_count": report.get("issue_count", 0),
            "daily_workflow_safety_scan_passed": report.get("safety_ok") is True,
        }
    )
    write_json(artifact_path / "daily_workflow_safety_scan_015.result.json", report)
    write_text(artifact_path / "daily_workflow_safety_scan_015.md", render_daily_workflow_safety_scan_markdown(report))
    return report


def render_daily_workflow_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    base = render_practical_safety_scan_markdown(report)
    return (
        base
        + "\n## PRACTICAL-015 Confirmations\n\n"
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


def _tracked_markets(paper_snapshot: Mapping[str, Any], public_dashboard: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = _mapping_rows(paper_snapshot.get("tracked_markets")) or _mapping_rows(public_dashboard.get("tracked_markets"))
    return [
        {
            "market_id": clean_text(row.get("market_id")),
            "market_title": clean_text(row.get("market_title")),
            "market_class": clean_text(row.get("market_class")),
            "status": clean_text(row.get("status")),
            "paper_hypothesis_id": clean_text(row.get("paper_hypothesis_id")),
            "paper_hypothesis_path": clean_text(row.get("paper_hypothesis_path")),
            "outcome_record_path": clean_text(row.get("outcome_record_path")),
        }
        for row in rows
    ]


def _unresolved_outcomes(paper_snapshot: Mapping[str, Any], outcome_recheck: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    unresolved = _mapping_rows(paper_snapshot.get("unresolved_outcomes"))
    if unresolved:
        return unresolved
    return [row for row in _mapping_rows(outcome_recheck.get("recheck_items")) if row.get("outcome_status") == "unresolved"]


def _blocked_items(*, unresolved_count: int, feedback_ready_count: int, source_backlog_count: int) -> list[dict[str, Any]]:
    blocked = []
    if unresolved_count:
        blocked.append(
            {
                "item": "outcome_feedback",
                "count": unresolved_count,
                "reason": "Outcome feedback is blocked until saved local resolution evidence exists.",
            }
        )
    if feedback_ready_count == 0:
        blocked.append(
            {
                "item": "feedback_packets",
                "count": 0,
                "reason": "No manual feedback packet is ready yet.",
            }
        )
    if source_backlog_count:
        blocked.append(
            {
                "item": "source_url_backlog",
                "count": source_backlog_count,
                "reason": "Some source URLs require manual repair before any later scoped source task.",
            }
        )
    blocked.append(
        {
            "item": "real_autonomous_trading",
            "count": 0,
            "reason": "Real trading remains outside the approved practical workflow.",
        }
    )
    return blocked


def _next_operator_actions(unresolved_count: int, source_backlog_count: int) -> list[str]:
    actions = [
        "Open the operator quickstart card, daily summary, feedback readiness dashboard, and outcome recheck queue.",
        "Check unresolved outcome count, feedback-ready count, and source URL backlog count.",
    ]
    if unresolved_count:
        actions.append("Leave outcomes unresolved unless saved local resolution evidence exists.")
    if source_backlog_count:
        actions.append("Collect replacement source URLs manually before a separate approved source task.")
    actions.append(f"Use `{NEXT_RECOMMENDED_ACTION}` for the next local-only expansion task.")
    return actions


def _manual_actions_required(source_backlog_items: Sequence[Mapping[str, Any]]) -> list[str]:
    actions = [
        "Review dashboard files directly; do not rely on memory.",
        "Fill manual outcome packets only after saved local resolution evidence exists.",
        "Choose paper result labels only after manual review.",
    ]
    for row in source_backlog_items:
        market_id = clean_text(row.get("market_id"))
        if market_id:
            actions.append(f"Repair source URL manually for market `{market_id}` before any later scoped source task.")
    return actions


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the PMBOT practical daily workflow summary from local artifacts.")
    parser.add_argument("--out-json", required=True, help="Output summary JSON.")
    parser.add_argument("--out-md", required=True, help="Output summary Markdown.")
    parser.add_argument("--public-evidence-dashboard", default=str(DEFAULT_PUBLIC_DASHBOARD_PATH))
    parser.add_argument("--source-url-backlog", default=str(DEFAULT_SOURCE_URL_BACKLOG_PATH))
    parser.add_argument("--paper-tracking-snapshot", default=str(DEFAULT_PAPER_SNAPSHOT_PATH))
    parser.add_argument("--outcome-recheck-queue", default=str(DEFAULT_OUTCOME_RECHECK_PATH))
    parser.add_argument("--source-learning-scorecard", default=str(DEFAULT_SOURCE_LEARNING_SCORECARD_PATH))
    parser.add_argument("--feedback-readiness-dashboard", default=str(DEFAULT_FEEDBACK_DASHBOARD_PATH))
    args = parser.parse_args(argv)
    run_daily_workflow_summary(
        out_json_path=args.out_json,
        out_md_path=args.out_md,
        public_dashboard_path=args.public_evidence_dashboard,
        source_url_backlog_path=args.source_url_backlog,
        paper_snapshot_path=args.paper_tracking_snapshot,
        outcome_recheck_path=args.outcome_recheck_queue,
        source_learning_scorecard_path=args.source_learning_scorecard,
        feedback_dashboard_path=args.feedback_readiness_dashboard,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
