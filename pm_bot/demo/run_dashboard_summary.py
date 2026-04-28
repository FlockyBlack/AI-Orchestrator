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
    parser = argparse.ArgumentParser(description="Build the PMBOT BATCH-003 dashboard summary.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_dashboard_summary(root: Path):
    support = _load_module(root / "pm_bot" / "reports" / "pmbot_batch_003_support.py", "pmbot_batch_003_support")
    scenarios = _load_module(root / "pm_bot" / "scenarios" / "run_demo_scenarios_v3.py", "pmbot_scenarios_v3")
    portfolio = _load_module(root / "pm_bot" / "reports" / "portfolio_paper_report.py", "pmbot_portfolio_v1")
    audit = _load_module(root / "pm_bot" / "audit" / "static_safety_audit_v2.py", "pmbot_audit_v2")

    bundle = support.load_bundle(root)
    suite = support.load_json(root / "pm_bot" / "scenarios" / "scenario_suite.v3.json")
    scenario_report = scenarios.build_scenario_report(suite, bundle)
    portfolio_report = portfolio.build_portfolio_report(root)
    audit_report = audit.build_static_audit_report(root)

    top_risk_flags = portfolio_report["risk_flags"][:5]
    return {
        "schema_version": "v1",
        "dashboard_id": "PMBOT-BATCH-003-DASHBOARD",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "no_network": True,
        "no_live_api": True,
        "no_wallet": True,
        "no_real_orders": True,
        "no_runtime_wiring": True,
        "fixture_count": len(bundle["markets"]),
        "scenario_count": scenario_report["scenario_count"],
        "paper_candidate_count": portfolio_report["paper_candidate_count"],
        "accepted_paper_candidates": scenario_report["accepted_paper_candidates"],
        "rejected_paper_candidates": scenario_report["rejected_paper_candidates"],
        "warning_count": len(portfolio_report["risk_flags"]),
        "top_risk_flags": top_risk_flags,
        "portfolio_summary_headline": (
            f"{portfolio_report['paper_position_count']} accepted paper positions, "
            f"${portfolio_report['allocated_paper_capital_usd']:.2f} allocated, macro concentration warning active."
        ),
        "audit_status_headline": (
            f"Static audit v2 {'passed' if audit_report['audit_passed'] else 'failed'} with "
            f"{len(audit_report['blocking_findings'])} blocking findings."
        ),
        "demo_readiness_status": "ready_for_local_demo" if audit_report["audit_passed"] else "audit_blocked",
        "safety_boundary_status": (
            "fixture-only, paper-only, local-only, no network, no live API, no wallet, no real orders, no runtime wiring"
        ),
        "final_recommendation": "run_local_demo_and_queue_flocky_validation",
    }


def render_markdown(report):
    top_flags = ", ".join(report["top_risk_flags"]) if report["top_risk_flags"] else "none"
    return "\n".join(
        [
            "# PMBOT Dashboard Summary",
            "",
            "Deterministic local dashboard summary for synthetic PMBOT fixtures. No network, no wallet, no real orders, and no runtime wiring.",
            "",
            "## Counts",
            f"- Fixture count: {report['fixture_count']}",
            f"- Scenario count: {report['scenario_count']}",
            f"- Paper candidate count: {report['paper_candidate_count']}",
            f"- Accepted paper candidates: {report['accepted_paper_candidates']}",
            f"- Rejected paper candidates: {report['rejected_paper_candidates']}",
            f"- Warning count: {report['warning_count']}",
            "",
            "## Headlines",
            f"- Portfolio: {report['portfolio_summary_headline']}",
            f"- Audit: {report['audit_status_headline']}",
            f"- Demo readiness: {report['demo_readiness_status']}",
            "",
            "## Top Risk Flags",
            f"- {top_flags}",
            "",
            "## Safety Boundary",
            f"- {report['safety_boundary_status']}",
            "",
        ]
    )


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_dashboard_summary(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
