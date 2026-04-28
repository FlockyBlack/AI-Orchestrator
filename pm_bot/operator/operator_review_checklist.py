import argparse
import json
from pathlib import Path


def _parse_args():
    parser = argparse.ArgumentParser(description="Build the PMBOT operator review checklist.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_operator_review_checklist(root: Path):
    _ = root
    items = [
        "verify fixture-only source",
        "verify paper-only mode",
        "verify no live API",
        "verify no wallet/private key",
        "verify no real order execution",
        "review accepted paper candidates",
        "review rejected cases",
        "review watchlist no-action cases",
        "review audit status",
        "review adversarial validation status",
        "confirm no live execution approval exists",
        "confirm future live mode requires separate approval",
    ]
    return {
        "schema_version": "v1",
        "checklist_id": "PMBOT-BATCH-006-OPERATOR-CHECKLIST",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "operator_review_only": True,
        "items": [{"step": item, "required": True, "status": "pending_human_review"} for item in items],
        "explicit_no_execution_statement": "Checklist completion does not authorize live fetchers, wallet use, orders, trades, or runtime wiring.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Operator Review Checklist",
        "",
        "Human review checklist for the PMBOT-BATCH-006 export bundle.",
        "",
    ]
    lines.extend(f"- [ ] {item['step']}" for item in report["items"])
    lines.extend(["", f"- {report['explicit_no_execution_statement']}", ""])
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_operator_review_checklist(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
