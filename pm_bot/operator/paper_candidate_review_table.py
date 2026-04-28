import argparse
import importlib.util
import json
from pathlib import Path


def _load_support(root: Path):
    path = root / "pm_bot" / "operator" / "operator_support.py"
    spec = importlib.util.spec_from_file_location("pmbot_operator_support", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args():
    parser = argparse.ArgumentParser(description="Build the PMBOT paper candidate review table.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_paper_candidate_review_table(root: Path):
    rows = _load_support(root).build_candidate_rows(root)
    return {
        "schema_version": "v1",
        "table_id": "PMBOT-BATCH-006-PAPER-CANDIDATE-REVIEW",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "operator_review_only": True,
        "allowed_operator_actions": [
            "review_only",
            "reject_no_action",
            "watchlist_no_action",
            "paper_monitor_no_action",
        ],
        "rows": rows,
        "explicit_no_execution_statement": (
            "This review table is for paper research and operator review only. No buy, sell, trade, submit_order, "
            "execute, live_action, or real_position behavior exists."
        ),
    }


def render_markdown(report):
    lines = [
        "# PMBOT Paper Candidate Review Table",
        "",
        "Deterministic synthetic candidate table for local operator review only.",
        "",
        "| candidate_id | decision | confidence | operator_action | reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['candidate_id']} | {row['decision']} | {row['confidence_score']} ({row['confidence_band']}) | "
            f"{row['operator_action']} | {row['rejection_or_watchlist_reason']} |"
        )
    lines.extend(["", f"- {report['explicit_no_execution_statement']}", ""])
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_paper_candidate_review_table(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
