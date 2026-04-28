import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Process a local inbox of snapshot JSON files against an offline paper portfolio state.")
    parser.add_argument("--inbox", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--out-state", default=None)
    parser.add_argument("--out-run-ledger", default=None)
    parser.add_argument("--run-id", default=None)
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


def _file_sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_from_payload(payload):
    if "snapshot" in payload:
        return payload
    snapshots = payload.get("snapshots", [])
    if len(snapshots) != 1:
        raise ValueError("Inbox snapshot files must contain one snapshot entry.")
    return snapshots[0]


def _discover_snapshots(inbox: Path):
    rows = []
    for path in sorted(inbox.glob("*.json"), key=lambda item: item.name):
        snapshot = _snapshot_from_payload(_load_json(path))
        rows.append({
            "file_name": path.name,
            "path": str(path),
            "sha256": _file_sha256(path),
            "snapshot_id": snapshot["snapshot_id"],
            "observed_at": snapshot["observed_at"],
            "snapshot": snapshot,
        })
    rows.sort(key=lambda row: (row["observed_at"], row["snapshot_id"], row["file_name"]))
    return rows


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


def _public_discovered(rows):
    return [
        {
            "file_name": row["file_name"],
            "path": row["path"],
            "sha256": row["sha256"],
            "snapshot_id": row["snapshot_id"],
            "observed_at": row["observed_at"],
        }
        for row in rows
    ]


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


def _build_run_ledger(report, run_id, out_state_path):
    before = report["input_state"]["summary"]
    after = {
        "processed_snapshots": len(report["output_state"].get("processed_snapshot_ids", [])),
        "processed_market_side_keys": len(report["output_state"].get("processed_market_side_keys", [])),
        "open_positions": report["run_summary"]["open_positions_after_run"],
        "settled_positions": report["run_summary"]["settled_positions_after_run"],
        "total_paper_notional": report["run_summary"]["total_paper_notional_after_run"],
        "open_paper_notional": report["run_summary"]["exposure_after_run"],
        "realized_paper_pnl": report["run_summary"]["realized_paper_pnl_after_run"],
        "unrealized_paper_pnl": report["run_summary"]["unrealized_paper_pnl_after_run"],
    }
    return {
        "schema_version": "v1",
        "task_id": "PMBOT-BRAIN-023-LOCAL-INBOX-RUN-LEDGER",
        "workflow": "local_snapshot_inbox_paper_portfolio",
        "run_id": run_id,
        "deterministic": True,
        "input_inbox_path": report["inbox"]["path"],
        "input_state_path": report["input_state"]["source_path"],
        "output_state_path": str(Path(out_state_path)) if out_state_path else None,
        "snapshot_files_discovered": report["inbox"]["snapshot_files_discovered"],
        "snapshots_skipped_already_processed": report["snapshots_skipped_already_processed"],
        "snapshots_processed": report["snapshots_processed"],
        "before_state_summary": before,
        "after_state_summary": after,
        "new_paper_orders_created": report["run_summary"]["new_paper_orders_created"],
        "duplicate_orders_blocked": report["run_summary"]["duplicate_orders_blocked"],
        "risk_limit_orders_blocked": report["run_summary"]["risk_limit_orders_blocked"],
        "reason_counts": report["run_summary"]["risk_limit_reason_counts"],
        "realized_paper_pnl_delta": round(after["realized_paper_pnl"] - before["realized_paper_pnl"], 2),
        "final_realized_paper_pnl": after["realized_paper_pnl"],
        "safety_flags_locked": report["run_summary"]["safety_flags_locked"],
        "offline_only": report["offline_only"],
        "paper_only": report["paper_only"],
        "live_fetcher_implemented": report["live_fetcher_implemented"],
        "execution_allowed": report["execution_allowed"],
        "trading_allowed": report["trading_allowed"],
        "real_order_created": report["real_order_created"],
        "wallet_used": report["wallet_used"],
        "api_used": report["api_used"],
        "network_used": report["network_used"],
    }


def build_local_snapshot_inbox_paper_portfolio(
    root: Path,
    inbox_path=None,
    state_path=None,
    out_state_path=None,
    out_run_ledger_path=None,
    run_id=None,
):
    paper_dir = root / "pm_bot" / "paper"
    state_runner = _load_module(paper_dir / "run_local_snapshot_paper_portfolio_state.py", "pmbot_inbox_state")
    portfolio = _load_module(paper_dir / "run_local_snapshot_series_paper_portfolio.py", "pmbot_inbox_portfolio")

    inbox = Path(inbox_path) if inbox_path else paper_dir / "local_snapshot_inbox"
    state_source = Path(state_path) if state_path else paper_dir / "paper_portfolio_state.v1.json"
    state = _load_json(state_source)
    risk_limits = _load_json(paper_dir / "portfolio_risk_limits.v1.json")
    discovered = _discover_snapshots(inbox)
    processed_ids = set(state.get("processed_snapshot_ids", []))
    positions = state_runner._positions_by_key(portfolio, state)
    input_summary = _state_summary(state)
    resolved_run_id = run_id or "local-snapshot-inbox-paper-portfolio-v1"

    skipped = []
    processed = []
    snapshot_reports = []
    portfolio_events = []
    total_snapshot_markets = 0
    adapted_raw_markets = 0
    adapter_rejections_count = 0
    intake_rejections_count = 0
    scoring_rejections_count = 0
    new_paper_orders_created = 0
    duplicate_orders_blocked = 0
    risk_limit_orders_blocked = 0

    for row in discovered:
        snapshot_entry = row["snapshot"]
        snapshot_id = snapshot_entry["snapshot_id"]
        if snapshot_id in processed_ids:
            skipped.append({
            "file_name": row["file_name"],
            "sha256": row["sha256"],
            "snapshot_id": snapshot_id,
            "observed_at": snapshot_entry["observed_at"],
            "reason": "already_processed_in_state",
        })
            continue

        snapshot_fixture = snapshot_entry["snapshot"]
        total_snapshot_markets += len(snapshot_fixture["markets"])
        order_plan, adapter_rejections, intake_rejections, scoring_rejections, score_report, review_table = state_runner._build_order_plan(
            root,
            portfolio,
            snapshot_entry,
        )
        created, duplicates, risk_blocked, events = portfolio._process_order_plan(order_plan, positions, snapshot_entry, risk_limits)
        portfolio._apply_current_prices(positions, snapshot_entry.get("current_prices", {}))
        settlement_events = portfolio._apply_settlements(positions, snapshot_entry.get("settlements", []), snapshot_entry["observed_at"])
        events.extend(settlement_events)
        portfolio_events.extend(events)

        output_state = state_runner._build_state(portfolio, state, positions, snapshot_id)
        state = output_state
        processed_ids = set(state.get("processed_snapshot_ids", []))
        exposure = portfolio._exposure_summary(positions)

        processed.append({
            "file_name": row["file_name"],
            "sha256": row["sha256"],
            "snapshot_id": snapshot_id,
            "observed_at": snapshot_entry["observed_at"],
        })
        adapted_raw_markets += len(snapshot_fixture["markets"]) - len(adapter_rejections)
        adapter_rejections_count += len(adapter_rejections)
        intake_rejections_count += len(intake_rejections)
        scoring_rejections_count += len(scoring_rejections)
        new_paper_orders_created += created
        duplicate_orders_blocked += duplicates
        risk_limit_orders_blocked += risk_blocked
        snapshot_reports.append({
            "file_name": row["file_name"],
            "snapshot_id": snapshot_id,
            "observed_at": snapshot_entry["observed_at"],
            "snapshot_markets": len(snapshot_fixture["markets"]),
            "adapted_raw_markets": len(snapshot_fixture["markets"]) - len(adapter_rejections),
            "adapter_rejections": len(adapter_rejections),
            "intake_rejections": len(intake_rejections),
            "markets_scored": score_report["markets_scored"],
            "paper_candidates": review_table["group_counts"]["paper_candidate"],
            "watchlist": review_table["group_counts"]["watchlist"],
            "rejected_after_scoring": review_table["group_counts"]["reject"],
            "paper_orders_created": created,
            "duplicate_orders_blocked": duplicates,
            "risk_limit_orders_blocked": risk_blocked,
            "exposure_summary": exposure,
            **portfolio.SAFETY_FLAGS,
        })

    processed_snapshot_ids = state.get("processed_snapshot_ids", [])
    if processed_snapshot_ids:
        output_state = state_runner._build_state(portfolio, state, positions, processed_snapshot_ids[-1])
    else:
        output_state = dict(state)
        output_state["paper_positions"] = list(positions.values())
        output_state["exposure_summary"] = portfolio._exposure_summary(positions)
    out_state_written = False
    if out_state_path:
        _write_json(Path(out_state_path), output_state)
        out_state_written = True

    output_summary = _state_summary(output_state)
    report = {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-022-LOCAL-SNAPSHOT-INBOX-PROCESSOR",
        "deterministic": True,
        **portfolio.SAFETY_FLAGS,
        "inbox": {
            "path": str(inbox),
            "snapshot_files_discovered": _public_discovered(discovered),
        },
        "input_state": {
            "state_id": _load_json(state_source).get("state_id"),
            "source_path": str(state_source),
            "summary": input_summary,
        },
        "portfolio_risk_limits": risk_limits,
        "run_summary": {
            "snapshot_files_discovered": len(discovered),
            "snapshots_skipped_already_processed": len(skipped),
            "snapshots_processed": len(processed),
            "new_paper_orders_created": new_paper_orders_created,
            "duplicate_orders_blocked": duplicate_orders_blocked,
            "risk_limit_orders_blocked": risk_limit_orders_blocked,
            "risk_limit_reason_counts": _reason_counts(portfolio_events),
            "open_positions_after_run": output_summary["open_positions"],
            "settled_positions_after_run": output_summary["settled_positions"],
            "exposure_after_run": output_summary["open_paper_notional"],
            "total_paper_notional_after_run": output_summary["total_paper_notional"],
            "realized_paper_pnl_after_run": output_summary["realized_paper_pnl"],
            "unrealized_paper_pnl_after_run": output_summary["unrealized_paper_pnl"],
            "bad_entries": 0,
            "out_state_path": str(Path(out_state_path)) if out_state_path else None,
            "out_state_written": out_state_written,
            "run_id": resolved_run_id,
            "out_run_ledger_path": str(Path(out_run_ledger_path)) if out_run_ledger_path else None,
            "out_run_ledger_written": False,
            "safety_flags_locked": False,
        },
        "pipeline_summary": {
            "total_snapshot_markets": total_snapshot_markets,
            "adapted_raw_markets": adapted_raw_markets,
            "adapter_rejections": adapter_rejections_count,
            "intake_rejections": intake_rejections_count,
            "scoring_rejections": scoring_rejections_count,
        },
        "snapshots_skipped_already_processed": skipped,
        "snapshots_processed": processed,
        "snapshot_reports": snapshot_reports,
        "portfolio_events": portfolio_events,
        "open_positions_after_run": [row for row in output_state["paper_positions"] if not row["settled"]],
        "settled_positions_after_run": [row for row in output_state["paper_positions"] if row["settled"]],
        "output_state": output_state,
        "limitations": [
            "Uses deterministic local snapshot inbox files and paper state fixtures only; no live fetcher, network, external API, credentials, wallet access, real orders, or live trading is included.",
            "Default run is read-only and writes state only when --out-state is provided.",
            "No runtime integration, command-routing changes, prompt automation, broad refactor, or new validation layer is included.",
        ],
        "review_note": "Offline local snapshot inbox processing for manual paper portfolio review only.",
    }
    safety_rows = snapshot_reports + portfolio_events + output_state["paper_positions"]
    report["run_summary"]["safety_flags_locked"] = _safety_locked(portfolio, report, safety_rows)
    run_ledger = _build_run_ledger(report, resolved_run_id, out_state_path)
    if out_run_ledger_path:
        _write_json(Path(out_run_ledger_path), run_ledger)
        report["run_summary"]["out_run_ledger_written"] = True
    report["run_ledger"] = {
        "run_id": resolved_run_id,
        "out_run_ledger_path": str(Path(out_run_ledger_path)) if out_run_ledger_path else None,
        "out_run_ledger_written": bool(out_run_ledger_path),
        "realized_paper_pnl_delta": run_ledger["realized_paper_pnl_delta"],
        "final_realized_paper_pnl": run_ledger["final_realized_paper_pnl"],
    }
    return report


def render_markdown(report):
    summary = report["run_summary"]
    input_summary = report["input_state"]["summary"]
    lines = [
        "# PMBOT Local Snapshot Inbox Paper Portfolio",
        "",
        "Deterministic offline processing of local snapshot inbox files against a saved paper portfolio state.",
        "",
        "## Input",
        "",
        f"- Inbox path: {report['inbox']['path']}",
        f"- Input state path: {report['input_state']['source_path']}",
        f"- Input processed snapshots: {input_summary['processed_snapshots']}",
        f"- Input open positions: {input_summary['open_positions']}",
        f"- Input settled positions: {input_summary['settled_positions']}",
        f"- Input exposure: {input_summary['open_paper_notional']:.2f}",
        f"- Input realized paper PnL: {input_summary['realized_paper_pnl']:.2f}",
        "",
        "## Summary",
        "",
        f"- Snapshot files discovered: {summary['snapshot_files_discovered']}",
        f"- Snapshots skipped already processed: {summary['snapshots_skipped_already_processed']}",
        f"- Snapshots processed: {summary['snapshots_processed']}",
        f"- New paper orders created: {summary['new_paper_orders_created']}",
        f"- Duplicate orders blocked: {summary['duplicate_orders_blocked']}",
        f"- Risk-limit orders blocked: {summary['risk_limit_orders_blocked']}",
        f"- Open positions after run: {summary['open_positions_after_run']}",
        f"- Settled positions after run: {summary['settled_positions_after_run']}",
        f"- Exposure after run: {summary['exposure_after_run']:.2f}",
        f"- Realized paper PnL after run: {summary['realized_paper_pnl_after_run']:.2f}",
        f"- Output state path: {summary['out_state_path'] or ''}",
        f"- Output state written: {str(summary['out_state_written']).lower()}",
        f"- Run ledger path: {summary['out_run_ledger_path'] or ''}",
        f"- Run ledger written: {str(summary['out_run_ledger_written']).lower()}",
        f"- Safety flags locked: {str(summary['safety_flags_locked']).lower()}",
        "",
        "## Snapshot Files",
        "",
        "| file | snapshot_id | observed_at | status |",
        "| --- | --- | --- | --- |",
    ]
    skipped_ids = {row["snapshot_id"] for row in report["snapshots_skipped_already_processed"]}
    processed_ids = {row["snapshot_id"] for row in report["snapshots_processed"]}
    for row in report["inbox"]["snapshot_files_discovered"]:
        status = "processed" if row["snapshot_id"] in processed_ids else "skipped" if row["snapshot_id"] in skipped_ids else "unprocessed"
        lines.append(f"| {row['file_name']} | {row['snapshot_id']} | {row['observed_at']} | {status} |")
    lines.extend([
        "",
        "## Snapshot Runs",
        "",
        "| snapshot_id | orders | duplicates | risk_blocks | open | settled | exposure | realized_pnl |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in report["snapshot_reports"]:
        exposure = row["exposure_summary"]
        lines.append(
            f"| {row['snapshot_id']} | {row['paper_orders_created']} | {row['duplicate_orders_blocked']} | "
            f"{row['risk_limit_orders_blocked']} | {exposure['open_positions']} | {exposure['settled_positions']} | "
            f"{exposure['open_paper_notional']:.2f} | {exposure['realized_paper_pnl']:.2f} |"
        )
    lines.extend(["", "## Portfolio Events", "", "| event_type | timestamp | market_id | side | reason |", "| --- | --- | --- | --- | --- |"])
    for event in report["portfolio_events"]:
        lines.append(f"| {event['event_type']} | {event['timestamp']} | {event['market_id']} | {event['side']} | {event.get('reason', '')} |")
    if summary["out_run_ledger_written"]:
        lines.extend([
            "",
            "## Run Ledger",
            "",
            f"- Run ID: {summary['run_id']}",
            f"- Path: {summary['out_run_ledger_path']}",
            f"- Realized paper PnL delta: {report['run_ledger']['realized_paper_pnl_delta']:.2f}",
            f"- Final realized paper PnL: {report['run_ledger']['final_realized_paper_pnl']:.2f}",
        ])
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; live_fetcher_implemented=false; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_local_snapshot_inbox_paper_portfolio(
        root,
        args.inbox,
        args.state,
        args.out_state,
        args.out_run_ledger,
        args.run_id,
    )
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
