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


def _load_support(root: Path):
    return _load_module(root / "pm_bot" / "operator" / "operator_support.py", "pmbot_operator_support_export")


def _parse_args():
    parser = argparse.ArgumentParser(description="Build the PMBOT review export package.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_review_export_package(root: Path):
    support = _load_support(root)
    bundle = _load_module(root / "pm_bot" / "operator" / "build_operator_review_bundle.py", "pmbot_operator_bundle_export").build_operator_review_bundle(root)
    table = _load_module(root / "pm_bot" / "operator" / "paper_candidate_review_table.py", "pmbot_review_table_export").build_paper_candidate_review_table(root)
    watchlist = _load_module(root / "pm_bot" / "operator" / "watchlist_policy_report.py", "pmbot_watchlist_export").build_watchlist_policy_report(root)
    rejection = _load_module(root / "pm_bot" / "reports" / "rejection_summary_report.py", "pmbot_rejection_export").build_rejection_summary_report(root)
    risk_summary = _load_module(root / "pm_bot" / "operator" / "risk_audit_summary.py", "pmbot_risk_export").build_risk_audit_summary(root)
    checklist = _load_module(root / "pm_bot" / "operator" / "operator_review_checklist.py", "pmbot_checklist_export").build_operator_review_checklist(root)
    return {
        "schema_version": "v1",
        "package_id": "PMBOT-BATCH-006-REVIEW-EXPORT-PACKAGE",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "operator_review_only": True,
        "operator_review_bundle": bundle,
        "paper_candidate_review_table": table,
        "watchlist_policy_report": watchlist,
        "rejection_summary": rejection,
        "risk_audit_summary": risk_summary,
        "demo_readiness_headline": support.demo_readiness_headline(bundle, risk_summary),
        "final_operator_checklist": checklist,
        "explicit_no_execution_statement": (
            "Export package is for human review only. No execution instructions, no live orders, no wallet, and no API path exist."
        ),
    }


def render_markdown(report):
    lines = [
        "# PMBOT Review Export Package",
        "",
        "Human-review export package for deterministic PMBOT paper research outputs.",
        "",
        f"- Demo readiness: {report['demo_readiness_headline']}",
        f"- Accepted paper candidates: {len(report['operator_review_bundle']['accepted_paper_candidates'])}",
        f"- Review table rows: {len(report['paper_candidate_review_table']['rows'])}",
        f"- Watchlist policy no-action: {str(report['watchlist_policy_report']['watchlist_is_no_action']).lower()}",
        f"- Blocking findings: {report['risk_audit_summary']['blocking_findings_count']}",
        "",
        f"- {report['explicit_no_execution_statement']}",
        "",
    ]
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_review_export_package(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
