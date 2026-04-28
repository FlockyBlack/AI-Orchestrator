import argparse
import importlib.util
import json
from pathlib import Path


def _load_support(root: Path):
    path = root / "pm_bot" / "quality" / "research_quality_support.py"
    spec = importlib.util.spec_from_file_location("pmbot_research_quality_support", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args():
    parser = argparse.ArgumentParser(description="Build the PMBOT bad-signal rejection report.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_bad_signal_rejection_report(root: Path):
    support = _load_support(root)
    cases = support.load_cases(root)["cases"]
    rejected = []
    grouped = {}
    improvements = {
        "low_liquidity": "Use a synthetic case with liquidity above the local floor.",
        "wide_spread": "Tighten spread assumptions before promoting the case.",
        "stale_data": "Refresh the local fixture timestamp before reconsidering the case.",
        "conflicting_signals": "Resolve the contradiction between synthetic signals.",
        "insufficient_edge": "Improve the synthetic edge or downgrade the case to no-action.",
        "resolved_or_closed_market": "Exclude resolved or closed markets from forward research.",
    }
    for case in cases:
        breakdown = support.compute_confidence_breakdown(case)
        if breakdown["final_decision"] not in {"reject", "exclude"}:
            continue
        reasons = breakdown["hard_reject_reasons"] or ["resolved_or_closed_market"]
        rejected.append(
            {
                "case_id": case["case_id"],
                "market_id": case["market_id"],
                "final_decision": breakdown["final_decision"],
                "confidence_score": breakdown["total_confidence_score"],
                "rejection_reasons": reasons,
                "improvement_actions": [improvements[reason] for reason in reasons if reason in improvements],
            }
        )
        for reason in reasons:
            grouped[reason] = grouped.get(reason, 0) + 1
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-004-BAD-SIGNAL-REJECTION-REPORT",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "rejected_cases_count": len(rejected),
        "rejection_reasons_grouped": dict(sorted(grouped.items())),
        "examples_of_bad_signals": rejected,
        "paper_only_no_action_confirmation": "All rejected cases remain paper-only and produce no real order.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Bad-Signal Rejection Report",
        "",
        "Deterministic rejection review for fixture-only PMBOT research cases.",
        "",
        f"- Rejected cases count: {report['rejected_cases_count']}",
        f"- Rejection reasons grouped: {json.dumps(report['rejection_reasons_grouped'], sort_keys=True)}",
        f"- Confirmation: {report['paper_only_no_action_confirmation']}",
        "",
        "## Examples",
    ]
    for item in report["examples_of_bad_signals"]:
        lines.append(
            f"- {item['case_id']}: {', '.join(item['rejection_reasons'])}; improve via {' | '.join(item['improvement_actions'])}"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_bad_signal_rejection_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
