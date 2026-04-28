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
    parser = argparse.ArgumentParser(description="Run the PMBOT adversarial validation demo bundle.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_adversarial_validation_demo(root: Path):
    replay = _load_module(root / "pm_bot" / "replay" / "run_adversarial_replay.py", "pmbot_adversarial_replay")
    shocks = _load_module(root / "pm_bot" / "adversarial" / "run_market_shock_scenarios.py", "pmbot_market_shocks")
    false_positive = _load_module(root / "pm_bot" / "validation" / "false_positive_prevention_report.py", "pmbot_false_positive")
    scorecard = _load_module(root / "pm_bot" / "validation" / "replay_safety_scorecard.py", "pmbot_replay_scorecard")
    audit = _load_module(root / "pm_bot" / "audit" / "static_safety_audit_v4.py", "pmbot_audit_v4")

    replay_report = replay.build_adversarial_replay_report(root)
    shock_report = shocks.build_market_shock_report(root)
    false_positive_report = false_positive.build_false_positive_prevention_report(root)
    scorecard_report = scorecard.build_replay_safety_scorecard(root)
    audit_report = audit.build_static_audit_report(root)

    return {
        "schema_version": "v1",
        "demo_id": "PMBOT-BATCH-005-ADVERSARIAL-VALIDATION-DEMO",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "adversarial_replay_report": {
            "total_cases": replay_report["total_cases"],
            "passed_cases": replay_report["passed_cases"],
            "false_positive_count": replay_report["false_positive_count"],
        },
        "market_shock_report": {
            "total_scenarios": shock_report["total_scenarios"],
            "passed_scenarios": shock_report["passed_scenarios"],
            "rejection_reason_counts": shock_report["rejection_reason_counts"],
        },
        "false_positive_prevention_report": {
            "false_positives_count": false_positive_report["false_positives_count"],
            "high_risk_false_positives_count": false_positive_report["high_risk_false_positives_count"],
            "missed_warning_count": false_positive_report["missed_warning_count"],
        },
        "replay_safety_scorecard": {
            "total_score": scorecard_report["total_score"],
            "score_by_section": scorecard_report["score_by_section"],
        },
        "audit_headline": {
            "static_audit_v4_passed": audit_report["audit_passed"],
            "blocking_findings": len(audit_report["blocking_findings"]),
        },
        "final_paper_only_safety_boundary_summary": "Fixture-only adversarial replay validation. No network, no API, no wallet, no real orders, and no runtime wiring.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Adversarial Validation Demo",
        "",
        "Integrated deterministic demo bundle for replay containment, hostile market shocks, and static safety coverage.",
        "",
        f"- Replay cases passed: {report['adversarial_replay_report']['passed_cases']} / {report['adversarial_replay_report']['total_cases']}",
        f"- Market shock scenarios passed: {report['market_shock_report']['passed_scenarios']} / {report['market_shock_report']['total_scenarios']}",
        f"- False positives: {report['false_positive_prevention_report']['false_positives_count']}",
        f"- Replay safety score: {report['replay_safety_scorecard']['total_score']}",
        f"- Static audit v4 passed: {report['audit_headline']['static_audit_v4_passed']}",
        f"- Safety boundary: {report['final_paper_only_safety_boundary_summary']}",
        "",
    ]
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_adversarial_validation_demo(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
