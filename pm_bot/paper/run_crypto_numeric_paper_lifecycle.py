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
    "real_order_created": False,
    "wallet_used": False,
    "api_used": False,
    "network_used": False,
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
    parser = argparse.ArgumentParser(description="Run the PMBOT crypto numeric paper lifecycle chain.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _rows_by_decision(review_table, decision):
    return [row for row in review_table["rows"] if row["decision"] == decision]


def _canonical_market_id(market_id):
    if market_id.startswith("raw_"):
        return "crypto_numeric_" + market_id[4:]
    return market_id


def _align_execution_fixture(order_plan, execution_fixture):
    executions = {row["market_id"]: row for row in execution_fixture["market_executions"]}
    aligned = dict(execution_fixture)
    aligned_rows = []
    for entry in order_plan["entries"]:
        source_id = entry["market_id"]
        execution = executions.get(source_id) or executions.get(_canonical_market_id(source_id))
        if execution is None:
            continue
        aligned_row = dict(execution)
        aligned_row["market_id"] = source_id
        aligned_rows.append(aligned_row)
    aligned["market_executions"] = aligned_rows
    return aligned


def _portfolio_summary(intake_report, score_report, review_table, ledger_report):
    ledger = ledger_report["ledger_summary"]
    open_positions = sum(1 for row in ledger_report["paper_positions"] if row["status"] == "open")
    settled_positions = sum(1 for row in ledger_report["paper_positions"] if row["settled"])
    return {
        "raw_markets": intake_report["summary"]["raw_markets"],
        "normalized_supported": intake_report["summary"]["normalized_supported"],
        "rejected_raw_markets": intake_report["summary"]["rejected"],
        "markets_scored": score_report["markets_scored"],
        "paper_candidates": review_table["group_counts"]["paper_candidate"],
        "watchlist": review_table["group_counts"]["watchlist"],
        "rejected_after_scoring": review_table["group_counts"]["reject"],
        "paper_orders_submitted": ledger["paper_orders_submitted"],
        "paper_orders_filled": ledger["paper_orders_filled"],
        "open_positions": open_positions,
        "settled_positions": settled_positions,
        "total_paper_notional": ledger["total_paper_notional"],
        "total_max_loss": ledger["total_max_loss"],
        "paper_pnl": ledger["paper_pnl"],
        "no_action_entries": ledger["no_action_entries"],
    }


def build_crypto_numeric_paper_lifecycle(root: Path):
    scoring_dir = root / "pm_bot" / "scoring"
    paper_dir = root / "pm_bot" / "paper"
    intake = _load_module(scoring_dir / "crypto_numeric_market_intake.py", "pmbot_lifecycle_intake")
    scorer = _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_lifecycle_scorer")
    review = _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_lifecycle_review")
    planner = _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_lifecycle_planner")
    ledger = _load_module(paper_dir / "crypto_numeric_paper_execution_ledger.py", "pmbot_lifecycle_ledger")

    raw_fixture = _load_json(scoring_dir / "crypto_numeric_raw_market_fixtures.v1.json")
    execution_fixture = _load_json(paper_dir / "crypto_numeric_execution_fixture.v1.json")
    intake_report = intake.build_intake_report(raw_fixture)
    normalized_fixture = intake_report["normalized_scorer_fixture"]
    score_report = scorer.score_fixture(normalized_fixture)
    review_table = review.build_review_table(score_report)
    order_plan = planner.build_paper_order_plan(review_table)
    aligned_execution_fixture = _align_execution_fixture(order_plan, execution_fixture)
    ledger_report = ledger.build_execution_ledger(order_plan, aligned_execution_fixture)
    lifecycle_summary = _portfolio_summary(intake_report, score_report, review_table, ledger_report)

    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-011-CRYPTO-NUMERIC-PAPER-LIFECYCLE-CHAIN",
        "source_fixture_id": raw_fixture["fixture_id"],
        "normalized_fixture_id": normalized_fixture["fixture_id"],
        "execution_fixture_id": execution_fixture["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "lifecycle_summary": lifecycle_summary,
        "intake_summary": intake_report["summary"],
        "score_summary": {
            "markets_scored": score_report["markets_scored"],
            "paper_candidates": review_table["group_counts"]["paper_candidate"],
            "watchlist": review_table["group_counts"]["watchlist"],
            "rejected_after_scoring": review_table["group_counts"]["reject"],
        },
        "portfolio_exposure_summary": {
            "paper_orders_submitted": lifecycle_summary["paper_orders_submitted"],
            "paper_orders_filled": lifecycle_summary["paper_orders_filled"],
            "open_positions": lifecycle_summary["open_positions"],
            "settled_positions": lifecycle_summary["settled_positions"],
            "total_paper_notional": lifecycle_summary["total_paper_notional"],
            "total_max_loss": lifecycle_summary["total_max_loss"],
            "paper_pnl": lifecycle_summary["paper_pnl"],
            "no_action_entries": lifecycle_summary["no_action_entries"],
            **SAFETY_FLAGS,
        },
        "rejected_raw_markets": intake_report["rejections"],
        "scoring_rejections": _rows_by_decision(review_table, "reject"),
        "watchlist_rows": _rows_by_decision(review_table, "watchlist"),
        "paper_candidate_rows": _rows_by_decision(review_table, "paper_candidate"),
        "generated_paper_order_plan": order_plan,
        "paper_execution_ledger": ledger_report,
        "paper_positions": ledger_report["paper_positions"],
        "limitations": [
            "Uses raw market, scoring, and execution fixtures only; no live markets, prices, or APIs are fetched.",
            "Execution fixture prices are aligned deterministically to raw-intake market IDs for this lifecycle command.",
            "Paper fills, settlement, exposure, and PnL are offline review calculations only.",
            "No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.",
        ],
        "review_note": "End-to-end crypto numeric paper lifecycle chain for offline operator review only.",
    }


def render_markdown(report):
    summary = report["lifecycle_summary"]
    lines = [
        "# PMBOT Crypto Numeric Paper Lifecycle",
        "",
        "Deterministic offline/paper lifecycle: raw intake -> scorer -> review -> paper plan -> execution ledger -> portfolio exposure.",
        "",
        "## Summary",
        "",
        f"- Raw markets: {summary['raw_markets']}",
        f"- Normalized supported: {summary['normalized_supported']}",
        f"- Rejected raw markets: {summary['rejected_raw_markets']}",
        f"- Markets scored: {summary['markets_scored']}",
        f"- Paper candidates: {summary['paper_candidates']}",
        f"- Watchlist: {summary['watchlist']}",
        f"- Rejected after scoring: {summary['rejected_after_scoring']}",
        f"- Paper orders submitted: {summary['paper_orders_submitted']}",
        f"- Paper orders filled: {summary['paper_orders_filled']}",
        f"- Open positions: {summary['open_positions']}",
        f"- Settled positions: {summary['settled_positions']}",
        f"- Total paper notional: {summary['total_paper_notional']:.2f}",
        f"- Total max loss: {summary['total_max_loss']:.2f}",
        f"- Paper PnL: {summary['paper_pnl']:.2f}",
        f"- No-action entries: {summary['no_action_entries']}",
        "",
        "## Rejected Raw Markets",
        "",
        "| market_id | reason_code | reason |",
        "| --- | --- | --- |",
    ]
    for row in report["rejected_raw_markets"]:
        lines.append(f"| {row['market_id']} | {row['reason_code']} | {row['reason']} |")

    lines.extend(["", "## Scoring Rejections", "", "| market_id | asset | side | edge_after_buffer | reason |", "| --- | --- | --- | --- | --- |"])
    for row in report["scoring_rejections"]:
        lines.append(f"| {row['market_id']} | {row['asset']} | {row['side']} | {row['edge_after_buffer']:.4f} | {row['short_reason']} |")

    lines.extend(["", "## Paper Positions", "", "| market_id | status | fill_price | shares | notional | max_loss | paper_pnl |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for position in report["paper_positions"]:
        lines.append(
            f"| {position['market_id']} | {position['status']} | {position['fill_price']:.4f} | "
            f"{position['shares']:.4f} | {position['paper_notional']:.2f} | {position['max_loss']:.2f} | "
            f"{position['paper_pnl']:.2f} |"
        )

    lines.extend(["", "## Ledger Events", "", "| event_type | market_id | reason |", "| --- | --- | --- |"])
    for event in report["paper_execution_ledger"]["events"]:
        lines.append(f"| {event['event_type']} | {event['market_id']} | {event['reason']} |")

    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_crypto_numeric_paper_lifecycle(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
