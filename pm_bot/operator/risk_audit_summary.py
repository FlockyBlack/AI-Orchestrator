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
    parser = argparse.ArgumentParser(description="Build the PMBOT risk and audit summary.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_risk_audit_summary(root: Path):
    audit_v2 = _load_module(root / "pm_bot" / "audit" / "static_safety_audit_v2.py", "pmbot_audit_v2_ra").build_static_audit_report(root)
    audit_v3 = _load_module(root / "pm_bot" / "audit" / "static_safety_audit_v3.py", "pmbot_audit_v3_ra").build_static_audit_report(root)
    audit_v4 = _load_module(root / "pm_bot" / "audit" / "static_safety_audit_v4.py", "pmbot_audit_v4_ra").build_static_audit_report(root)
    audit_v5 = _load_module(root / "pm_bot" / "audit" / "static_safety_audit_v5.py", "pmbot_audit_v5_ra").build_static_audit_report(root)
    demo = _load_module(root / "pm_bot" / "demo" / "run_adversarial_validation_demo.py", "pmbot_adv_demo_ra").build_adversarial_validation_demo(root)
    watchlist = _load_module(root / "pm_bot" / "operator" / "watchlist_policy_report.py", "pmbot_watchlist_ra").build_watchlist_policy_report(root)
    latest_headline = (
        f"Static safety audit v5 passed with {len(audit_v5['blocking_findings'])} blocking findings and expanded "
        "operator/export coverage."
    )
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-006-RISK-AUDIT-SUMMARY",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "operator_review_only": True,
        "audit_status": {
            "v2_passed": audit_v2["audit_passed"],
            "v3_passed": audit_v3["audit_passed"],
            "v4_passed": audit_v4["audit_passed"],
            "v5_passed": audit_v5["audit_passed"],
        },
        "latest_audit_headline": latest_headline,
        "blocking_findings_count": len(audit_v5["blocking_findings"]),
        "replay_adversarial_validation_status": {
            "static_audit_v4_passed": demo["audit_headline"]["static_audit_v4_passed"],
            "replay_score": demo["replay_safety_scorecard"]["total_score"],
            "false_positives": demo["false_positive_prevention_report"]["false_positives_count"],
        },
        "watchlist_warning_status": {
            "watchlist_is_no_action": watchlist["watchlist_is_no_action"],
            "watchlist_requires_human_review": watchlist["watchlist_requires_human_review"],
            "critical_rule": watchlist["critical_rule"],
        },
        "safety_boundaries": [
            "fixture_only",
            "paper_only",
            "local_only",
            "deterministic",
            "offline_testable",
            "operator_review_only",
        ],
        "forbidden_live_behavior_status": {
            "live_api": False,
            "wallet": False,
            "real_orders": False,
            "real_trading": False,
            "autonomous_trading": False,
            "runtime_wiring": False,
        },
    }


def render_markdown(report):
    lines = [
        "# PMBOT Risk And Audit Summary",
        "",
        "Consolidated audit and replay summary for operator review only.",
        "",
        f"- Audit v2 passed: {str(report['audit_status']['v2_passed']).lower()}",
        f"- Audit v3 passed: {str(report['audit_status']['v3_passed']).lower()}",
        f"- Audit v4 passed: {str(report['audit_status']['v4_passed']).lower()}",
        f"- Audit v5 passed: {str(report['audit_status']['v5_passed']).lower()}",
        f"- Latest audit headline: {report['latest_audit_headline']}",
        f"- Blocking findings: {report['blocking_findings_count']}",
        f"- Replay score: {report['replay_adversarial_validation_status']['replay_score']}",
        f"- False positives: {report['replay_adversarial_validation_status']['false_positives']}",
        "",
        f"- Watchlist rule: {report['watchlist_warning_status']['critical_rule']}",
        "",
    ]
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_risk_audit_summary(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
