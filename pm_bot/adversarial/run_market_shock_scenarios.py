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
    parser = argparse.ArgumentParser(description="Run deterministic PMBOT market shock scenarios.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_market_shock_report(root: Path):
    support = _load_support(root)
    scenarios = support.load_market_shock_scenarios(root)
    evaluations = [support.evaluate_market_shock_scenario(scenario) for scenario in scenarios]
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-005-MARKET-SHOCKS",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "total_scenarios": len(evaluations),
        "passed_scenarios": sum(1 for item in evaluations if item["decision_matches_expected"]),
        "shock_types": [item["shock_type"] for item in evaluations],
        "rejection_reason_counts": support.count_reasons(evaluations, "reject_reasons"),
        "warning_reason_counts": support.count_reasons(evaluations, "warning_reasons"),
        "scenario_results": evaluations,
        "paper_only_summary": "Shock scenarios stress paper-only decision logic and never produce live execution.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Market Shock Report",
        "",
        "Deterministic hostile market shock sweep for synthetic PMBOT candidates.",
        "",
        f"- Total scenarios: {report['total_scenarios']}",
        f"- Passed scenarios: {report['passed_scenarios']}",
        f"- Rejection reasons: {json.dumps(report['rejection_reason_counts'], sort_keys=True)}",
        f"- Warning reasons: {json.dumps(report['warning_reason_counts'], sort_keys=True)}",
        f"- Summary: {report['paper_only_summary']}",
        "",
        "## Scenario Results",
    ]
    for item in report["scenario_results"]:
        lines.append(
            f"- {item['scenario_id']}: expected {item['expected_decision']}, actual {item['actual_decision']}, "
            f"flags {', '.join(item['safety_flags']) or 'none'}"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_market_shock_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
