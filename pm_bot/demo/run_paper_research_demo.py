import argparse
import importlib.util
import json
from pathlib import Path


def _parse_args():
    parser = argparse.ArgumentParser(description="Run the PMBOT fixture-only paper research demo.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_demo_report(root: Path):
    bundle = _load_json(root / "pm_bot" / "demo" / "demo_market_bundle.v1.json")
    module_refs = bundle["module_refs"]

    validation_module = _load_module(root / module_refs["validation"], "pmbot_validation")
    normalization_module = _load_module(root / module_refs["normalization"], "pmbot_normalization")
    signals_module = _load_module(root / module_refs["signals"], "pmbot_signals")
    hedges_module = _load_module(root / module_refs["hedges"], "pmbot_hedges")
    paper_module = _load_module(root / module_refs["paper"], "pmbot_paper")
    risk_module = _load_module(root / module_refs["risk"], "pmbot_risk")
    accounting_module = _load_module(root / module_refs["accounting"], "pmbot_accounting")
    reports_module = _load_module(root / module_refs["reports"], "pmbot_reports")
    postmortem_module = _load_module(root / module_refs["postmortem"], "pmbot_postmortem")
    audit_module = _load_module(root / module_refs["audit"], "pmbot_audit")

    validation_fixture_path = root / bundle["validation_fixture_ref"]
    validation_fixture = _load_json(validation_fixture_path)
    normalized_expected = _load_json(root / bundle["normalized_market_ref"])
    signal_expected = _load_json(root / bundle["signal_report_ref"])
    hedge_expected = _load_json(root / bundle["hedge_relationship_report_ref"])
    paper_expected = _load_json(root / bundle["paper_simulation_ref"])
    risk_expected = _load_json(root / bundle["risk_report_ref"])
    accounting_expected = _load_json(root / bundle["accounting_report_ref"])
    dashboard_expected = _load_json(root / bundle["dashboard_report_ref"])
    postmortem_expected = _load_json(root / bundle["postmortem_report_ref"])

    validation_report = validation_module.validate_snapshot(str(validation_fixture_path))
    normalized_report = normalization_module.normalize_snapshot(validation_fixture)
    signal_report = signals_module.score_market(normalized_report)
    hedge_fixture = _load_json(root / bundle["hedge_fixture_ref"])
    hedge_report = hedges_module.discover_relationships(hedge_fixture["markets"])
    paper_report = paper_module.simulate_paper_plan(_load_json(root / bundle["paper_plan_ref"]))
    risk_report = risk_module.evaluate_risk_limits(_load_json(root / bundle["risk_fixture_ref"]))
    accounting_report = accounting_module.calculate_fee_slippage(_load_json(root / bundle["accounting_fixture_ref"]))
    dashboard_report = reports_module.build_research_dashboard(
        {
            "signal": signal_report,
            "risk": risk_report,
            "accounting": accounting_report,
            "paper": paper_report,
        }
    )
    postmortem_report = postmortem_module.summarize_postmortem(
        {
            "market_id": signal_report["market_id"],
            "gross_pnl": paper_report["gross_pnl"],
            "total_cost": accounting_report["total_cost"],
            "risk_breaches": risk_report["breaches"],
            "decision_basis": "research_only_fixture_signal",
        }
    )
    audit_report = audit_module.audit_directory(root / bundle["audit_target_ref"])

    return {
        "schema_version": "v1",
        "demo_id": bundle["demo_id"],
        "source_type": "fixture",
        "research_only": True,
        "paper_only": True,
        "live_data_used": False,
        "execution_allowed": False,
        "trading_allowed": False,
        "network_used": False,
        "api_used": False,
        "wallet_used": False,
        "credential_material_required": False,
        "market_summary": {
            "market_id": normalized_report["market_id"],
            "title": normalized_report["title"],
            "outcome_count": normalized_report["outcome_count"],
            "price_sum": normalized_report["price_sum"],
            "validation_status": validation_report["status"],
            "normalized_matches_expected": normalized_report == normalized_expected,
        },
        "signal_summary": {
            "lead_outcome": signal_report["lead_outcome"],
            "confidence": signal_report["confidence"],
            "recommendation_type": signal_report["recommendation_type"],
            "matches_expected": signal_report == signal_expected,
        },
        "hedge_summary": {
            "relationship_count": hedge_report["relationship_count"],
            "strongest_confidence": max(item["confidence"] for item in hedge_report["relationships"]),
            "matches_expected": hedge_report == hedge_expected,
        },
        "paper_simulation_summary": {
            "gross_pnl": paper_report["gross_pnl"],
            "effective_entry_price": paper_report["effective_entry_price"],
            "effective_exit_price": paper_report["effective_exit_price"],
            "matches_expected": paper_report == paper_expected,
        },
        "risk_summary": {
            "approved": risk_report["approved"],
            "breach_count": len(risk_report["breaches"]),
            "breaches": list(risk_report["breaches"]),
            "matches_expected": risk_report == risk_expected,
        },
        "accounting_summary": {
            "total_cost": accounting_report["total_cost"],
            "fee_cost": accounting_report["fee_cost"],
            "slippage_cost": accounting_report["slippage_cost"],
            "matches_expected": accounting_report == accounting_expected,
        },
        "dashboard_summary": {
            "headline": dashboard_report["headline"],
            "net_pnl_after_costs": dashboard_report["net_pnl_after_costs"],
            "execution_blocked": dashboard_report["safety_gates"]["execution_blocked"],
            "matches_expected": dashboard_report == dashboard_expected,
        },
        "postmortem_summary": {
            "grade": postmortem_report["grade"],
            "net_pnl": postmortem_report["net_pnl"],
            "recommended_action": postmortem_report["recommended_action"],
            "matches_expected": postmortem_report == postmortem_expected,
        },
        "static_safety_audit_summary": {
            "audit_passed": audit_report["audit_passed"],
            "blocking_finding_count": len(audit_report["blocking_findings"]),
            "non_blocking_mention_count": len(audit_report["non_blocking_mentions"]),
            "runtime_wiring_added": audit_report["runtime_wiring_added"],
        },
        "recommended_next_action": "Run Flocky validation PMBOT-BATCH-002-V.",
        "final_flocky_done_claimed": False,
        "runtime_wiring_added": False,
    }


def render_markdown(report):
    return "\n".join(
        [
            "# PMBOT Paper Research Demo",
            "",
            "Fixture-only and paper-only local demo. No live API, no wallet or private key usage, no real trading, and no runtime wiring.",
            "",
            "## Market Summary",
            f"- Market: {report['market_summary']['market_id']}",
            f"- Title: {report['market_summary']['title']}",
            f"- Outcomes: {report['market_summary']['outcome_count']}",
            f"- Validation status: {report['market_summary']['validation_status']}",
            "",
            "## Signal Summary",
            f"- Lead outcome: {report['signal_summary']['lead_outcome']}",
            f"- Confidence: {report['signal_summary']['confidence']:.2f}",
            f"- Recommendation type: {report['signal_summary']['recommendation_type']}",
            "",
            "## Risk Summary",
            f"- Approved: {str(report['risk_summary']['approved']).lower()}",
            f"- Breaches: {', '.join(report['risk_summary']['breaches']) if report['risk_summary']['breaches'] else 'none'}",
            "",
            "## Paper Simulation Summary",
            f"- Gross PnL: {report['paper_simulation_summary']['gross_pnl']}",
            f"- Effective entry: {report['paper_simulation_summary']['effective_entry_price']}",
            f"- Effective exit: {report['paper_simulation_summary']['effective_exit_price']}",
            "",
            "## Accounting Summary",
            f"- Total cost: {report['accounting_summary']['total_cost']}",
            f"- Fee cost: {report['accounting_summary']['fee_cost']}",
            f"- Slippage cost: {report['accounting_summary']['slippage_cost']}",
            "",
            "## Hedge Summary",
            f"- Relationship count: {report['hedge_summary']['relationship_count']}",
            f"- Strongest confidence: {report['hedge_summary']['strongest_confidence']:.2f}",
            "",
            "## Audit Summary",
            f"- Audit passed: {str(report['static_safety_audit_summary']['audit_passed']).lower()}",
            f"- Blocking findings: {report['static_safety_audit_summary']['blocking_finding_count']}",
            f"- Non-blocking mentions: {report['static_safety_audit_summary']['non_blocking_mention_count']}",
            "",
            "## Next Safe Step",
            f"- {report['recommended_next_action']}",
            "",
        ]
    )


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_demo_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
