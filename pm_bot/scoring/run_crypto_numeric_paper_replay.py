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
    parser = argparse.ArgumentParser(description="Run the PMBOT crypto numeric paper replay.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _case_outcome(case):
    resolved_price = float(case["resolved_price"])
    target_price = float(case["target_price"])
    if case["side"] == "above":
        return resolved_price > target_price
    if case["side"] == "below":
        return resolved_price < target_price
    raise ValueError(f"unsupported side: {case['side']}")


def _paper_pnl(entry, won):
    if entry["action"] != "paper_limit_order":
        return 0.0
    if not won:
        return -round(float(entry["max_loss"]), 2)
    limit_price = float(entry["limit_price"])
    paper_notional = float(entry["paper_notional"])
    return round((paper_notional / limit_price) - paper_notional, 2)


def _replay_row(case, score, review_row, plan_entry):
    won = _case_outcome(case)
    has_paper_order = plan_entry["action"] == "paper_limit_order"
    simulated_result = "win" if has_paper_order and won else "loss" if has_paper_order else "no_fill_or_no_action"
    paper_pnl = _paper_pnl(plan_entry, won)
    return {
        "market_id": case["market_id"],
        "asset": case["asset"],
        "side": case["side"],
        "target_price": case["target_price"],
        "expiry": case["expiry"],
        "snapshot": {
            "current_price": case["current_price"],
            "market_yes_price": case["market_yes_price"],
            "liquidity_usd": case["liquidity_usd"],
            "spread": case["spread"],
        },
        "resolved_price": case["resolved_price"],
        "final_outcome": case["final_outcome"],
        "decision": review_row["decision"],
        "action": plan_entry["action"],
        "model_probability": score["model_probability"],
        "market_probability": score["market_probability"],
        "edge_after_buffer": score["edge_after_buffer"],
        "simulated_result": simulated_result,
        "paper_pnl": paper_pnl,
        "max_loss": round(float(plan_entry.get("max_loss", 0.0)), 2),
        "reason": plan_entry["reason"],
        **SAFETY_FLAGS,
    }


def build_crypto_numeric_paper_replay(root: Path):
    scoring_dir = root / "pm_bot" / "scoring"
    scorer = _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_crypto_numeric_replay_scorer")
    review = _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_crypto_numeric_replay_review")
    planner = _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_crypto_numeric_replay_planner")

    replay_fixture = _load_json(scoring_dir / "crypto_numeric_replay_cases.v1.json")
    score_fixture = {
        "fixture_id": replay_fixture["fixture_id"],
        "scoring_config": replay_fixture["scoring_config"],
        "markets": replay_fixture["replay_cases"],
    }
    score_report = scorer.score_fixture(score_fixture)
    review_table = review.build_review_table(score_report)
    order_plan = planner.build_paper_order_plan(review_table)

    scores_by_market = {row["market_id"]: row for row in score_report["scores"]}
    review_by_market = {row["market_id"]: row for row in review_table["rows"]}
    plan_by_market = {row["market_id"]: row for row in order_plan["entries"]}
    replay_rows = [
        _replay_row(case, scores_by_market[case["market_id"]], review_by_market[case["market_id"]], plan_by_market[case["market_id"]])
        for case in replay_fixture["replay_cases"]
    ]

    paper_orders = sum(1 for row in replay_rows if row["action"] == "paper_limit_order")
    wins = sum(1 for row in replay_rows if row["simulated_result"] == "win")
    losses = sum(1 for row in replay_rows if row["simulated_result"] == "loss")
    no_action = sum(1 for row in replay_rows if row["simulated_result"] == "no_fill_or_no_action")
    bad_entries = losses
    rejected_bad_cases = sum(
        1
        for row in replay_rows
        if row["decision"] == "reject" and row["action"] == "no_action" and row["final_outcome"] == "no"
    )
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-005-CRYPTO-NUMERIC-PAPER-REPLAY",
        "fixture_id": replay_fixture["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "summary": {
            "replay_cases": len(replay_rows),
            "paper_orders": paper_orders,
            "wins": wins,
            "losses": losses,
            "no_action": no_action,
            "total_paper_pnl": round(sum(row["paper_pnl"] for row in replay_rows), 2),
            "false_positive_or_bad_entry": bad_entries,
            "rejected_bad_cases": rejected_bad_cases,
        },
        "replay_rows": replay_rows,
        "limitations": [
            "Uses fixture replay cases only; no live markets, prices, or APIs are fetched.",
            "Paper PnL is simulated from fixture resolution prices and paper plan entries only.",
            "No runtime integration, prompt automation, credentials, or wallet access is included.",
        ],
        "review_note": "Replay output is for offline paper review only.",
    }


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# PMBOT Crypto Numeric Paper Replay",
        "",
        "Deterministic offline/paper replay for crypto numeric scoring and paper-plan decisions.",
        "",
        "## Summary",
        "",
        f"- Replay cases: {summary['replay_cases']}",
        f"- Paper orders: {summary['paper_orders']}",
        f"- Wins: {summary['wins']}",
        f"- Losses: {summary['losses']}",
        f"- No action: {summary['no_action']}",
        f"- Total paper PnL: {summary['total_paper_pnl']:.2f}",
        f"- Bad entries: {summary['false_positive_or_bad_entry']}",
        f"- Rejected bad cases: {summary['rejected_bad_cases']}",
        "",
        "## Replay Rows",
        "",
        "| market_id | asset | side | decision | action | result | paper_pnl | max_loss | reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["replay_rows"]:
        lines.append(
            f"| {row['market_id']} | {row['asset']} | {row['side']} | {row['decision']} | {row['action']} | "
            f"{row['simulated_result']} | {row['paper_pnl']:.2f} | {row['max_loss']:.2f} | {row['reason']} |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_crypto_numeric_paper_replay(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
