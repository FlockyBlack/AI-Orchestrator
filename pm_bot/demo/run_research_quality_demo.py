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
    parser = argparse.ArgumentParser(description="Run the PMBOT research quality demo bundle.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_research_quality_demo(root: Path):
    explainability = _load_module(root / "pm_bot" / "explainability" / "signal_explainer.py", "pmbot_signal_explainer")
    confidence = _load_module(root / "pm_bot" / "quality" / "confidence_breakdown.py", "pmbot_confidence_breakdown")
    rejection = _load_module(root / "pm_bot" / "quality" / "bad_signal_rejection_report.py", "pmbot_bad_signal_rejection")
    comparison = _load_module(root / "pm_bot" / "reports" / "candidate_comparison_report.py", "pmbot_candidate_comparison")
    scorecard = _load_module(root / "pm_bot" / "quality" / "research_quality_scorecard.py", "pmbot_research_quality_scorecard")
    trace = _load_module(root / "pm_bot" / "explainability" / "reasoning_trace.py", "pmbot_reasoning_trace")
    audit = _load_module(root / "pm_bot" / "audit" / "static_safety_audit_v3.py", "pmbot_static_audit_v3")

    signal_report = explainability.build_signal_explanations(root)
    confidence_report = confidence.build_confidence_breakdown(root)
    rejection_report = rejection.build_bad_signal_rejection_report(root)
    comparison_report = comparison.build_candidate_comparison_report(root)
    scorecard_report = scorecard.build_research_quality_scorecard(root)
    trace_report = trace.build_reasoning_trace_report(root)
    audit_report = audit.build_static_audit_report(root)

    return {
        "schema_version": "v1",
        "demo_id": "PMBOT-BATCH-004-RESEARCH-QUALITY-DEMO",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "signal_explanations": signal_report["explanations"],
        "confidence_breakdowns": confidence_report["breakdowns"],
        "bad_signal_rejection_summary": {
            "rejected_cases_count": rejection_report["rejected_cases_count"],
            "rejection_reasons_grouped": rejection_report["rejection_reasons_grouped"],
        },
        "candidate_comparison": comparison_report["ranked_candidates"],
        "research_quality_scorecard": {
            "total_score": scorecard_report["total_score"],
            "score_by_section": scorecard_report["score_by_section"],
        },
        "reasoning_traces": trace_report["traces"],
        "safety_boundary_summary": {
            "static_audit_v3_passed": audit_report["audit_passed"],
            "blocking_findings": len(audit_report["blocking_findings"]),
            "summary": "Fixture-only, paper-only, local-only, deterministic, and no runtime wiring.",
        },
    }


def render_markdown(report):
    lines = [
        "# PMBOT Research Quality Demo",
        "",
        "Local deterministic demo bundle for PMBOT BATCH-004 explainability and research quality artifacts.",
        "",
        f"- Signal explanations: {len(report['signal_explanations'])}",
        f"- Confidence breakdowns: {len(report['confidence_breakdowns'])}",
        f"- Rejected cases: {report['bad_signal_rejection_summary']['rejected_cases_count']}",
        f"- Scorecard total: {report['research_quality_scorecard']['total_score']}",
        f"- Static audit v3 passed: {report['safety_boundary_summary']['static_audit_v3_passed']}",
        f"- Safety summary: {report['safety_boundary_summary']['summary']}",
        "",
    ]
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_research_quality_demo(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
