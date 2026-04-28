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
    parser = argparse.ArgumentParser(description="Build the PMBOT candidate comparison report.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_candidate_comparison_report(root: Path):
    support = _load_support(root)
    cases = support.load_cases(root)["cases"]
    ranked = []
    for case, breakdown in support.sort_cases_for_comparison(cases):
        ranked.append(
            {
                "case_id": case["case_id"],
                "market_id": case["market_id"],
                "decision": breakdown["final_decision"],
                "confidence_score": breakdown["total_confidence_score"],
                "confidence_band": breakdown["confidence_band"],
                "risk_score": min(
                    breakdown["component_scores"]["correlation_risk"],
                    breakdown["component_scores"]["concentration_risk"],
                ),
                "data_quality_score": min(
                    breakdown["component_scores"]["data_freshness"],
                    breakdown["component_scores"]["research_completeness"],
                ),
                "liquidity_spread_caution": sorted(
                    reason
                    for reason in breakdown["warnings"]
                    if reason in {"low_liquidity", "wide_spread"}
                ),
                "warning_flags": breakdown["warnings"],
                "rejection_reasons": breakdown["hard_reject_reasons"],
                "watchlist_reasons": [
                    reason for reason in breakdown["warnings"] if breakdown["final_decision"] == "watchlist"
                ],
            }
        )
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-004-CANDIDATE-COMPARISON",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "ranked_candidates": ranked,
        "not_trading_advice": "Synthetic research comparison only. No trading advice and no real order is created.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Candidate Comparison Report",
        "",
        "Deterministic comparison of accepted, watchlist, rejected, excluded, and no-action synthetic cases.",
        "",
        f"- Notice: {report['not_trading_advice']}",
        "",
        "## Ranked Candidates",
    ]
    for item in report["ranked_candidates"]:
        lines.append(
            f"- {item['case_id']}: {item['decision']} | confidence {item['confidence_score']} ({item['confidence_band']}) | "
            f"risk {item['risk_score']} | data-quality {item['data_quality_score']} | flags {', '.join(item['warning_flags']) or 'none'}"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_candidate_comparison_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
