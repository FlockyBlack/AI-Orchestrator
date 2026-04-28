import argparse
import json
import sys
from pathlib import Path


RISK_LIMITS = {
    "max_paper_notional_per_market": 100.0,
    "max_total_paper_notional": 250.0,
    "minimum_edge_after_buffer": 0.04,
    "reject_low_liquidity": True,
    "reject_wide_spread": True,
    "reject_risk_fail": True,
}

SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "execution_allowed": False,
    "trading_allowed": False,
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Build the PMBOT crypto numeric paper order plan.")
    parser.add_argument("review_table", help="Path to crypto numeric review table JSON.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _no_action_reason(row):
    reasons = []
    if row["decision"] != "paper_candidate":
        reasons.append(f"decision is {row['decision']}")
    if float(row["edge_after_buffer"]) < RISK_LIMITS["minimum_edge_after_buffer"]:
        reasons.append("edge_after_buffer below minimum")
    if row["liquidity_status"] == "fail":
        reasons.append("low liquidity rejected")
    if row["spread_status"] == "fail":
        reasons.append("wide spread rejected")
    if row["risk_status"] == "fail":
        reasons.append("risk fail rejected")
    if row["risk_status"] == "watch":
        reasons.append("risk needs operator review")
    return "; ".join(reasons) if reasons else "paper plan not allowed by review gates"


def _can_plan(row):
    return (
        row["decision"] == "paper_candidate"
        and float(row["edge_after_buffer"]) >= RISK_LIMITS["minimum_edge_after_buffer"]
        and row["liquidity_status"] != "fail"
        and row["spread_status"] != "fail"
        and row["risk_status"] != "fail"
    )


def _paper_plan(row, remaining_total):
    paper_notional = min(RISK_LIMITS["max_paper_notional_per_market"], remaining_total)
    limit_price = round(float(row["market_probability"]), 4)
    return {
        "market_id": row["market_id"],
        "asset": row["asset"],
        "side": row["side"],
        "action": "paper_limit_order",
        "limit_price": limit_price,
        "paper_notional": round(paper_notional, 2),
        "max_loss": round(paper_notional, 2),
        "reason": "Paper candidate clears edge, liquidity, spread, and risk limits.",
        "risk_limits_applied": RISK_LIMITS,
        **SAFETY_FLAGS,
    }


def _no_action_entry(row):
    return {
        "market_id": row["market_id"],
        "asset": row["asset"],
        "side": row["side"],
        "action": "no_action",
        "reason": _no_action_reason(row),
        "risk_limits_applied": RISK_LIMITS,
        **SAFETY_FLAGS,
    }


def build_paper_order_plan(review_table):
    entries = []
    total_planned_notional = 0.0
    for row in review_table["rows"]:
        remaining_total = round(RISK_LIMITS["max_total_paper_notional"] - total_planned_notional, 2)
        if _can_plan(row) and remaining_total > 0:
            entry = _paper_plan(row, remaining_total)
            total_planned_notional = round(total_planned_notional + entry["paper_notional"], 2)
        else:
            entry = _no_action_entry(row)
        entries.append(entry)

    paper_order_count = sum(1 for entry in entries if entry["action"] == "paper_limit_order")
    no_action_count = sum(1 for entry in entries if entry["action"] == "no_action")
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-003-CRYPTO-NUMERIC-PAPER-ORDER-PLAN",
        "source_report_id": review_table["report_id"],
        "fixture_id": review_table["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "operator_review_only": True,
        "risk_limits": RISK_LIMITS,
        "paper_order_count": paper_order_count,
        "no_action_count": no_action_count,
        "total_planned_paper_notional": round(total_planned_notional, 2),
        "entries": entries,
        "review_note": "Paper order plans are offline review artifacts only. No execution, trading, order placement, or runtime action is allowed.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Crypto Numeric Paper Order Plan",
        "",
        "Offline paper-only plan generated from the crypto numeric review table.",
        "",
        f"- Paper limit orders: {report['paper_order_count']}",
        f"- No-action entries: {report['no_action_count']}",
        f"- Total planned paper notional: {report['total_planned_paper_notional']:.2f}",
        "",
        "| market_id | asset | side | action | limit_price | paper_notional | max_loss | reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in report["entries"]:
        limit_price = f"{entry['limit_price']:.4f}" if entry["action"] == "paper_limit_order" else ""
        paper_notional = f"{entry['paper_notional']:.2f}" if entry["action"] == "paper_limit_order" else ""
        max_loss = f"{entry['max_loss']:.2f}" if entry["action"] == "paper_limit_order" else ""
        lines.append(
            f"| {entry['market_id']} | {entry['asset']} | {entry['side']} | {entry['action']} | "
            f"{limit_price} | {paper_notional} | {max_loss} | {entry['reason']} |"
        )
    lines.extend(["", f"- {report['review_note']}", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    review_table = _load_json(Path(args.review_table))
    report = build_paper_order_plan(review_table)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
