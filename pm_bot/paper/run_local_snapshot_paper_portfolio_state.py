import argparse
import importlib.util
import json
import sys
from pathlib import Path


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Process one local snapshot against a saved offline paper portfolio state.")
    parser.add_argument("--snapshot", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--out-state", default=None)
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _positions_by_key(portfolio, state):
    positions = {}
    for row in state.get("paper_positions", []):
        positions[portfolio._position_key(row["market_id"], row["side"])] = dict(row)
    return positions


def _state_summary(state):
    exposure = state["exposure_summary"]
    return {
        "processed_snapshots": len(state.get("processed_snapshot_ids", [])),
        "processed_market_side_keys": len(state.get("processed_market_side_keys", [])),
        "open_positions": exposure["open_positions"],
        "settled_positions": exposure["settled_positions"],
        "total_paper_notional": exposure["total_paper_notional"],
        "open_paper_notional": exposure["open_paper_notional"],
        "realized_paper_pnl": exposure["realized_paper_pnl"],
        "unrealized_paper_pnl": exposure["unrealized_paper_pnl"],
    }


def _select_snapshot(snapshot_payload, state):
    if "snapshot" in snapshot_payload:
        return snapshot_payload
    snapshots = sorted(snapshot_payload["snapshots"], key=lambda row: row["observed_at"])
    processed = set(state.get("processed_snapshot_ids", []))
    for snapshot in snapshots:
        if snapshot["snapshot_id"] not in processed:
            return snapshot
    return snapshots[-1]


def _processed_keys(portfolio, positions):
    return sorted(portfolio._position_key(row["market_id"], row["side"]) for row in positions.values())


def _build_state(portfolio, prior_state, positions, snapshot_id):
    processed_snapshots = list(prior_state.get("processed_snapshot_ids", []))
    if snapshot_id not in processed_snapshots:
        processed_snapshots.append(snapshot_id)
    exposure = portfolio._exposure_summary(positions)
    return {
        "schema_version": "v1",
        "state_id": "paper_portfolio_state_after_snapshot_v1",
        "fixture_only": True,
        "paper_only": True,
        "processed_snapshot_ids": processed_snapshots,
        "processed_market_side_keys": _processed_keys(portfolio, positions),
        "paper_positions": list(positions.values()),
        "exposure_summary": exposure,
        **portfolio.SAFETY_FLAGS,
    }


def _reason_counts(events):
    counts = {}
    for event in events:
        if event["event_type"] != "risk_limit_paper_order_blocked":
            continue
        for reason_code in event["reason_codes"]:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return counts


def _safety_locked(portfolio, report, rows):
    return all(report.get(key) == value for key, value in portfolio.SAFETY_FLAGS.items()) and all(
        all(row.get(key) == value for key, value in portfolio.SAFETY_FLAGS.items()) for row in rows
    )


def _build_order_plan(root, portfolio, snapshot_entry):
    scoring_dir = root / "pm_bot" / "scoring"
    adapter = _load_module(scoring_dir / "adapt_live_shaped_crypto_snapshot.py", "pmbot_state_adapter")
    intake = _load_module(scoring_dir / "crypto_numeric_market_intake.py", "pmbot_state_intake")
    scorer = _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_state_scorer")
    review = _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_state_review")
    planner = _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_state_planner")
    raw_fixture, adapter_rejections = portfolio._adapt_snapshot_fixture(adapter, snapshot_entry["snapshot"], snapshot_entry["snapshot_id"])
    intake_report = intake.build_intake_report(raw_fixture)
    score_report = scorer.score_fixture(intake_report["normalized_scorer_fixture"])
    review_table = review.build_review_table(score_report)
    order_plan = planner.build_paper_order_plan(review_table)
    return order_plan, adapter_rejections, intake_report["rejections"], portfolio._rows_by_decision(review_table, "reject"), score_report, review_table


def build_local_snapshot_paper_portfolio_state(root: Path, snapshot_path=None, state_path=None, out_state_path=None):
    paper_dir = root / "pm_bot" / "paper"
    portfolio = _load_module(paper_dir / "run_local_snapshot_series_paper_portfolio.py", "pmbot_state_portfolio")
    snapshot_source = Path(snapshot_path) if snapshot_path else paper_dir / "local_snapshot_series_fixture.v1.json"
    state_source = Path(state_path) if state_path else paper_dir / "paper_portfolio_state.v1.json"
    snapshot_payload = _load_json(snapshot_source)
    state = _load_json(state_source)
    snapshot_entry = _select_snapshot(snapshot_payload, state)
    risk_limits = _load_json(paper_dir / "portfolio_risk_limits.v1.json")

    positions = _positions_by_key(portfolio, state)
    input_summary = _state_summary(state)
    order_plan, adapter_rejections, intake_rejections, scoring_rejections, score_report, review_table = _build_order_plan(root, portfolio, snapshot_entry)
    created, duplicates, risk_blocked, events = portfolio._process_order_plan(order_plan, positions, snapshot_entry, risk_limits)
    portfolio._apply_current_prices(positions, snapshot_entry.get("current_prices", {}))
    settlement_events = portfolio._apply_settlements(positions, snapshot_entry.get("settlements", []), snapshot_entry["observed_at"])
    events.extend(settlement_events)
    output_state = _build_state(portfolio, state, positions, snapshot_entry["snapshot_id"])
    out_state_written = False
    if out_state_path:
        _write_json(Path(out_state_path), output_state)
        out_state_written = True

    output_summary = _state_summary(output_state)
    report = {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-021-LOCAL-PAPER-PORTFOLIO-STATE",
        "deterministic": True,
        **portfolio.SAFETY_FLAGS,
        "input_snapshot": {
            "snapshot_id": snapshot_entry["snapshot_id"],
            "observed_at": snapshot_entry["observed_at"],
            "source_path": str(snapshot_source),
        },
        "input_state": {
            "state_id": state.get("state_id"),
            "source_path": str(state_source),
            "summary": input_summary,
        },
        "portfolio_risk_limits": risk_limits,
        "run_summary": {
            "new_paper_orders_created": created,
            "duplicate_orders_blocked": duplicates,
            "risk_limit_orders_blocked": risk_blocked,
            "risk_limit_reason_counts": _reason_counts(events),
            "open_positions_after_run": output_summary["open_positions"],
            "settled_positions_after_run": output_summary["settled_positions"],
            "exposure_after_run": output_summary["open_paper_notional"],
            "total_paper_notional_after_run": output_summary["total_paper_notional"],
            "realized_paper_pnl_after_run": output_summary["realized_paper_pnl"],
            "unrealized_paper_pnl_after_run": output_summary["unrealized_paper_pnl"],
            "bad_entries": 0,
            "out_state_path": str(Path(out_state_path)) if out_state_path else None,
            "out_state_written": out_state_written,
            "safety_flags_locked": False,
        },
        "pipeline_summary": {
            "adapter_rejections": len(adapter_rejections),
            "intake_rejections": len(intake_rejections),
            "scoring_rejections": len(scoring_rejections),
            "markets_scored": score_report["markets_scored"],
            "paper_candidates": review_table["group_counts"]["paper_candidate"],
            "watchlist": review_table["group_counts"]["watchlist"],
            "rejected_after_scoring": review_table["group_counts"]["reject"],
        },
        "portfolio_events": events,
        "output_state": output_state,
        "limitations": [
            "Uses deterministic local snapshot and paper state fixtures only; no live fetcher, network, external API, credentials, wallet access, real orders, or live trading is included.",
            "Default run is read-only and writes state only when --out-state is provided.",
            "No runtime integration, command-routing changes, prompt automation, broad refactor, or new validation layer is included.",
        ],
        "review_note": "Offline incremental paper portfolio state processing for manual paper review only.",
    }
    report["run_summary"]["safety_flags_locked"] = _safety_locked(
        portfolio,
        report,
        events + output_state["paper_positions"],
    )
    return report


def render_markdown(report):
    summary = report["run_summary"]
    input_summary = report["input_state"]["summary"]
    lines = [
        "# PMBOT Local Snapshot Paper Portfolio State",
        "",
        "Deterministic offline processing of one local snapshot against a saved paper portfolio state.",
        "",
        "## Input",
        "",
        f"- Snapshot: {report['input_snapshot']['snapshot_id']}",
        f"- Observed at: {report['input_snapshot']['observed_at']}",
        f"- Input open positions: {input_summary['open_positions']}",
        f"- Input settled positions: {input_summary['settled_positions']}",
        f"- Input exposure: {input_summary['open_paper_notional']:.2f}",
        f"- Input realized paper PnL: {input_summary['realized_paper_pnl']:.2f}",
        "",
        "## Summary",
        "",
        f"- New paper orders created: {summary['new_paper_orders_created']}",
        f"- Duplicate orders blocked: {summary['duplicate_orders_blocked']}",
        f"- Risk-limit orders blocked: {summary['risk_limit_orders_blocked']}",
        f"- Open positions after run: {summary['open_positions_after_run']}",
        f"- Settled positions after run: {summary['settled_positions_after_run']}",
        f"- Exposure after run: {summary['exposure_after_run']:.2f}",
        f"- Realized paper PnL after run: {summary['realized_paper_pnl_after_run']:.2f}",
        f"- Output state path: {summary['out_state_path'] or ''}",
        f"- Output state written: {str(summary['out_state_written']).lower()}",
        f"- Safety flags locked: {str(summary['safety_flags_locked']).lower()}",
        "",
        "## Events",
        "",
        "| event_type | timestamp | market_id | side | reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for event in report["portfolio_events"]:
        lines.append(f"| {event['event_type']} | {event['timestamp']} | {event['market_id']} | {event['side']} | {event.get('reason', '')} |")
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; live_fetcher_implemented=false; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_local_snapshot_paper_portfolio_state(root, args.snapshot, args.state, args.out_state)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
