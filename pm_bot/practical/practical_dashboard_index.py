from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, load_json_object, normalize_path, safe_summary, write_json, write_text

DASHBOARD_INDEX_CONTRACT_VERSION = "pmbot_practical_dashboard_index.v1"

CATEGORY_BY_CONTRACT = {
    "pmbot_one_market_analysis_result.v1": "analyses",
    "pmbot_one_market_paper_feedback_result.v1": "feedback_results",
    "pmbot_source_learning_ledger.v1": "source_ledgers",
    "pmbot_source_learning_batch_ledger.v1": "source_ledgers",
    "pmbot_market_queue_summary.v1": "queue_summaries",
    "pmbot_practical_operator_console.v1": "operator_consoles",
    "pmbot_outcome_check_queue.v1": "outcome_queues",
}


def build_practical_dashboard_index(artifact_dirs: Sequence[str | Path]) -> dict[str, Any]:
    index: dict[str, Any] = {
        "contract_version": DASHBOARD_INDEX_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "artifact_dirs": [normalize_path(path) for path in artifact_dirs],
        "analyses": [],
        "feedback_results": [],
        "source_ledgers": [],
        "queue_summaries": [],
        "operator_consoles": [],
        "outcome_queues": [],
        "next_operator_actions": [],
        "safety_summary": safe_summary(),
    }
    for root in [Path(path) for path in artifact_dirs]:
        if not root.exists() or not root.is_dir():
            continue
        for path in sorted(root.rglob("*.json")):
            try:
                payload = load_json_object(path, label="artifact")
            except ValueError:
                continue
            category = CATEGORY_BY_CONTRACT.get(str(payload.get("contract_version")))
            if not category:
                continue
            entry = _artifact_entry(path, payload)
            index[category].append(entry)
            for action in payload.get("next_operator_actions", []):
                if isinstance(action, Mapping):
                    index["next_operator_actions"].append(dict(action))
    return index


def run_practical_dashboard_index(
    *,
    artifact_dirs: Sequence[str | Path],
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    index = build_practical_dashboard_index(artifact_dirs)
    if out_json_path is not None:
        write_json(out_json_path, index)
    if out_md_path is not None:
        write_text(out_md_path, render_practical_dashboard_index_markdown(index))
    return index


def render_practical_dashboard_index_markdown(index: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Practical Dashboard Index",
            "",
            f"- Generated at: `{index['generated_at']}`",
            f"- Analyses: {len(index['analyses'])}",
            f"- Feedback results: {len(index['feedback_results'])}",
            f"- Source ledgers: {len(index['source_ledgers'])}",
            f"- Queue summaries: {len(index['queue_summaries'])}",
            f"- Operator consoles: {len(index['operator_consoles'])}",
            f"- Outcome queues: {len(index['outcome_queues'])}",
            "",
            "## Next operator actions",
            "",
            *bullet_lines(
                f"`{row.get('market_id', row.get('queue_item_id', 'unknown'))}` - {row.get('next_operator_action')}"
                for row in index["next_operator_actions"][:10]
            ),
            "",
            "## Safety boundary",
            "",
            "- Only explicit artifact directories are scanned.",
            "- No repository-wide scan or live fetch is performed.",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index PMBOT practical artifacts from explicit local directories.")
    parser.add_argument("--artifact-dir", action="append", required=True, help="Artifact directory to scan; repeatable.")
    parser.add_argument("--out-json", required=True, help="Output dashboard index JSON.")
    parser.add_argument("--out-md", required=True, help="Output dashboard index Markdown.")
    args = parser.parse_args(argv)
    run_practical_dashboard_index(artifact_dirs=args.artifact_dir, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


def _artifact_entry(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "path": normalize_path(path),
        "contract_version": str(payload.get("contract_version", "")),
        "id": str(
            payload.get("analysis_id")
            or payload.get("feedback_id")
            or payload.get("ledger_id")
            or payload.get("contract_version")
        ),
        "generated_at": str(payload.get("generated_at", "")),
    }


if __name__ == "__main__":
    raise SystemExit(main())
