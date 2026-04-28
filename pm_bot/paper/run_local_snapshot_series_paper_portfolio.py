import argparse
import importlib.util
import json
import sys
from pathlib import Path


SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "live_fetcher_implemented": False,
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
    parser = argparse.ArgumentParser(description="Replay local live-shaped snapshot series into an offline paper portfolio.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _reason_counts(rejections):
    counts = {}
    for item in rejections:
        counts[item["reason_code"]] = counts.get(item["reason_code"], 0) + 1
    return counts


def _risk_limit_reason_counts(events):
    counts = {}
    for event in events:
        if event["event_type"] != "risk_limit_paper_order_blocked":
            continue
        for reason_code in event["reason_codes"]:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return counts


def _risk_limit_decisions(events):
    decisions = []
    for event in events:
        if event["event_type"] != "risk_limit_paper_order_blocked":
            continue
        decisions.append({
            "timestamp": event["timestamp"],
            "market_id": event["market_id"],
            "asset": event["asset"],
            "side": event["side"],
            "paper_notional": event["paper_notional"],
            "decision": "blocked",
            "action": "no_action",
            "reason": event["reason"],
            "reason_codes": event["reason_codes"],
            "risk_limit_reasons": event["risk_limit_reasons"],
            "portfolio_risk_limits": event["portfolio_risk_limits"],
            **SAFETY_FLAGS,
        })
    return decisions


def _adapt_snapshot_fixture(adapter, snapshot_fixture, snapshot_id):
    adapted = []
    rejections = []
    for snapshot in snapshot_fixture["markets"]:
        raw_record, rejection = adapter._adapt_snapshot(snapshot)
        if rejection is None:
            adapted.append(raw_record)
        else:
            row = dict(rejection)
            row["snapshot_id"] = snapshot_id
            rejections.append(row)
    return {
        "schema_version": "v1",
        "fixture_id": f"{snapshot_id}_adapted_raw_markets_v1",
        "fixture_only": True,
        "paper_only": True,
        "raw_markets": adapted,
    }, rejections


def _rows_by_decision(review_table, decision):
    return [row for row in review_table["rows"] if row["decision"] == decision]


def _position_key(market_id, side):
    return f"{market_id}|{side}"


def _shares(paper_notional, fill_price):
    if fill_price <= 0:
        return 0.0
    return round(paper_notional / fill_price, 4)


def _position_pnl(position):
    final_price = float(position["settlement_value"]) if position["settled"] else float(position["current_yes_price"])
    return round((float(position["shares"]) * final_price) - float(position["paper_notional"]), 2)


def _apply_current_prices(positions, current_prices):
    for position in positions.values():
        if position["settled"]:
            continue
        if position["market_id"] in current_prices:
            position["current_yes_price"] = round(float(current_prices[position["market_id"]]), 4)
            position["paper_pnl"] = _position_pnl(position)


def _apply_settlements(positions, settlements, timestamp):
    settled_events = []
    for settlement in settlements:
        key = _position_key(settlement["market_id"], settlement["side"])
        position = positions.get(key)
        if position is None or position["settled"]:
            continue
        outcome = settlement["settlement_outcome"]
        position["status"] = "settled"
        position["settled"] = True
        position["settled_at"] = timestamp
        position["settlement_outcome"] = outcome
        position["settlement_value"] = 1.0 if outcome == "yes" else 0.0
        position["current_yes_price"] = position["settlement_value"]
        position["paper_pnl"] = _position_pnl(position)
        settled_events.append({
            "event_type": "paper_position_settled",
            "timestamp": timestamp,
            "market_id": position["market_id"],
            "side": position["side"],
            "settlement_outcome": outcome,
            "paper_pnl": position["paper_pnl"],
            **SAFETY_FLAGS,
        })
    return settled_events


def _exposure_summary(positions):
    rows = list(positions.values())
    open_rows = [row for row in rows if not row["settled"]]
    settled_rows = [row for row in rows if row["settled"]]
    return {
        "open_positions": len(open_rows),
        "settled_positions": len(settled_rows),
        "total_paper_notional": round(sum(float(row["paper_notional"]) for row in rows), 2),
        "open_paper_notional": round(sum(float(row["paper_notional"]) for row in open_rows), 2),
        "realized_paper_pnl": round(sum(float(row["paper_pnl"]) for row in settled_rows), 2),
        "unrealized_paper_pnl": round(sum(float(row["paper_pnl"]) for row in open_rows), 2),
    }


def _open_positions(positions):
    return [row for row in positions.values() if not row["settled"]]


def _open_paper_notional(positions):
    return round(sum(float(row["paper_notional"]) for row in _open_positions(positions)), 2)


def _open_asset_paper_notional(positions, asset):
    return round(sum(float(row["paper_notional"]) for row in _open_positions(positions) if row["asset"] == asset), 2)


def _safety_locked(report):
    return all(report.get(key) == value for key, value in SAFETY_FLAGS.items())


def _all_nested_safety_locked(rows):
    return all(all(row.get(key) == value for key, value in SAFETY_FLAGS.items()) for row in rows)


def _create_position(entry, observed_price, timestamp):
    fill_price = round(float(observed_price), 4)
    shares = _shares(float(entry["paper_notional"]), fill_price)
    position = {
        "market_id": entry["market_id"],
        "asset": entry["asset"],
        "side": entry["side"],
        "status": "open",
        "opened_at": timestamp,
        "settled_at": None,
        "fill_price": fill_price,
        "shares": shares,
        "paper_notional": entry["paper_notional"],
        "max_loss": entry["max_loss"],
        "current_yes_price": fill_price,
        "settled": False,
        "settlement_outcome": None,
        "settlement_value": None,
        **SAFETY_FLAGS,
    }
    position["paper_pnl"] = _position_pnl(position)
    return position


def _risk_limit_reasons(entry, positions, risk_limits, snapshot_orders_created):
    reasons = []
    paper_notional = float(entry["paper_notional"])
    projected_total = round(_open_paper_notional(positions) + paper_notional, 2)
    projected_asset = round(_open_asset_paper_notional(positions, entry["asset"]) + paper_notional, 2)
    projected_open_positions = len(_open_positions(positions)) + 1
    if projected_total > float(risk_limits["max_total_paper_exposure"]):
        reasons.append({
            "reason_code": "max_total_paper_exposure_exceeded",
            "reason": "Paper order would exceed max_total_paper_exposure.",
            "projected_value": projected_total,
            "limit": risk_limits["max_total_paper_exposure"],
        })
    if projected_asset > float(risk_limits["max_asset_paper_exposure"]):
        reasons.append({
            "reason_code": "max_asset_paper_exposure_exceeded",
            "reason": "Paper order would exceed max_asset_paper_exposure.",
            "projected_value": projected_asset,
            "limit": risk_limits["max_asset_paper_exposure"],
        })
    if snapshot_orders_created >= int(risk_limits["max_orders_per_snapshot"]):
        reasons.append({
            "reason_code": "max_orders_per_snapshot_exceeded",
            "reason": "Paper order would exceed max_orders_per_snapshot.",
            "projected_value": snapshot_orders_created + 1,
            "limit": risk_limits["max_orders_per_snapshot"],
        })
    if projected_open_positions > int(risk_limits["max_open_positions"]):
        reasons.append({
            "reason_code": "max_open_positions_exceeded",
            "reason": "Paper order would exceed max_open_positions.",
            "projected_value": projected_open_positions,
            "limit": risk_limits["max_open_positions"],
        })
    return reasons


def _process_order_plan(order_plan, positions, snapshot_entry, risk_limits):
    events = []
    orders_created = 0
    duplicates_blocked = 0
    risk_limit_orders_blocked = 0
    timestamp = snapshot_entry["observed_at"]
    observed_prices = snapshot_entry.get("observed_prices", {})
    for entry in order_plan["entries"]:
        if entry["action"] != "paper_limit_order":
            events.append({
                "event_type": "no_action_preserved",
                "timestamp": timestamp,
                "market_id": entry["market_id"],
                "side": entry["side"],
                "reason": entry["reason"],
                **SAFETY_FLAGS,
            })
            continue
        key = _position_key(entry["market_id"], entry["side"])
        if key in positions:
            duplicates_blocked += 1
            events.append({
                "event_type": "duplicate_paper_order_blocked",
                "timestamp": timestamp,
                "market_id": entry["market_id"],
                "side": entry["side"],
                "reason": "Paper position already exists for this market and side.",
                **SAFETY_FLAGS,
            })
            continue
        risk_reasons = _risk_limit_reasons(entry, positions, risk_limits, orders_created)
        if risk_reasons:
            risk_limit_orders_blocked += 1
            events.append({
                "event_type": "risk_limit_paper_order_blocked",
                "timestamp": timestamp,
                "market_id": entry["market_id"],
                "asset": entry["asset"],
                "side": entry["side"],
                "paper_notional": entry["paper_notional"],
                "reason": "; ".join(row["reason"] for row in risk_reasons),
                "reason_codes": [row["reason_code"] for row in risk_reasons],
                "risk_limit_reasons": risk_reasons,
                "portfolio_risk_limits": risk_limits,
                **SAFETY_FLAGS,
            })
            continue
        observed_price = observed_prices.get(entry["market_id"], entry["limit_price"])
        if float(observed_price) > float(entry["limit_price"]):
            events.append({
                "event_type": "paper_order_not_filled",
                "timestamp": timestamp,
                "market_id": entry["market_id"],
                "side": entry["side"],
                "limit_price": entry["limit_price"],
                "observed_yes_price": round(float(observed_price), 4),
                "reason": "Fixture observed_yes_price is above the paper limit price.",
                **SAFETY_FLAGS,
            })
            continue
        position = _create_position(entry, observed_price, timestamp)
        positions[key] = position
        orders_created += 1
        events.append({
            "event_type": "paper_order_created",
            "timestamp": timestamp,
            "market_id": entry["market_id"],
            "side": entry["side"],
            "limit_price": entry["limit_price"],
            "fill_price": position["fill_price"],
            "paper_notional": position["paper_notional"],
            "shares": position["shares"],
            "reason": "Paper candidate filled from local series fixture observed_yes_price.",
            **SAFETY_FLAGS,
        })
    return orders_created, duplicates_blocked, risk_limit_orders_blocked, events


def build_local_snapshot_series_paper_portfolio(root: Path):
    scoring_dir = root / "pm_bot" / "scoring"
    paper_dir = root / "pm_bot" / "paper"
    adapter = _load_module(scoring_dir / "adapt_live_shaped_crypto_snapshot.py", "pmbot_series_adapter")
    intake = _load_module(scoring_dir / "crypto_numeric_market_intake.py", "pmbot_series_intake")
    scorer = _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_series_scorer")
    review = _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_series_review")
    planner = _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_series_planner")

    fixture = _load_json(paper_dir / "local_snapshot_series_fixture.v1.json")
    portfolio_risk_limits = _load_json(paper_dir / "portfolio_risk_limits.v1.json")
    snapshots = sorted(fixture["snapshots"], key=lambda row: row["observed_at"])
    positions = {}
    snapshot_reports = []
    portfolio_events = []
    adapter_rejections = []
    intake_rejections = []
    scoring_rejections = []
    total_snapshot_markets = 0
    adapted_raw_markets = 0
    paper_orders_created = 0
    duplicate_orders_blocked = 0
    risk_limit_orders_blocked = 0
    max_exposure = 0.0
    bad_entries = 0

    for snapshot_entry in snapshots:
        snapshot_id = snapshot_entry["snapshot_id"]
        snapshot_fixture = snapshot_entry["snapshot"]
        total_snapshot_markets += len(snapshot_fixture["markets"])
        raw_fixture, snapshot_adapter_rejections = _adapt_snapshot_fixture(adapter, snapshot_fixture, snapshot_id)
        adapter_rejections.extend(snapshot_adapter_rejections)
        adapted_raw_markets += len(raw_fixture["raw_markets"])
        intake_report = intake.build_intake_report(raw_fixture)
        normalized_fixture = intake_report["normalized_scorer_fixture"]
        score_report = scorer.score_fixture(normalized_fixture)
        review_table = review.build_review_table(score_report)
        order_plan = planner.build_paper_order_plan(review_table)
        snapshot_intake_rejections = [dict(row, snapshot_id=snapshot_id) for row in intake_report["rejections"]]
        snapshot_scoring_rejections = [dict(row, snapshot_id=snapshot_id) for row in _rows_by_decision(review_table, "reject")]
        intake_rejections.extend(snapshot_intake_rejections)
        scoring_rejections.extend(snapshot_scoring_rejections)

        created, duplicates, risk_blocked, events = _process_order_plan(order_plan, positions, snapshot_entry, portfolio_risk_limits)
        paper_orders_created += created
        duplicate_orders_blocked += duplicates
        risk_limit_orders_blocked += risk_blocked
        portfolio_events.extend(events)
        _apply_current_prices(positions, snapshot_entry.get("current_prices", {}))
        settlement_events = _apply_settlements(positions, snapshot_entry.get("settlements", []), snapshot_entry["observed_at"])
        portfolio_events.extend(settlement_events)
        exposure = _exposure_summary(positions)
        max_exposure = max(max_exposure, exposure["open_paper_notional"])
        snapshot_reports.append({
            "snapshot_id": snapshot_id,
            "observed_at": snapshot_entry["observed_at"],
            "snapshot_markets": len(snapshot_fixture["markets"]),
            "adapted_raw_markets": len(raw_fixture["raw_markets"]),
            "adapter_rejections": len(snapshot_adapter_rejections),
            "intake_rejections": len(snapshot_intake_rejections),
            "markets_scored": score_report["markets_scored"],
            "paper_candidates": review_table["group_counts"]["paper_candidate"],
            "watchlist": review_table["group_counts"]["watchlist"],
            "rejected_after_scoring": review_table["group_counts"]["reject"],
            "paper_orders_created": created,
            "duplicate_orders_blocked": duplicates,
            "risk_limit_orders_blocked": risk_blocked,
            "risk_limit_reason_counts": _risk_limit_reason_counts(events),
            "exposure_summary": exposure,
            **SAFETY_FLAGS,
        })

    exposure = _exposure_summary(positions)
    risk_limit_reason_counts = _risk_limit_reason_counts(portfolio_events)
    risk_limit_decisions = _risk_limit_decisions(portfolio_events)
    report = {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-019-LOCAL-SNAPSHOT-SERIES-PAPER-PORTFOLIO-RISK-LIMITS",
        "source_fixture_id": fixture["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "portfolio_risk_limits": portfolio_risk_limits,
        "portfolio_series_summary": {
            "snapshots_processed": len(snapshots),
            "total_snapshot_markets": total_snapshot_markets,
            "adapted_raw_markets": adapted_raw_markets,
            "adapter_rejections": len(adapter_rejections),
            "paper_orders_created": paper_orders_created,
            "duplicate_orders_blocked": duplicate_orders_blocked,
            "risk_limit_orders_blocked": risk_limit_orders_blocked,
            "risk_limit_reason_counts": risk_limit_reason_counts,
            "open_positions": exposure["open_positions"],
            "settled_positions": exposure["settled_positions"],
            "total_paper_notional": exposure["total_paper_notional"],
            "max_exposure": round(max_exposure, 2),
            "realized_paper_pnl": exposure["realized_paper_pnl"],
            "unrealized_paper_pnl": exposure["unrealized_paper_pnl"],
            "bad_entries": bad_entries,
            "safety_flags_locked": False,
        },
        "snapshot_reports": snapshot_reports,
        "adapter_rejections": adapter_rejections,
        "intake_rejections": intake_rejections,
        "scoring_rejections": scoring_rejections,
        "risk_limit_decisions": risk_limit_decisions,
        "portfolio_events": portfolio_events,
        "paper_positions": list(positions.values()),
        "limitations": [
            "Uses a local fixture series of live-shaped snapshots only; no live fetcher, network, or external API is implemented.",
            "Paper orders, duplicate blocking, portfolio risk limits, carry-forward positions, settlements, exposure, and PnL are deterministic local calculations only.",
            "No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.",
        ],
        "review_note": "Offline multi-snapshot paper portfolio replay for manual review only.",
    }
    safety_rows = snapshot_reports + risk_limit_decisions + portfolio_events + list(positions.values())
    report["portfolio_series_summary"]["safety_flags_locked"] = _safety_locked(report) and _all_nested_safety_locked(safety_rows)
    return report


def render_markdown(report):
    summary = report["portfolio_series_summary"]
    risk_limits = report["portfolio_risk_limits"]
    lines = [
        "# PMBOT Local Snapshot Series Paper Portfolio",
        "",
        "Deterministic offline replay of repeated local live-shaped snapshot reviews into a carried paper portfolio.",
        "",
        "## Summary",
        "",
        f"- Snapshots processed: {summary['snapshots_processed']}",
        f"- Total snapshot markets: {summary['total_snapshot_markets']}",
        f"- Adapted raw markets: {summary['adapted_raw_markets']}",
        f"- Adapter rejections: {summary['adapter_rejections']}",
        f"- Paper orders created: {summary['paper_orders_created']}",
        f"- Duplicate orders blocked: {summary['duplicate_orders_blocked']}",
        f"- Risk-limit orders blocked: {summary['risk_limit_orders_blocked']}",
        f"- Open positions: {summary['open_positions']}",
        f"- Settled positions: {summary['settled_positions']}",
        f"- Total paper notional: {summary['total_paper_notional']:.2f}",
        f"- Max exposure: {summary['max_exposure']:.2f}",
        f"- Realized paper PnL: {summary['realized_paper_pnl']:.2f}",
        f"- Unrealized paper PnL: {summary['unrealized_paper_pnl']:.2f}",
        f"- Bad entries: {summary['bad_entries']}",
        f"- Safety flags locked: {str(summary['safety_flags_locked']).lower()}",
        "",
        "## Risk Limits",
        "",
        "| limit | value |",
        "| --- | --- |",
        f"| max_total_paper_exposure | {risk_limits['max_total_paper_exposure']:.2f} |",
        f"| max_asset_paper_exposure | {risk_limits['max_asset_paper_exposure']:.2f} |",
        f"| max_orders_per_snapshot | {risk_limits['max_orders_per_snapshot']} |",
        f"| max_open_positions | {risk_limits['max_open_positions']} |",
        "",
        "## Risk-Limit Reasons",
        "",
        "| reason_code | count |",
        "| --- | --- |",
    ]
    for reason_code in sorted(summary["risk_limit_reason_counts"]):
        lines.append(f"| {reason_code} | {summary['risk_limit_reason_counts'][reason_code]} |")
    lines.extend([
        "",
        "## Risk-Limit Decisions",
        "",
        "| timestamp | market_id | asset | side | decision | reason_codes |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for row in report["risk_limit_decisions"]:
        reason_codes = ", ".join(row["reason_codes"])
        lines.append(f"| {row['timestamp']} | {row['market_id']} | {row['asset']} | {row['side']} | {row['decision']} | {reason_codes} |")
    lines.extend([
        "",
        "## Snapshot Exposure",
        "",
        "| snapshot_id | markets | adapted | candidates | orders | duplicates | risk_blocks | open | settled | exposure | realized_pnl | unrealized_pnl |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in report["snapshot_reports"]:
        exposure = row["exposure_summary"]
        lines.append(
            f"| {row['snapshot_id']} | {row['snapshot_markets']} | {row['adapted_raw_markets']} | "
            f"{row['paper_candidates']} | {row['paper_orders_created']} | {row['duplicate_orders_blocked']} | "
            f"{row['risk_limit_orders_blocked']} | "
            f"{exposure['open_positions']} | {exposure['settled_positions']} | {exposure['open_paper_notional']:.2f} | "
            f"{exposure['realized_paper_pnl']:.2f} | {exposure['unrealized_paper_pnl']:.2f} |"
        )
    lines.extend(["", "## Portfolio Events", "", "| event_type | timestamp | market_id | side | reason |", "| --- | --- | --- | --- | --- |"])
    for event in report["portfolio_events"]:
        lines.append(f"| {event['event_type']} | {event['timestamp']} | {event['market_id']} | {event['side']} | {event.get('reason', '')} |")
    lines.extend(["", "## Paper Positions", "", "| market_id | side | status | fill_price | shares | notional | paper_pnl |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for position in report["paper_positions"]:
        lines.append(
            f"| {position['market_id']} | {position['side']} | {position['status']} | {position['fill_price']:.4f} | "
            f"{position['shares']:.4f} | {position['paper_notional']:.2f} | {position['paper_pnl']:.2f} |"
        )
    lines.extend(["", "## Rejections", "", "| stage | snapshot_id | market_id | reason_code | reason |", "| --- | --- | --- | --- | --- |"])
    for row in report["adapter_rejections"]:
        lines.append(f"| adapter | {row['snapshot_id']} | {row['market_id']} | {row['reason_code']} | {row['reason']} |")
    for row in report["intake_rejections"]:
        lines.append(f"| intake | {row['snapshot_id']} | {row['market_id']} | {row['reason_code']} | {row['reason']} |")
    for row in report["scoring_rejections"]:
        lines.append(f"| scoring | {row['snapshot_id']} | {row['market_id']} | reject | {row['short_reason']} |")
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; live_fetcher_implemented=false; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_local_snapshot_series_paper_portfolio(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
