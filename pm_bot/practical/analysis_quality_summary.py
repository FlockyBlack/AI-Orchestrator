from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.paper_feedback import FEEDBACK_RESULT_CONTRACT_VERSION
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, safe_summary, write_json, write_text

QUALITY_SUMMARY_CONTRACT_VERSION = "pmbot_analysis_quality_summary.v1"
QUALITY_LABELS = (
    "useful",
    "incomplete",
    "wrong_due_to_missing_evidence",
    "wrong_due_to_bad_reasoning",
    "unresolved",
    "ambiguous",
)


def build_analysis_quality_summary(feedback_dir: str | Path) -> dict[str, Any]:
    feedback_results = _load_feedback_dir(feedback_dir)
    counts = Counter(clean_text(row.get("analysis_quality_label") or "unresolved") for row in feedback_results)
    missing_lessons = Counter(
        lesson
        for feedback in feedback_results
        for lesson in feedback.get("missing_evidence_lessons", [])
        if isinstance(lesson, str)
    )
    reasoning_lessons = Counter(
        lesson for feedback in feedback_results for lesson in feedback.get("reasoning_lessons", []) if isinstance(lesson, str)
    )
    improvements = Counter(
        note for feedback in feedback_results for note in feedback.get("next_prompt_improvements", []) if isinstance(note, str)
    )
    return {
        "contract_version": QUALITY_SUMMARY_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "feedback_dir": normalize_path(feedback_dir),
        "total_feedback_items": len(feedback_results),
        "useful_count": counts.get("useful", 0),
        "incomplete_count": counts.get("incomplete", 0),
        "wrong_due_to_missing_evidence_count": counts.get("wrong_due_to_missing_evidence", 0),
        "wrong_due_to_bad_reasoning_count": counts.get("wrong_due_to_bad_reasoning", 0),
        "unresolved_count": counts.get("unresolved", 0),
        "ambiguous_count": counts.get("ambiguous", 0),
        "recurring_missing_evidence": [item for item, _ in missing_lessons.most_common()],
        "recurring_reasoning_lessons": [item for item, _ in reasoning_lessons.most_common()],
        "next_prompt_improvements": [item for item, _ in improvements.most_common()],
        "safety_summary": safe_summary(),
    }


def run_analysis_quality_summary(
    *,
    feedback_dir: str | Path,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    summary = build_analysis_quality_summary(feedback_dir)
    if out_json_path is not None:
        write_json(out_json_path, summary)
    if out_md_path is not None:
        write_text(out_md_path, render_analysis_quality_summary_markdown(summary))
    return summary


def render_analysis_quality_summary_markdown(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Analysis Quality Summary",
            "",
            f"- Feedback items: {summary['total_feedback_items']}",
            f"- Useful: {summary['useful_count']}",
            f"- Incomplete: {summary['incomplete_count']}",
            f"- Missing-evidence failures: {summary['wrong_due_to_missing_evidence_count']}",
            f"- Bad-reasoning failures: {summary['wrong_due_to_bad_reasoning_count']}",
            f"- Unresolved: {summary['unresolved_count']}",
            f"- Ambiguous: {summary['ambiguous_count']}",
            "",
            "## Recurring missing evidence",
            "",
            *bullet_lines(summary["recurring_missing_evidence"]),
            "",
            "## Recurring reasoning lessons",
            "",
            *bullet_lines(summary["recurring_reasoning_lessons"]),
            "",
            "## Next prompt improvements",
            "",
            *bullet_lines(summary["next_prompt_improvements"]),
            "",
            "## Safety boundary",
            "",
            "- Local paper feedback artifacts only.",
            "- No autonomous training is performed.",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate local PMBOT paper feedback quality labels.")
    parser.add_argument("--feedback-dir", required=True, help="Directory containing local feedback JSON artifacts.")
    parser.add_argument("--out-json", required=True, help="Output quality summary JSON.")
    parser.add_argument("--out-md", required=True, help="Output quality summary Markdown.")
    args = parser.parse_args(argv)
    run_analysis_quality_summary(feedback_dir=args.feedback_dir, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


def _load_feedback_dir(feedback_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(feedback_dir)
    if not root.exists() or not root.is_dir():
        return []
    results = []
    for path in sorted(root.glob("*.json")):
        try:
            payload = load_json_object(path, label="feedback result")
        except ValueError:
            continue
        if payload.get("contract_version") == FEEDBACK_RESULT_CONTRACT_VERSION:
            results.append(payload)
    return results


if __name__ == "__main__":
    raise SystemExit(main())
