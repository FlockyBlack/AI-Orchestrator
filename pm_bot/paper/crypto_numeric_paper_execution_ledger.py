import argparse
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


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Build a deterministic crypto numeric paper execution ledger.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _execution_by_market(execution_fixture):
    return {row["market_id"]: row for row in execution_fixture["market_executions"]}


def _shares(paper_notional, fill_price):
    if fill_price <= 0:
        return 0.0
    return round(paper_notional / fill_price, 4)


def _paper_pnl(position):
    if position["settled"]:
        final_value = float(position["settlement_value"])
    else:
        final_value = float(position["current_yes_price"])
    return round((float(position["shares"]) * final_value) - float(position["paper_notional"]), 2)


def _submitted_event(entry, timestamp):
    return {
        "event_type": "paper_order_submitted",
        "timestamp": timestamp,
        "market_id": entry["market_id"],
        "asset": entry["asset"],
        "side": entry["side"],
        "limit_price": entry["limit_price"],
        "paper_notional": entry["paper_notional"],
        "max_loss": entry["max_loss"],
        "reason": entry["reason"],
        **SAFETY_FLAGS,
    }


def _filled_event(entry, execution, timestamp):
    fill_price = round(float(execution["observed_yes_price"]), 4)
    shares = _shares(float(entry["paper_notional"]), fill_price)
    return {
        "event_type": "paper_order_filled",
        "timestamp": timestamp,
        "market_id": entry["market_id"],
        "asset": entry["asset"],
        "side": entry["side"],
        "limit_price": entry["limit_price"],
        "fill_price": fill_price,
        "shares": shares,
        "paper_notional": entry["paper_notional"],
        "max_loss": entry["max_loss"],
        "reason": "Fixture observed_yes_price is at or below the paper limit price.",
        **SAFETY_FLAGS,
    }


def _not_filled_event(entry, execution, timestamp, reason=None):
    return {
        "event_type": "paper_order_not_filled",
        "timestamp": timestamp,
        "market_id": entry["market_id"],
        "asset": entry["asset"],
        "side": entry["side"],
        "limit_price": entry["limit_price"],
        "observed_yes_price": round(float(execution["observed_yes_price"]), 4),
        "paper_notional": entry["paper_notional"],
        "max_loss": entry["max_loss"],
        "reason": reason or "Fixture observed_yes_price is above the paper limit price.",
        **SAFETY_FLAGS,
    }


def _no_action_entry(entry, timestamp):
    return {
        "event_type": "no_action_preserved",
        "timestamp": timestamp,
        "market_id": entry["market_id"],
        "asset": entry["asset"],
        "side": entry["side"],
        "action": "no_action",
        "reason": entry["reason"],
        **SAFETY_FLAGS,
    }


def _position(entry, execution, fill_event, settlement_timestamp):
    settled = bool(execution.get("settled", False))
    settlement_outcome = execution.get("settlement_outcome") if settled else None
    settlement_value = 1.0 if settlement_outcome == "yes" else 0.0 if settlement_outcome == "no" else None
    position = {
        "market_id": entry["market_id"],
        "asset": entry["asset"],
        "side": entry["side"],
        "status": "settled" if settled else "open",
        "opened_at": fill_event["timestamp"],
        "settled_at": settlement_timestamp if settled else None,
        "fill_price": fill_event["fill_price"],
        "shares": fill_event["shares"],
        "paper_notional": entry["paper_notional"],
        "max_loss": entry["max_loss"],
        "current_yes_price": round(float(execution["current_yes_price"]), 4),
        "settled": settled,
        "settlement_outcome": settlement_outcome,
        "settlement_value": settlement_value,
        **SAFETY_FLAGS,
    }
    position["paper_pnl"] = _paper_pnl(position)
    return position


def build_execution_ledger(order_plan, execution_fixture):
    executions = _execution_by_market(execution_fixture)
    events = []
    positions = []
    no_action_entries = []
    submitted = 0
    filled = 0
    not_filled = 0

    execution_timestamp = execution_fixture["execution_timestamp"]
    settlement_timestamp = execution_fixture["settlement_timestamp"]
    for entry in order_plan["entries"]:
        if entry["action"] != "paper_limit_order":
            no_action = _no_action_entry(entry, execution_timestamp)
            no_action_entries.append(no_action)
            events.append(no_action)
            continue

        submitted += 1
        events.append(_submitted_event(entry, execution_timestamp))
        execution = executions[entry["market_id"]]
        if execution.get("settled") and execution.get("settlement_outcome") == "no":
            not_filled += 1
            events.append(_not_filled_event(entry, execution, execution_timestamp, "Fixture market is already settled no; paper fill blocked."))
        elif float(execution["observed_yes_price"]) <= float(entry["limit_price"]):
            filled += 1
            fill_event = _filled_event(entry, execution, execution_timestamp)
            events.append(fill_event)
            positions.append(_position(entry, execution, fill_event, settlement_timestamp))
        else:
            not_filled += 1
            events.append(_not_filled_event(entry, execution, execution_timestamp))

    summary = {
        "paper_orders_seen": sum(1 for entry in order_plan["entries"] if entry["action"] == "paper_limit_order"),
        "paper_orders_submitted": submitted,
        "paper_orders_filled": filled,
        "paper_orders_not_filled": not_filled,
        "paper_positions_opened": len(positions),
        "paper_positions_closed_or_settled": sum(1 for position in positions if position["settled"]),
        "no_action_entries": len(no_action_entries),
        "total_paper_notional": round(sum(float(position["paper_notional"]) for position in positions), 2),
        "total_max_loss": round(sum(float(position["max_loss"]) for position in positions), 2),
        "paper_pnl": round(sum(float(position["paper_pnl"]) for position in positions), 2),
    }
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-010-CRYPTO-NUMERIC-PAPER-EXECUTION-LEDGER",
        "source_report_id": order_plan["report_id"],
        "fixture_id": execution_fixture["fixture_id"],
        "source_order_plan_fixture_id": order_plan["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "ledger_summary": summary,
        "events": events,
        "paper_positions": positions,
        "no_action_entries": no_action_entries,
        "limitations": [
            "Uses fixture paper order plan and fixture execution prices only; no live market data is fetched.",
            "Paper fills, settlement, and PnL are deterministic local calculations only.",
            "No real order, wallet, credential, network, runtime integration, or trading path is included.",
        ],
        "review_note": "Paper execution ledger is an offline lifecycle review artifact only.",
    }


def render_markdown(report):
    summary = report["ledger_summary"]
    lines = [
        "# PMBOT Crypto Numeric Paper Execution Ledger",
        "",
        "Deterministic offline/paper ledger for crypto numeric paper order plans.",
        "",
        "## Summary",
        "",
        f"- Paper orders seen: {summary['paper_orders_seen']}",
        f"- Paper orders submitted: {summary['paper_orders_submitted']}",
        f"- Paper orders filled: {summary['paper_orders_filled']}",
        f"- Paper orders not filled: {summary['paper_orders_not_filled']}",
        f"- Paper positions opened: {summary['paper_positions_opened']}",
        f"- Paper positions closed or settled: {summary['paper_positions_closed_or_settled']}",
        f"- No-action entries: {summary['no_action_entries']}",
        f"- Total paper notional: {summary['total_paper_notional']:.2f}",
        f"- Total max loss: {summary['total_max_loss']:.2f}",
        f"- Paper PnL: {summary['paper_pnl']:.2f}",
        "",
        "## Events",
        "",
        "| event_type | market_id | paper_notional | price | reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for event in report["events"]:
        price = ""
        if event["event_type"] == "paper_order_submitted":
            price = f"limit {event['limit_price']:.4f}"
        elif event["event_type"] == "paper_order_filled":
            price = f"fill {event['fill_price']:.4f}"
        elif event["event_type"] == "paper_order_not_filled":
            price = f"observed {event['observed_yes_price']:.4f}"
        paper_notional = f"{event.get('paper_notional', 0.0):.2f}" if "paper_notional" in event else ""
        lines.append(f"| {event['event_type']} | {event['market_id']} | {paper_notional} | {price} | {event['reason']} |")

    lines.extend(["", "## Paper Positions", "", "| market_id | status | fill_price | shares | paper_notional | max_loss | settlement | paper_pnl |", "| --- | --- | --- | --- | --- | --- | --- | --- |"])
    for position in report["paper_positions"]:
        settlement = position["settlement_outcome"] if position["settled"] else "open"
        lines.append(
            f"| {position['market_id']} | {position['status']} | {position['fill_price']:.4f} | "
            f"{position['shares']:.4f} | {position['paper_notional']:.2f} | {position['max_loss']:.2f} | "
            f"{settlement} | {position['paper_pnl']:.2f} |"
        )

    lines.extend(["", "## No Action", "", "| market_id | reason |", "| --- | --- |"])
    for entry in report["no_action_entries"]:
        lines.append(f"| {entry['market_id']} | {entry['reason']} |")

    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    order_plan = _load_json(root / "pm_bot" / "scoring" / "expected_crypto_numeric_paper_order_plan.v1.json")
    execution_fixture = _load_json(root / "pm_bot" / "paper" / "crypto_numeric_execution_fixture.v1.json")
    report = build_execution_ledger(order_plan, execution_fixture)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
