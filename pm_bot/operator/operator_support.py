import importlib.util
from pathlib import Path


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_prior_reports(root: Path):
    reports = {}
    reports["portfolio"] = load_module(
        root / "pm_bot" / "reports" / "portfolio_paper_report.py",
        "pmbot_batch_003_portfolio",
    ).build_portfolio_report(root)
    reports["research_demo"] = load_module(
        root / "pm_bot" / "demo" / "run_research_quality_demo.py",
        "pmbot_batch_004_demo",
    ).build_research_quality_demo(root)
    reports["candidate_comparison"] = load_module(
        root / "pm_bot" / "reports" / "candidate_comparison_report.py",
        "pmbot_batch_004_comparison",
    ).build_candidate_comparison_report(root)
    reports["signal_explainer"] = load_module(
        root / "pm_bot" / "explainability" / "signal_explainer.py",
        "pmbot_batch_004_signal_explainer",
    )
    reports["adversarial_demo"] = load_module(
        root / "pm_bot" / "demo" / "run_adversarial_validation_demo.py",
        "pmbot_batch_005_demo",
    ).build_adversarial_validation_demo(root)
    reports["false_positive"] = load_module(
        root / "pm_bot" / "validation" / "false_positive_prevention_report.py",
        "pmbot_batch_005_false_positive",
    ).build_false_positive_prevention_report(root)
    reports["scorecard"] = load_module(
        root / "pm_bot" / "validation" / "replay_safety_scorecard.py",
        "pmbot_batch_005_scorecard",
    ).build_replay_safety_scorecard(root)
    reports["audit_v2"] = load_module(
        root / "pm_bot" / "audit" / "static_safety_audit_v2.py",
        "pmbot_audit_v2",
    ).build_static_audit_report(root)
    reports["audit_v3"] = load_module(
        root / "pm_bot" / "audit" / "static_safety_audit_v3.py",
        "pmbot_audit_v3",
    ).build_static_audit_report(root)
    reports["audit_v4"] = load_module(
        root / "pm_bot" / "audit" / "static_safety_audit_v4.py",
        "pmbot_audit_v4",
    ).build_static_audit_report(root)
    return reports


def build_candidate_rows(root: Path):
    support = load_module(
        root / "pm_bot" / "quality" / "research_quality_support.py",
        "pmbot_research_quality_support_operator",
    )
    cases = support.load_cases(root)["cases"]
    rows = []
    for case, breakdown in support.sort_cases_for_comparison(cases):
        explanation = support.build_signal_explanation(case)
        reasons = breakdown["hard_reject_reasons"] or breakdown["warnings"] or breakdown["missing_information"]
        operator_action = {
            "accept": "paper_monitor_no_action",
            "watchlist": "watchlist_no_action",
            "reject": "reject_no_action",
            "exclude": "reject_no_action",
            "no_action": "review_only",
        }[breakdown["final_decision"]]
        rows.append(
            {
                "candidate_id": case["case_id"],
                "market_id": case["market_id"],
                "category": case["category"],
                "decision": breakdown["final_decision"],
                "confidence_band": breakdown["confidence_band"],
                "confidence_score": breakdown["total_confidence_score"],
                "risk_flags": sorted(set(breakdown["warnings"] + breakdown["hard_reject_reasons"])),
                "explanation_headline": explanation["headline"],
                "rejection_or_watchlist_reason": ", ".join(reasons) if reasons else "accepted_for_paper_monitoring_only",
                "operator_action": operator_action,
            }
        )
    return rows


def watchlist_policy_statement():
    return (
        "Watchlist status is review-only and no-action. It cannot become an accepted, live, order, trade, or "
        "execution candidate without separate future approval."
    )


def demo_readiness_headline(bundle, risk_summary):
    accepted_count = len(bundle["accepted_paper_candidates"])
    watchlist_count = len(bundle["watchlist_candidates"])
    return (
        f"Operator review bundle is ready for deterministic human inspection with {accepted_count} paper candidates, "
        f"{watchlist_count} watchlist cases, audit status {risk_summary['latest_audit_headline']}, and no executable path."
    )
