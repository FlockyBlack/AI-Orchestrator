from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.paper_update_approval import current_utc_timestamp
from pm_bot.practical.practical_io import bullet_lines, clean_text, load_json_object, normalize_path, safe_summary, write_json, write_text

OUTCOME_RECHECK_QUEUE_CONTRACT_VERSION = "pmbot_outcome_recheck_queue.v1"

DEFAULT_SNAPSHOT_PATH = Path("pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.json")
DEFAULT_WATCHLIST_PATH = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011/unresolved_outcome_evidence_watchlist_011.json")
DEFAULT_MARKET_QUEUE_PATH = Path("pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json")
DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/outcome_recheck_source_learning_013")

VALID_OUTCOME_RECORD_CONTRACT = "pmbot_one_market_outcome_record.v1"
RESOLUTION_STATUSES = {"resolved", "ambiguous", "void"}


def build_outcome_recheck_queue(
    *,
    snapshot_path: str | Path = DEFAULT_SNAPSHOT_PATH,
    watchlist_path: str | Path = DEFAULT_WATCHLIST_PATH,
    market_queue_path: str | Path = DEFAULT_MARKET_QUEUE_PATH,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or current_utc_timestamp()
    snapshot = load_json_object(snapshot_path, label="PRACTICAL-012 paper tracking snapshot")
    watchlist = load_json_object(watchlist_path, label="PRACTICAL-011 unresolved outcome watchlist")
    market_queue = load_json_object(market_queue_path, label="PRACTICAL-004 market queue")

    active_by_market = _by_market_id(snapshot.get("active_paper_hypotheses", []))
    watchlist_by_market = _by_market_id(watchlist.get("watchlist_items", []))
    queue_by_market = _by_market_id(market_queue.get("items", []))
    tracked_markets = _tracked_markets(snapshot, market_queue)

    recheck_items = []
    for market in tracked_markets:
        market_id = clean_text(market.get("market_id"))
        active = active_by_market.get(market_id, {})
        watch = watchlist_by_market.get(market_id, {})
        queue_item = queue_by_market.get(market_id, {})
        outcome_path = clean_text(market.get("outcome_record_path") or queue_item.get("outcome_record_path"))
        outcome_record = _load_valid_outcome_record(outcome_path, market_id)
        outcome_status = _outcome_status(outcome_record)
        update_ids = active.get("applied_paper_update_ids", [])
        if not isinstance(update_ids, list):
            update_ids = []
        evidence_available = bool(watch.get("available_public_evidence")) or bool(watch.get("paper_update_candidate_exists"))
        local_resolution_available = outcome_status in RESOLUTION_STATUSES
        recheck_items.append(
            {
                "market_id": market_id,
                "market_title": clean_text(market.get("market_title") or active.get("market_title")),
                "hypothesis_id": clean_text(active.get("hypothesis_id") or market.get("paper_hypothesis_id")),
                "current_paper_tracking_summary": clean_text(
                    active.get("paper_tracking_summary_after")
                    or active.get("paper_hypothesis_summary")
                    or "Paper tracking summary unavailable in local artifacts."
                ),
                "outcome_status": outcome_status,
                "local_outcome_record_path": outcome_path if outcome_record else "",
                "resolution_source_reference": _resolution_reference(outcome_record),
                "recheck_priority": _recheck_priority(outcome_status, len(update_ids), evidence_available),
                "why_recheck_needed": _why_recheck_needed(outcome_status, len(update_ids), evidence_available),
                "source_evidence_available": evidence_available,
                "source_evidence_details": {
                    "available_public_evidence": bool(watch.get("available_public_evidence")),
                    "evidence_still_missing": bool(watch.get("evidence_still_missing")),
                    "paper_update_candidate_exists": bool(watch.get("paper_update_candidate_exists")),
                    "paper_update_candidate_id": clean_text(watch.get("paper_update_candidate_id")),
                },
                "update_applied_count": len(update_ids),
                "applied_paper_update_ids": [clean_text(update_id) for update_id in update_ids],
                "next_operator_action": _next_operator_action(outcome_status, local_resolution_available),
            }
        )

    counts = _status_counts(recheck_items)
    return {
        "contract_version": OUTCOME_RECHECK_QUEUE_CONTRACT_VERSION,
        "queue_id": "outcome-recheck-queue-013",
        "generated_at": generated_at,
        "tracked_market_count": len(tracked_markets),
        "unresolved_count": counts["unresolved"],
        "resolved_count": counts["resolved"],
        "ambiguous_count": counts["ambiguous"],
        "void_count": counts["void"],
        "recheck_items": recheck_items,
        "no_local_resolution_available_count": len([row for row in recheck_items if row["outcome_status"] not in RESOLUTION_STATUSES]),
        "local_resolution_record_count": len([row for row in recheck_items if row["outcome_status"] in RESOLUTION_STATUSES]),
        "next_recheck_actions": [
            "Keep unresolved markets in paper-only recheck status until a saved local resolution record exists.",
            "Prioritize the market with the applied paper update because it is the next feedback dependency.",
            "Use only local outcome records for any later status change.",
        ],
        "safety_summary": _outcome_recheck_safety_summary(),
    }


def write_outcome_recheck_queue_013(
    *,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    generated_at: str | None = None,
) -> dict[str, Any]:
    out_path = Path(out_dir)
    queue = build_outcome_recheck_queue(generated_at=generated_at)
    write_json(out_path / "outcome_recheck_queue_013.json", queue)
    write_text(out_path / "outcome_recheck_queue_013.md", render_outcome_recheck_queue_markdown(queue))
    return queue


def render_outcome_recheck_queue_markdown(queue: Mapping[str, Any]) -> str:
    lines = [
        "# Outcome Recheck Queue 013",
        "",
        f"- Queue ID: `{queue.get('queue_id')}`",
        f"- Tracked markets: {queue.get('tracked_market_count')}",
        f"- Unresolved outcomes: {queue.get('unresolved_count')}",
        f"- Local resolution records: {queue.get('local_resolution_record_count')}",
        "",
        "## Recheck Items",
        "",
    ]
    for item in queue.get("recheck_items", []):
        if not isinstance(item, Mapping):
            continue
        lines.extend(
            [
                f"- `{item.get('market_id')}` `{item.get('recheck_priority')}` `{item.get('outcome_status')}` - {item.get('market_title')}",
                f"  Next: {item.get('next_operator_action')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Next Recheck Actions",
            "",
            *bullet_lines(str(item) for item in queue.get("next_recheck_actions", [])),
            "",
            "## Safety Boundary",
            "",
            "- Local paper-tracking artifacts only.",
            "- No live outcome lookup is performed.",
            "- Outcome status stays unresolved unless a valid local resolution record exists.",
        ]
    )
    return "\n".join(lines) + "\n"


def _tracked_markets(snapshot: Mapping[str, Any], market_queue: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = snapshot.get("tracked_markets")
    if isinstance(rows, list) and rows:
        return [row for row in rows if isinstance(row, Mapping)]
    return [row for row in market_queue.get("items", []) if isinstance(row, Mapping)]


def _by_market_id(rows: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list):
        return {}
    return {clean_text(row.get("market_id")): row for row in rows if isinstance(row, Mapping) and clean_text(row.get("market_id"))}


def _load_valid_outcome_record(path: str, market_id: str) -> Mapping[str, Any] | None:
    if not path:
        return None
    try:
        record = load_json_object(path, label=f"local outcome record {market_id}")
    except Exception:
        return None
    if record.get("contract_version") != VALID_OUTCOME_RECORD_CONTRACT:
        return None
    if clean_text(record.get("market_id")) != market_id:
        return None
    return record


def _outcome_status(record: Mapping[str, Any] | None) -> str:
    if record is None:
        return "unknown"
    status = clean_text(record.get("outcome_status"))
    if status in {"unresolved", "resolved", "ambiguous", "void"}:
        return status
    return "unknown"


def _resolution_reference(record: Mapping[str, Any] | None) -> str | None:
    if record is None:
        return None
    if clean_text(record.get("outcome_status")) not in RESOLUTION_STATUSES:
        return None
    reference = clean_text(record.get("resolution_source_reference"))
    return reference or None


def _recheck_priority(outcome_status: str, update_applied_count: int, evidence_available: bool) -> str:
    if outcome_status in {"resolved", "ambiguous", "void"}:
        return "low"
    if update_applied_count:
        return "high"
    if evidence_available:
        return "medium"
    if outcome_status == "unresolved":
        return "medium"
    return "unknown"


def _why_recheck_needed(outcome_status: str, update_applied_count: int, evidence_available: bool) -> str:
    if outcome_status in {"resolved", "ambiguous", "void"}:
        return "Local outcome status is no longer unresolved; feedback review can use the saved local record."
    if update_applied_count:
        return "Applied paper tracking update cannot be judged until a saved local outcome resolution exists."
    if evidence_available:
        return "Saved public evidence exists, but outcome feedback remains blocked by unresolved local status."
    return "Outcome is still unresolved and no saved local resolution record is available."


def _next_operator_action(outcome_status: str, local_resolution_available: bool) -> str:
    if local_resolution_available:
        return "Review the local resolution record before creating a paper feedback packet."
    if outcome_status == "unresolved":
        return "When a valid local resolution record exists, attach it before changing feedback status."
    return "Inspect the local outcome record path and keep the market out of feedback review until status is clear."


def _status_counts(items: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {"unresolved": 0, "resolved": 0, "ambiguous": 0, "void": 0}
    for item in items:
        status = clean_text(item.get("outcome_status"))
        if status in counts:
            counts[status] += 1
    return counts


def _outcome_recheck_safety_summary() -> dict[str, Any]:
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
    parser = argparse.ArgumentParser(description="Generate the PRACTICAL-013 outcome recheck queue.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for PRACTICAL-013 artifacts.")
    args = parser.parse_args(argv)
    write_outcome_recheck_queue_013(out_dir=args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
