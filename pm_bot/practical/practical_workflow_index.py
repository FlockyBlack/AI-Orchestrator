from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.daily_workflow_summary import ARTIFACT_DIR_015, NEXT_RECOMMENDED_ACTION, daily_workflow_safety_summary
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, normalize_path, write_json, write_text

WORKFLOW_INDEX_CONTRACT_VERSION = "pmbot_practical_workflow_index.v1"


def build_practical_workflow_index(
    *, expected_paths: Sequence[str | Path] = (), generated_at: str = GENERATED_AT
) -> dict[str, Any]:
    primary_dashboard = "docs/PMBOT_PRACTICAL_DAILY_OPERATOR_RUNBOOK.md"
    daily_summary = _paired("daily_summary", ARTIFACT_DIR_015 / "daily_workflow_summary_015")
    outcome_recheck_queue = _paired(
        "outcome_recheck_queue",
        "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013",
    )
    source_learning_scorecard = _paired(
        "source_learning_scorecard",
        "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_operator_view_013",
    )
    manual_feedback_dashboard = _paired(
        "manual_feedback_dashboard",
        "pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014",
    )
    paper_tracking_snapshot = _paired(
        "paper_tracking_snapshot",
        "pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012",
    )
    public_evidence_dashboard = _paired(
        "public_evidence_dashboard",
        "pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011",
    )
    operator_morning_cards = [
        _file("operator_quickstart_card_015", ARTIFACT_DIR_015 / "operator_quickstart_card_015.md"),
        _file(
            "operator_morning_card_011",
            "pm_bot/practical/artifacts/public_evidence_dashboard_011/operator_morning_card_011.md",
        ),
        _file(
            "operator_morning_card_after_update_012",
            "pm_bot/practical/artifacts/paper_update_application_012/operator_morning_card_after_update_012.md",
        ),
        _file(
            "operator_console_feedback_loop_014",
            "pm_bot/practical/artifacts/manual_outcome_feedback_014/operator_console_feedback_loop_014.md",
        ),
    ]
    docs_to_read = [
        _file("daily_operator_runbook", primary_dashboard),
        _file("add_new_market_workflow", "docs/PMBOT_HOW_TO_ADD_A_NEW_LOCAL_MARKET_PACKET.md"),
        _file("process_resolved_market_workflow", "docs/PMBOT_HOW_TO_PROCESS_A_RESOLVED_MARKET_OUTCOME.md"),
        _file("public_evidence_dashboard_doc", "docs/PMBOT_PUBLIC_EVIDENCE_TRACKING_DASHBOARD.md"),
        _file("paper_update_application_doc", "docs/PMBOT_OPERATOR_APPROVED_PAPER_UPDATE_APPLICATION.md"),
        _file("manual_outcome_feedback_doc", "docs/PMBOT_MANUAL_OUTCOME_RESOLUTION_FEEDBACK_PACKET.md"),
    ]
    artifacts_by_phase = {
        "PRACTICAL-004": [
            "pm_bot/practical/artifacts/real_market_batch_004/selected_real_market_batch.md",
            "pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json",
        ],
        "PRACTICAL-008": [
            "pm_bot/practical/artifacts/public_read_only_fetch_execution_008/fetch_execution_summary_008.result.json",
            "pm_bot/practical/artifacts/public_read_only_fetch_execution_008/evidence_packets",
        ],
        "PRACTICAL-010": [
            "pm_bot/practical/artifacts/public_source_url_fixes_010/source_url_repair_result_summary_010.json",
            "pm_bot/practical/artifacts/public_source_url_fixes_010/evidence_packets",
        ],
        "PRACTICAL-011": [
            "pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.json",
            "pm_bot/practical/artifacts/public_evidence_dashboard_011/source_url_backlog_011.json",
        ],
        "PRACTICAL-012": [
            "pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.json",
            "pm_bot/practical/artifacts/paper_update_application_012/applied_paper_update_012.json",
        ],
        "PRACTICAL-013": [
            "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.json",
            "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_update_013.json",
        ],
        "PRACTICAL-014": [
            "pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.json",
            "pm_bot/practical/artifacts/manual_outcome_feedback_014/markets",
        ],
        "PRACTICAL-015": [
            normalize_path(ARTIFACT_DIR_015 / "daily_workflow_summary_015.json"),
            normalize_path(ARTIFACT_DIR_015 / "practical_command_catalog_015.json"),
            normalize_path(ARTIFACT_DIR_015 / "practical_daily_checklist_015.json"),
        ],
    }
    expected = _expected_paths(
        primary_dashboard=primary_dashboard,
        daily_summary=daily_summary,
        outcome_recheck_queue=outcome_recheck_queue,
        source_learning_scorecard=source_learning_scorecard,
        manual_feedback_dashboard=manual_feedback_dashboard,
        paper_tracking_snapshot=paper_tracking_snapshot,
        public_evidence_dashboard=public_evidence_dashboard,
        operator_morning_cards=operator_morning_cards,
        docs_to_read=docs_to_read,
        artifacts_by_phase=artifacts_by_phase,
        extra_paths=expected_paths,
    )
    return {
        "contract_version": WORKFLOW_INDEX_CONTRACT_VERSION,
        "generated_at": generated_at,
        "primary_dashboard": _file("primary_dashboard", primary_dashboard),
        "daily_summary": daily_summary,
        "outcome_recheck_queue": outcome_recheck_queue,
        "source_learning_scorecard": source_learning_scorecard,
        "manual_feedback_dashboard": manual_feedback_dashboard,
        "paper_tracking_snapshot": paper_tracking_snapshot,
        "public_evidence_dashboard": public_evidence_dashboard,
        "operator_morning_cards": operator_morning_cards,
        "docs_to_read": docs_to_read,
        "artifacts_by_phase": artifacts_by_phase,
        "missing_expected_artifacts": [
            {"path": normalize_path(path), "reason": "expected local workflow artifact is absent"}
            for path in expected
            if not Path(path).exists()
        ],
        "next_operator_actions": [
            "Open the primary dashboard first.",
            "Use the quickstart card for the first daily pass.",
            "Use the decision matrix before starting the next Codex task.",
            f"Default next task: `{NEXT_RECOMMENDED_ACTION}`.",
        ],
        "safety_summary": daily_workflow_safety_summary(),
    }


def run_practical_workflow_index(
    *,
    out_json_path: str | Path,
    out_md_path: str | Path,
    expected_paths: Sequence[str | Path] = (),
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    index = build_practical_workflow_index(expected_paths=expected_paths, generated_at=generated_at)
    write_json(out_json_path, index)
    write_text(out_md_path, render_practical_workflow_index_markdown(index))
    return index


def render_practical_workflow_index_markdown(index: Mapping[str, Any]) -> str:
    lines = [
        "# Practical Workflow Index 015",
        "",
        f"- Primary dashboard: `{index.get('primary_dashboard', {}).get('path')}`",
        f"- Missing expected artifacts: {len(index.get('missing_expected_artifacts', []))}",
        "",
        "## Open first",
        "",
        f"- `{index.get('daily_summary', {}).get('md_path')}`",
        f"- `{index.get('manual_feedback_dashboard', {}).get('md_path')}`",
        f"- `{index.get('outcome_recheck_queue', {}).get('md_path')}`",
        "",
        "## Operator morning cards",
        "",
        *bullet_lines(f"`{row.get('path')}`" for row in _mapping_rows(index.get("operator_morning_cards"))),
        "",
        "## Docs to read",
        "",
        *bullet_lines(f"`{row.get('path')}`" for row in _mapping_rows(index.get("docs_to_read"))),
        "",
        "## Missing expected artifacts",
        "",
        *bullet_lines(f"`{row.get('path')}` - {row.get('reason')}" for row in _mapping_rows(index.get("missing_expected_artifacts"))),
        "",
        "## Next operator actions",
        "",
        *bullet_lines(str(item) for item in index.get("next_operator_actions", [])),
    ]
    return "\n".join(lines) + "\n"


def _file(label: str, path: str | Path) -> dict[str, Any]:
    path_obj = Path(path)
    return {"label": label, "path": normalize_path(path_obj), "exists": path_obj.exists()}


def _paired(label: str, base: str | Path) -> dict[str, Any]:
    base_text = normalize_path(base)
    json_path = Path(f"{base_text}.json")
    md_path = Path(f"{base_text}.md")
    return {
        "label": label,
        "json_path": normalize_path(json_path),
        "md_path": normalize_path(md_path),
        "json_exists": json_path.exists(),
        "md_exists": md_path.exists(),
    }


def _expected_paths(
    *,
    primary_dashboard: str | Path,
    daily_summary: Mapping[str, Any],
    outcome_recheck_queue: Mapping[str, Any],
    source_learning_scorecard: Mapping[str, Any],
    manual_feedback_dashboard: Mapping[str, Any],
    paper_tracking_snapshot: Mapping[str, Any],
    public_evidence_dashboard: Mapping[str, Any],
    operator_morning_cards: Sequence[Mapping[str, Any]],
    docs_to_read: Sequence[Mapping[str, Any]],
    artifacts_by_phase: Mapping[str, Sequence[str]],
    extra_paths: Sequence[str | Path],
) -> list[str]:
    paths = [normalize_path(primary_dashboard)]
    for paired in (
        daily_summary,
        outcome_recheck_queue,
        source_learning_scorecard,
        manual_feedback_dashboard,
        paper_tracking_snapshot,
        public_evidence_dashboard,
    ):
        paths.extend([str(paired.get("json_path", "")), str(paired.get("md_path", ""))])
    paths.extend(str(row.get("path")) for row in operator_morning_cards)
    paths.extend(str(row.get("path")) for row in docs_to_read)
    for phase_paths in artifacts_by_phase.values():
        paths.extend(phase_paths)
    paths.extend(normalize_path(path) for path in extra_paths)
    return sorted({path for path in paths if path})


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index the main PMBOT practical workflow artifacts.")
    parser.add_argument("--out-json", required=True, help="Output workflow index JSON.")
    parser.add_argument("--out-md", required=True, help="Output workflow index Markdown.")
    parser.add_argument("--expected-path", action="append", default=[], help="Extra expected path to include.")
    args = parser.parse_args(argv)
    run_practical_workflow_index(
        out_json_path=args.out_json,
        out_md_path=args.out_md,
        expected_paths=args.expected_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
