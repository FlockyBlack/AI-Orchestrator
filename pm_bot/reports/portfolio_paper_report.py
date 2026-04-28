import argparse
import importlib.util
import json
from pathlib import Path


def _load_support(root: Path):
    module_path = root / "pm_bot" / "reports" / "pmbot_batch_003_support.py"
    spec = importlib.util.spec_from_file_location("pmbot_batch_003_support", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args():
    parser = argparse.ArgumentParser(description="Build a deterministic PMBOT paper portfolio report.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_portfolio_report(root: Path):
    support = _load_support(root)
    bundle = support.load_bundle(root)
    summary = support.summarize_bundle(bundle)
    accepted_positions = [
        {
            "market_id": item["market_id"],
            "category": item["category"],
            "allocation_usd": item["allocation_usd"],
            "expected_value_delta": item["expected_value_delta"],
            "warnings": list(item["warnings"]),
        }
        for item in summary["accepted_candidates"]
    ]

    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-003-PORTFOLIO-REPORT",
        "source_type": "fixture",
        "portfolio_mode": "paper_only",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "network_used": False,
        "api_used": False,
        "wallet_used": False,
        "real_orders_used": False,
        "total_paper_capital_usd": summary["total_paper_capital_usd"],
        "allocated_paper_capital_usd": summary["allocated_paper_capital_usd"],
        "unallocated_paper_capital_usd": summary["unallocated_paper_capital_usd"],
        "paper_position_count": summary["accepted_candidate_count"],
        "paper_candidate_count": summary["paper_candidate_count"],
        "accepted_positions": accepted_positions,
        "exposure_by_market": summary["exposure_by_market"],
        "exposure_by_category": summary["exposure_by_category"],
        "largest_paper_position": summary["largest_paper_position"],
        "concentration_warnings": list(summary["portfolio_warnings"]),
        "liquidity_warnings": [
            item["market_id"] for item in summary["market_analyses"] if "low_liquidity" in item["warnings"]
        ],
        "stale_data_warnings": [
            item["market_id"] for item in summary["market_analyses"] if "stale_data" in item["warnings"]
        ],
        "resolved_closed_market_exclusions": [item["market_id"] for item in summary["excluded_markets"]],
        "estimated_paper_value_delta": summary["estimated_paper_value_delta"],
        "risk_flags": summary["risk_flags"],
        "final_paper_only_recommendation_summary": (
            "Four paper candidates pass baseline checks, but macro concentration and correlated exposure keep the "
            "portfolio in monitor-only paper mode with no live action."
        ),
    }


def render_markdown(report):
    concentration = ", ".join(report["concentration_warnings"]) if report["concentration_warnings"] else "none"
    stale = ", ".join(report["stale_data_warnings"]) if report["stale_data_warnings"] else "none"
    liquidity = ", ".join(report["liquidity_warnings"]) if report["liquidity_warnings"] else "none"
    excluded = ", ".join(report["resolved_closed_market_exclusions"]) if report["resolved_closed_market_exclusions"] else "none"
    return "\n".join(
        [
            "# PMBOT Portfolio Paper Report",
            "",
            "Synthetic fixture-only and paper-only portfolio summary. No network, no wallet, no real orders, and no runtime wiring.",
            "",
            "## Capital Summary",
            f"- Total paper capital: {report['total_paper_capital_usd']}",
            f"- Allocated paper capital: {report['allocated_paper_capital_usd']}",
            f"- Unallocated paper capital: {report['unallocated_paper_capital_usd']}",
            f"- Paper positions: {report['paper_position_count']}",
            "",
            "## Exposure Summary",
            f"- Largest paper position: {report['largest_paper_position']['market_id']} at {report['largest_paper_position']['allocation_usd']}",
            f"- Exposure by category: {json.dumps(report['exposure_by_category'], ensure_ascii=False, sort_keys=True)}",
            "",
            "## Warnings",
            f"- Concentration warnings: {concentration}",
            f"- Liquidity warnings: {liquidity}",
            f"- Stale-data warnings: {stale}",
            f"- Resolved or closed exclusions: {excluded}",
            "",
            "## Paper Value Delta",
            f"- Estimated paper value delta: {report['estimated_paper_value_delta']}",
            "",
            "## Recommendation",
            f"- {report['final_paper_only_recommendation_summary']}",
            "",
        ]
    )


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_portfolio_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
