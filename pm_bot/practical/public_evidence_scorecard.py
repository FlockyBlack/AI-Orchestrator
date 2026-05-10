from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, load_json_object, safe_summary, write_json, write_text

SCORECARD_CONTRACT_VERSION = "pmbot_public_evidence_scorecard.v1"
DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/public_evidence_dashboard_011")
FETCH_008_SUMMARY_PATH = Path("pm_bot/practical/artifacts/public_read_only_fetch_execution_008/fetch_execution_summary_008.result.json")
FETCH_010_SUMMARY_PATH = Path(
    "pm_bot/practical/artifacts/public_source_url_fixes_010/second_fetch_execution_summary_010.result.json"
)
REPLAY_008_PATH = Path("pm_bot/practical/artifacts/public_read_only_fetch_execution_008/replay/replayed_source_packets_008.json")
REPLAY_010_PATH = Path("pm_bot/practical/artifacts/public_source_url_fixes_010/replay/replayed_source_packets_010.json")
REPAIR_SUMMARY_010_PATH = Path("pm_bot/practical/artifacts/public_source_url_fixes_010/source_url_repair_result_summary_010.json")
UPDATE_CANDIDATE_009_PATH = Path("pm_bot/practical/artifacts/public_evidence_review_009/paper_hypothesis_update_candidate_009.json")


def build_public_evidence_scorecard(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    fetch_008 = load_json_object(FETCH_008_SUMMARY_PATH)
    fetch_010 = load_json_object(FETCH_010_SUMMARY_PATH)
    replay_008 = load_json_object(REPLAY_008_PATH)
    replay_010 = load_json_object(REPLAY_010_PATH)
    repair_summary = load_json_object(REPAIR_SUMMARY_010_PATH)
    update_candidate_count = 1 if UPDATE_CANDIDATE_009_PATH.exists() else 0

    attempts = int(fetch_008.get("request_count_attempted", 0)) + int(fetch_010.get("request_count_attempted", 0))
    successes = int(fetch_008.get("request_count_succeeded", 0)) + int(fetch_010.get("request_count_succeeded", 0))
    failures = int(fetch_008.get("request_count_failed", 0)) + int(fetch_010.get("request_count_failed", 0))
    blocked = int(fetch_008.get("request_count_blocked", 0)) + int(fetch_010.get("request_count_blocked", 0))
    evidence_packet_count = int(fetch_008.get("evidence_packets_created_count", 0)) + int(
        fetch_010.get("evidence_packets_created_count", 0)
    )
    replay_success_count = sum(1 for replay in (replay_008, replay_010) if replay.get("replay_performed") is True)

    return {
        "contract_version": SCORECARD_CONTRACT_VERSION,
        "generated_at": generated_at,
        "total_fetch_attempts": attempts,
        "total_fetch_successes": successes,
        "total_fetch_failures": failures,
        "total_fetch_blocked": blocked,
        "evidence_packet_count": evidence_packet_count,
        "replay_success_count": replay_success_count,
        "update_candidate_count": update_candidate_count,
        "automatic_update_count": 0,
        "source_repair_count": int(repair_summary.get("repaired_executable_count", 0)),
        "source_still_missing_count": int(repair_summary.get("replacement_missing_count", 0)),
        "accessibility_success_rate_label": _accessibility_success_label(successes, attempts),
        "quality_notes": [
            "This scorecard covers public evidence collection and source accessibility only.",
            "Saved evidence packets exist for SCOTUS and Kraken source checks.",
            "Several source records still require operator review or manual URL collection.",
            "No paper hypothesis was updated automatically.",
        ],
        "next_source_improvement_actions": [
            "Review the source URL backlog before any later scoped public-source task.",
            "Collect missing replacement URLs manually where the saved artifacts do not contain a usable public URL.",
            "Keep outcome resolution separate from source accessibility review.",
        ],
        "safety_summary": safe_summary(),
    }


def write_public_evidence_scorecard_011(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    out_path = Path(out_dir)
    scorecard = build_public_evidence_scorecard()
    write_json(out_path / "public_evidence_scorecard_011.json", scorecard)
    write_text(out_path / "public_evidence_scorecard_011.md", render_public_evidence_scorecard_markdown(scorecard))
    return scorecard


def render_public_evidence_scorecard_markdown(scorecard: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Public Evidence Scorecard",
            "",
            f"- Fetch attempts: {scorecard.get('total_fetch_attempts', 0)}",
            f"- Fetch successes: {scorecard.get('total_fetch_successes', 0)}",
            f"- Fetch failures: {scorecard.get('total_fetch_failures', 0)}",
            f"- Fetch blocked: {scorecard.get('total_fetch_blocked', 0)}",
            f"- Evidence packets: {scorecard.get('evidence_packet_count', 0)}",
            f"- Accessibility label: `{scorecard.get('accessibility_success_rate_label')}`",
            "",
            "## Quality Notes",
            "",
            *bullet_lines(str(item) for item in scorecard.get("quality_notes", [])),
            "",
            "## Next Source Improvement Actions",
            "",
            *bullet_lines(str(item) for item in scorecard.get("next_source_improvement_actions", [])),
        ]
    ) + "\n"


def _accessibility_success_label(successes: int, attempts: int) -> str:
    if attempts <= 0:
        return "insufficient"
    rate = successes / attempts
    if rate >= 0.75:
        return "high"
    if rate >= 0.5:
        return "medium"
    if successes > 0:
        return "low"
    return "insufficient"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create the PRACTICAL-011 public evidence scorecard.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for scorecard artifacts.")
    args = parser.parse_args(argv)
    write_public_evidence_scorecard_011(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
