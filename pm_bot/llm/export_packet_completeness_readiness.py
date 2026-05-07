import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import packet_completeness_scorer as scorer  # noqa: E402


TASK_ID = scorer.TASK_ID
GENERATED_BY = "pm_bot/llm/export_packet_completeness_readiness.py"


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export deterministic local packet completeness readiness gate artifacts."
    )
    parser.add_argument("--write", action="store_true", help="Write JSON and Markdown gate artifacts.")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown instead of JSON.")
    return parser.parse_args(argv)


def write_packet_completeness_readiness_artifacts(root=ROOT):
    result = scorer.write_current_llm_batch_readiness_gate_artifacts(root=root)
    return {
        **result,
        "generated_by": GENERATED_BY,
        "network_calls_performed": 0,
        "orders_created": 0,
        "queue_items_created": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(
            json.dumps(
                write_packet_completeness_readiness_artifacts(ROOT),
                indent=2,
                ensure_ascii=True,
            )
        )
        return 0
    gate = scorer.build_batch_readiness_gate(root=ROOT)
    if args.markdown:
        print(scorer.render_batch_readiness_gate_markdown(gate), end="")
    else:
        print(json.dumps(gate, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
