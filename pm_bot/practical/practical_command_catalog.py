from __future__ import annotations

import argparse
from typing import Any, Mapping, Sequence

from pm_bot.practical.daily_workflow_summary import ARTIFACT_DIR_015, daily_workflow_safety_summary, prohibited_actions
from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, normalize_path, write_json, write_text

COMMAND_CATALOG_CONTRACT_VERSION = "pmbot_practical_command_catalog.v1"


def build_practical_command_catalog(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    artifact_dir = normalize_path(ARTIFACT_DIR_015)
    safe_commands = [
        _command(
            "view dashboard",
            f"python -m json.tool {artifact_dir}/daily_workflow_summary_015.json",
            "Print the daily summary JSON in a stable local format.",
            writes_files=False,
        ),
        _command(
            "summarize daily state",
            f"python -m pm_bot.practical.daily_workflow_summary --out-json {artifact_dir}/daily_workflow_summary_015.json --out-md {artifact_dir}/daily_workflow_summary_015.md",
            "Regenerate the local daily workflow summary from known artifact paths.",
        ),
        _command(
            "inspect active paper hypotheses",
            f"python -m pm_bot.practical.active_paper_hypotheses --queue pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json --out-json {artifact_dir}/active_paper_hypotheses_local_view.json --out-md {artifact_dir}/active_paper_hypotheses_local_view.md",
            "Create a local view of active paper hypotheses from the saved market queue.",
        ),
        _command(
            "inspect outcome recheck queue",
            "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.json",
            "View unresolved outcome status and recheck priority.",
            writes_files=False,
        ),
        _command(
            "inspect source learning scorecard",
            "python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_update_013.json",
            "View saved source status and source handling notes.",
            writes_files=False,
        ),
        _command(
            "inspect manual feedback packets",
            "python -m json.tool pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.json",
            "View pending manual feedback readiness across tracked markets.",
            writes_files=False,
        ),
        _command(
            "validate artifacts",
            f"python -m json.tool {artifact_dir}/practical_workflow_index_015.json",
            "Validate the workflow index JSON shape.",
            writes_files=False,
        ),
        _command(
            "run safety scan",
            f"python -m pm_bot.practical.practical_safety_scan --artifact-dir {artifact_dir} --out-json {artifact_dir}/daily_workflow_safety_scan_015.result.json --out-md {artifact_dir}/daily_workflow_safety_scan_015.md",
            "Scan daily workflow artifacts for unsafe action wording and unsafe flags.",
        ),
        _command(
            "prepare future outcome feedback",
            "python -m json.tool pm_bot/practical/artifacts/manual_outcome_feedback_014/manual_outcome_operator_guide_014.json",
            "Open the manual outcome guide before filling any future resolved outcome packet.",
            writes_files=False,
        ),
    ]
    return {
        "contract_version": COMMAND_CATALOG_CONTRACT_VERSION,
        "generated_at": generated_at,
        "safe_commands": safe_commands,
        "manual_only_steps": [
            "Collect actual outcome evidence outside PMBOT, then save it locally before any packet update.",
            "Curate replacement public source URLs manually before a separate approved source task.",
            "Review paper labels manually before generating feedback from a resolved packet.",
        ],
        "prohibited_commands": [
            "run-codex-once",
            "run-codex-batch",
            "Any OpenRouter command without separate approval.",
            "Any Polymarket API command without separate approval.",
            "Any wallet, signing, order, trading endpoint, scheduler, daemon, watcher, or polling command.",
        ],
        "command_notes": [
            "The daily catalog is local-only and finite.",
            "Public fetch commands are intentionally excluded from the daily runbook.",
            "Commands that write files target versioned local artifacts only.",
            "No command in safe_commands needs API keys, cookies, browser profiles, or authenticated endpoints.",
        ],
        "safety_summary": daily_workflow_safety_summary(),
    }


def run_practical_command_catalog(
    *, out_json_path: str, out_md_path: str, generated_at: str = GENERATED_AT
) -> dict[str, Any]:
    catalog = build_practical_command_catalog(generated_at=generated_at)
    write_json(out_json_path, catalog)
    write_text(out_md_path, render_practical_command_catalog_markdown(catalog))
    return catalog


def render_practical_command_catalog_markdown(catalog: Mapping[str, Any]) -> str:
    lines = ["# Practical Command Catalog 015", "", "## Safe local commands", ""]
    for row in catalog.get("safe_commands", []):
        if not isinstance(row, Mapping):
            continue
        lines.extend(
            [
                f"### {row.get('category')}",
                "",
                f"- Command: `{row.get('command')}`",
                f"- Purpose: {row.get('purpose')}",
                f"- Writes files: `{str(row.get('writes_files')).lower()}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Manual-only steps",
            "",
            *bullet_lines(str(item) for item in catalog.get("manual_only_steps", [])),
            "",
            "## Prohibited commands",
            "",
            *bullet_lines(str(item) for item in catalog.get("prohibited_commands", [])),
            "",
            "## Notes",
            "",
            *bullet_lines(str(item) for item in catalog.get("command_notes", [])),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _command(category: str, command: str, purpose: str, *, writes_files: bool = True) -> dict[str, Any]:
    return {
        "category": category,
        "command": command,
        "purpose": purpose,
        "local_only": True,
        "requires_api_key": False,
        "requires_network": False,
        "writes_files": writes_files,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a safe local PMBOT practical command catalog.")
    parser.add_argument("--out-json", required=True, help="Output command catalog JSON.")
    parser.add_argument("--out-md", required=True, help="Output command catalog Markdown.")
    args = parser.parse_args(argv)
    run_practical_command_catalog(out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
