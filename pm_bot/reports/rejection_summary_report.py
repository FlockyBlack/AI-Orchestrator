import argparse
import importlib.util
import json
from pathlib import Path


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args():
    parser = argparse.ArgumentParser(description="Build the PMBOT rejection summary report.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_rejection_summary_report(root: Path):
    bad_signal = _load_module(root / "pm_bot" / "quality" / "bad_signal_rejection_report.py", "pmbot_bad_signal_summary").build_bad_signal_rejection_report(root)
    portfolio = _load_module(root / "pm_bot" / "reports" / "portfolio_paper_report.py", "pmbot_portfolio_summary").build_portfolio_report(root)
    replay = _load_module(root / "pm_bot" / "replay" / "run_adversarial_replay.py", "pmbot_replay_summary").build_adversarial_replay_report(root)
    shocks = _load_module(root / "pm_bot" / "adversarial" / "run_market_shock_scenarios.py", "pmbot_shocks_summary").build_market_shock_report(root)
    false_positive = _load_module(root / "pm_bot" / "validation" / "false_positive_prevention_report.py", "pmbot_false_positive_summary").build_false_positive_prevention_report(root)
    combined_reasons = dict(bad_signal["rejection_reasons_grouped"])
    for reason, count in replay["decision_counts"].items():
        if reason in {"reject", "exclude"}:
            combined_reasons[f"replay_decision_{reason}"] = count
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-006-REJECTION-SUMMARY",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "operator_review_only": True,
        "rejection_count": bad_signal["rejected_cases_count"] + replay["decision_counts"]["reject"],
        "rejection_reasons": combined_reasons,
        "excluded_cases": portfolio["resolved_closed_market_exclusions"] + [
            item["market_id"] for item in replay["cases"] if item["actual_decision"] == "exclude"
        ],
        "common_bad_signal_patterns": bad_signal["examples_of_bad_signals"],
        "data_quality_failures": ["stale_data", "missing_market_status", "confidence_vs_data_mismatch"],
        "liquidity_spread_failures": ["low_liquidity", "wide_spread"],
        "stale_resolved_failures": ["stale_data", "resolved_market", "resolved_or_closed_market"],
        "contradiction_correlation_failures": ["conflicting_signals", "correlation_conflict"],
        "false_positive_prevention_summary": (
            f"False positives remained at {false_positive['false_positives_count']} while watchlist warnings stayed "
            "non-executable and deterministic."
        ),
        "shock_rejection_reason_counts": shocks["rejection_reason_counts"],
    }


def render_markdown(report):
    lines = [
        "# PMBOT Rejection Summary Report",
        "",
        "Deterministic summary of rejected and excluded PMBOT research outcomes.",
        "",
        f"- Rejection count: {report['rejection_count']}",
        f"- Excluded cases: {', '.join(report['excluded_cases'])}",
        f"- False-positive prevention: {report['false_positive_prevention_summary']}",
        f"- Rejection reasons: {json.dumps(report['rejection_reasons'], sort_keys=True)}",
        f"- Shock rejection reasons: {json.dumps(report['shock_rejection_reason_counts'], sort_keys=True)}",
        "",
    ]
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_rejection_summary_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
