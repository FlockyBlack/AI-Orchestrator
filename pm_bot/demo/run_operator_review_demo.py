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
    parser = argparse.ArgumentParser(description="Run the PMBOT operator review demo.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_operator_review_demo(root: Path):
    bundle = _load_module(root / "pm_bot" / "operator" / "build_operator_review_bundle.py", "pmbot_operator_bundle_demo").build_operator_review_bundle(root)
    package = _load_module(root / "pm_bot" / "export" / "build_review_export_package.py", "pmbot_export_package_demo").build_review_export_package(root)
    checklist = _load_module(root / "pm_bot" / "operator" / "operator_review_checklist.py", "pmbot_checklist_demo").build_operator_review_checklist(root)
    risk_summary = _load_module(root / "pm_bot" / "operator" / "risk_audit_summary.py", "pmbot_risk_demo").build_risk_audit_summary(root)
    return {
        "schema_version": "v1",
        "demo_id": "PMBOT-BATCH-006-OPERATOR-REVIEW-DEMO",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "operator_review_only": True,
        "operator_bundle_summary": {
            "accepted_paper_candidates": len(bundle["accepted_paper_candidates"]),
            "rejected_candidates": len(bundle["rejected_candidates"]),
            "watchlist_candidates": len(bundle["watchlist_candidates"]),
        },
        "export_package_summary": {
            "demo_readiness_headline": package["demo_readiness_headline"],
            "contains_checklist": True,
        },
        "checklist_summary": {
            "required_steps": len(checklist["items"]),
            "pending_steps": len([item for item in checklist["items"] if item["status"] == "pending_human_review"]),
        },
        "watchlist_no_action_statement": bundle["watchlist_warning_status"],
        "audit_status_headline": risk_summary["latest_audit_headline"],
    }


def render_markdown(report):
    lines = [
        "# PMBOT Operator Review Demo",
        "",
        "Deterministic local demo for the operator review and export package.",
        "",
        f"- Accepted paper candidates: {report['operator_bundle_summary']['accepted_paper_candidates']}",
        f"- Rejected candidates: {report['operator_bundle_summary']['rejected_candidates']}",
        f"- Watchlist candidates: {report['operator_bundle_summary']['watchlist_candidates']}",
        f"- Checklist steps: {report['checklist_summary']['required_steps']}",
        f"- Watchlist statement: {report['watchlist_no_action_statement']}",
        f"- Audit headline: {report['audit_status_headline']}",
        "",
    ]
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_operator_review_demo(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
