from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, safe_summary, write_json, write_text

QUEUE_CONTRACT_VERSION = "pmbot_pending_paper_update_queue.v1"
DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
ACTIVE_HYPOTHESES_PATH = Path(
    "pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.active_paper_hypotheses.result.json"
)
UPDATE_CANDIDATE_PATHS = (
    Path("pm_bot/practical/artifacts/public_evidence_review_009/paper_hypothesis_update_candidate_009.json"),
)
SECOND_UPDATE_CANDIDATE_DIR = Path("pm_bot/practical/artifacts/public_source_url_fixes_010")


def build_pending_paper_update_queue(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    active_hypotheses = _load_active_hypotheses()
    active_by_hypothesis = {row.get("hypothesis_id"): row for row in active_hypotheses if row.get("hypothesis_id")}
    active_by_market = {row.get("market_id"): row for row in active_hypotheses if row.get("market_id")}

    pending: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []

    for candidate in _load_update_candidates():
        hypothesis_id = clean_text(candidate.get("hypothesis_id"))
        market_id = clean_text(candidate.get("market_id"))
        active = active_by_hypothesis.get(hypothesis_id) or active_by_market.get(market_id)
        row = _summarize_candidate(candidate, active)
        if candidate.get("update_applied") is True:
            applied.append(row)
        elif not active:
            row["blocked_reason"] = "candidate_does_not_match_active_paper_hypothesis"
            blocked.append(row)
        elif candidate.get("operator_approval_required") is True:
            pending.append(row)
        else:
            row["blocked_reason"] = "operator_review_flag_missing"
            blocked.append(row)

    return {
        "contract_version": QUEUE_CONTRACT_VERSION,
        "generated_at": generated_at,
        "pending_update_count": len(pending),
        "pending_updates": pending,
        "blocked_updates": blocked,
        "already_applied_updates": applied,
        "operator_review_required_count": sum(1 for row in pending if row.get("operator_approval_required") is True),
        "next_operator_actions": [
            "Review pending paper update candidates against the saved evidence packet and active hypothesis.",
            "Keep original paper hypothesis artifacts unchanged until a later operator-approved application task.",
            "Leave unresolved outcome records unchanged until saved resolution evidence is available.",
        ],
        "automatic_update_performed": False,
        "safety_summary": safe_summary(),
    }


def write_pending_paper_update_queue_011(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    out_path = Path(out_dir)
    queue = build_pending_paper_update_queue()
    write_json(out_path / "pending_paper_update_queue_011.json", queue)
    write_text(out_path / "pending_paper_update_queue_011.md", render_pending_paper_update_queue_markdown(queue))
    return queue


def render_pending_paper_update_queue_markdown(queue: Mapping[str, Any]) -> str:
    pending = [row for row in queue.get("pending_updates", []) if isinstance(row, Mapping)]
    blocked = [row for row in queue.get("blocked_updates", []) if isinstance(row, Mapping)]
    applied = [row for row in queue.get("already_applied_updates", []) if isinstance(row, Mapping)]
    return "\n".join(
        [
            "# Pending Paper Update Queue",
            "",
            f"- Pending updates: {queue.get('pending_update_count', 0)}",
            f"- Blocked updates: {len(blocked)}",
            f"- Already applied updates: {len(applied)}",
            f"- Automatic update performed: `{str(queue.get('automatic_update_performed')).lower()}`",
            "",
            "## Pending Updates",
            "",
            *bullet_lines(
                f"`{row.get('update_candidate_id')}` -> market `{row.get('market_id')}` -> hypothesis `{row.get('hypothesis_id')}`"
                for row in pending
            ),
            "",
            "## Next Operator Actions",
            "",
            *bullet_lines(str(item) for item in queue.get("next_operator_actions", [])),
        ]
    ) + "\n"


def _load_active_hypotheses() -> list[dict[str, Any]]:
    payload = load_json_object(ACTIVE_HYPOTHESES_PATH)
    return [dict(row) for row in payload.get("active_hypotheses", []) if isinstance(row, Mapping)]


def _load_update_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in UPDATE_CANDIDATE_PATHS:
        if path.exists():
            row = load_json_object(path)
            row["candidate_artifact_path"] = normalize_path(path)
            candidates.append(row)
    if SECOND_UPDATE_CANDIDATE_DIR.exists():
        for path in sorted(SECOND_UPDATE_CANDIDATE_DIR.rglob("*update*candidate*.json"), key=normalize_path):
            row = load_json_object(path)
            row["candidate_artifact_path"] = normalize_path(path)
            candidates.append(row)
    return candidates


def _summarize_candidate(candidate: Mapping[str, Any], active: Mapping[str, Any] | None) -> dict[str, Any]:
    existing = candidate.get("existing_paper_hypothesis_summary", {})
    active_summary = active or existing if isinstance(existing, Mapping) else active or {}
    return {
        "update_candidate_id": clean_text(candidate.get("update_candidate_id")),
        "candidate_artifact_path": candidate.get("candidate_artifact_path", ""),
        "market_id": clean_text(candidate.get("market_id")),
        "market_title": clean_text(active_summary.get("market_title", "")) if isinstance(active_summary, Mapping) else "",
        "hypothesis_id": clean_text(candidate.get("hypothesis_id")),
        "active_paper_hypothesis_summary": clean_text(active_summary.get("paper_hypothesis_summary", ""))
        if isinstance(active_summary, Mapping)
        else "",
        "update_reason": clean_text(candidate.get("update_reason")),
        "evidence_summary": [clean_text(item) for item in candidate.get("evidence_summary", []) if clean_text(item)],
        "proposed_paper_tracking_update": [
            clean_text(item) for item in candidate.get("proposed_paper_tracking_update", []) if clean_text(item)
        ],
        "operator_approval_required": candidate.get("operator_approval_required") is True,
        "update_applied": candidate.get("update_applied") is True,
        "automatic_analysis_update_performed": candidate.get("automatic_analysis_update_performed") is True,
        "no_real_trade_decision": candidate.get("no_real_trade_decision") is True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create the PRACTICAL-011 pending paper update queue.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for pending update artifacts.")
    args = parser.parse_args(argv)
    write_pending_paper_update_queue_011(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
