from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.paper_update_approval import current_utc_timestamp
from pm_bot.practical.practical_io import bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

SNAPSHOT_CONTRACT_VERSION = "pmbot_paper_tracking_state_snapshot.v1"
DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/paper_update_application_012")


def build_paper_tracking_state_snapshot(
    *,
    source_dashboard: Mapping[str, Any],
    pending_update_queue: Mapping[str, Any],
    evidence_links: Mapping[str, Any],
    source_status_board: Mapping[str, Any],
    applied_updates: Sequence[Mapping[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    applied_update_ids = [clean_text(update.get("applied_update_id")) for update in applied_updates]
    applied_candidate_ids = {clean_text(update.get("update_candidate_id")) for update in applied_updates}
    applied_by_hypothesis = {
        clean_text(update.get("hypothesis_id")): update
        for update in applied_updates
        if clean_text(update.get("hypothesis_id"))
    }

    active_hypotheses = [
        _snapshot_hypothesis(row, applied_by_hypothesis)
        for row in source_dashboard.get("active_paper_hypotheses", [])
        if isinstance(row, Mapping)
    ]
    pending_remaining = [
        dict(row)
        for row in pending_update_queue.get("pending_updates", [])
        if isinstance(row, Mapping) and clean_text(row.get("update_candidate_id")) not in applied_candidate_ids
    ]

    snapshot = {
        "contract_version": SNAPSHOT_CONTRACT_VERSION,
        "snapshot_id": "paper-tracking-state-snapshot-012",
        "generated_at": generated_at or current_utc_timestamp(),
        "source_dashboard_id": source_dashboard.get("dashboard_id"),
        "applied_update_ids": applied_update_ids,
        "tracked_markets": list(source_dashboard.get("tracked_markets", [])),
        "active_paper_hypotheses": active_hypotheses,
        "applied_paper_updates": [dict(update) for update in applied_updates],
        "pending_paper_updates_remaining": pending_remaining,
        "pending_paper_updates_remaining_count": len(pending_remaining),
        "unresolved_outcomes": list(source_dashboard.get("unresolved_outcomes", [])),
        "evidence_links": list(evidence_links.get("links", [])),
        "source_status_summary": _source_status_summary(source_dashboard, source_status_board),
        "operator_next_actions": [
            "Review saved outcome evidence when it exists before changing any outcome status.",
            "Keep monitoring unresolved outcome records as paper-only follow-up work.",
            "Use the applied update to judge source usefulness only after outcome reconciliation.",
        ],
        "safety_summary": _snapshot_safety_summary(),
    }
    return snapshot


def write_paper_tracking_state_snapshot_012(
    *,
    source_dashboard: Mapping[str, Any],
    pending_update_queue: Mapping[str, Any],
    evidence_links: Mapping[str, Any],
    source_status_board: Mapping[str, Any],
    applied_updates: Sequence[Mapping[str, Any]],
    out_dir: str | Path = DEFAULT_OUT_DIR,
    generated_at: str | None = None,
) -> dict[str, Any]:
    snapshot = build_paper_tracking_state_snapshot(
        source_dashboard=source_dashboard,
        pending_update_queue=pending_update_queue,
        evidence_links=evidence_links,
        source_status_board=source_status_board,
        applied_updates=applied_updates,
        generated_at=generated_at,
    )
    out_path = Path(out_dir)
    write_json(out_path / "paper_tracking_state_snapshot_012.json", snapshot)
    write_text(out_path / "paper_tracking_state_snapshot_012.md", render_paper_tracking_state_snapshot_markdown(snapshot))
    return snapshot


def render_paper_tracking_state_snapshot_markdown(snapshot: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Paper Tracking State Snapshot",
            "",
            f"- Snapshot ID: `{snapshot.get('snapshot_id')}`",
            f"- Source dashboard: `{snapshot.get('source_dashboard_id')}`",
            f"- Applied updates: {len(snapshot.get('applied_update_ids', []))}",
            f"- Remaining pending updates: {snapshot.get('pending_paper_updates_remaining_count', 0)}",
            f"- Unresolved outcomes: {len(snapshot.get('unresolved_outcomes', []))}",
            "",
            "## Tracked Markets",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` - {row.get('market_title')}"
                for row in snapshot.get("tracked_markets", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Active Paper Hypotheses",
            "",
            *bullet_lines(
                f"`{row.get('hypothesis_id')}` - {row.get('paper_tracking_summary_after') or row.get('paper_hypothesis_summary')}"
                for row in snapshot.get("active_paper_hypotheses", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Applied Paper Updates",
            "",
            *bullet_lines(f"`{update_id}`" for update_id in snapshot.get("applied_update_ids", [])),
            "",
            "## Pending Paper Updates Remaining",
            "",
            *bullet_lines(
                f"`{row.get('update_candidate_id')}` for market `{row.get('market_id')}`"
                for row in snapshot.get("pending_paper_updates_remaining", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Unresolved Outcomes",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` - `{row.get('outcome_status')}`"
                for row in snapshot.get("unresolved_outcomes", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Operator Next Actions",
            "",
            *bullet_lines(str(item) for item in snapshot.get("operator_next_actions", [])),
            "",
            "## Safety Boundary",
            "",
            "- Snapshot is paper-only and non-executable.",
            "- Original hypothesis artifacts remain unchanged.",
            "- Outcome status is not changed without a valid local outcome record.",
        ]
    ) + "\n"


def _snapshot_hypothesis(
    hypothesis: Mapping[str, Any],
    applied_by_hypothesis: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    row = dict(hypothesis)
    update = applied_by_hypothesis.get(clean_text(row.get("hypothesis_id")))
    if update is None:
        row["update_applied_in_snapshot"] = False
        row["applied_paper_update_ids"] = []
        row["paper_tracking_summary_before"] = row.get("paper_hypothesis_summary", "")
        row["paper_tracking_summary_after"] = row.get("paper_hypothesis_summary", "")
        return row

    row["update_applied_in_snapshot"] = True
    row["applied_paper_update_ids"] = [update.get("applied_update_id")]
    row["paper_tracking_summary_before"] = update.get("previous_paper_tracking_summary", "")
    row["paper_tracking_summary_after"] = update.get("applied_paper_tracking_summary", "")
    row["original_artifacts_preserved"] = update.get("original_artifacts_preserved") is True
    row["operator_approval_id"] = update.get("operator_approval_id")
    row["outcome_status"] = update.get("outcome_status_after_update", row.get("outcome_status", "unresolved"))
    return row


def _source_status_summary(
    source_dashboard: Mapping[str, Any],
    source_status_board: Mapping[str, Any],
) -> dict[str, Any]:
    existing = dict(source_dashboard.get("source_status_summary", {}))
    existing.update(
        {
            "source_record_count": len(source_status_board.get("source_records", [])),
            "reachable_source_count": len(source_status_board.get("reachable_sources", [])),
            "failed_source_count": len(source_status_board.get("failed_sources", [])),
            "repaired_source_count": len(source_status_board.get("repaired_sources", [])),
            "sources_with_evidence_packets_count": len(source_status_board.get("sources_with_evidence_packets", [])),
        }
    )
    return existing


def _snapshot_safety_summary() -> dict[str, Any]:
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a paper tracking state snapshot from local artifacts.")
    parser.add_argument("--dashboard", required=True)
    parser.add_argument("--queue", required=True)
    parser.add_argument("--links", required=True)
    parser.add_argument("--source-board", required=True)
    parser.add_argument("--applied-update", action="append", required=True)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args(argv)

    write_paper_tracking_state_snapshot_012(
        source_dashboard=load_json_object(args.dashboard, label="source dashboard"),
        pending_update_queue=load_json_object(args.queue, label="pending update queue"),
        evidence_links=load_json_object(args.links, label="evidence links"),
        source_status_board=load_json_object(args.source_board, label="source status board"),
        applied_updates=[load_json_object(path, label="applied update") for path in args.applied_update],
        out_dir=args.out_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
