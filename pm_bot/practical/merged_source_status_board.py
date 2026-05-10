from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

SOURCE_BOARD_CONTRACT_VERSION = "pmbot_merged_source_status_board.v1"
DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
LEARNING_009_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/source_accessibility_learning_009.json")
LEARNING_010_PATH = Path("pm_bot/practical/artifacts/public_source_url_fixes_010/source_accessibility_learning_010.json")
REPAIR_SUMMARY_010_PATH = Path("pm_bot/practical/artifacts/public_source_url_fixes_010/source_url_repair_result_summary_010.json")
FAILURE_DIAGNOSIS_009_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/public_fetch_failure_diagnosis_009.json")


def build_merged_source_status_board(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    learning_009 = load_json_object(LEARNING_009_PATH)
    learning_010 = load_json_object(LEARNING_010_PATH)
    repair_summary = load_json_object(REPAIR_SUMMARY_010_PATH)
    failure_diagnosis = load_json_object(FAILURE_DIAGNOSIS_009_PATH)

    records_by_source: dict[str, dict[str, Any]] = {}
    for row in learning_009.get("source_accessibility_records", []):
        if isinstance(row, Mapping):
            source_id = clean_text(row.get("request_intent_id"))
            if source_id:
                records_by_source[source_id] = _base_record_from_009(row)

    for row in learning_010.get("source_accessibility_records", []):
        if not isinstance(row, Mapping):
            continue
        source_id = clean_text(row.get("request_intent_id"))
        if not source_id:
            continue
        existing = records_by_source.setdefault(source_id, _empty_record(source_id))
        existing.update(
            {
                "latest_accessibility_status": clean_text(row.get("accessibility_status")),
                "latest_task_id": "PRACTICAL-010",
                "latest_source_url": clean_text(row.get("source_url")) or existing.get("latest_source_url", ""),
                "latest_evidence_packet_id": clean_text(row.get("evidence_packet_id")),
                "evidence_usable": row.get("evidence_usable") is True,
                "replay_usable": row.get("replay_usable") is True,
                "repair_status": clean_text(row.get("repair_status")) or existing.get("repair_status", ""),
                "operator_review_required": row.get("operator_review_required") is True,
            }
        )

    failure_by_source = {
        clean_text(row.get("request_intent_id")): row
        for row in failure_diagnosis.get("failed_requests", [])
        if isinstance(row, Mapping) and clean_text(row.get("request_intent_id"))
    }
    for source_id, row in records_by_source.items():
        failure = failure_by_source.get(source_id, {})
        if isinstance(failure, Mapping):
            row["failure_error"] = clean_text(failure.get("error"))
        row["requires_manual_review"] = True
        row["has_evidence_packet"] = bool(row.get("latest_evidence_packet_id") or row.get("first_evidence_packet_id"))

    source_records = sorted(records_by_source.values(), key=lambda row: (row.get("market_id", ""), row.get("source_id", "")))
    reachable = [row for row in source_records if row.get("latest_accessibility_status") == "reachable"]
    repaired = [
        row
        for row in source_records
        if row.get("first_accessibility_status") == "failed" and row.get("latest_accessibility_status") == "reachable"
    ]
    no_retry = [row for row in source_records if row.get("latest_accessibility_status") == "no_retry"]
    missing = [row for row in source_records if row.get("latest_accessibility_status") == "replacement_missing"]
    blocked = [row for row in source_records if row.get("latest_accessibility_status") == "blocked"]
    failed = [
        row
        for row in source_records
        if row.get("latest_accessibility_status") in {"failed", "no_retry", "replacement_missing", "blocked"}
    ]
    with_packets = [row for row in source_records if row.get("has_evidence_packet") is True]

    return {
        "contract_version": SOURCE_BOARD_CONTRACT_VERSION,
        "generated_at": generated_at,
        "source_records": source_records,
        "reachable_sources": reachable,
        "failed_sources": failed,
        "repaired_sources": repaired,
        "no_retry_sources": no_retry,
        "replacement_missing_sources": missing,
        "blocked_sources": blocked,
        "sources_with_evidence_packets": with_packets,
        "sources_requiring_manual_review": [row for row in source_records if row.get("requires_manual_review") is True],
        "recommended_source_handling_updates": _recommended_source_handling_updates(source_records),
        "repair_result_summary": {
            "repaired_executable_count": repair_summary.get("repaired_executable_count", 0),
            "no_retry_count": repair_summary.get("no_retry_count", 0),
            "replacement_missing_count": repair_summary.get("replacement_missing_count", 0),
            "blocked_count": repair_summary.get("blocked_count", 0),
            "second_fetch_succeeded": repair_summary.get("second_fetch_succeeded", 0),
            "second_fetch_failed": repair_summary.get("second_fetch_failed", 0),
        },
        "no_autonomous_training_performed": True,
        "safety_summary": safe_summary(),
    }


def write_merged_source_status_board_011(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    out_path = Path(out_dir)
    board = build_merged_source_status_board()
    write_json(out_path / "merged_source_status_board_011.json", board)
    write_text(out_path / "merged_source_status_board_011.md", render_merged_source_status_board_markdown(board))
    return board


def render_merged_source_status_board_markdown(board: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Merged Source Status Board",
            "",
            f"- Source records: {len(board.get('source_records', []))}",
            f"- Reachable sources: {len(board.get('reachable_sources', []))}",
            f"- Failed or blocked sources: {len(board.get('failed_sources', []))}",
            f"- Repaired sources: {len(board.get('repaired_sources', []))}",
            f"- No autonomous training performed: `{str(board.get('no_autonomous_training_performed')).lower()}`",
            "",
            "## Reachable Sources",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('source_id')}` - {row.get('latest_source_url')}"
                for row in board.get("reachable_sources", [])
                if isinstance(row, Mapping)
            ),
            "",
            "## Sources Requiring Manual Review",
            "",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('source_id')}` - {row.get('latest_accessibility_status')}"
                for row in board.get("sources_requiring_manual_review", [])
                if isinstance(row, Mapping)
            ),
        ]
    ) + "\n"


def _base_record_from_009(row: Mapping[str, Any]) -> dict[str, Any]:
    status = clean_text(row.get("accessibility_status"))
    evidence_packet_id = clean_text(row.get("evidence_packet_id"))
    return {
        "source_id": clean_text(row.get("request_intent_id")),
        "request_intent_id": clean_text(row.get("request_intent_id")),
        "market_id": clean_text(row.get("market_id")),
        "market_title": clean_text(row.get("market_title")),
        "source_name": clean_text(row.get("source_name")),
        "source_category": clean_text(row.get("source_category")),
        "first_source_url": clean_text(row.get("source_url")),
        "latest_source_url": clean_text(row.get("source_url")),
        "first_accessibility_status": status,
        "latest_accessibility_status": status,
        "first_task_id": "PRACTICAL-009",
        "latest_task_id": "PRACTICAL-009",
        "first_evidence_packet_id": evidence_packet_id,
        "latest_evidence_packet_id": evidence_packet_id,
        "evidence_usable": row.get("evidence_usable") is True,
        "replay_usable": row.get("replay_usable") is True,
        "failure_category": clean_text(row.get("failure_category")),
        "failure_error": "",
        "recommended_handling": clean_text(row.get("recommended_handling")),
        "repair_status": "not_repaired",
        "operator_review_required": True,
        "requires_manual_review": True,
        "has_evidence_packet": bool(evidence_packet_id),
    }


def _empty_record(source_id: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "request_intent_id": source_id,
        "market_id": "",
        "market_title": "",
        "source_name": "",
        "source_category": "",
        "first_source_url": "",
        "latest_source_url": "",
        "first_accessibility_status": "unknown",
        "latest_accessibility_status": "unknown",
        "first_task_id": "",
        "latest_task_id": "",
        "first_evidence_packet_id": "",
        "latest_evidence_packet_id": "",
        "evidence_usable": False,
        "replay_usable": False,
        "failure_category": "",
        "failure_error": "",
        "recommended_handling": "",
        "repair_status": "",
        "operator_review_required": True,
        "requires_manual_review": True,
        "has_evidence_packet": False,
    }


def _recommended_source_handling_updates(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for row in records:
        status = clean_text(row.get("latest_accessibility_status"))
        handling = clean_text(row.get("repair_status")) or clean_text(row.get("recommended_handling")) or status
        updates.append(
            {
                "request_intent_id": clean_text(row.get("request_intent_id")),
                "market_id": clean_text(row.get("market_id")),
                "source_url": clean_text(row.get("latest_source_url")),
                "recommended_handling": handling,
                "requires_operator_review": True,
            }
        )
    return updates


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create the PRACTICAL-011 merged source status board.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for source status artifacts.")
    args = parser.parse_args(argv)
    write_merged_source_status_board_011(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
