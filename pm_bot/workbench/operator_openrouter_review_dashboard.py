import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-OPENROUTER-053-OPERATOR-OPENROUTER-REVIEW-DASHBOARD"
SCHEMA_VERSION = "operator_openrouter_review_dashboard.v1"
GENERATED_BY = "pm_bot/workbench/operator_openrouter_review_dashboard.py"

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import openrouter_operator_review_artifacts_053 as artifacts_053  # noqa: E402
from pm_bot.llm import export_packet_completeness_readiness as packet_readiness  # noqa: E402
from pm_bot.llm import resolution_source_normalizer as source_normalizer  # noqa: E402


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export the static PMBOT OpenRouter operator review dashboard."
    )
    parser.add_argument("--write", action="store_true", help="Write dashboard JSON and Markdown artifacts.")
    parser.add_argument("--markdown", action="store_true", help="Print dashboard Markdown instead of JSON.")
    return parser.parse_args(argv)


def build_operator_openrouter_review_dashboard(root=ROOT):
    return artifacts_053.build_operator_openrouter_review_dashboard(root=root)


def render_markdown(dashboard):
    return artifacts_053.render_operator_openrouter_review_dashboard_markdown(dashboard)


def write_operator_openrouter_review_dashboard_artifacts(root=ROOT):
    gate_result = packet_readiness.write_packet_completeness_readiness_artifacts(root=root)
    source_result = source_normalizer.write_resolution_source_normalization_artifacts(root=root)
    dashboard = build_operator_openrouter_review_dashboard(root=root)
    artifacts_053._write_json(artifacts_053.SOURCE_PATHS["dashboard_json"], dashboard, root=root)
    artifacts_053._write_text(
        artifacts_053.SOURCE_PATHS["dashboard_md"],
        render_markdown(dashboard),
        root=root,
    )
    return {
        "task_id": TASK_ID,
        "status": "operator_openrouter_review_dashboard_created",
        "files_written": [
            *gate_result["files_written"],
            *source_result["files_written"],
            artifacts_053.SOURCE_PATHS["dashboard_json"],
            artifacts_053.SOURCE_PATHS["dashboard_md"],
        ],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "network_calls": 0,
        "orders_created": 0,
        "queue_items_created": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_operator_openrouter_review_dashboard_artifacts(ROOT), indent=2, ensure_ascii=True))
        return 0
    dashboard = build_operator_openrouter_review_dashboard(ROOT)
    if args.markdown:
        print(render_markdown(dashboard), end="")
    else:
        print(json.dumps(dashboard, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
