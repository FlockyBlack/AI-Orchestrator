import argparse
import importlib.util
import json
import sys
from pathlib import Path


SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "execution_allowed": False,
    "trading_allowed": False,
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Run PMBOT crypto numeric raw intake through the paper chain.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _rows_by_decision(review_table, decision):
    return [row for row in review_table["rows"] if row["decision"] == decision]


def _sum_max_loss(order_plan):
    return round(
        sum(float(entry.get("max_loss", 0.0)) for entry in order_plan["entries"] if entry["action"] == "paper_limit_order"),
        2,
    )


def build_crypto_numeric_intake_to_chain(root: Path):
    scoring_dir = root / "pm_bot" / "scoring"
    intake = _load_module(scoring_dir / "crypto_numeric_market_intake.py", "pmbot_crypto_numeric_intake_to_chain_intake")
    scorer = _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_crypto_numeric_intake_to_chain_scorer")
    review = _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_crypto_numeric_intake_to_chain_review")
    planner = _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_crypto_numeric_intake_to_chain_planner")

    raw_fixture = _load_json(scoring_dir / "crypto_numeric_raw_market_fixtures.v1.json")
    intake_report = intake.build_intake_report(raw_fixture)
    normalized_fixture = intake_report["normalized_scorer_fixture"]
    score_report = scorer.score_fixture(normalized_fixture)
    review_table = review.build_review_table(score_report)
    order_plan = planner.build_paper_order_plan(review_table)

    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-009-CRYPTO-NUMERIC-INTAKE-TO-CHAIN",
        "source_fixture_id": raw_fixture["fixture_id"],
        "fixture_id": normalized_fixture["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "intake_summary": intake_report["summary"],
        "score_summary": {
            "markets_scored": score_report["markets_scored"],
            "paper_candidates": review_table["group_counts"]["paper_candidate"],
            "watchlist": review_table["group_counts"]["watchlist"],
            "rejected_after_scoring": review_table["group_counts"]["reject"],
        },
        "review_summary": {
            "paper_candidates": review_table["group_counts"]["paper_candidate"],
            "watchlist": review_table["group_counts"]["watchlist"],
            "rejected_after_scoring": review_table["group_counts"]["reject"],
            "operator_review_only": True,
        },
        "paper_order_summary": {
            "paper_limit_orders": order_plan["paper_order_count"],
            "no_action_entries": order_plan["no_action_count"],
            "total_planned_paper_notional": order_plan["total_planned_paper_notional"],
            "max_loss": _sum_max_loss(order_plan),
        },
        "rejected_raw_markets": intake_report["rejections"],
        "normalized_supported_markets": normalized_fixture["markets"],
        "score_report": score_report,
        "review_table": review_table,
        "paper_candidate_rows": _rows_by_decision(review_table, "paper_candidate"),
        "watchlist_rows": _rows_by_decision(review_table, "watchlist"),
        "rejected_after_scoring_rows": _rows_by_decision(review_table, "reject"),
        "generated_paper_order_plan": order_plan,
        "limitations": [
            "Uses raw fixture input only; no live markets, prices, or APIs are fetched.",
            "Rejected raw markets are retained with deterministic rejection reason codes.",
            "Generated paper order plan is an offline review artifact only; no real order is created.",
            "No runtime integration, prompt automation, credentials, or wallet access is included.",
        ],
        "review_note": "End-to-end raw intake -> scorer -> review table -> paper order plan for operator review only.",
    }


def render_markdown(packet):
    intake_summary = packet["intake_summary"]
    score_summary = packet["score_summary"]
    order_summary = packet["paper_order_summary"]
    lines = [
        "# PMBOT Crypto Numeric Intake To Chain",
        "",
        "Deterministic offline/paper chain: raw fixture intake -> scorer -> review table -> paper order plan.",
        "",
        "## Summary",
        "",
        f"- Raw markets: {intake_summary['raw_markets']}",
        f"- Normalized supported: {intake_summary['normalized_supported']}",
        f"- Rejected raw markets: {intake_summary['rejected']}",
        f"- Markets scored: {score_summary['markets_scored']}",
        f"- Paper candidates: {score_summary['paper_candidates']}",
        f"- Watchlist: {score_summary['watchlist']}",
        f"- Rejected after scoring: {score_summary['rejected_after_scoring']}",
        f"- Paper limit orders: {order_summary['paper_limit_orders']}",
        f"- Total planned paper notional: {order_summary['total_planned_paper_notional']:.2f}",
        f"- Max loss: {order_summary['max_loss']:.2f}",
        "",
        "## Rejected Raw Markets",
        "",
        "| market_id | reason_code | reason |",
        "| --- | --- | --- |",
    ]
    for row in packet["rejected_raw_markets"]:
        lines.append(f"| {row['market_id']} | {row['reason_code']} | {row['reason']} |")

    lines.extend(["", "## Paper Candidates", "", "| market_id | asset | side | edge_after_buffer | decision | reason |", "| --- | --- | --- | --- | --- | --- |"])
    for row in packet["paper_candidate_rows"]:
        lines.append(
            f"| {row['market_id']} | {row['asset']} | {row['side']} | {row['edge_after_buffer']:.4f} | "
            f"{row['decision']} | {row['short_reason']} |"
        )

    lines.extend(["", "## Watchlist", "", "| market_id | asset | side | edge_after_buffer | decision | reason |", "| --- | --- | --- | --- | --- | --- |"])
    for row in packet["watchlist_rows"]:
        lines.append(
            f"| {row['market_id']} | {row['asset']} | {row['side']} | {row['edge_after_buffer']:.4f} | "
            f"{row['decision']} | {row['short_reason']} |"
        )

    lines.extend(["", "## Rejected After Scoring", "", "| market_id | asset | side | edge_after_buffer | decision | reason |", "| --- | --- | --- | --- | --- | --- |"])
    for row in packet["rejected_after_scoring_rows"]:
        lines.append(
            f"| {row['market_id']} | {row['asset']} | {row['side']} | {row['edge_after_buffer']:.4f} | "
            f"{row['decision']} | {row['short_reason']} |"
        )

    lines.extend(["", "## Generated Paper Order Plan", "", "| market_id | action | limit_price | paper_notional | max_loss | reason |", "| --- | --- | --- | --- | --- | --- |"])
    for entry in packet["generated_paper_order_plan"]["entries"]:
        limit_price = f"{entry['limit_price']:.4f}" if entry["action"] == "paper_limit_order" else ""
        paper_notional = f"{entry['paper_notional']:.2f}" if entry["action"] == "paper_limit_order" else ""
        max_loss = f"{entry['max_loss']:.2f}" if entry["action"] == "paper_limit_order" else ""
        lines.append(
            f"| {entry['market_id']} | {entry['action']} | {limit_price} | {paper_notional} | {max_loss} | {entry['reason']} |"
        )

    lines.extend(["", "## Limitations", ""])
    for item in packet["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    packet = build_crypto_numeric_intake_to_chain(root)
    if args.markdown:
        print(render_markdown(packet), end="")
    else:
        print(json.dumps(packet, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
