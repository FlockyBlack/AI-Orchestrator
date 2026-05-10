from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.paper_update_approval import current_utc_timestamp
from pm_bot.practical.practical_io import bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

SOURCE_LEARNING_SCORECARD_CONTRACT_VERSION = "pmbot_source_learning_scorecard_update.v1"

DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/outcome_recheck_source_learning_013")
SOURCE_LEARNING_AFTER_UPDATE_PATH = Path(
    "pm_bot/practical/artifacts/paper_update_application_012/source_learning_after_paper_update_012.json"
)
SOURCE_LEARNING_009_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/source_accessibility_learning_009.json")
SOURCE_LEARNING_010_PATH = Path("pm_bot/practical/artifacts/public_source_url_fixes_010/source_accessibility_learning_010.json")
PUBLIC_EVIDENCE_SCORECARD_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_scorecard_011.json")
SOURCE_STATUS_BOARD_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/merged_source_status_board_011.json")
SOURCE_REPAIR_SUMMARY_PATH = Path("pm_bot/practical/artifacts/public_source_url_fixes_010/source_url_repair_result_summary_010.json")
SNAPSHOT_PATH = Path("pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.json")

SOURCE_USEFULNESS_LABELS = [
    "useful_for_paper_tracking_update",
    "accessible_but_pending_outcome",
    "failed_access",
    "repaired_access",
    "missing_replacement",
    "blocked",
    "unknown",
]


def build_source_learning_scorecard_update(
    *,
    source_learning_after_update_path: str | Path = SOURCE_LEARNING_AFTER_UPDATE_PATH,
    source_learning_009_path: str | Path = SOURCE_LEARNING_009_PATH,
    source_learning_010_path: str | Path = SOURCE_LEARNING_010_PATH,
    public_evidence_scorecard_path: str | Path = PUBLIC_EVIDENCE_SCORECARD_PATH,
    source_status_board_path: str | Path = SOURCE_STATUS_BOARD_PATH,
    source_repair_summary_path: str | Path = SOURCE_REPAIR_SUMMARY_PATH,
    snapshot_path: str | Path = SNAPSHOT_PATH,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or current_utc_timestamp()
    learning_after_update = load_json_object(source_learning_after_update_path, label="PRACTICAL-012 source learning")
    learning_009 = load_json_object(source_learning_009_path, label="PRACTICAL-009 source learning")
    learning_010 = load_json_object(source_learning_010_path, label="PRACTICAL-010 source learning")
    scorecard_011 = load_json_object(public_evidence_scorecard_path, label="PRACTICAL-011 public evidence scorecard")
    source_board = load_json_object(source_status_board_path, label="PRACTICAL-011 source status board")
    repair_summary = load_json_object(source_repair_summary_path, label="PRACTICAL-010 source repair summary")
    snapshot = load_json_object(snapshot_path, label="PRACTICAL-012 paper tracking snapshot")

    linked_update_source_ids = {
        clean_text(source_id) for source_id in learning_after_update.get("linked_source_ids", []) if clean_text(source_id)
    }
    unresolved_market_ids = {
        clean_text(row.get("market_id"))
        for row in snapshot.get("unresolved_outcomes", [])
        if isinstance(row, Mapping) and clean_text(row.get("market_id"))
    }
    source_records = [
        _source_record(row, linked_update_source_ids=linked_update_source_ids, unresolved_market_ids=unresolved_market_ids)
        for row in source_board.get("source_records", [])
        if isinstance(row, Mapping)
    ]

    return {
        "contract_version": SOURCE_LEARNING_SCORECARD_CONTRACT_VERSION,
        "scorecard_update_id": "source-learning-scorecard-update-013",
        "generated_at": generated_at,
        "input_learning_artifacts": [
            str(source_learning_after_update_path).replace("\\", "/"),
            str(source_learning_009_path).replace("\\", "/"),
            str(source_learning_010_path).replace("\\", "/"),
            str(public_evidence_scorecard_path).replace("\\", "/"),
            str(source_status_board_path).replace("\\", "/"),
            str(source_repair_summary_path).replace("\\", "/"),
        ],
        "source_records": source_records,
        "sources_useful_for_paper_tracking": [
            row for row in source_records if row.get("source_usefulness_label") == "useful_for_paper_tracking_update"
        ],
        "sources_accessible": [row for row in source_records if row.get("latest_accessibility_status") == "reachable"],
        "sources_failed": _project_sources(source_board.get("failed_sources", []), source_records),
        "sources_repaired": _project_sources(source_board.get("repaired_sources", []), source_records),
        "sources_still_missing": _project_sources(source_board.get("replacement_missing_sources", []), source_records),
        "sources_blocked": _project_sources(source_board.get("blocked_sources", []), source_records),
        "sources_pending_outcome_resolution": [row for row in source_records if row.get("pending_outcome_resolution") is True],
        "source_usefulness_labels": list(SOURCE_USEFULNESS_LABELS),
        "source_usefulness_label_definitions": {
            "useful_for_paper_tracking_update": "Supported an operator-approved paper tracking update, without outcome validation.",
            "accessible_but_pending_outcome": "A saved public source packet or reachable source exists, but outcome feedback is still pending.",
            "failed_access": "The saved source attempt failed or was marked no-retry.",
            "repaired_access": "A previously failed source has a saved repaired public source packet.",
            "missing_replacement": "A replacement public URL was not available in local artifacts.",
            "blocked": "The source remains blocked by access-control or simple request limitations.",
            "unknown": "Local source status is incomplete.",
        },
        "recommended_future_source_handling": _recommended_future_handling(source_records),
        "scorecard_context": {
            "public_evidence_accessibility_label": scorecard_011.get("accessibility_success_rate_label"),
            "evidence_packet_count": scorecard_011.get("evidence_packet_count"),
            "source_repair_count": scorecard_011.get("source_repair_count"),
            "source_still_missing_count": scorecard_011.get("source_still_missing_count"),
            "repair_summary": {
                "repaired_executable_count": repair_summary.get("repaired_executable_count", 0),
                "replacement_missing_count": repair_summary.get("replacement_missing_count", 0),
                "blocked_count": repair_summary.get("blocked_count", 0),
                "no_retry_count": repair_summary.get("no_retry_count", 0),
            },
            "learning_009_record_count": len(learning_009.get("source_accessibility_records", [])),
            "learning_010_record_count": len(learning_010.get("source_accessibility_records", [])),
            "requires_outcome_resolution_for_accuracy_judgement": learning_after_update.get(
                "requires_outcome_resolution_for_accuracy_judgement"
            )
            is True,
        },
        "no_autonomous_training_performed": True,
        "no_real_trade_decision": True,
        "safety_summary": _source_learning_safety_summary(),
    }


def write_source_learning_scorecard_update_013(
    *,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    generated_at: str | None = None,
) -> dict[str, Any]:
    out_path = Path(out_dir)
    scorecard = build_source_learning_scorecard_update(generated_at=generated_at)
    write_json(out_path / "source_learning_scorecard_update_013.json", scorecard)
    write_text(out_path / "source_learning_scorecard_update_013.md", render_source_learning_scorecard_update_markdown(scorecard))
    return scorecard


def render_source_learning_scorecard_update_markdown(scorecard: Mapping[str, Any]) -> str:
    lines = [
        "# Source Learning Scorecard Update 013",
        "",
        f"- Source records: {len(scorecard.get('source_records', []))}",
        f"- Useful for paper tracking update: {len(scorecard.get('sources_useful_for_paper_tracking', []))}",
        f"- Accessible sources: {len(scorecard.get('sources_accessible', []))}",
        f"- Pending outcome resolution: {len(scorecard.get('sources_pending_outcome_resolution', []))}",
        "",
        "## Source Records",
        "",
    ]
    for record in scorecard.get("source_records", []):
        if not isinstance(record, Mapping):
            continue
        lines.extend(
            [
                f"- `{record.get('source_id')}` `{record.get('source_usefulness_label')}`",
                f"  Market: `{record.get('market_id')}` - {record.get('market_title')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Recommended Future Source Handling",
            "",
            *bullet_lines(
                f"`{row.get('source_id')}` - {row.get('handling')}"
                for row in scorecard.get("recommended_future_source_handling", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Boundary",
            "",
            "- Source usefulness can be marked for paper tracking update support only.",
            "- Outcome records are still required before judging source correctness.",
            "- No autonomous training or real trade decision is performed.",
        ]
    )
    return "\n".join(lines) + "\n"


def _source_record(
    row: Mapping[str, Any],
    *,
    linked_update_source_ids: set[str],
    unresolved_market_ids: set[str],
) -> dict[str, Any]:
    source_id = clean_text(row.get("source_id") or row.get("request_intent_id"))
    latest_status = clean_text(row.get("latest_accessibility_status"))
    repair_status = clean_text(row.get("repair_status"))
    label = _source_label(row, linked_update_source_ids)
    market_id = clean_text(row.get("market_id"))
    return {
        "source_id": source_id,
        "request_intent_id": clean_text(row.get("request_intent_id") or source_id),
        "source_name": clean_text(row.get("source_name")),
        "source_category": clean_text(row.get("source_category")),
        "market_id": market_id,
        "market_title": clean_text(row.get("market_title")),
        "first_source_url": clean_text(row.get("first_source_url")),
        "latest_source_url": clean_text(row.get("latest_source_url")),
        "first_accessibility_status": clean_text(row.get("first_accessibility_status")),
        "latest_accessibility_status": latest_status,
        "repair_status": repair_status,
        "has_evidence_packet": row.get("has_evidence_packet") is True,
        "latest_evidence_packet_id": clean_text(row.get("latest_evidence_packet_id")),
        "recommended_handling": clean_text(row.get("recommended_handling")),
        "source_usefulness_label": label,
        "pending_outcome_resolution": market_id in unresolved_market_ids,
        "outcome_validated": False,
        "paper_tracking_update_support": source_id in linked_update_source_ids,
        "usefulness_limit": "Outcome resolution is pending; this is not a prediction accuracy judgement.",
    }


def _source_label(row: Mapping[str, Any], linked_update_source_ids: set[str]) -> str:
    source_id = clean_text(row.get("source_id") or row.get("request_intent_id"))
    latest_status = clean_text(row.get("latest_accessibility_status"))
    repair_status = clean_text(row.get("repair_status"))
    has_packet = row.get("has_evidence_packet") is True
    if source_id in linked_update_source_ids:
        return "useful_for_paper_tracking_update"
    if latest_status == "blocked" or repair_status == "blocked":
        return "blocked"
    if latest_status == "replacement_missing" or repair_status == "replacement_missing":
        return "missing_replacement"
    if repair_status in {"executable_candidate", "repaired"}:
        return "repaired_access"
    if latest_status in {"failed", "no_retry"} or repair_status == "no_retry":
        return "failed_access"
    if latest_status == "reachable" or has_packet:
        return "accessible_but_pending_outcome"
    return "unknown"


def _project_sources(rows: Any, source_records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    source_by_id = {clean_text(row.get("source_id")): row for row in source_records}
    projected = []
    if not isinstance(rows, list):
        return projected
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        source_id = clean_text(row.get("source_id") or row.get("request_intent_id"))
        projected.append(source_by_id.get(source_id, row))
    return projected


def _recommended_future_handling(source_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    handling = []
    for record in source_records:
        label = clean_text(record.get("source_usefulness_label"))
        if label == "useful_for_paper_tracking_update":
            action = "Keep for paper tracking review; wait for local outcome resolution before judging correctness."
        elif label == "accessible_but_pending_outcome":
            action = "Keep accessible saved source metadata available for later outcome review."
        elif label == "repaired_access":
            action = "Keep repaired public source path visible and verify relevance during operator review."
        elif label == "missing_replacement":
            action = "Collect a concrete replacement public URL manually before a later scoped source task."
        elif label == "blocked":
            action = "Use a different public source; do not use access-control workarounds."
        elif label == "failed_access":
            action = "Treat as lower operational usefulness until a local replacement or repair artifact exists."
        else:
            action = "Inspect local source artifacts before using this source for paper review."
        handling.append(
            {
                "source_id": clean_text(record.get("source_id")),
                "market_id": clean_text(record.get("market_id")),
                "source_usefulness_label": label,
                "handling": action,
            }
        )
    return handling


def _source_learning_safety_summary() -> dict[str, Any]:
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
        }
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the PRACTICAL-013 source learning scorecard update.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for PRACTICAL-013 artifacts.")
    args = parser.parse_args(argv)
    write_source_learning_scorecard_update_013(out_dir=args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
