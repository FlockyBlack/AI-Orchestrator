import argparse
import importlib.util
import json
import sys
from pathlib import Path


SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "live_fetcher_implemented": False,
    "network_used": False,
    "api_used": False,
    "credentials_used": False,
    "wallet_used": False,
    "real_order_created": False,
    "trading_allowed": False,
}


class SnapshotInputError(ValueError):
    pass


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
    parser = argparse.ArgumentParser(description="Run live-shaped snapshot adapter through the offline paper lifecycle.")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--snapshot", help="Local live-shaped snapshot JSON file. Defaults to the bundled fixture.")
    return parser.parse_args(argv[1:])


def _rows_by_decision(review_table, decision):
    return [row for row in review_table["rows"] if row["decision"] == decision]


def _canonical_market_id(market_id):
    if market_id.startswith("live_"):
        return "crypto_numeric_" + market_id[5:]
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
            execution = {
                "market_id": source_id,
                "observed_yes_price": entry.get("limit_price", 1.0),
                "current_yes_price": entry.get("limit_price", 0.0),
                "settled": False,
            }
        aligned_row = dict(execution)
        aligned_row["market_id"] = source_id
        aligned_rows.append(aligned_row)
    aligned["market_executions"] = aligned_rows
    return aligned


def _validated_snapshot_fixture(path: Path):
    if not path.exists():
        raise SnapshotInputError(f"--snapshot path does not exist: {path}")
    if not path.is_file():
        raise SnapshotInputError(f"--snapshot path is not a file: {path}")
    try:
        payload = _load_json(path)
    except json.JSONDecodeError as exc:
        raise SnapshotInputError(f"--snapshot file is not valid JSON: {path}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise SnapshotInputError("--snapshot file must contain a JSON object.")
    markets = payload.get("markets")
    if not isinstance(markets, list):
        raise SnapshotInputError("--snapshot file must contain a markets list.")
    for index, market in enumerate(markets):
        if not isinstance(market, dict):
            raise SnapshotInputError(f"--snapshot markets[{index}] must be a JSON object.")
    return payload


def _build_adapter_report_from_fixture(adapter, fixture):
    adapted = []
    rejections = []
    for snapshot in fixture["markets"]:
        raw_record, rejection = adapter._adapt_snapshot(snapshot)
        if rejection is not None:
            rejections.append(rejection)
        else:
            adapted.append(raw_record)
    raw_fixture = {
        "schema_version": "v1",
        "fixture_id": "crypto_numeric_live_shaped_adapted_raw_markets_v1",
        "fixture_only": True,
        "paper_only": True,
        "raw_markets": adapted,
    }
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-015-LIVE-SHAPED-MARKET-SNAPSHOT-ADAPTER",
        "source_fixture_id": fixture.get("fixture_id", "local_live_shaped_snapshot_file"),
        "deterministic": True,
        **SAFETY_FLAGS,
        "adapter_summary": {
            "snapshot_markets": len(fixture["markets"]),
            "adapted_raw_markets": len(adapted),
            "adapter_rejections": len(rejections),
            "rejection_reasons": adapter._reason_counts(rejections),
            "intake_chain_check_passed": True,
        },
        "adapted_raw_fixture": raw_fixture,
        "adapter_rejections": rejections,
    }


def _portfolio_summary(adapter_report, intake_report, score_report, review_table, ledger_report):
    ledger = ledger_report["ledger_summary"]
    open_positions = sum(1 for row in ledger_report["paper_positions"] if row["status"] == "open")
    settled_positions = sum(1 for row in ledger_report["paper_positions"] if row["settled"])
    return {
        "snapshot_markets": adapter_report["adapter_summary"]["snapshot_markets"],
        "adapted_raw_markets": adapter_report["adapter_summary"]["adapted_raw_markets"],
        "adapter_rejections": adapter_report["adapter_summary"]["adapter_rejections"],
        "normalized_supported": intake_report["summary"]["normalized_supported"],
        "intake_rejections": intake_report["summary"]["rejected"],
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


def build_live_shaped_snapshot_paper_lifecycle(root: Path, snapshot_path: Path = None):
    scoring_dir = root / "pm_bot" / "scoring"
    paper_dir = root / "pm_bot" / "paper"
    adapter = _load_module(scoring_dir / "adapt_live_shaped_crypto_snapshot.py", "pmbot_live_snapshot_lifecycle_adapter")
    intake = _load_module(scoring_dir / "crypto_numeric_market_intake.py", "pmbot_live_snapshot_lifecycle_intake")
    scorer = _load_module(scoring_dir / "crypto_numeric_market_scorer.py", "pmbot_live_snapshot_lifecycle_scorer")
    review = _load_module(scoring_dir / "crypto_numeric_review_table.py", "pmbot_live_snapshot_lifecycle_review")
    planner = _load_module(scoring_dir / "crypto_numeric_paper_order_plan.py", "pmbot_live_snapshot_lifecycle_planner")
    ledger = _load_module(paper_dir / "crypto_numeric_paper_execution_ledger.py", "pmbot_live_snapshot_lifecycle_ledger")

    if snapshot_path is None:
        adapter_report = adapter.build_adapter_report(root)
    else:
        adapter_report = _build_adapter_report_from_fixture(adapter, _validated_snapshot_fixture(snapshot_path))
    raw_fixture = adapter_report["adapted_raw_fixture"]
    execution_fixture = _load_json(paper_dir / "crypto_numeric_execution_fixture.v1.json")
    intake_report = intake.build_intake_report(raw_fixture)
    normalized_fixture = intake_report["normalized_scorer_fixture"]
    score_report = scorer.score_fixture(normalized_fixture)
    review_table = review.build_review_table(score_report)
    order_plan = planner.build_paper_order_plan(review_table)
    aligned_execution_fixture = _align_execution_fixture(order_plan, execution_fixture)
    ledger_report = ledger.build_execution_ledger(order_plan, aligned_execution_fixture)
    lifecycle_summary = _portfolio_summary(adapter_report, intake_report, score_report, review_table, ledger_report)

    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-016-LIVE-SHAPED-SNAPSHOT-TO-PAPER-LIFECYCLE",
        "source_fixture_id": adapter_report["source_fixture_id"],
        "adapted_raw_fixture_id": raw_fixture["fixture_id"],
        "normalized_fixture_id": normalized_fixture["fixture_id"],
        "execution_fixture_id": execution_fixture["fixture_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "lifecycle_summary": lifecycle_summary,
        "adapter_summary": adapter_report["adapter_summary"],
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
        "adapter_rejections": adapter_report["adapter_rejections"],
        "rejected_raw_markets": intake_report["rejections"],
        "scoring_rejections": _rows_by_decision(review_table, "reject"),
        "watchlist_rows": _rows_by_decision(review_table, "watchlist"),
        "paper_candidate_rows": _rows_by_decision(review_table, "paper_candidate"),
        "adapted_raw_fixture": raw_fixture,
        "normalized_scorer_fixture": normalized_fixture,
        "score_report": score_report,
        "review_table": review_table,
        "generated_paper_order_plan": order_plan,
        "paper_execution_ledger": ledger_report,
        "paper_positions": ledger_report["paper_positions"],
        "limitations": [
            "Uses fixture live-shaped snapshots only; no live fetcher, network, or external API is implemented.",
            "Adapter output is passed through the existing offline intake, scorer, review, paper plan, and paper ledger modules.",
            "Execution fixture prices are aligned deterministically to live-shaped adapted market IDs for this lifecycle command.",
            "Paper fills, settlement, exposure, and PnL are offline review calculations only.",
            "No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.",
        ],
        "review_note": "Live-shaped snapshot to paper lifecycle chain for offline operator review only.",
    }


def render_markdown(report):
    summary = report["lifecycle_summary"]
    lines = [
        "# PMBOT Live-Shaped Snapshot Paper Lifecycle",
        "",
        "Deterministic offline/paper lifecycle: live-shaped fixture -> adapter -> intake -> scorer -> review -> paper plan -> execution ledger -> portfolio exposure.",
        "",
        "## Summary",
        "",
        f"- Snapshot markets: {summary['snapshot_markets']}",
        f"- Adapted raw markets: {summary['adapted_raw_markets']}",
        f"- Adapter rejections: {summary['adapter_rejections']}",
        f"- Normalized supported: {summary['normalized_supported']}",
        f"- Intake rejections: {summary['intake_rejections']}",
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
        "## Adapter Rejections",
        "",
        "| market_id | reason_code | reason |",
        "| --- | --- | --- |",
    ]
    for row in report["adapter_rejections"]:
        lines.append(f"| {row['market_id']} | {row['reason_code']} | {row['reason']} |")

    lines.extend(["", "## Intake Rejections", "", "| market_id | reason_code | reason |", "| --- | --- | --- |"])
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
    lines.extend(["", "- offline_only=true; paper_only=true; live_fetcher_implemented=false; network_used=false; api_used=false; credentials_used=false; wallet_used=false; real_order_created=false; trading_allowed=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    snapshot_path = Path(args.snapshot) if args.snapshot else None
    try:
        report = build_live_shaped_snapshot_paper_lifecycle(root, snapshot_path)
    except SnapshotInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
