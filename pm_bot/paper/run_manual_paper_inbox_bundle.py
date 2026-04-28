import argparse
import importlib.util
import json
import sys
from pathlib import Path


DEFAULT_RUN_ID = "manual-paper-inbox-bundle-fixture-v1"


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Create an optional deterministic offline paper inbox run bundle.")
    parser.add_argument("--inbox", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _bundle_paths(out_dir):
    if not out_dir:
        return {}
    root = Path(out_dir)
    return {
        "output_directory": str(root),
        "state_after": str(root / "state_after.json"),
        "run_ledger": str(root / "run_ledger.json"),
        "run_summary": str(root / "run_summary.md"),
    }


def _artifact_list(paths):
    if not paths:
        return []
    return [
        {"artifact": "state_after", "path": paths["state_after"]},
        {"artifact": "run_ledger", "path": paths["run_ledger"]},
        {"artifact": "run_summary", "path": paths["run_summary"]},
    ]


def _summary_from_report(report):
    before = report["input_state"]["summary"]
    after = report["run_summary"]
    return {
        "before_exposure": before["open_paper_notional"],
        "after_exposure": after["exposure_after_run"],
        "realized_paper_pnl_delta": report["run_ledger"]["realized_paper_pnl_delta"],
        "final_realized_paper_pnl": report["run_ledger"]["final_realized_paper_pnl"],
    }


def render_operator_summary(bundle):
    lines = [
        "# Manual Paper Inbox Run Bundle",
        "",
        f"- Run ID: {bundle['run_id']}",
        f"- Inbox: {bundle['inbox_path']}",
        f"- Input state: {bundle['input_state_path']}",
        f"- Snapshots discovered: {bundle['snapshot_files_discovered']}",
        f"- Snapshots processed: {bundle['snapshots_processed']}",
        f"- Snapshots skipped already processed: {bundle['snapshots_skipped_already_processed']}",
        f"- New paper orders created: {bundle['new_paper_orders_created']}",
        f"- Duplicate orders blocked: {bundle['duplicate_orders_blocked']}",
        f"- Risk-limit orders blocked: {bundle['risk_limit_orders_blocked']}",
        f"- Before exposure: {bundle['before_exposure']:.2f}",
        f"- After exposure: {bundle['exposure_after_run']:.2f}",
        f"- Realized paper PnL delta: {bundle['realized_paper_pnl_delta']:.2f}",
        f"- Final realized paper PnL: {bundle['final_realized_paper_pnl']:.2f}",
        "",
        "## Output Artifacts",
        "",
    ]
    if bundle["output_files"]:
        for item in bundle["output_files"]:
            lines.append(f"- {item['artifact']}: {item['path']}")
    else:
        lines.append("- None written")
    lines.extend([
        "",
        "## Safety",
        "",
        "- Offline/paper only. No live fetcher, API, network, wallet, real order, live trading, runtime wiring, or prompt automation.",
        "",
    ])
    return "\n".join(lines)


def build_manual_paper_inbox_bundle(root: Path, inbox_path=None, state_path=None, out_dir=None, run_id=None):
    paper_dir = root / "pm_bot" / "paper"
    inbox_runner = _load_module(paper_dir / "run_local_snapshot_inbox_paper_portfolio.py", "pmbot_manual_bundle_inbox")
    resolved_run_id = run_id or DEFAULT_RUN_ID
    paths = _bundle_paths(out_dir)
    out_state = paths.get("state_after")
    out_ledger = paths.get("run_ledger")
    report = inbox_runner.build_local_snapshot_inbox_paper_portfolio(
        root,
        inbox_path,
        state_path,
        out_state,
        out_ledger,
        resolved_run_id,
    )
    run_delta = _summary_from_report(report)
    bundle = {
        "schema_version": "v1",
        "task_id": "PMBOT-BRAIN-024-MANUAL-PAPER-RUN-BUNDLE",
        "workflow": "manual_paper_inbox_bundle",
        "deterministic": True,
        "run_id": resolved_run_id,
        "inbox_path": report["inbox"]["path"],
        "input_state_path": report["input_state"]["source_path"],
        "output_directory": paths.get("output_directory"),
        "output_files": _artifact_list(paths),
        "bundle_written": bool(out_dir),
        "snapshot_files_discovered": report["run_summary"]["snapshot_files_discovered"],
        "snapshots_processed": report["run_summary"]["snapshots_processed"],
        "snapshots_skipped_already_processed": report["run_summary"]["snapshots_skipped_already_processed"],
        "new_paper_orders_created": report["run_summary"]["new_paper_orders_created"],
        "duplicate_orders_blocked": report["run_summary"]["duplicate_orders_blocked"],
        "risk_limit_orders_blocked": report["run_summary"]["risk_limit_orders_blocked"],
        "open_positions_after_run": report["run_summary"]["open_positions_after_run"],
        "settled_positions_after_run": report["run_summary"]["settled_positions_after_run"],
        "before_exposure": run_delta["before_exposure"],
        "exposure_after_run": report["run_summary"]["exposure_after_run"],
        "realized_paper_pnl_delta": run_delta["realized_paper_pnl_delta"],
        "final_realized_paper_pnl": run_delta["final_realized_paper_pnl"],
        "inbox_report_summary": {
            "run_id": report["run_summary"]["run_id"],
            "out_state_written": report["run_summary"]["out_state_written"],
            "out_run_ledger_written": report["run_summary"]["out_run_ledger_written"],
            "safety_flags_locked": report["run_summary"]["safety_flags_locked"],
        },
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
    summary_md = render_operator_summary(bundle)
    if out_dir:
        _write_text(Path(paths["run_summary"]), summary_md)
    return bundle, summary_md


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    bundle, summary_md = build_manual_paper_inbox_bundle(root, args.inbox, args.state, args.out_dir, args.run_id)
    if args.markdown:
        print(summary_md, end="")
    else:
        print(json.dumps(bundle, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
