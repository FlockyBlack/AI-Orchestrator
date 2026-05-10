from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.daily_workflow_summary import (
    ARTIFACT_DIR_015,
    build_daily_workflow_summary,
    daily_workflow_safety_summary,
    prohibited_actions,
)
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, load_json_object, write_json, write_text

DAILY_CHECKLIST_CONTRACT_VERSION = "pmbot_practical_daily_checklist.v1"


def build_practical_daily_checklist(
    *, summary_path: str | Path | None = None, generated_at: str = GENERATED_AT
) -> dict[str, Any]:
    summary = load_json_object(summary_path, label="daily workflow summary") if summary_path else build_daily_workflow_summary()
    checklist_items = [
        _item("Morning check", "Open the quickstart card and daily workflow summary.", "can_run_now"),
        _item("Morning check", "Record unresolved outcome count, feedback-ready count, and source URL backlog count.", "can_run_now"),
        _item("Evidence check", "Open the public evidence dashboard and confirm saved evidence packet count.", "can_run_now"),
        _item("Source URL check", "Open source_url_backlog_011.md and note replacement needs.", "manual_required"),
        _item("Outcome recheck", "Open outcome_recheck_queue_013.md and keep unresolved markets pending.", "manual_required"),
        _item("Paper update review", "Open paper_tracking_state_snapshot_012.md and check applied update count.", "can_run_now"),
        _item("Feedback readiness check", "Open feedback_readiness_dashboard_014.md and confirm feedback-ready count.", "can_run_now"),
        _item("Safety check", "Run the daily workflow safety scan after artifact changes.", "can_run_now"),
        _item("End-of-day notes", "Write local notes for changed source URLs or resolved outcomes.", "manual_required"),
    ]
    return {
        "contract_version": DAILY_CHECKLIST_CONTRACT_VERSION,
        "generated_at": generated_at,
        "checklist_items": checklist_items,
        "blocked_items": summary.get("blocked_items", []),
        "manual_required_items": [row for row in checklist_items if row["status"] == "manual_required"],
        "can_run_now_items": [row for row in checklist_items if row["status"] == "can_run_now"],
        "should_not_run_items": [
            {"item": action, "reason": "Outside PRACTICAL-015 safety boundary"} for action in prohibited_actions()
        ],
        "safety_summary": daily_workflow_safety_summary(),
    }


def run_practical_daily_checklist(
    *,
    out_json_path: str | Path,
    out_md_path: str | Path,
    summary_path: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    checklist = build_practical_daily_checklist(summary_path=summary_path, generated_at=generated_at)
    write_json(out_json_path, checklist)
    write_text(out_md_path, render_practical_daily_checklist_markdown(checklist))
    return checklist


def render_practical_daily_checklist_markdown(checklist: Mapping[str, Any]) -> str:
    lines = ["# Practical Daily Checklist 015", ""]
    for section in (
        "Morning check",
        "Evidence check",
        "Source URL check",
        "Outcome recheck",
        "Paper update review",
        "Feedback readiness check",
        "Safety check",
        "End-of-day notes",
    ):
        lines.extend([f"## {section}", ""])
        rows = [row for row in checklist.get("checklist_items", []) if isinstance(row, Mapping) and row.get("section") == section]
        lines.extend(bullet_lines(f"{row.get('item')} (`{row.get('status')}`)" for row in rows))
        lines.append("")
    lines.extend(
        [
            "## Do not run",
            "",
            *bullet_lines(str(row.get("item")) for row in checklist.get("should_not_run_items", []) if isinstance(row, Mapping)),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _item(section: str, item: str, status: str) -> dict[str, str]:
    return {"section": section, "item": item, "status": status}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a short PMBOT practical daily checklist.")
    parser.add_argument("--out-json", required=True, help="Output checklist JSON.")
    parser.add_argument("--out-md", required=True, help="Output checklist Markdown.")
    parser.add_argument(
        "--summary",
        default=str(ARTIFACT_DIR_015 / "daily_workflow_summary_015.json"),
        help="Optional existing daily summary JSON.",
    )
    args = parser.parse_args(argv)
    summary_path = args.summary if Path(args.summary).exists() else None
    run_practical_daily_checklist(out_json_path=args.out_json, out_md_path=args.out_md, summary_path=summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
