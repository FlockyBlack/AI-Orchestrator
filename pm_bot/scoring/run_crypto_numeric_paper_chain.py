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
    parser = argparse.ArgumentParser(description="Run the PMBOT crypto numeric paper brain chain.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _rows_by_decision(review_table, decision):
    return [row for row in review_table["rows"] if row["decision"] == decision]


def _sum_max_loss(order_plan):
    return round(
        sum(float(entry.get("max_loss", 0.0)) for entry in order_plan["entries"] if entry["action"] == "paper_limit_order"),
        2,
    )


def build_crypto_numeric_paper_chain(root: Path):
    scoring_dir = root / "pm_bot" / "scoring"
    scorer = _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_crypto_numeric_chain_scorer")
    review = _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_crypto_numeric_chain_review")
    planner = _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_crypto_numeric_chain_planner")

    fixture = _load_json(scoring_dir / "crypto_numeric_fixture.v1.json")
    score_report = scorer.score_fixture(fixture)
    review_table = review.build_review_table(score_report)
    order_plan = planner.build_paper_order_plan(review_table)
    rejected_rows = _rows_by_decision(review_table, "reject")

    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-004-CRYPTO-NUMERIC-PAPER-CHAIN",
        "fixture_id": score_report["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "score_summary": {
            "markets_scored": score_report["markets_scored"],
            "paper_candidates": review_table["group_counts"]["paper_candidate"],
            "watchlist": review_table["group_counts"]["watchlist"],
            "rejected": review_table["group_counts"]["reject"],
        },
        "review_summary": {
            "paper_candidates": review_table["group_counts"]["paper_candidate"],
            "watchlist": review_table["group_counts"]["watchlist"],
            "rejected": review_table["group_counts"]["reject"],
            "operator_review_only": True,
        },
        "paper_order_summary": {
            "paper_limit_orders": order_plan["paper_order_count"],
            "no_action_entries": order_plan["no_action_count"],
            "total_planned_paper_notional": order_plan["total_planned_paper_notional"],
            "max_loss": _sum_max_loss(order_plan),
        },
        "paper_candidate_rows": _rows_by_decision(review_table, "paper_candidate"),
        "watchlist_rows": _rows_by_decision(review_table, "watchlist"),
        "rejected_rows": rejected_rows,
        "generated_paper_order_plan": order_plan,
        "limitations": [
            "Uses fixture input only; no live markets, prices, or APIs are fetched.",
            "Generated paper order plan is an offline review artifact only; no real order is created.",
            "No runtime integration, prompt automation, credentials, or wallet access is included.",
        ],
        "review_note": "End-to-end crypto numeric paper chain for operator review only.",
    }


def render_markdown(packet):
    lines = [
        "# PMBOT Crypto Numeric Paper Chain",
        "",
        "Deterministic offline/paper chain: scorer -> review table -> paper order plan.",
        "",
        "## Summary",
        "",
        f"- Markets scored: {packet['score_summary']['markets_scored']}",
        f"- Paper candidates: {packet['review_summary']['paper_candidates']}",
        f"- Watchlist: {packet['review_summary']['watchlist']}",
        f"- Rejected: {packet['review_summary']['rejected']}",
        f"- Paper limit orders: {packet['paper_order_summary']['paper_limit_orders']}",
        f"- Total planned paper notional: {packet['paper_order_summary']['total_planned_paper_notional']:.2f}",
        f"- Max loss: {packet['paper_order_summary']['max_loss']:.2f}",
        "",
        "## Paper Candidates",
        "",
        "| market_id | asset | side | edge_after_buffer | decision | reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
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
    lines.extend(["", "## Rejected", "", "| market_id | asset | side | edge_after_buffer | decision | reason |", "| --- | --- | --- | --- | --- | --- |"])
    for row in packet["rejected_rows"]:
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
    packet = build_crypto_numeric_paper_chain(root)
    if args.markdown:
        print(render_markdown(packet), end="")
    else:
        print(json.dumps(packet, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
