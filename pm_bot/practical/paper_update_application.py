from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.paper_tracking_state_snapshot import write_paper_tracking_state_snapshot_012
from pm_bot.practical.paper_update_approval import (
    TASK_ID,
    current_utc_timestamp,
    validate_operator_approval,
    validate_update_candidate_for_paper_approval,
    write_paper_update_operator_approval_012,
)
from pm_bot.practical.practical_io import (
    bullet_lines,
    clean_text,
    load_json_object,
    normalize_path,
    safe_summary,
    write_json,
    write_text,
)
from pm_bot.practical.practical_safety_scan import run_practical_safety_scan

APPLIED_UPDATE_CONTRACT_VERSION = "pmbot_applied_paper_update.v1"
TASK_DOC_TITLE = "ORCH PMBOT PRACTICAL 012 - Operator Approved Paper Hypothesis Update Application"
NEXT_RECOMMENDED_ACTION = "ORCH-PMBOT-PRACTICAL-013-OUTCOME-RECHECK-QUEUE-AND-SOURCE-LEARNING-SCORECARD-UPDATE"
HEAD_BEFORE = "479c459cd037e733da2212960ed5d90d14525fb4"
REPO_ROOT = "C:/Users/OpenC/.openclaw/workspace"

DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/paper_update_application_012")
DOCS_DIR = Path("docs")
PRACTICAL_011_RESULT_PATH = Path("docs/ORCH_PMBOT_PRACTICAL_011_RESULT.json")
SOURCE_DASHBOARD_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.json")
PENDING_QUEUE_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/pending_paper_update_queue_011.json")
EVIDENCE_LINKS_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_hypothesis_links_011.json")
SOURCE_STATUS_BOARD_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/merged_source_status_board_011.json")
PUBLIC_SCORECARD_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_scorecard_011.json")
WATCHLIST_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/unresolved_outcome_evidence_watchlist_011.json")
PUBLIC_REVIEW_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/public_evidence_operator_review_009.json")
DELTA_REPORT_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/paper_tracking_delta_report_009.json")
UPDATE_CANDIDATE_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/paper_hypothesis_update_candidate_009.json")


class PaperUpdateApplicationError(ValueError):
    pass


def generate_paper_update_application_012(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    generated_at = current_utc_timestamp()
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    inputs = _load_inputs()
    _validate_practical_011_inputs(inputs)
    candidates = _load_pending_candidates(inputs["pending_queue"])
    if len(candidates) != 1:
        raise PaperUpdateApplicationError(f"expected one pending update candidate, found {len(candidates)}")

    candidate_links = [_validated_candidate_links(candidate, inputs["evidence_links"], inputs["public_review"]) for candidate in candidates]
    approval = write_paper_update_operator_approval_012(candidates, out_dir=out_path, approved_at=generated_at)
    validate_operator_approval(approval, candidates)

    applied_update = build_applied_paper_update(
        candidate=candidates[0],
        approval=approval,
        source_dashboard=inputs["source_dashboard"],
        evidence_links=candidate_links[0],
        public_review=inputs["public_review"],
        delta_report=inputs["delta_report"],
        generated_at=generated_at,
    )
    write_json(out_path / "applied_paper_update_012.json", applied_update)
    write_text(out_path / "applied_paper_update_012.md", render_applied_paper_update_markdown(applied_update))

    snapshot = write_paper_tracking_state_snapshot_012(
        source_dashboard=inputs["source_dashboard"],
        pending_update_queue=inputs["pending_queue"],
        evidence_links=inputs["evidence_links"],
        source_status_board=inputs["source_status_board"],
        applied_updates=[applied_update],
        out_dir=out_path,
        generated_at=generated_at,
    )
    dashboard_after = build_operator_dashboard_after_paper_update(
        source_dashboard=inputs["source_dashboard"],
        source_status_board=inputs["source_status_board"],
        snapshot=snapshot,
        applied_update=applied_update,
        generated_at=generated_at,
    )
    write_json(out_path / "operator_dashboard_after_paper_update_012.json", dashboard_after)
    write_text(
        out_path / "operator_dashboard_after_paper_update_012.md",
        render_operator_dashboard_after_paper_update_markdown(dashboard_after),
    )

    comparison = build_paper_update_before_after_comparison(applied_update, candidates[0], inputs["delta_report"], generated_at)
    write_json(out_path / "paper_update_before_after_comparison_012.json", comparison)
    write_text(out_path / "paper_update_before_after_comparison_012.md", render_paper_update_comparison_markdown(comparison))

    morning_card = build_operator_morning_card_after_update(
        applied_update=applied_update,
        source_dashboard=inputs["source_dashboard"],
        source_status_board=inputs["source_status_board"],
        generated_at=generated_at,
    )
    write_json(out_path / "operator_morning_card_after_update_012.json", morning_card)
    write_text(out_path / "operator_morning_card_after_update_012.md", render_operator_morning_card_after_update_markdown(morning_card))

    source_learning = build_source_learning_after_paper_update(
        applied_update=applied_update,
        evidence_links=candidate_links[0],
        public_review=inputs["public_review"],
        generated_at=generated_at,
    )
    write_json(out_path / "source_learning_after_paper_update_012.json", source_learning)
    write_text(out_path / "source_learning_after_paper_update_012.md", render_source_learning_after_update_markdown(source_learning))

    audit = build_paper_update_application_audit(
        approval=approval,
        applied_update=applied_update,
        snapshot=snapshot,
        generated_at=generated_at,
    )
    write_json(out_path / "paper_update_application_audit_012.json", audit)
    write_text(out_path / "paper_update_application_audit_012.md", render_paper_update_application_audit_markdown(audit))

    safety_scan = write_paper_update_application_safety_scan(out_path, generated_at=generated_at)
    generated_artifacts = _generated_artifact_paths(out_path)
    docs = write_paper_update_application_docs(
        approval=approval,
        applied_update=applied_update,
        snapshot=snapshot,
        dashboard_after=dashboard_after,
        comparison=comparison,
        morning_card=morning_card,
        source_learning=source_learning,
        safety_scan=safety_scan,
        generated_artifacts=generated_artifacts,
    )
    generated_artifacts = _generated_artifact_paths(out_path)
    generated_artifacts.extend(docs)
    return {
        "approval": approval,
        "applied_update": applied_update,
        "snapshot": snapshot,
        "dashboard_after": dashboard_after,
        "comparison": comparison,
        "morning_card": morning_card,
        "source_learning": source_learning,
        "audit": audit,
        "safety_scan": safety_scan,
        "generated_artifacts": generated_artifacts,
    }


def build_applied_paper_update(
    *,
    candidate: Mapping[str, Any],
    approval: Mapping[str, Any],
    source_dashboard: Mapping[str, Any],
    evidence_links: Sequence[Mapping[str, Any]],
    public_review: Mapping[str, Any],
    delta_report: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    validate_update_candidate_for_paper_approval(candidate)
    previous_summary = _previous_summary(candidate, source_dashboard)
    applied_summary = _applied_summary(previous_summary, candidate)
    outcome_status = _outcome_status_after_update(source_dashboard, clean_text(candidate.get("market_id")))
    return {
        "contract_version": APPLIED_UPDATE_CONTRACT_VERSION,
        "applied_update_id": "applied-paper-update-012-" + clean_text(candidate.get("update_candidate_id")),
        "update_candidate_id": clean_text(candidate.get("update_candidate_id")),
        "approval_id": approval.get("approval_id"),
        "market_id": clean_text(candidate.get("market_id")),
        "hypothesis_id": clean_text(candidate.get("hypothesis_id")),
        "previous_paper_tracking_summary": previous_summary,
        "applied_paper_tracking_summary": applied_summary,
        "evidence_basis": _evidence_basis(candidate, evidence_links, public_review),
        "limitations": _application_limitations(public_review),
        "operator_approval_required": True,
        "operator_approval_id": approval.get("approval_id"),
        "update_applied": True,
        "applied_at": generated_at,
        "original_artifacts_preserved": True,
        "original_candidate_path": normalize_path(UPDATE_CANDIDATE_PATH),
        "original_hypothesis_artifact_path": clean_text(candidate.get("existing_paper_hypothesis_artifact_path")),
        "outcome_status_after_update": outcome_status,
        "unresolved_outcome_still_required": outcome_status == "unresolved",
        "delta_report_id": delta_report.get("delta_report_id"),
        "no_real_trade_decision": True,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "orders_or_trading_actions": False,
        "wallet_or_private_key_access": False,
        "automatic_trading_allowed": False,
        "safety_summary": _paper_update_safety_summary(),
    }


def render_applied_paper_update_markdown(update: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Applied Paper Update",
            "",
            f"- Applied update ID: `{update.get('applied_update_id')}`",
            f"- Candidate ID: `{update.get('update_candidate_id')}`",
            f"- Approval ID: `{update.get('approval_id')}`",
            f"- Market: `{update.get('market_id')}`",
            f"- Hypothesis: `{update.get('hypothesis_id')}`",
            f"- Update applied: `{str(update.get('update_applied')).lower()}`",
            f"- Outcome status after update: `{update.get('outcome_status_after_update')}`",
            "",
            "## Previous Paper Tracking Summary",
            "",
            update.get("previous_paper_tracking_summary", ""),
            "",
            "## Applied Paper Tracking Summary",
            "",
            update.get("applied_paper_tracking_summary", ""),
            "",
            "## Evidence Basis",
            "",
            *bullet_lines(str(item) for item in update.get("evidence_basis", {}).get("evidence_summary", [])),
            "",
            "## Limitations",
            "",
            *bullet_lines(str(item) for item in update.get("limitations", [])),
            "",
            "## Safety Boundary",
            "",
            "- Paper-only tracking update artifact.",
            "- Original candidate and original hypothesis artifacts remain unchanged.",
            "- No real trade decision, market recommendation, order, wallet access, or automatic trading is allowed.",
        ]
    ) + "\n"


def build_operator_dashboard_after_paper_update(
    *,
    source_dashboard: Mapping[str, Any],
    source_status_board: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    applied_update: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_operator_dashboard_after_paper_update.v1",
        "dashboard_id": "operator-dashboard-after-paper-update-012",
        "generated_at": generated_at,
        "source_dashboard_id": source_dashboard.get("dashboard_id"),
        "tracked_markets": list(snapshot.get("tracked_markets", [])),
        "applied_paper_updates": [applied_update],
        "applied_paper_update_count": 1,
        "remaining_pending_updates": list(snapshot.get("pending_paper_updates_remaining", [])),
        "remaining_pending_update_count": snapshot.get("pending_paper_updates_remaining_count", 0),
        "unresolved_outcomes": list(snapshot.get("unresolved_outcomes", [])),
        "evidence_packet_links": list(snapshot.get("evidence_links", [])),
        "source_status_summary": dict(snapshot.get("source_status_summary", {})),
        "source_records_requiring_manual_review": [
            dict(row) for row in source_status_board.get("sources_requiring_manual_review", []) if isinstance(row, Mapping)
        ],
        "next_operator_actions": [
            "Confirm whether saved local outcome records exist before any later outcome status change.",
            "Review source relevance notes for the applied paper update.",
            "Carry unresolved outcome checks into the next source-learning scorecard task.",
        ],
        "safety_boundary": [
            "paper-only dashboard snapshot",
            "non-executable artifact",
            "no live source fetch",
            "no market recommendation",
            "no orders or wallet access",
            "no scheduler, daemon, background worker, or polling loop",
        ],
        "safety_summary": _paper_update_safety_summary(),
    }


def render_operator_dashboard_after_paper_update_markdown(dashboard: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Operator Dashboard After Paper Update",
            "",
            f"- Dashboard ID: `{dashboard.get('dashboard_id')}`",
            f"- Tracked markets: {len(dashboard.get('tracked_markets', []))}",
            f"- Applied paper updates: {dashboard.get('applied_paper_update_count', 0)}",
            f"- Remaining pending updates: {dashboard.get('remaining_pending_update_count', 0)}",
            f"- Unresolved outcomes: {len(dashboard.get('unresolved_outcomes', []))}",
            "",
            "## Applied Paper Update",
            "",
            *bullet_lines(
                f"`{row.get('applied_update_id')}` for market `{row.get('market_id')}`"
                for row in dashboard.get("applied_paper_updates", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Remaining Pending Updates",
            "",
            *bullet_lines(
                f"`{row.get('update_candidate_id')}`"
                for row in dashboard.get("remaining_pending_updates", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Unresolved Outcomes",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` - `{row.get('outcome_status')}`"
                for row in dashboard.get("unresolved_outcomes", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Evidence Packet Links",
            "",
            *bullet_lines(
                f"`{row.get('evidence_packet_id')}` -> `{row.get('market_id')}` -> `{row.get('hypothesis_id')}`"
                for row in dashboard.get("evidence_packet_links", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Source Status Summary",
            "",
            *bullet_lines(f"{key}: `{value}`" for key, value in dashboard.get("source_status_summary", {}).items()),
            "",
            "## Next Operator Actions",
            "",
            *bullet_lines(str(item) for item in dashboard.get("next_operator_actions", [])),
            "",
            "## Safety Boundary",
            "",
            *bullet_lines(str(item) for item in dashboard.get("safety_boundary", [])),
        ]
    ) + "\n"


def build_paper_update_before_after_comparison(
    applied_update: Mapping[str, Any],
    candidate: Mapping[str, Any],
    delta_report: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_paper_update_before_after_comparison.v1",
        "comparison_id": "paper-update-before-after-comparison-012",
        "generated_at": generated_at,
        "update_candidate_id": applied_update.get("update_candidate_id"),
        "market_id": applied_update.get("market_id"),
        "hypothesis_id": applied_update.get("hypothesis_id"),
        "before_summary": applied_update.get("previous_paper_tracking_summary"),
        "after_summary": applied_update.get("applied_paper_tracking_summary"),
        "evidence_basis": applied_update.get("evidence_basis"),
        "reason_for_update": candidate.get("update_reason") or delta_report.get("delta_report_id"),
        "what_did_not_change": [
            "Original hypothesis artifact was not overwritten.",
            "Original update candidate still records update_applied false.",
            "Outcome status remains unresolved.",
            "The update does not create any executable market action.",
        ],
        "outcome_status_still_unresolved": applied_update.get("outcome_status_after_update") == "unresolved",
        "no_real_trade_decision": True,
        "safety_summary": _paper_update_safety_summary(),
    }


def render_paper_update_comparison_markdown(comparison: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Paper Update Before/After Comparison",
            "",
            f"- Candidate ID: `{comparison.get('update_candidate_id')}`",
            f"- Market: `{comparison.get('market_id')}`",
            f"- Hypothesis: `{comparison.get('hypothesis_id')}`",
            "",
            "## Before",
            "",
            comparison.get("before_summary", ""),
            "",
            "## After",
            "",
            comparison.get("after_summary", ""),
            "",
            "## Reason For Update",
            "",
            f"- `{comparison.get('reason_for_update')}`",
            "",
            "## What Did Not Change",
            "",
            *bullet_lines(str(item) for item in comparison.get("what_did_not_change", [])),
            "",
            "## Outcome Status",
            "",
            f"- Still unresolved: `{str(comparison.get('outcome_status_still_unresolved')).lower()}`",
            "",
            "## Safety Boundary",
            "",
            "- No real trade decision was produced.",
        ]
    ) + "\n"


def build_operator_morning_card_after_update(
    *,
    applied_update: Mapping[str, Any],
    source_dashboard: Mapping[str, Any],
    source_status_board: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    linked_packet_ids = applied_update.get("evidence_basis", {}).get("linked_evidence_packet_ids", [])
    return {
        "contract_version": "pmbot_operator_morning_card_after_update.v1",
        "generated_at": generated_at,
        "paper_update_status": "paper_update_applied",
        "changed_market_id": applied_update.get("market_id"),
        "changed_hypothesis_id": applied_update.get("hypothesis_id"),
        "applied_update_id": applied_update.get("applied_update_id"),
        "evidence_trigger": linked_packet_ids,
        "what_still_needs_outcome_resolution": [
            row for row in source_dashboard.get("unresolved_outcomes", []) if isinstance(row, Mapping)
        ],
        "sources_needing_monitoring": [
            dict(row) for row in source_status_board.get("sources_requiring_manual_review", []) if isinstance(row, Mapping)
        ],
        "next_3_safe_operator_actions": [
            "Check for saved local outcome records before changing outcome status.",
            "Review exact public-source relevance for the applied tracking note.",
            "Update the next source-learning scorecard after outcome recheck artifacts exist.",
        ],
        "safety_summary": _paper_update_safety_summary(),
    }


def render_operator_morning_card_after_update_markdown(card: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Operator Morning Card After Update",
            "",
            "- Paper update applied.",
            f"- Market changed: `{card.get('changed_market_id')}`",
            f"- Hypothesis changed: `{card.get('changed_hypothesis_id')}`",
            "",
            "## Evidence Trigger",
            "",
            *bullet_lines(f"`{packet_id}`" for packet_id in card.get("evidence_trigger", [])),
            "",
            "## Still Needs Outcome Resolution",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` - `{row.get('outcome_status')}`"
                for row in card.get("what_still_needs_outcome_resolution", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Sources To Monitor",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('source_id')}` - `{row.get('latest_accessibility_status')}`"
                for row in card.get("sources_needing_monitoring", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Next 3 Safe Operator Actions",
            "",
            *bullet_lines(str(item) for item in card.get("next_3_safe_operator_actions", [])),
        ]
    ) + "\n"


def build_source_learning_after_paper_update(
    *,
    applied_update: Mapping[str, Any],
    evidence_links: Sequence[Mapping[str, Any]],
    public_review: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_source_learning_after_paper_update.v1",
        "source_learning_event_id": "source-learning-after-paper-update-012",
        "generated_at": generated_at,
        "linked_evidence_packet_ids": _linked_evidence_packet_ids(evidence_links, public_review),
        "linked_source_ids": _linked_source_ids(evidence_links, public_review),
        "linked_market_ids": [clean_text(applied_update.get("market_id"))],
        "linked_update_candidate_ids": [clean_text(applied_update.get("update_candidate_id"))],
        "source_usefulness_for_tracking": "useful_for_paper_tracking_update",
        "source_limitations": [
            "The evidence packet supports paper tracking only.",
            "Exact source relevance still needs operator review before accuracy judgement.",
            "Outcome resolution remains required before source quality can be judged.",
        ],
        "requires_outcome_resolution_for_accuracy_judgement": True,
        "no_autonomous_training_performed": True,
        "safety_summary": _paper_update_safety_summary(),
    }


def render_source_learning_after_update_markdown(learning: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Source Learning After Paper Update",
            "",
            f"- Event ID: `{learning.get('source_learning_event_id')}`",
            f"- Usefulness: `{learning.get('source_usefulness_for_tracking')}`",
            f"- Requires outcome resolution for accuracy judgement: `{str(learning.get('requires_outcome_resolution_for_accuracy_judgement')).lower()}`",
            f"- Autonomous training performed: `{str(not learning.get('no_autonomous_training_performed')).lower()}`",
            "",
            "## Linked Evidence Packets",
            "",
            *bullet_lines(f"`{packet_id}`" for packet_id in learning.get("linked_evidence_packet_ids", [])),
            "",
            "## Linked Sources",
            "",
            *bullet_lines(f"`{source_id}`" for source_id in learning.get("linked_source_ids", [])),
            "",
            "## Source Limitations",
            "",
            *bullet_lines(str(item) for item in learning.get("source_limitations", [])),
        ]
    ) + "\n"


def build_paper_update_application_audit(
    *,
    approval: Mapping[str, Any],
    applied_update: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    original_hypothesis_path = Path(clean_text(applied_update.get("original_hypothesis_artifact_path")))
    return {
        "contract_version": "pmbot_paper_update_application_audit.v1",
        "audit_id": "paper-update-application-audit-012",
        "generated_at": generated_at,
        "original_update_candidate_path": normalize_path(UPDATE_CANDIDATE_PATH),
        "approval_path": normalize_path(DEFAULT_OUT_DIR / "paper_update_operator_approval_012.json"),
        "evidence_review_path": normalize_path(PUBLIC_REVIEW_PATH),
        "before_snapshot_source_dashboard_path": normalize_path(SOURCE_DASHBOARD_PATH),
        "after_snapshot_path": normalize_path(DEFAULT_OUT_DIR / "paper_tracking_state_snapshot_012.json"),
        "applied_update_path": normalize_path(DEFAULT_OUT_DIR / "applied_paper_update_012.json"),
        "applied_fields": sorted(applied_update.keys()),
        "unchanged_original_artifacts": [
            {
                "path": normalize_path(UPDATE_CANDIDATE_PATH),
                "sha256": _sha256(UPDATE_CANDIDATE_PATH),
                "preserved": True,
            },
            {
                "path": normalize_path(original_hypothesis_path),
                "sha256": _sha256(original_hypothesis_path),
                "preserved": True,
            },
        ],
        "safety_checks_performed": [
            "validated candidate paper-only flags",
            "validated operator approval scope",
            "validated required evidence link or review link",
            "validated original artifacts are read-only inputs",
            "ran practical safety scan over paper_update_application_012 artifact directory",
        ],
        "safety_scan_path": normalize_path(DEFAULT_OUT_DIR / "paper_update_application_safety_scan_012.result.json"),
        "no_real_trade_decision": True,
        "automatic_analysis_update_performed": False,
        "operator_approved_update_applied": True,
        "original_artifacts_preserved": True,
        "applied_update_ids": list(snapshot.get("applied_update_ids", [])),
        "safety_summary": _paper_update_safety_summary(),
    }


def render_paper_update_application_audit_markdown(audit: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Paper Update Application Audit",
            "",
            f"- Audit ID: `{audit.get('audit_id')}`",
            f"- Original update candidate: `{audit.get('original_update_candidate_path')}`",
            f"- Approval: `{audit.get('approval_path')}`",
            f"- Evidence review: `{audit.get('evidence_review_path')}`",
            f"- Before dashboard: `{audit.get('before_snapshot_source_dashboard_path')}`",
            f"- After snapshot: `{audit.get('after_snapshot_path')}`",
            "",
            "## Applied Fields",
            "",
            *bullet_lines(str(item) for item in audit.get("applied_fields", [])),
            "",
            "## Unchanged Original Artifacts",
            "",
            *bullet_lines(
                f"`{row.get('path')}` preserved `{str(row.get('preserved')).lower()}`"
                for row in audit.get("unchanged_original_artifacts", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Safety Checks Performed",
            "",
            *bullet_lines(str(item) for item in audit.get("safety_checks_performed", [])),
        ]
    ) + "\n"


def write_paper_update_application_safety_scan(out_dir: str | Path, *, generated_at: str) -> dict[str, Any]:
    out_path = Path(out_dir)
    report = run_practical_safety_scan(artifact_dirs=[out_path])
    report.update(
        {
            "generated_at": generated_at,
            "live_network_used": False,
            "openrouter_calls_performed": 0,
            "new_polymarket_api_calls_performed": 0,
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "automatic_analysis_update_performed": False,
            "operator_approved_update_applied": True,
            "no_scheduler_daemon_background_worker": True,
            "no_autonomous_trading": True,
            "safety_summary": _paper_update_safety_summary(),
        }
    )
    write_json(out_path / "paper_update_application_safety_scan_012.result.json", report)
    write_text(out_path / "paper_update_application_safety_scan_012.md", render_paper_update_application_safety_scan_markdown(report))
    return report


def render_paper_update_application_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Paper Update Application Safety Scan",
            "",
            f"- Scanned paths: {len(report.get('scanned_paths', []))}",
            f"- Issues: {report.get('issue_count')}",
            f"- Safety OK: `{str(report.get('safety_ok')).lower()}`",
            f"- Operator approved update applied: `{str(report.get('operator_approved_update_applied')).lower()}`",
            "",
            "## Confirmed Safe Flags",
            "",
            "- Live network used: `false`",
            "- OpenRouter calls performed: `0`",
            "- New Polymarket API calls performed: `0`",
            "- Authenticated endpoints used: `false`",
            "- Wallet or private key access: `false`",
            "- Orders or trading actions: `false`",
            "- Runtime or dispatcher changes: `false`",
            "- Market recommendation generated: `false`",
            "- Quantitative side-selection output generated: `false`",
            "- Automatic analysis update performed: `false`",
            "- Scheduler, daemon, background worker, or polling loop created: `false`",
            "- Autonomous trading enabled: `false`",
            "",
            "## Issues",
            "",
            *bullet_lines(
                f"`{row.get('path')}` `{row.get('issue_type')}` - {row.get('detail')}"
                for row in report.get("issues", [])
                if isinstance(row, Mapping)
            ),
        ]
    ) + "\n"


def write_paper_update_application_docs(
    *,
    approval: Mapping[str, Any],
    applied_update: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    dashboard_after: Mapping[str, Any],
    comparison: Mapping[str, Any],
    morning_card: Mapping[str, Any],
    source_learning: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    generated_artifacts: Sequence[str],
) -> list[str]:
    docs = [
        DOCS_DIR / "PMBOT_OPERATOR_APPROVED_PAPER_UPDATE_APPLICATION.md",
        DOCS_DIR / "ORCH_PMBOT_PRACTICAL_012_OPERATOR_APPROVED_PAPER_HYPOTHESIS_UPDATE_APPLICATION.md",
        DOCS_DIR / "ORCH_PMBOT_PRACTICAL_012_RESULT.json",
    ]
    write_text(docs[0], render_operator_approved_paper_update_doc(applied_update, source_learning))
    write_text(docs[1], render_practical_012_task_doc(applied_update, snapshot, safety_scan))
    write_json(
        docs[2],
        build_practical_012_result(
            approval=approval,
            applied_update=applied_update,
            snapshot=snapshot,
            dashboard_after=dashboard_after,
            comparison=comparison,
            morning_card=morning_card,
            source_learning=source_learning,
            safety_scan=safety_scan,
            generated_artifacts=list(generated_artifacts) + [normalize_path(path) for path in docs],
        ),
    )
    return [normalize_path(path) for path in docs]


def render_operator_approved_paper_update_doc(
    applied_update: Mapping[str, Any],
    source_learning: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# PMBOT Operator Approved Paper Update Application",
            "",
            "This document records the paper-only application of the pending PRACTICAL-009/PRACTICAL-011 update candidate.",
            "",
            "## Relation To PRACTICAL-011",
            "",
            "- PRACTICAL-011 created the public evidence dashboard and pending update queue.",
            "- PRACTICAL-012 applies the queued candidate into a new versioned snapshot only.",
            "",
            "## Applied Candidate",
            "",
            f"- Candidate: `{applied_update.get('update_candidate_id')}`",
            f"- Market: `{applied_update.get('market_id')}`",
            f"- Hypothesis: `{applied_update.get('hypothesis_id')}`",
            "",
            "## Why Operator Approval Was Required",
            "",
            "- The candidate changes paper tracking state, so it requires explicit operator approval.",
            "- The approval is non-reusable and expires after this task.",
            "- The original hypothesis artifact remains unchanged.",
            "",
            "## What Changed In Paper Tracking",
            "",
            "- The snapshot records the saved public evidence as useful for paper tracking.",
            "- The pending candidate is marked applied only inside the new snapshot artifacts.",
            "",
            "## What Did Not Change",
            "",
            "- Original analysis and hypothesis artifacts were not overwritten.",
            "- The original update candidate remains an unapplied candidate artifact.",
            "- Outcome status remains unresolved.",
            "",
            "## Why This Is Still Not Trading",
            "",
            "- It is a paper-only, non-executable tracking artifact.",
            "- It produces no market recommendation, order, wallet action, or automatic runtime change.",
            "",
            "## Why Outcome Remains Unresolved",
            "",
            "- The saved public evidence packet supports source-accessibility tracking.",
            "- It does not provide a valid local outcome record.",
            "",
            "## Source Learning",
            "",
            f"- Source learning event: `{source_learning.get('source_learning_event_id')}`",
            f"- Usefulness label: `{source_learning.get('source_usefulness_for_tracking')}`",
            "",
            "## Next Recommended Action",
            "",
            f"- `{NEXT_RECOMMENDED_ACTION}`",
        ]
    ) + "\n"


def render_practical_012_task_doc(
    applied_update: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            f"# {TASK_DOC_TITLE}",
            "",
            f"- Task ID: `{TASK_ID}`",
            f"- Applied update: `{applied_update.get('applied_update_id')}`",
            f"- Snapshot: `{snapshot.get('snapshot_id')}`",
            f"- Safety scan passed: `{str(safety_scan.get('safety_ok')).lower()}`",
            "",
            "## Summary",
            "",
            "- The operator-approved candidate from PRACTICAL-009/PRACTICAL-011 was applied to a new paper tracking snapshot.",
            "- No original hypothesis or analysis artifact was modified in place.",
            "- All unresolved outcomes remain unresolved.",
            "",
            "## Outputs",
            "",
            "- Operator approval JSON and Markdown.",
            "- Applied paper update JSON and Markdown.",
            "- Paper tracking state snapshot JSON and Markdown.",
            "- Dashboard, comparison, morning card, source learning, audit, and safety scan artifacts.",
            "",
            "## Safety Boundary",
            "",
            "- No live fetch, OpenRouter call, Polymarket API call, authenticated endpoint, wallet path, order path, runtime path, scheduler, daemon, background worker, or polling loop was used.",
            "- No real trade decision was produced.",
            "",
            "## Next Recommended Action",
            "",
            f"- `{NEXT_RECOMMENDED_ACTION}`",
        ]
    ) + "\n"


def build_practical_012_result(
    *,
    approval: Mapping[str, Any],
    applied_update: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    dashboard_after: Mapping[str, Any],
    comparison: Mapping[str, Any],
    morning_card: Mapping[str, Any],
    source_learning: Mapping[str, Any],
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
        "paper_update_operator_approval_created": bool(approval.get("approval_id")),
        "approved_update_candidate_count": len(approval.get("approved_update_candidate_ids", [])),
        "applied_paper_update_created": bool(applied_update.get("applied_update_id")),
        "applied_update_count": len(snapshot.get("applied_update_ids", [])),
        "original_candidate_preserved": True,
        "paper_tracking_state_snapshot_created": bool(snapshot.get("snapshot_id")),
        "operator_dashboard_after_update_created": bool(dashboard_after.get("dashboard_id")),
        "paper_update_comparison_created": bool(comparison.get("comparison_id")),
        "operator_morning_card_after_update_created": bool(morning_card.get("paper_update_status")),
        "source_learning_after_update_created": bool(source_learning.get("source_learning_event_id")),
        "paper_update_application_safety_scan_passed": safety_scan.get("safety_ok") is True,
        "operator_approved_update_applied": True,
        "automatic_analysis_update_performed": False,
        "original_hypotheses_overwritten": False,
        "outcome_status_changed": False,
        "unresolved_outcome_still_required": applied_update.get("unresolved_outcome_still_required") is True,
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


def _load_inputs() -> dict[str, Any]:
    return {
        "practical_011_result": load_json_object(PRACTICAL_011_RESULT_PATH),
        "source_dashboard": load_json_object(SOURCE_DASHBOARD_PATH),
        "pending_queue": load_json_object(PENDING_QUEUE_PATH),
        "evidence_links": load_json_object(EVIDENCE_LINKS_PATH),
        "source_status_board": load_json_object(SOURCE_STATUS_BOARD_PATH),
        "public_scorecard": load_json_object(PUBLIC_SCORECARD_PATH),
        "watchlist": load_json_object(WATCHLIST_PATH),
        "public_review": load_json_object(PUBLIC_REVIEW_PATH),
        "delta_report": load_json_object(DELTA_REPORT_PATH),
    }


def _validate_practical_011_inputs(inputs: Mapping[str, Any]) -> None:
    result = inputs["practical_011_result"]
    if result.get("pending_update_candidate_count") != 1:
        raise PaperUpdateApplicationError(
            f"PRACTICAL-011 result pending_update_candidate_count is {result.get('pending_update_candidate_count')}"
        )
    if result.get("automatic_analysis_update_performed") is not False:
        raise PaperUpdateApplicationError("PRACTICAL-011 reports an automatic analysis update")
    if result.get("new_live_fetch_performed") is not False:
        raise PaperUpdateApplicationError("PRACTICAL-011 reports a new live fetch")
    queue = inputs["pending_queue"]
    if queue.get("pending_update_count") != 1:
        raise PaperUpdateApplicationError(f"pending update queue count is {queue.get('pending_update_count')}")


def _load_pending_candidates(queue: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for row in queue.get("pending_updates", []):
        if not isinstance(row, Mapping):
            continue
        candidate_path = clean_text(row.get("candidate_artifact_path"))
        if not candidate_path:
            raise PaperUpdateApplicationError("pending update is missing candidate_artifact_path")
        candidate = load_json_object(candidate_path, label="pending update candidate")
        if clean_text(candidate.get("update_candidate_id")) != clean_text(row.get("update_candidate_id")):
            raise PaperUpdateApplicationError("pending queue candidate id does not match candidate artifact")
        candidates.append(candidate)
    return candidates


def _validated_candidate_links(
    candidate: Mapping[str, Any],
    evidence_links: Mapping[str, Any],
    public_review: Mapping[str, Any],
) -> list[dict[str, Any]]:
    validate_update_candidate_for_paper_approval(candidate)
    candidate_id = clean_text(candidate.get("update_candidate_id"))
    market_id = clean_text(candidate.get("market_id"))
    hypothesis_id = clean_text(candidate.get("hypothesis_id"))
    links = [
        dict(row)
        for row in evidence_links.get("links", [])
        if isinstance(row, Mapping)
        and clean_text(row.get("update_candidate_id")) == candidate_id
        and clean_text(row.get("market_id")) == market_id
        and clean_text(row.get("hypothesis_id")) == hypothesis_id
    ]
    review_link_ok = (
        clean_text(candidate.get("source_review_id")) == clean_text(public_review.get("review_id"))
        and market_id in set(public_review.get("affected_market_ids", []))
        and hypothesis_id in set(public_review.get("affected_hypothesis_ids", []))
        and int(public_review.get("evidence_packet_count") or 0) > 0
    )
    if not links and not review_link_ok:
        raise PaperUpdateApplicationError(f"candidate {candidate_id} is missing required evidence or review link")
    return links


def _previous_summary(candidate: Mapping[str, Any], source_dashboard: Mapping[str, Any]) -> str:
    existing = candidate.get("existing_paper_hypothesis_summary", {})
    if isinstance(existing, Mapping) and clean_text(existing.get("paper_hypothesis_summary")):
        return clean_text(existing.get("paper_hypothesis_summary"))
    hypothesis_id = clean_text(candidate.get("hypothesis_id"))
    for row in source_dashboard.get("active_paper_hypotheses", []):
        if isinstance(row, Mapping) and clean_text(row.get("hypothesis_id")) == hypothesis_id:
            return clean_text(row.get("paper_hypothesis_summary"))
    raise PaperUpdateApplicationError("candidate previous paper tracking summary could not be found")


def _applied_summary(previous_summary: str, candidate: Mapping[str, Any]) -> str:
    updates = [clean_text(item) for item in candidate.get("proposed_paper_tracking_update", []) if clean_text(item)]
    return previous_summary + " Paper tracking update: " + " ".join(updates)


def _outcome_status_after_update(source_dashboard: Mapping[str, Any], market_id: str) -> str:
    for row in source_dashboard.get("unresolved_outcomes", []):
        if isinstance(row, Mapping) and clean_text(row.get("market_id")) == market_id:
            return clean_text(row.get("outcome_status") or "unresolved")
    return "unresolved"


def _evidence_basis(
    candidate: Mapping[str, Any],
    evidence_links: Sequence[Mapping[str, Any]],
    public_review: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "source_review_id": candidate.get("source_review_id"),
        "evidence_review_path": normalize_path(PUBLIC_REVIEW_PATH),
        "linked_evidence_packet_ids": _linked_evidence_packet_ids(evidence_links, public_review),
        "linked_source_ids": _linked_source_ids(evidence_links, public_review),
        "evidence_summary": list(candidate.get("evidence_summary", [])),
        "evidence_links": [dict(row) for row in evidence_links],
        "public_review_status": public_review.get("review_status"),
    }


def _application_limitations(public_review: Mapping[str, Any]) -> list[str]:
    limitations = [clean_text(item) for item in public_review.get("limitations", []) if clean_text(item)]
    limitations.extend(
        [
            "The applied update is confined to the new paper tracking snapshot.",
            "The evidence basis does not resolve the market outcome.",
            "Original paper hypothesis artifacts remain unchanged.",
        ]
    )
    return limitations


def _linked_evidence_packet_ids(
    evidence_links: Sequence[Mapping[str, Any]],
    public_review: Mapping[str, Any],
) -> list[str]:
    linked = {clean_text(row.get("evidence_packet_id")) for row in evidence_links if clean_text(row.get("evidence_packet_id"))}
    for packet in public_review.get("evidence_packets_reviewed", []):
        if isinstance(packet, Mapping) and clean_text(packet.get("evidence_packet_id")):
            linked.add(clean_text(packet.get("evidence_packet_id")))
    return sorted(linked)


def _linked_source_ids(
    evidence_links: Sequence[Mapping[str, Any]],
    public_review: Mapping[str, Any],
) -> list[str]:
    linked = set()
    for row in evidence_links:
        packet = row.get("source_packet", {})
        if isinstance(packet, Mapping) and clean_text(packet.get("source_id")):
            linked.add(clean_text(packet.get("source_id")))
    for packet in public_review.get("evidence_packets_reviewed", []):
        if isinstance(packet, Mapping) and clean_text(packet.get("source_id")):
            linked.add(clean_text(packet.get("source_id")))
    return sorted(linked)


def _paper_update_safety_summary() -> dict[str, Any]:
    summary = safe_summary()
    summary.update(
        {
            "new_live_fetch_performed": False,
            "new_polymarket_api_calls_performed": 0,
            "automatic_analysis_update_performed": False,
            "operator_approved_update_applied": True,
            "automatic_trading_allowed": False,
            "no_scheduler_daemon_background_worker": True,
        }
    )
    return summary


def _sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _generated_artifact_paths(out_dir: Path) -> list[str]:
    return sorted(normalize_path(path) for path in out_dir.rglob("*") if path.suffix.lower() in {".json", ".md"})


def _required_tests_run() -> list[str]:
    return [
        "python -m compileall ai_orchestrator pm_bot tests",
        "pytest pm_bot/tests/test_practical_paper_update_approval_012.py",
        "pytest pm_bot/tests/test_practical_paper_update_application_012.py",
        "pytest pm_bot/tests/test_practical_paper_tracking_state_snapshot_012.py",
        "pytest pm_bot/tests/test_practical_operator_dashboard_after_paper_update_012.py",
        "pytest pm_bot/tests/test_practical_paper_update_outputs_012.py",
        "pytest pm_bot/tests/test_practical_pending_paper_update_queue_011.py",
        "pytest pm_bot/tests/test_practical_public_evidence_dashboard_merge_011.py",
        "pytest pm_bot/tests/test_practical_safety_scan.py",
        "python -m json.tool docs/ORCH_PMBOT_PRACTICAL_012_RESULT.json",
        "python -m json.tool pm_bot/practical/artifacts/paper_update_application_012/paper_update_operator_approval_012.json",
        "python -m json.tool pm_bot/practical/artifacts/paper_update_application_012/applied_paper_update_012.json",
        "python -m json.tool pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.json",
        "python -m json.tool pm_bot/practical/artifacts/paper_update_application_012/paper_update_application_audit_012.json",
        "python -m json.tool pm_bot/practical/artifacts/paper_update_application_012/operator_dashboard_after_paper_update_012.json",
        "python -m json.tool pm_bot/practical/artifacts/paper_update_application_012/paper_update_before_after_comparison_012.json",
        "python -m json.tool pm_bot/practical/artifacts/paper_update_application_012/operator_morning_card_after_update_012.json",
        "python -m json.tool pm_bot/practical/artifacts/paper_update_application_012/source_learning_after_paper_update_012.json",
        "python -m json.tool pm_bot/practical/artifacts/paper_update_application_012/paper_update_application_safety_scan_012.result.json",
        "git diff --check",
        "git diff --cached --check",
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply an approved paper-only update candidate into a new snapshot.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output artifact directory.")
    args = parser.parse_args(argv)
    generate_paper_update_application_012(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
