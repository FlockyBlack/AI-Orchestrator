import argparse
import importlib.util
import json
from pathlib import Path


def _load_support(root: Path):
    path = root / "pm_bot" / "validation" / "adversarial_support.py"
    spec = importlib.util.spec_from_file_location("pmbot_adversarial_support", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args():
    parser = argparse.ArgumentParser(description="Run deterministic PMBOT adversarial replay validation.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_adversarial_replay_report(root: Path):
    support = _load_support(root)
    cases = support.load_replay_cases(root)
    evaluations = [support.evaluate_replay_case(case) for case in cases]
    pass_count = sum(1 for item in evaluations if item["decision_matches_expected"])
    false_positives = [item for item in evaluations if item["is_false_positive"]]
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-005-ADVERSARIAL-REPLAY",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "total_cases": len(evaluations),
        "passed_cases": pass_count,
        "failed_cases": len(evaluations) - pass_count,
        "false_positive_count": len(false_positives),
        "cases": evaluations,
        "decision_counts": {
            "exclude": sum(1 for item in evaluations if item["actual_decision"] == "exclude"),
            "reject": sum(1 for item in evaluations if item["actual_decision"] == "reject"),
            "watchlist": sum(1 for item in evaluations if item["actual_decision"] == "watchlist"),
            "accept": sum(1 for item in evaluations if item["actual_decision"] == "accept"),
        },
        "strongest_rejection_reasons": support.top_reasons(evaluations, "reject_reasons", 4),
        "paper_only_no_action_summary": "Replay runner validates adversarial fixtures only. No network, no API, no wallet, and no real order path.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Adversarial Replay Report",
        "",
        "Deterministic replay validation for hostile synthetic PMBOT market cases.",
        "",
        f"- Total cases: {report['total_cases']}",
        f"- Passed cases: {report['passed_cases']}",
        f"- Failed cases: {report['failed_cases']}",
        f"- False positives: {report['false_positive_count']}",
        f"- Decision counts: {json.dumps(report['decision_counts'], sort_keys=True)}",
        f"- Strongest rejection reasons: {', '.join(report['strongest_rejection_reasons'])}",
        f"- Summary: {report['paper_only_no_action_summary']}",
        "",
        "## Case Results",
    ]
    for item in report["cases"]:
        lines.append(
            f"- {item['case_id']}: expected {item['expected_decision']}, actual {item['actual_decision']}, "
            f"flags {', '.join(item['safety_flags']) or 'none'}"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_adversarial_replay_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
