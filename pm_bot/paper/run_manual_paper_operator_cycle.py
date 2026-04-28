import argparse
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-BRAIN-029-MANUAL-PAPER-OPERATOR-CYCLE"
WORKFLOW = "manual_paper_operator_cycle"
SCHEMA_VERSION = "v1"
DEFAULT_RUN_ID = "manual-paper-operator-cycle-fixture-v1"
DEFAULT_THRESHOLD_HIT_REVIEW_SOURCE = Path(
    r"C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_500_001.json"
)
SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "live_fetcher_implemented": False,
    "api_used": False,
    "network_used": False,
    "wallet_used": False,
    "real_order_created": False,
    "trading_allowed": False,
    "runtime_wiring_changed": False,
    "dispatcher_touched": False,
    "prompt_automation_added": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Run a deterministic offline manual paper operator cycle.")
    parser.add_argument("--source", default=None)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--write-inbox", action="store_true")
    parser.add_argument("--write-run", action="store_true")
    parser.add_argument("--commit-state", action="store_true")
    parser.add_argument("--out-manifest", default=None)
    parser.add_argument("--allow-identical-rerun", action="store_true")
    parser.add_argument("--include-threshold-hit-review", action="store_true")
    parser.add_argument("--threshold-reference-context", default=None)
    parser.add_argument("--threshold-decision-policy", default=None)
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


def _import_phase_report(import_report):
    summary = import_report["summary"]
    return {
        "workflow": import_report["workflow"],
        "source_path": import_report["source_path"],
        "workspace_path": import_report["workspace_path"],
        "inbox_path": import_report["inbox_path"],
        "write_inbox": import_report["write_inbox"],
        "manifest_path": import_report["manifest_path"],
        "manifest_written": import_report["manifest_written"],
        "discovered_inputs": summary["discovered_inputs"],
        "importable_snapshots": summary["importable_snapshots"],
        "imported_snapshots": summary["imported_snapshots"],
        "skipped_or_quarantined_inputs": summary["skipped_or_quarantined_inputs"],
        "reason_counts": summary["reason_counts"],
        "imported_records": import_report["imported_records"],
        "skipped_quarantined_records": import_report["skipped_quarantined_records"],
        "output_inbox_files": import_report["output_inbox_files"],
    }


def _workspace_phase_report(workspace_report, import_report, write_inbox):
    imported_snapshots = import_report["summary"]["imported_snapshots"]
    importable_snapshots = import_report["summary"]["importable_snapshots"]
    previewed_not_added = bool(importable_snapshots and not write_inbox)
    includes_imported = bool(imported_snapshots and write_inbox)
    if previewed_not_added:
        phase_note = "Importable snapshots were previewed but not added to the workspace inbox because --write-inbox was not provided."
    elif includes_imported:
        phase_note = "Newly imported snapshots were written to the workspace inbox before workspace processing."
    else:
        phase_note = "Workspace processing used the existing workspace inbox."
    return {
        "workflow": workspace_report["workflow"],
        "run_id": workspace_report["run_id"],
        "workspace_path": workspace_report["workspace_path"],
        "inbox_path": workspace_report["inbox_path"],
        "current_state_path": workspace_report["current_state_path"],
        "run_directory_path": workspace_report["run_directory_path"],
        "workspace_phase_includes_imported_snapshots": includes_imported,
        "imported_snapshots_previewed_but_not_added_to_inbox": previewed_not_added,
        "phase_note": phase_note,
        "run_artifacts_written": workspace_report["run_artifacts_written"],
        "state_committed": workspace_report["state_committed"],
        "output_files": workspace_report["output_files"],
        "input_files_discovered": workspace_report["input_files_discovered"],
        "valid_snapshot_files_discovered": workspace_report["valid_snapshot_files_discovered"],
        "snapshot_files_discovered": workspace_report["snapshot_files_discovered"],
        "snapshots_processed": workspace_report["snapshots_processed"],
        "snapshots_skipped_already_processed": workspace_report["snapshots_skipped_already_processed"],
        "quarantine_count": workspace_report["quarantine_count"],
        "quarantine_reason_counts": workspace_report["quarantine_reason_counts"],
        "quarantine_records": workspace_report["quarantine_records"],
        "new_paper_orders_created": workspace_report["new_paper_orders_created"],
        "duplicate_orders_blocked": workspace_report["duplicate_orders_blocked"],
        "risk_limit_orders_blocked": workspace_report["risk_limit_orders_blocked"],
        "open_positions_after_run": workspace_report["open_positions_after_run"],
        "settled_positions_after_run": workspace_report["settled_positions_after_run"],
        "exposure_before": workspace_report["exposure_before"],
        "exposure_after_run": workspace_report["exposure_after_run"],
        "realized_paper_pnl_delta": workspace_report["realized_paper_pnl_delta"],
        "final_realized_paper_pnl": workspace_report["final_realized_paper_pnl"],
        "current_state_after_command": workspace_report["current_state_after_command"],
    }


def _workspace_summary(workspace_phase):
    return {
        "input_files_discovered": workspace_phase["input_files_discovered"],
        "valid_snapshot_files_discovered": workspace_phase["valid_snapshot_files_discovered"],
        "snapshot_files_discovered": workspace_phase["snapshot_files_discovered"],
        "snapshots_processed": workspace_phase["snapshots_processed"],
        "snapshots_skipped_already_processed": workspace_phase["snapshots_skipped_already_processed"],
        "quarantine_count": workspace_phase["quarantine_count"],
        "quarantine_reason_counts": workspace_phase["quarantine_reason_counts"],
        "new_paper_orders_created": workspace_phase["new_paper_orders_created"],
        "duplicate_orders_blocked": workspace_phase["duplicate_orders_blocked"],
        "risk_limit_orders_blocked": workspace_phase["risk_limit_orders_blocked"],
        "exposure_before": workspace_phase["exposure_before"],
        "exposure_after_run": workspace_phase["exposure_after_run"],
        "realized_paper_pnl_delta": workspace_phase["realized_paper_pnl_delta"],
        "final_realized_paper_pnl": workspace_phase["final_realized_paper_pnl"],
    }


def _top_level_summary(run_id, source_path, workspace_path, import_phase, workspace_phase):
    workspace_summary = _workspace_summary(workspace_phase)
    return {
        "run_id": run_id,
        "source_path": source_path,
        "workspace_path": workspace_path,
        "import_phase_summary": {
            "discovered_inputs": import_phase["discovered_inputs"],
            "importable_snapshots": import_phase["importable_snapshots"],
            "imported_snapshots": import_phase["imported_snapshots"],
            "skipped_or_quarantined_inputs": import_phase["skipped_or_quarantined_inputs"],
            "reason_counts": import_phase["reason_counts"],
        },
        "workspace_phase_summary": workspace_summary,
        "inbox_files_written": bool(import_phase["output_inbox_files"]),
        "manifest_written": import_phase["manifest_written"],
        "run_artifacts_written": workspace_phase["run_artifacts_written"],
        "state_committed": workspace_phase["state_committed"],
        "imported_snapshot_count": import_phase["imported_snapshots"],
        "importable_snapshot_count": import_phase["importable_snapshots"],
        "skipped_or_quarantined_import_count": import_phase["skipped_or_quarantined_inputs"],
        "import_skip_quarantine_reason_counts": import_phase["reason_counts"],
        "workspace_snapshots_discovered": workspace_phase["snapshot_files_discovered"],
        "workspace_snapshots_processed": workspace_phase["snapshots_processed"],
        "workspace_snapshots_skipped": workspace_phase["snapshots_skipped_already_processed"],
        "workspace_quarantine_count": workspace_phase["quarantine_count"],
        "new_paper_orders_created": workspace_phase["new_paper_orders_created"],
        "duplicate_orders_blocked": workspace_phase["duplicate_orders_blocked"],
        "risk_limit_orders_blocked": workspace_phase["risk_limit_orders_blocked"],
        "exposure_before": workspace_phase["exposure_before"],
        "exposure_after_run": workspace_phase["exposure_after_run"],
        "realized_paper_pnl_delta": workspace_phase["realized_paper_pnl_delta"],
        "final_realized_paper_pnl": workspace_phase["final_realized_paper_pnl"],
        "safety_flags": SAFETY_FLAGS,
    }


def _threshold_hit_candidate_rows(threshold_report):
    rows = []
    for row in threshold_report["rows"]:
        rows.append(
            {
                "market_id": row["market_id"],
                "asset": row["asset"],
                "target": row["target_display"] or row["target"],
                "market_type": row["market_type"],
                "review_decision": row["review_decision"],
                "reason_codes": row["reason_codes"],
            }
        )
    return rows


def _threshold_hit_review_summary(threshold_report, artifact_paths):
    summary = threshold_report["summary"]
    return {
        "threshold_hit_review_included": True,
        "threshold_hit_source_path": threshold_report["source_path"],
        "threshold_hit_reference_context_used": summary["reference_context_used"],
        "threshold_hit_decision_policy_used": summary.get("decision_policy_used", False),
        "threshold_hit_decision_policy_version": summary.get("decision_policy_version"),
        "threshold_hit_candidates": summary["threshold_hit_candidates"],
        "threshold_hit_candidate_rows": _threshold_hit_candidate_rows(threshold_report),
        "threshold_hit_watchlist_count": summary["watchlist_count"],
        "threshold_hit_policy_blocked_count": summary.get("policy_blocked_count", 0),
        "threshold_hit_paper_candidate_count": summary["paper_candidate_count"],
        "threshold_hit_paper_orders_created": 0,
        "threshold_hit_artifact_paths": artifact_paths,
        "safety_flags": SAFETY_FLAGS,
    }


def _build_threshold_hit_review(
    root: Path,
    threshold_reference_context_path=None,
    threshold_decision_policy_path=None,
):
    paper_dir = root / "pm_bot" / "paper"
    threshold_runner = _load_module(
        paper_dir / "run_crypto_threshold_hit_review_table.py",
        "pmbot_operator_cycle_threshold_hit_review",
    )
    reference_context = (
        threshold_runner._load_reference_context(threshold_reference_context_path)
        if threshold_reference_context_path
        else None
    )
    decision_policy = (
        threshold_runner._load_decision_policy(threshold_decision_policy_path)
        if threshold_decision_policy_path
        else None
    )
    threshold_report = threshold_runner.build_crypto_threshold_hit_review_table(
        root,
        DEFAULT_THRESHOLD_HIT_REVIEW_SOURCE,
        reference_context=reference_context,
        decision_policy=decision_policy,
    )
    return threshold_report, threshold_runner


def _write_threshold_hit_review_artifacts(run_directory_path, threshold_report, threshold_runner):
    if not run_directory_path:
        return {}
    run_dir = Path(run_directory_path)
    json_path = run_dir / "threshold_hit_review.json"
    markdown_path = run_dir / "threshold_hit_review.md"
    _write_json(json_path, threshold_report)
    markdown_path.write_text(threshold_runner.render_markdown(threshold_report), encoding="utf-8")
    return {
        "json": str(json_path),
        "markdown": str(markdown_path),
    }


def build_manual_paper_operator_cycle(
    root: Path,
    source_path=None,
    workspace_path=None,
    run_id=None,
    write_inbox=False,
    write_run=False,
    commit_state=False,
    out_manifest_path=None,
    allow_identical_rerun=False,
    include_threshold_hit_review=False,
    threshold_reference_context_path=None,
    threshold_decision_policy_path=None,
):
    paper_dir = root / "pm_bot" / "paper"
    import_runner = _load_module(
        paper_dir / "run_manual_snapshot_workspace_import.py",
        "pmbot_operator_cycle_import",
    )
    workspace_runner = _load_module(
        paper_dir / "run_manual_paper_workspace.py",
        "pmbot_operator_cycle_workspace",
    )
    resolved_run_id = run_id or DEFAULT_RUN_ID
    import_report = import_runner.build_manual_snapshot_workspace_import(
        root,
        source_path,
        workspace_path,
        out_manifest_path,
        write_inbox,
    )
    workspace_report = workspace_runner.build_manual_paper_workspace(
        root,
        workspace_path,
        resolved_run_id,
        write_run,
        commit_state,
        allow_identical_rerun,
    )
    import_phase = _import_phase_report(import_report)
    workspace_phase = _workspace_phase_report(workspace_report, import_report, write_inbox)
    write_controls = {
        "write_inbox": bool(write_inbox),
        "write_run": bool(write_run or commit_state),
        "commit_state": bool(commit_state),
        "commit_state_implies_write_run": bool(commit_state),
        "allow_identical_rerun": bool(allow_identical_rerun),
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "workflow": WORKFLOW,
        "deterministic": True,
        "phase_order": ["import", "workspace"],
        "run_id": resolved_run_id,
        "source_path": import_phase["source_path"],
        "workspace_path": workspace_phase["workspace_path"],
        "inbox_path": workspace_phase["inbox_path"],
        "write_controls": write_controls,
        "import_phase": import_phase,
        "workspace_phase": workspace_phase,
        "summary": _top_level_summary(
            resolved_run_id,
            import_phase["source_path"],
            workspace_phase["workspace_path"],
            import_phase,
            workspace_phase,
        ),
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Runs deterministic local manual snapshot import first, then deterministic manual paper workspace processing.",
            "Default run is read-only: no inbox files, import manifest, run artifacts, or current_state promotion are written.",
            "No live fetcher, network, external API, credentials, wallet access, real orders, live trading, runtime wiring, dispatcher change, prompt automation, broad refactor, or new validation layer is included.",
        ],
    }
    if include_threshold_hit_review:
        threshold_report, threshold_runner = _build_threshold_hit_review(
            root,
            threshold_reference_context_path,
            threshold_decision_policy_path,
        )
        threshold_artifact_paths = _write_threshold_hit_review_artifacts(
            workspace_phase["run_directory_path"],
            threshold_report,
            threshold_runner,
        )
        threshold_summary = _threshold_hit_review_summary(threshold_report, threshold_artifact_paths)
        report["phase_order"] = ["import", "workspace", "threshold_hit_review"]
        report["threshold_hit_review"] = threshold_summary
        report["summary"].update(threshold_summary)
        report["limitations"].append(
            "Optional threshold-hit review is an offline operator artifact only; it does not create paper orders, mutate paper state, alter risk limits, or affect workspace processing decisions."
        )
    return report


def render_markdown(report):
    summary = report["summary"]
    import_summary = summary["import_phase_summary"]
    workspace_summary = summary["workspace_phase_summary"]
    lines = [
        "# Manual Paper Operator Cycle",
        "",
        f"- Run ID: {report['run_id']}",
        f"- Source: {report['source_path']}",
        f"- Workspace: {report['workspace_path']}",
        f"- Inbox: {report['inbox_path']}",
        f"- Write inbox: {str(report['write_controls']['write_inbox']).lower()}",
        f"- Manifest written: {str(summary['manifest_written']).lower()}",
        f"- Run artifacts written: {str(summary['run_artifacts_written']).lower()}",
        f"- State committed: {str(summary['state_committed']).lower()}",
        f"- Workspace note: {report['workspace_phase']['phase_note']}",
        "",
        "## Import Phase",
        "",
        f"- Inputs discovered: {import_summary['discovered_inputs']}",
        f"- Importable snapshots: {import_summary['importable_snapshots']}",
        f"- Imported snapshots: {import_summary['imported_snapshots']}",
        f"- Skipped/quarantined inputs: {import_summary['skipped_or_quarantined_inputs']}",
        f"- Reason counts: {json.dumps(import_summary['reason_counts'], sort_keys=True)}",
        "",
        "## Workspace Phase",
        "",
        f"- Input files discovered: {workspace_summary['input_files_discovered']}",
        f"- Valid snapshots discovered: {workspace_summary['valid_snapshot_files_discovered']}",
        f"- Snapshots discovered: {workspace_summary['snapshot_files_discovered']}",
        f"- Snapshots processed: {workspace_summary['snapshots_processed']}",
        f"- Snapshots skipped already processed: {workspace_summary['snapshots_skipped_already_processed']}",
        f"- Quarantine records: {workspace_summary['quarantine_count']}",
        f"- Quarantine reason counts: {json.dumps(workspace_summary['quarantine_reason_counts'], sort_keys=True)}",
        f"- New paper orders created: {workspace_summary['new_paper_orders_created']}",
        f"- Duplicate orders blocked: {workspace_summary['duplicate_orders_blocked']}",
        f"- Risk-limit orders blocked: {workspace_summary['risk_limit_orders_blocked']}",
        f"- Before exposure: {workspace_summary['exposure_before']:.2f}",
        f"- After exposure: {workspace_summary['exposure_after_run']:.2f}",
        f"- Realized paper PnL delta: {workspace_summary['realized_paper_pnl_delta']:.2f}",
        f"- Final realized paper PnL: {workspace_summary['final_realized_paper_pnl']:.2f}",
        "",
        "## Output Artifacts",
        "",
    ]
    output_files = report["import_phase"]["output_inbox_files"] + report["workspace_phase"]["output_files"]
    if output_files:
        for item in output_files:
            artifact = item.get("artifact", "inbox_file")
            path = item.get("path")
            lines.append(f"- {artifact}: {path}")
    else:
        lines.append("- None written")
    threshold_summary = report.get("threshold_hit_review")
    if threshold_summary:
        lines.extend(
            [
                "",
                "## Threshold-Hit Review",
                "",
                f"- threshold_hit_review_included: {str(threshold_summary['threshold_hit_review_included']).lower()}",
                f"- threshold_hit_source_path: {threshold_summary['threshold_hit_source_path']}",
                f"- threshold_hit_reference_context_used: {str(threshold_summary['threshold_hit_reference_context_used']).lower()}",
                f"- threshold_hit_decision_policy_used: {str(threshold_summary['threshold_hit_decision_policy_used']).lower()}",
                f"- threshold_hit_decision_policy_version: {threshold_summary['threshold_hit_decision_policy_version'] or ''}",
                f"- threshold_hit_candidates: {threshold_summary['threshold_hit_candidates']}",
                f"- threshold_hit_watchlist_count: {threshold_summary['threshold_hit_watchlist_count']}",
                f"- threshold_hit_policy_blocked_count: {threshold_summary['threshold_hit_policy_blocked_count']}",
                f"- threshold_hit_paper_candidate_count: {threshold_summary['threshold_hit_paper_candidate_count']}",
                f"- threshold_hit_paper_orders_created: {threshold_summary['threshold_hit_paper_orders_created']}",
                f"- threshold_hit_artifact_paths: {json.dumps(threshold_summary['threshold_hit_artifact_paths'], sort_keys=True)}",
                f"- threshold_hit_candidate_rows: {json.dumps(threshold_summary['threshold_hit_candidate_rows'], sort_keys=True)}",
            ]
        )
    lines.extend([
        "",
        "## Safety",
        "",
        "- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false",
        "",
    ])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    try:
        report = build_manual_paper_operator_cycle(
            root,
            args.source,
            args.workspace,
            args.run_id,
            args.write_inbox,
            args.write_run,
            args.commit_state,
            args.out_manifest,
            args.allow_identical_rerun,
            args.include_threshold_hit_review,
            args.threshold_reference_context,
            args.threshold_decision_policy,
        )
    except FileExistsError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 2
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
