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
    parser = argparse.ArgumentParser(description="Run crypto numeric guardrail coverage cases.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _directional_gap(case):
    current_price = float(case["current_price"])
    target_price = float(case["target_price"])
    if case["side"] == "above":
        return round((current_price - target_price) / target_price, 4)
    if case["side"] == "below":
        return round((target_price - current_price) / target_price, 4)
    raise ValueError(f"unsupported side: {case['side']}")


def _coverage_row(case, score, review_row, plan_entry):
    expected_decision = case["expected_decision"]
    expected_trigger = bool(case["expected_guardrail_triggered"])
    actual_trigger = expected_trigger and review_row["decision"] == "watchlist"
    unexpected_block = (
        not expected_trigger
        and expected_decision == "paper_candidate"
        and review_row["decision"] != "paper_candidate"
    )
    unexpected_allow = expected_trigger and plan_entry["action"] == "paper_limit_order"
    return {
        "case_id": case["case_id"],
        "market_id": case["market_id"],
        "asset": case["asset"],
        "side": case["side"],
        "target_price": case["target_price"],
        "current_price": case["current_price"],
        "market_yes_price": case["market_yes_price"],
        "directional_gap": _directional_gap(case),
        "expected_guardrail_triggered": expected_trigger,
        "guardrail_triggered": actual_trigger,
        "expected_decision": expected_decision,
        "actual_decision": review_row["decision"],
        "paper_action": plan_entry["action"],
        "model_probability": score["model_probability"],
        "edge_after_buffer": score["edge_after_buffer"],
        "unexpected_block": unexpected_block,
        "unexpected_allow": unexpected_allow,
        **SAFETY_FLAGS,
    }


def build_crypto_numeric_guardrail_coverage(root: Path):
    scoring_dir = root / "pm_bot" / "scoring"
    scorer = _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_crypto_numeric_guardrail_scorer")
    review = _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_crypto_numeric_guardrail_review")
    planner = _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_crypto_numeric_guardrail_planner")

    fixture = _load_json(scoring_dir / "crypto_numeric_guardrail_coverage_cases.v1.json")
    score_fixture = {
        "fixture_id": fixture["fixture_id"],
        "scoring_config": fixture["scoring_config"],
        "markets": fixture["coverage_cases"],
    }
    score_report = scorer.score_fixture(score_fixture)
    review_table = review.build_review_table(score_report)
    order_plan = planner.build_paper_order_plan(review_table)

    scores_by_market = {row["market_id"]: row for row in score_report["scores"]}
    review_by_market = {row["market_id"]: row for row in review_table["rows"]}
    plan_by_market = {row["market_id"]: row for row in order_plan["entries"]}
    rows = [
        _coverage_row(case, scores_by_market[case["market_id"]], review_by_market[case["market_id"]], plan_by_market[case["market_id"]])
        for case in fixture["coverage_cases"]
    ]
    summary = {
        "coverage_cases": len(rows),
        "guardrail_triggered": sum(1 for row in rows if row["guardrail_triggered"]),
        "paper_candidates_preserved": sum(1 for row in rows if row["actual_decision"] == "paper_candidate"),
        "watchlist_caps": sum(1 for row in rows if row["expected_guardrail_triggered"] and row["actual_decision"] == "watchlist"),
        "unexpected_blocks": sum(1 for row in rows if row["unexpected_block"]),
        "unexpected_allows": sum(1 for row in rows if row["unexpected_allow"]),
    }
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-007-CRYPTO-NUMERIC-GUARDRAIL-COVERAGE",
        "fixture_id": fixture["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "coverage_summary": summary,
        "coverage_rows": rows,
        "limitations": [
            "Uses fixture coverage cases only; no live markets, prices, or APIs are fetched.",
            "Coverage characterizes the current extension rule and does not broaden it.",
            "No runtime integration, prompt automation, credentials, or wallet access is included.",
        ],
        "review_note": "Guardrail coverage output is for offline paper review only.",
    }


def render_markdown(report):
    summary = report["coverage_summary"]
    lines = [
        "# PMBOT Crypto Numeric Guardrail Coverage",
        "",
        "Fixture-only coverage around the extension guard threshold.",
        "",
        "## Summary",
        "",
        f"- Coverage cases: {summary['coverage_cases']}",
        f"- Guardrail triggered: {summary['guardrail_triggered']}",
        f"- Paper candidates preserved: {summary['paper_candidates_preserved']}",
        f"- Watchlist caps: {summary['watchlist_caps']}",
        f"- Unexpected blocks: {summary['unexpected_blocks']}",
        f"- Unexpected allows: {summary['unexpected_allows']}",
        "",
        "## Coverage Rows",
        "",
        "| case_id | gap | yes_price | expected_trigger | decision | action | unexpected_block | unexpected_allow |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["coverage_rows"]:
        lines.append(
            f"| {row['case_id']} | {row['directional_gap']:.4f} | {row['market_yes_price']:.4f} | "
            f"{str(row['expected_guardrail_triggered']).lower()} | {row['actual_decision']} | {row['paper_action']} | "
            f"{str(row['unexpected_block']).lower()} | {str(row['unexpected_allow']).lower()} |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_crypto_numeric_guardrail_coverage(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
