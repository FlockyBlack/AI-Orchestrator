import argparse
import importlib.util
import json
from pathlib import Path


def _load_support(root: Path):
    path = root / "pm_bot" / "operator" / "operator_support.py"
    spec = importlib.util.spec_from_file_location("pmbot_operator_support_bundle", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args():
    parser = argparse.ArgumentParser(description="Build the PMBOT operator review bundle.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_operator_review_bundle(root: Path):
    support = _load_support(root)
    prior = support.load_prior_reports(root)
    rows = support.build_candidate_rows(root)
    accepted_positions = [
        {
            "market_id": item["market_id"],
            "category": item["category"],
            "allocation_usd": item["allocation_usd"],
            "expected_value_delta": item["expected_value_delta"],
        }
        for item in prior["portfolio"]["accepted_positions"]
    ]
    rejected_candidates = [
        {
            "candidate_id": row["candidate_id"],
            "market_id": row["market_id"],
            "reason": row["rejection_or_watchlist_reason"],
        }
        for row in rows
        if row["decision"] == "reject"
    ]
    watchlist_candidates = [
        {
            "candidate_id": row["candidate_id"],
            "market_id": row["market_id"],
            "reason": row["rejection_or_watchlist_reason"],
            "operator_action": row["operator_action"],
        }
        for row in rows
        if row["decision"] in {"watchlist", "no_action"}
    ]
    blocked_or_excluded_cases = [
        {
            "candidate_id": row["candidate_id"],
            "market_id": row["market_id"],
            "reason": row["rejection_or_watchlist_reason"],
        }
        for row in rows
        if row["decision"] == "exclude"
    ]
    top_risk_flags = sorted(
        set(prior["portfolio"]["risk_flags"])
        | set(prior["false_positive"]["strongest_rejection_reasons"])
        | {"watchlist_no_action"}
    )
    return {
        "schema_version": "v1",
        "bundle_id": "PMBOT-BATCH-006-OPERATOR-REVIEW-BUNDLE",
        "generated_from_local_artifacts": True,
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "operator_review_only": True,
        "accepted_paper_candidates": accepted_positions,
        "rejected_candidates": rejected_candidates,
        "watchlist_candidates": watchlist_candidates,
        "blocked_or_excluded_cases": blocked_or_excluded_cases,
        "top_risk_flags": top_risk_flags,
        "audit_headline": (
            f"audit_v4_passed={str(prior['adversarial_demo']['audit_headline']['static_audit_v4_passed']).lower()}, "
            f"blocking_findings={prior['adversarial_demo']['audit_headline']['blocking_findings']}"
        ),
        "adversarial_validation_headline": (
            f"replay_passed={prior['adversarial_demo']['adversarial_replay_report']['passed_cases']}/"
            f"{prior['adversarial_demo']['adversarial_replay_report']['total_cases']}, "
            f"false_positives={prior['adversarial_demo']['false_positive_prevention_report']['false_positives_count']}"
        ),
        "watchlist_warning_status": support.watchlist_policy_statement(),
        "final_paper_only_operator_recommendation": (
            "Maintain paper-monitoring only. Review accepted candidates for research continuity, keep watchlist and "
            "no-action cases non-executable, and reject or exclude unsafe cases."
        ),
        "operator_next_steps": [
            "Review accepted paper candidates against current fixture assumptions.",
            "Confirm watchlist and no-action cases remain non-executable.",
            "Review rejection and exclusion reasons for recurring weak signals.",
            "Verify audit and adversarial validation status before any future approval discussion.",
        ],
        "explicit_no_execution_statement": (
            "This bundle is for local operator review only. It does not authorize live APIs, wallets, orders, trades, "
            "autonomous execution, or runtime wiring."
        ),
    }


def render_markdown(report):
    lines = [
        "# PMBOT Operator Review Bundle",
        "",
        "Consolidated local-only review bundle for PMBOT paper research outputs.",
        "",
        f"- Accepted paper candidates: {len(report['accepted_paper_candidates'])}",
        f"- Rejected candidates: {len(report['rejected_candidates'])}",
        f"- Watchlist candidates: {len(report['watchlist_candidates'])}",
        f"- Blocked or excluded cases: {len(report['blocked_or_excluded_cases'])}",
        f"- Audit headline: {report['audit_headline']}",
        f"- Adversarial validation headline: {report['adversarial_validation_headline']}",
        f"- Watchlist status: {report['watchlist_warning_status']}",
        "",
        "## Operator Next Steps",
    ]
    lines.extend(f"- {item}" for item in report["operator_next_steps"])
    lines.extend(["", f"- {report['explicit_no_execution_statement']}", ""])
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_operator_review_bundle(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
