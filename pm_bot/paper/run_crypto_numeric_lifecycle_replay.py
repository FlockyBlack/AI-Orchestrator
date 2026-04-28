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
    parser = argparse.ArgumentParser(description="Run deterministic crypto numeric paper lifecycle replay scenarios.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _rows_by_decision(review_table, decision):
    return [row for row in review_table["rows"] if row["decision"] == decision]


def _raw_fixture(case):
    return {
        "schema_version": "v1",
        "fixture_id": f"{case['scenario_id']}_raw_fixture_v1",
        "fixture_only": True,
        "paper_only": True,
        "raw_markets": case["raw_markets"],
    }


def _execution_fixture(case):
    return {
        "schema_version": "v1",
        "fixture_id": f"{case['scenario_id']}_execution_fixture_v1",
        "fixture_only": True,
        "paper_only": True,
        "execution_timestamp": "2026-05-31T16:00:00Z",
        "settlement_timestamp": "2026-05-31T23:59:00Z",
        "market_executions": case["market_executions"],
    }


def _scenario_status(case, ledger_report):
    if case["lifecycle_status"] == "rejected_raw_market":
        return "rejected_raw_market"
    if case["lifecycle_status"] == "no_action_watchlist_or_reject":
        return "no_action_watchlist_or_reject"
    summary = ledger_report["ledger_summary"]
    if summary["paper_orders_not_filled"]:
        return "not_filled"
    if ledger_report["paper_positions"]:
        position = ledger_report["paper_positions"][0]
        if position["status"] == "open":
            return "open_position"
        if position["paper_pnl"] > 0 and case["lifecycle_status"] == "filled_win":
            return "filled_win"
        if position["paper_pnl"] < 0:
            return "filled_loss"
        return "settled_position"
    return case["lifecycle_status"]


def _scenario_row(case, intake_report, review_table, ledger_report):
    ledger_summary = ledger_report["ledger_summary"]
    open_positions = sum(1 for row in ledger_report["paper_positions"] if row["status"] == "open")
    settled_positions = sum(1 for row in ledger_report["paper_positions"] if row["settled"])
    paper_pnl = ledger_summary["paper_pnl"]
    return {
        "scenario_id": case["scenario_id"],
        "lifecycle_status": _scenario_status(case, ledger_report),
        "paper_orders_submitted": ledger_summary["paper_orders_submitted"],
        "paper_orders_filled": ledger_summary["paper_orders_filled"],
        "paper_orders_not_filled": ledger_summary["paper_orders_not_filled"],
        "open_positions": open_positions,
        "settled_positions": settled_positions,
        "paper_pnl": paper_pnl,
        "no_action_entries": ledger_summary["no_action_entries"],
        "rejected_raw_markets": intake_report["summary"]["rejected"],
        "rejected_after_scoring": review_table["group_counts"]["reject"],
        "scoring_rejections": _rows_by_decision(review_table, "reject"),
        "expected_bad_case_rejected": bool(case["expected_bad_case_rejected"]),
        **SAFETY_FLAGS,
    }


def _build_scenario(case, modules):
    intake, scorer, review, planner, ledger = modules
    intake_report = intake.build_intake_report(_raw_fixture(case))
    normalized_fixture = intake_report["normalized_scorer_fixture"]
    normalized_fixture["fixture_id"] = f"{case['scenario_id']}_normalized_fixture_v1"
    score_report = scorer.score_fixture(normalized_fixture)
    review_table = review.build_review_table(score_report)
    order_plan = planner.build_paper_order_plan(review_table)
    execution_fixture = _execution_fixture(case)
    ledger_report = ledger.build_execution_ledger(order_plan, execution_fixture)
    scenario = _scenario_row(case, intake_report, review_table, ledger_report)
    scenario["paper_positions"] = ledger_report["paper_positions"]
    scenario["ledger_events"] = ledger_report["events"]
    scenario["rejected_raw_market_rows"] = intake_report["rejections"]
    return scenario


def _aggregate(scenarios):
    wins = sum(1 for row in scenarios if row["settled_positions"] and row["paper_pnl"] > 0)
    losses = sum(1 for row in scenarios if row["settled_positions"] and row["paper_pnl"] < 0)
    return {
        "scenarios": len(scenarios),
        "filled_orders": sum(row["paper_orders_filled"] for row in scenarios),
        "not_filled_orders": sum(row["paper_orders_not_filled"] for row in scenarios),
        "open_positions": sum(row["open_positions"] for row in scenarios),
        "settled_positions": sum(row["settled_positions"] for row in scenarios),
        "wins": wins,
        "losses": losses,
        "total_paper_pnl": round(sum(float(row["paper_pnl"]) for row in scenarios), 2),
        "bad_entries": losses,
        "rejected_bad_cases": sum(
            1 for row in scenarios if row["expected_bad_case_rejected"] and row["rejected_raw_markets"] > 0
        ),
    }


def build_lifecycle_replay(root: Path):
    scoring_dir = root / "pm_bot" / "scoring"
    paper_dir = root / "pm_bot" / "paper"
    modules = (
        _load_module(scoring_dir / "crypto_numeric_market_intake.py", "pmbot_replay_intake"),
        _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_replay_scorer"),
        _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_replay_review"),
        _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_replay_planner"),
        _load_module(paper_dir / "crypto_numeric_paper_execution_ledger.py", "pmbot_replay_ledger"),
    )
    fixture = _load_json(paper_dir / "crypto_numeric_lifecycle_replay_cases.v1.json")
    scenarios = [_build_scenario(case, modules) for case in fixture["scenarios"]]
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-012-MULTI-SCENARIO-PAPER-LIFECYCLE-REPLAY",
        "fixture_id": fixture["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "replay_summary": _aggregate(scenarios),
        "scenarios": scenarios,
        "limitations": [
            "Uses fixture replay scenarios only; no live markets, prices, or APIs are fetched.",
            "Each scenario composes the offline intake, scoring, review, paper plan, and paper execution ledger components.",
            "Paper fills, no-fills, open status, settlement, and PnL are deterministic local calculations only.",
            "No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.",
        ],
        "review_note": "Multi-scenario crypto numeric paper lifecycle replay for offline review only.",
    }


def render_markdown(report):
    summary = report["replay_summary"]
    lines = [
        "# PMBOT Crypto Numeric Lifecycle Replay",
        "",
        "Deterministic offline/paper replay across lifecycle outcomes.",
        "",
        "## Summary",
        "",
        f"- Scenarios: {summary['scenarios']}",
        f"- Filled orders: {summary['filled_orders']}",
        f"- Not-filled orders: {summary['not_filled_orders']}",
        f"- Open positions: {summary['open_positions']}",
        f"- Settled positions: {summary['settled_positions']}",
        f"- Wins: {summary['wins']}",
        f"- Losses: {summary['losses']}",
        f"- Total paper PnL: {summary['total_paper_pnl']:.2f}",
        f"- Bad entries: {summary['bad_entries']}",
        f"- Rejected bad cases: {summary['rejected_bad_cases']}",
        "",
        "## Scenarios",
        "",
        "| scenario_id | status | submitted | filled | not_filled | open | settled | pnl | no_action | raw_rejects |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["scenarios"]:
        lines.append(
            f"| {row['scenario_id']} | {row['lifecycle_status']} | {row['paper_orders_submitted']} | "
            f"{row['paper_orders_filled']} | {row['paper_orders_not_filled']} | {row['open_positions']} | "
            f"{row['settled_positions']} | {row['paper_pnl']:.2f} | {row['no_action_entries']} | "
            f"{row['rejected_raw_markets']} |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_lifecycle_replay(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
