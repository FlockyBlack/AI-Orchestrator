from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, safe_summary, write_json, write_text

LINKS_CONTRACT_VERSION = "pmbot_public_evidence_hypothesis_links.v1"
DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
ACTIVE_HYPOTHESES_PATH = Path(
    "pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.active_paper_hypotheses.result.json"
)
MARKET_QUEUE_PATH = Path("pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json")
EVIDENCE_PACKET_DIRS = (
    Path("pm_bot/practical/artifacts/public_read_only_fetch_execution_008/evidence_packets"),
    Path("pm_bot/practical/artifacts/public_source_url_fixes_010/evidence_packets"),
)
REPLAY_PATHS = (
    Path("pm_bot/practical/artifacts/public_read_only_fetch_execution_008/replay/replayed_source_packets_008.json"),
    Path("pm_bot/practical/artifacts/public_source_url_fixes_010/replay/replayed_source_packets_010.json"),
)
UPDATE_CANDIDATE_PATHS = (
    Path("pm_bot/practical/artifacts/public_evidence_review_009/paper_hypothesis_update_candidate_009.json"),
)
SECOND_UPDATE_CANDIDATE_DIR = Path("pm_bot/practical/artifacts/public_source_url_fixes_010")


def build_public_evidence_hypothesis_links(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    active_hypotheses = _load_active_hypotheses()
    active_by_hypothesis = {row["hypothesis_id"]: row for row in active_hypotheses if row.get("hypothesis_id")}
    active_by_market = {row["market_id"]: row for row in active_hypotheses if row.get("market_id")}
    market_titles = _load_market_titles()
    update_candidates = _load_update_candidates()
    candidates_by_hypothesis = {
        clean_text(row.get("hypothesis_id")): row
        for row in update_candidates
        if clean_text(row.get("hypothesis_id"))
    }
    candidates_by_market = {
        clean_text(row.get("market_id")): row
        for row in update_candidates
        if clean_text(row.get("market_id"))
    }
    source_packets_by_evidence = _load_replayed_source_packets()
    evidence_packets = _load_evidence_packets()

    links: list[dict[str, Any]] = []
    unlinked: list[dict[str, Any]] = []
    linked_hypotheses: set[str] = set()
    linked_markets: set[str] = set()

    for packet in evidence_packets:
        packet_id = clean_text(packet.get("evidence_packet_id"))
        market_ids = _string_list(packet.get("market_ids")) or [clean_text(packet.get("market_id"))]
        market_ids = [market_id for market_id in market_ids if market_id]
        hypothesis_ids = _string_list(packet.get("hypothesis_ids"))
        if not hypothesis_ids:
            hypothesis_ids = [
                active_by_market[market_id]["hypothesis_id"]
                for market_id in market_ids
                if market_id in active_by_market and active_by_market[market_id].get("hypothesis_id")
            ]
        source_packet = source_packets_by_evidence.get(packet_id, {})

        if not packet_id or not market_ids or not hypothesis_ids:
            unlinked.append(
                {
                    "evidence_packet_id": packet_id,
                    "evidence_packet_path": packet.get("artifact_path", ""),
                    "reason": "missing_market_or_hypothesis_link",
                    "operator_review_required": True,
                }
            )
            continue

        for market_id in market_ids:
            hypothesis_id = hypothesis_ids[0]
            active = active_by_hypothesis.get(hypothesis_id) or active_by_market.get(market_id, {})
            candidate = candidates_by_hypothesis.get(hypothesis_id) or candidates_by_market.get(market_id)
            link = {
                "link_id": f"public-evidence-link-011-{market_id}-{packet_id}",
                "evidence_packet_id": packet_id,
                "evidence_packet_path": packet.get("artifact_path", ""),
                "evidence_task_id": packet.get("source_task_id", ""),
                "source_packet": {
                    "source_id": source_packet.get("source_id") or packet.get("source_id", ""),
                    "source_name": source_packet.get("source_name") or packet.get("source_name", ""),
                    "source_category": source_packet.get("source_category") or packet.get("source_category", ""),
                    "source_url_or_reference": source_packet.get("source_url_or_reference")
                    or packet.get("source_reference", ""),
                    "freshness_status": source_packet.get("freshness_status") or packet.get("freshness_status", ""),
                    "replay_mode": source_packet.get("replay_mode", True),
                },
                "market_id": market_id,
                "market_title": active.get("market_title") or market_titles.get(market_id, ""),
                "hypothesis_id": hypothesis_id,
                "active_paper_hypothesis_summary": active.get("paper_hypothesis_summary", ""),
                "update_candidate_id": candidate.get("update_candidate_id", "") if isinstance(candidate, Mapping) else "",
                "update_candidate_status": _candidate_status(candidate),
                "link_basis": [
                    "saved evidence packet market id",
                    "saved evidence packet hypothesis id",
                    "replayed source packet evidence id",
                ],
                "link_quality": "direct_market_and_hypothesis_id_match",
                "operator_review_required": True,
            }
            links.append(link)
            linked_hypotheses.add(hypothesis_id)
            linked_markets.add(market_id)

    hypotheses_without_evidence = [
        {
            "hypothesis_id": row["hypothesis_id"],
            "market_id": row["market_id"],
            "market_title": row.get("market_title", ""),
            "reason": "no_saved_public_evidence_packet_linked",
        }
        for row in active_hypotheses
        if row.get("hypothesis_id") not in linked_hypotheses
    ]
    markets_without_evidence = [
        {
            "market_id": row["market_id"],
            "market_title": row.get("market_title", ""),
            "hypothesis_id": row.get("hypothesis_id", ""),
            "reason": "no_saved_public_evidence_packet_linked",
        }
        for row in active_hypotheses
        if row.get("market_id") not in linked_markets
    ]

    return {
        "contract_version": LINKS_CONTRACT_VERSION,
        "generated_at": generated_at,
        "links": links,
        "unlinked_evidence_packets": unlinked,
        "hypotheses_without_public_evidence": hypotheses_without_evidence,
        "markets_without_public_evidence": markets_without_evidence,
        "link_quality_notes": [
            "Links are built only from saved local artifacts.",
            "Direct links require saved evidence packet market and hypothesis identifiers.",
            "Operator review remains required before any paper hypothesis update is applied.",
        ],
        "operator_review_required": True,
        "safety_summary": safe_summary(),
    }


def write_public_evidence_hypothesis_links_011(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    out_path = Path(out_dir)
    links = build_public_evidence_hypothesis_links()
    write_json(out_path / "public_evidence_hypothesis_links_011.json", links)
    write_text(out_path / "public_evidence_hypothesis_links_011.md", render_public_evidence_hypothesis_links_markdown(links))
    return links


def render_public_evidence_hypothesis_links_markdown(links_model: Mapping[str, Any]) -> str:
    links = [row for row in links_model.get("links", []) if isinstance(row, Mapping)]
    missing = [row for row in links_model.get("hypotheses_without_public_evidence", []) if isinstance(row, Mapping)]
    return "\n".join(
        [
            "# Public Evidence to Paper Hypothesis Links",
            "",
            f"- Link count: {len(links)}",
            f"- Unlinked evidence packets: {len(links_model.get('unlinked_evidence_packets', []))}",
            f"- Hypotheses without public evidence: {len(missing)}",
            f"- Operator review required: `{str(links_model.get('operator_review_required')).lower()}`",
            "",
            "## Links",
            "",
            *bullet_lines(
                f"`{row.get('evidence_packet_id')}` -> market `{row.get('market_id')}` -> hypothesis `{row.get('hypothesis_id')}`"
                + (
                    f" -> update candidate `{row.get('update_candidate_id')}`"
                    if row.get("update_candidate_id")
                    else " -> no update candidate"
                )
                for row in links
            ),
            "",
            "## Hypotheses Without Public Evidence",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('hypothesis_id')}` - {row.get('market_title')}" for row in missing
            ),
            "",
            "## Notes",
            "",
            *bullet_lines(str(item) for item in links_model.get("link_quality_notes", [])),
        ]
    ) + "\n"


def load_linked_evidence_packets() -> list[dict[str, Any]]:
    return _load_evidence_packets()


def _load_active_hypotheses() -> list[dict[str, Any]]:
    payload = load_json_object(ACTIVE_HYPOTHESES_PATH)
    return [dict(row) for row in payload.get("active_hypotheses", []) if isinstance(row, Mapping)]


def _load_market_titles() -> dict[str, str]:
    payload = load_json_object(MARKET_QUEUE_PATH)
    return {
        clean_text(row.get("market_id")): clean_text(row.get("market_title"))
        for row in payload.get("items", [])
        if isinstance(row, Mapping) and clean_text(row.get("market_id"))
    }


def _load_evidence_packets() -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for directory in EVIDENCE_PACKET_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json"), key=normalize_path):
            packet = load_json_object(path)
            packet["artifact_path"] = normalize_path(path)
            packet["source_task_id"] = _source_task_id_for_path(path)
            packets.append(packet)
    return packets


def _load_replayed_source_packets() -> dict[str, dict[str, Any]]:
    source_packets: dict[str, dict[str, Any]] = {}
    for path in REPLAY_PATHS:
        if not path.exists():
            continue
        replay = load_json_object(path)
        for row in replay.get("source_packets", []):
            if isinstance(row, Mapping) and clean_text(row.get("evidence_packet_id")):
                source_packets[clean_text(row.get("evidence_packet_id"))] = dict(row)
    return source_packets


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


def _candidate_status(candidate: Any) -> str:
    if not isinstance(candidate, Mapping):
        return "none"
    if candidate.get("update_applied") is True:
        return "already_applied"
    if candidate.get("operator_approval_required") is True:
        return "pending_operator_review"
    return "candidate_present"


def _source_task_id_for_path(path: Path) -> str:
    normalized = normalize_path(path)
    if "public_read_only_fetch_execution_008" in normalized:
        return "PRACTICAL-008"
    if "public_source_url_fixes_010" in normalized:
        return "PRACTICAL-010"
    return "unknown"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [clean_text(item) for item in value if clean_text(item)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create public evidence to paper hypothesis link artifacts.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for PRACTICAL-011 link artifacts.")
    args = parser.parse_args(argv)
    write_public_evidence_hypothesis_links_011(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
