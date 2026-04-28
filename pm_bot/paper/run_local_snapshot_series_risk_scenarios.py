import argparse
import importlib.util
import json
import sys
from pathlib import Path


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Replay local snapshot series portfolio risk scenarios.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_portfolio_runner(root: Path):
    path = root / "pm_bot" / "paper" / "run_local_snapshot_series_paper_portfolio.py"
    spec = importlib.util.spec_from_file_location("pmbot_portfolio_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _merge_counts(target, source):
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def _risk_reason_counts(events):
    counts = {}
    for event in events:
        if event["event_type"] != "risk_limit_paper_order_blocked":
            continue
        for reason_code in event["reason_codes"]:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return counts


def _nested_safety_locked(portfolio, rows):
    return all(all(row.get(key) == value for key, value in portfolio.SAFETY_FLAGS.items()) for row in rows)


def _process_scenario(portfolio, scenario):
    positions = {}
    portfolio_events = []
    snapshot_reports = []
    paper_orders_created = 0
    duplicate_orders_blocked = 0
    risk_limit_orders_blocked = 0
    max_exposure = 0.0
    bad_entries = 0

    for snapshot in sorted(scenario["snapshots"], key=lambda row: row["observed_at"]):
        order_plan = {"entries": snapshot["entries"]}
        created, duplicates, risk_blocked, events = portfolio._process_order_plan(
            order_plan,
            positions,
            snapshot,
            scenario["risk_limits"],
        )
        paper_orders_created += created
        duplicate_orders_blocked += duplicates
        risk_limit_orders_blocked += risk_blocked
        portfolio_events.extend(events)
        portfolio._apply_current_prices(positions, snapshot.get("current_prices", {}))
        settlement_events = portfolio._apply_settlements(positions, snapshot.get("settlements", []), snapshot["observed_at"])
        portfolio_events.extend(settlement_events)
        exposure = portfolio._exposure_summary(positions)
        max_exposure = max(max_exposure, exposure["open_paper_notional"])
        snapshot_reports.append({
            "snapshot_id": snapshot["snapshot_id"],
            "observed_at": snapshot["observed_at"],
            "plan_entries": len(snapshot["entries"]),
            "paper_orders_created": created,
            "duplicate_orders_blocked": duplicates,
            "risk_limit_orders_blocked": risk_blocked,
            "exposure_summary": exposure,
            **portfolio.SAFETY_FLAGS,
        })

    exposure = portfolio._exposure_summary(positions)
    scenario_summary = {
        "snapshots_processed": len(scenario["snapshots"]),
        "paper_orders_created": paper_orders_created,
        "duplicate_orders_blocked": duplicate_orders_blocked,
        "risk_limit_orders_blocked": risk_limit_orders_blocked,
        "risk_limit_reason_counts": _risk_reason_counts(portfolio_events),
        "open_positions": exposure["open_positions"],
        "settled_positions": exposure["settled_positions"],
        "total_paper_notional": exposure["total_paper_notional"],
        "max_exposure": round(max_exposure, 2),
        "realized_paper_pnl": exposure["realized_paper_pnl"],
        "unrealized_paper_pnl": exposure["unrealized_paper_pnl"],
        "bad_entries": bad_entries,
        "safety_flags_locked": False,
    }
    safety_rows = snapshot_reports + portfolio_events + list(positions.values())
    scenario_summary["safety_flags_locked"] = _nested_safety_locked(portfolio, safety_rows)
    return {
        "scenario_id": scenario["scenario_id"],
        "description": scenario["description"],
        "risk_limits": scenario["risk_limits"],
        "scenario_summary": scenario_summary,
        "snapshot_reports": snapshot_reports,
        "portfolio_events": portfolio_events,
        "paper_positions": list(positions.values()),
        **portfolio.SAFETY_FLAGS,
    }


def build_local_snapshot_series_risk_scenarios(root: Path):
    paper_dir = root / "pm_bot" / "paper"
    portfolio = _load_portfolio_runner(root)
    fixture = _load_json(paper_dir / "local_snapshot_series_risk_scenarios.v1.json")
    scenario_reports = [_process_scenario(portfolio, scenario) for scenario in fixture["scenarios"]]
    reason_counts = {}
    for report in scenario_reports:
        _merge_counts(reason_counts, report["scenario_summary"]["risk_limit_reason_counts"])
    summary = {
        "scenario_count": len(scenario_reports),
        "paper_orders_created": sum(row["scenario_summary"]["paper_orders_created"] for row in scenario_reports),
        "duplicate_orders_blocked": sum(row["scenario_summary"]["duplicate_orders_blocked"] for row in scenario_reports),
        "risk_limit_orders_blocked": sum(row["scenario_summary"]["risk_limit_orders_blocked"] for row in scenario_reports),
        "risk_limit_reason_counts": reason_counts,
        "realized_paper_pnl": round(sum(row["scenario_summary"]["realized_paper_pnl"] for row in scenario_reports), 2),
        "bad_entries": sum(row["scenario_summary"]["bad_entries"] for row in scenario_reports),
        "safety_flags_locked": all(row["scenario_summary"]["safety_flags_locked"] for row in scenario_reports),
    }
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-020-LOCAL-SNAPSHOT-SERIES-RISK-SCENARIOS",
        "source_fixture_id": fixture["fixture_id"],
        "deterministic": True,
        **portfolio.SAFETY_FLAGS,
        "scenario_suite_summary": summary,
        "scenario_reports": scenario_reports,
        "limitations": [
            "Uses local fixture scenario series only; no live fetcher, network, external API, credentials, wallet access, real orders, or live trading is included.",
            "Scenario entries are deterministic paper plan artifacts replayed through the same local portfolio duplicate, risk-limit, fill, carry-forward, settlement, exposure, and PnL behavior.",
            "No runtime integration, command-routing changes, prompt automation, broad refactor, or new validation layer is included.",
        ],
        "review_note": "Offline paper portfolio risk scenario coverage for deterministic local review only.",
    }


def render_markdown(report):
    summary = report["scenario_suite_summary"]
    lines = [
        "# PMBOT Local Snapshot Series Portfolio Risk Scenarios",
        "",
        "Deterministic offline replay of local paper portfolio risk-limit scenarios.",
        "",
        "## Summary",
        "",
        f"- Scenario count: {summary['scenario_count']}",
        f"- Paper orders created: {summary['paper_orders_created']}",
        f"- Duplicate orders blocked: {summary['duplicate_orders_blocked']}",
        f"- Risk-limit orders blocked: {summary['risk_limit_orders_blocked']}",
        f"- Realized paper PnL: {summary['realized_paper_pnl']:.2f}",
        f"- Bad entries: {summary['bad_entries']}",
        f"- Safety flags locked: {str(summary['safety_flags_locked']).lower()}",
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
        "## Scenarios",
        "",
        "| scenario_id | orders | duplicates | risk_blocks | realized_pnl | bad_entries | reason_counts |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    for report_row in report["scenario_reports"]:
        row = report_row["scenario_summary"]
        reason_counts = ", ".join(f"{key}={value}" for key, value in sorted(row["risk_limit_reason_counts"].items()))
        lines.append(
            f"| {report_row['scenario_id']} | {row['paper_orders_created']} | {row['duplicate_orders_blocked']} | "
            f"{row['risk_limit_orders_blocked']} | {row['realized_paper_pnl']:.2f} | {row['bad_entries']} | {reason_counts} |"
        )
    lines.extend(["", "## Portfolio Events", "", "| scenario_id | event_type | timestamp | market_id | side | reason |", "| --- | --- | --- | --- | --- | --- |"])
    for report_row in report["scenario_reports"]:
        for event in report_row["portfolio_events"]:
            lines.append(
                f"| {report_row['scenario_id']} | {event['event_type']} | {event['timestamp']} | "
                f"{event['market_id']} | {event['side']} | {event.get('reason', '')} |"
            )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; live_fetcher_implemented=false; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_local_snapshot_series_risk_scenarios(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
