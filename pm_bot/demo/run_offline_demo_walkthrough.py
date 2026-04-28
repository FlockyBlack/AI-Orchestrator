import argparse
import json
import subprocess
import sys
from pathlib import Path


COMMANDS = [
    {
        "id": "operator_review_demo",
        "argv": ["pm_bot/demo/run_operator_review_demo.py"],
    },
    {
        "id": "review_export_package",
        "argv": ["pm_bot/export/build_review_export_package.py"],
    },
    {
        "id": "paper_research_demo",
        "argv": ["pm_bot/demo/run_paper_research_demo.py"],
    },
    {
        "id": "adversarial_replay",
        "argv": ["pm_bot/replay/run_adversarial_replay.py"],
    },
    {
        "id": "raw_ingestion_manifest",
        "argv": ["pm_bot/raw_artifacts/build_ingestion_manifest.py"],
    },
    {
        "id": "static_safety_audit_v7",
        "argv": ["pm_bot/audit/static_safety_audit_v7.py"],
    },
    {
        "id": "rejection_summary",
        "argv": ["pm_bot/reports/rejection_summary_report.py"],
    },
    {
        "id": "paper_simulation",
        "argv": ["pm_bot/paper/simulate_paper_plan.py", "pm_bot/paper/paper_plan_fixture.v1.json"],
    },
    {
        "id": "accounting_report",
        "argv": ["pm_bot/accounting/calculate_fee_slippage.py", "pm_bot/accounting/accounting_fixture.v1.json"],
    },
    {
        "id": "risk_report",
        "argv": ["pm_bot/risk/evaluate_risk_limits.py", "pm_bot/risk/risk_fixture.v1.json"],
    },
]


def _parse_args():
    parser = argparse.ArgumentParser(description="Run the PMBOT offline demo walkthrough.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def _run_json_command(root: Path, argv: list[str]) -> dict:
    completed = subprocess.run(
        [sys.executable, *argv],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


def build_offline_demo_walkthrough(root: Path) -> dict:
    outputs = []
    for command in COMMANDS:
        outputs.append(
            {
                "id": command["id"],
                "command": f"python {' '.join(command['argv'])}",
                "output": _run_json_command(root, command["argv"]),
            }
        )

    output_by_id = {item["id"]: item["output"] for item in outputs}
    operator_demo = output_by_id["operator_review_demo"]
    export_package = output_by_id["review_export_package"]
    paper_demo = output_by_id["paper_research_demo"]
    replay = output_by_id["adversarial_replay"]
    raw_manifest = output_by_id["raw_ingestion_manifest"]
    audit = output_by_id["static_safety_audit_v7"]
    rejection = output_by_id["rejection_summary"]
    paper = output_by_id["paper_simulation"]
    accounting = output_by_id["accounting_report"]
    risk = output_by_id["risk_report"]

    return {
        "schema_version": "v1",
        "bundle_id": "PMBOT-BATCH-012-OFFLINE-DEMO-WALKTHROUGH",
        "offline_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "review_only": True,
        "execution_allowed": False,
        "trading_allowed": False,
        "network_used": False,
        "api_used": False,
        "wallet_used": False,
        "commands_run": [
            {
                "id": item["id"],
                "command": item["command"],
                "status": "pass",
            }
            for item in outputs
        ],
        "presentation_summary": {
            "accepted_paper_candidates": operator_demo["operator_bundle_summary"]["accepted_paper_candidates"],
            "watchlist_candidates": operator_demo["operator_bundle_summary"]["watchlist_candidates"],
            "review_table_rows": len(export_package["paper_candidate_review_table"]["rows"]),
            "paper_demo_market": paper_demo["market_summary"]["market_id"],
            "paper_demo_recommendation_type": paper_demo["signal_summary"]["recommendation_type"],
            "paper_simulation_gross_pnl": paper["gross_pnl"],
            "accounting_total_cost": accounting["total_cost"],
            "risk_approved": risk["approved"],
            "risk_breaches": risk["breaches"],
            "adversarial_replay_passed": replay["passed_cases"],
            "adversarial_replay_total": replay["total_cases"],
            "false_positive_count": replay["false_positive_count"],
            "raw_artifacts_accepted": raw_manifest["counts"]["accepted"],
            "raw_artifacts_quarantined": raw_manifest["counts"]["quarantined"],
            "rejection_count": rejection["rejection_count"],
            "static_audit_passed": audit["audit_passed"],
            "static_audit_blocking_findings": len(audit["blocking_findings"]),
        },
        "safety_evidence": {
            "operator_review_only": operator_demo["operator_review_only"],
            "watchlist_no_action_statement": operator_demo["watchlist_no_action_statement"],
            "export_no_execution_statement": export_package["explicit_no_execution_statement"],
            "paper_demo_execution_allowed": paper_demo["execution_allowed"],
            "paper_demo_trading_allowed": paper_demo["trading_allowed"],
            "paper_demo_network_used": paper_demo["network_used"],
            "paper_demo_api_used": paper_demo["api_used"],
            "paper_demo_wallet_used": paper_demo["wallet_used"],
            "paper_simulation_execution_allowed": paper["execution_allowed"],
            "paper_simulation_trading_allowed": paper["trading_allowed"],
            "accounting_execution_allowed": accounting["execution_allowed"],
            "accounting_trading_allowed": accounting["trading_allowed"],
            "risk_execution_allowed": risk["execution_allowed"],
            "risk_trading_allowed": risk["trading_allowed"],
            "raw_manifest_validation_passed": raw_manifest["validation_passed"],
            "raw_manifest_network_detected": raw_manifest["safety_summary"]["network_used_detected"],
            "raw_manifest_wallet_detected": raw_manifest["safety_summary"]["wallet_detected"],
            "raw_manifest_order_or_trading_detected": raw_manifest["safety_summary"]["order_or_trading_capability_detected"],
            "static_audit_passed": audit["audit_passed"],
            "static_audit_blocking_finding_count": len(audit["blocking_findings"]),
        },
        "limitations": [
            "No live bot.",
            "No live fetcher.",
            "No normalization implementation.",
            "No wallet, credentials, private keys, or signing.",
            "No real orders or live trading.",
            "No runtime wiring.",
        ],
        "recommended_next_task": "PMBOT-BATCH-013-DEMO-PACKET-POLISH",
    }


def render_markdown(report: dict) -> str:
    summary = report["presentation_summary"]
    lines = [
        "# PMBOT Offline Demo Walkthrough",
        "",
        "Deterministic local PMBOT walkthrough for Monday presentation.",
        "",
        "## Boundary",
        "",
        "- Offline only: true",
        "- Paper only: true",
        "- Execution allowed: false",
        "- Trading allowed: false",
        "- Network used: false",
        "- API used: false",
        "- Wallet used: false",
        "",
        "## Run Summary",
        "",
    ]
    for command in report["commands_run"]:
        lines.append(f"- {command['status']}: `{command['command']}`")
    lines.extend(
        [
            "",
            "## Presentation Highlights",
            "",
            f"- Accepted paper candidates: {summary['accepted_paper_candidates']}",
            f"- Watchlist candidates: {summary['watchlist_candidates']}",
            f"- Review table rows: {summary['review_table_rows']}",
            f"- Paper demo market: {summary['paper_demo_market']}",
            f"- Paper recommendation type: {summary['paper_demo_recommendation_type']}",
            f"- Paper simulation gross PnL: {summary['paper_simulation_gross_pnl']}",
            f"- Accounting total cost: {summary['accounting_total_cost']}",
            f"- Risk approved: {str(summary['risk_approved']).lower()}",
            f"- Risk breaches: {', '.join(summary['risk_breaches']) if summary['risk_breaches'] else 'none'}",
            f"- Adversarial replay: {summary['adversarial_replay_passed']}/{summary['adversarial_replay_total']} passed",
            f"- False positives: {summary['false_positive_count']}",
            f"- Raw artifacts accepted: {summary['raw_artifacts_accepted']}",
            f"- Raw artifacts quarantined: {summary['raw_artifacts_quarantined']}",
            f"- Rejection count: {summary['rejection_count']}",
            f"- Static audit passed: {str(summary['static_audit_passed']).lower()}",
            f"- Static audit blocking findings: {summary['static_audit_blocking_findings']}",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", f"Next: `{report['recommended_next_task']}`", ""])
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_offline_demo_walkthrough(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
