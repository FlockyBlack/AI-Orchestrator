import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path


DEFAULT_RUN_ID = "manual-paper-workspace-fixture-v1"
RUN_FILES = ("state_before.json", "state_after.json", "run_ledger.json", "run_summary.md")


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Run a deterministic offline paper workspace inbox preview or commit.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--commit-state", action="store_true")
    parser.add_argument("--write-run", action="store_true")
    parser.add_argument("--allow-identical-rerun", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _workspace_paths(root: Path, workspace_path=None):
    workspace = Path(workspace_path) if workspace_path else root / "pm_bot" / "paper" / "manual_paper_workspace"
    return {
        "workspace": workspace,
        "inbox": workspace / "inbox",
        "state_dir": workspace / "state",
        "current_state": workspace / "state" / "current_state.json",
        "previous_state": workspace / "state" / "current_state.previous.json",
        "runs": workspace / "runs",
    }


def _run_dir(paths, run_id):
    return paths["runs"] / run_id


def _copy_state_before(current_state: Path, run_dir: Path):
    shutil.copyfile(current_state, run_dir / "state_before.json")


def _artifact_bytes(path: Path, replacements=None):
    data = path.read_bytes()
    for old, new in replacements or ():
        data = data.replace(old.encode("utf-8"), new.encode("utf-8"))
    return data


def _compare_dirs(left: Path, right: Path, replacements=None):
    return all(_artifact_bytes(left / name) == _artifact_bytes(right / name, replacements) for name in RUN_FILES)


def _existing_files(run_dir: Path):
    return sorted(path.name for path in run_dir.iterdir() if path.is_file()) if run_dir.exists() else []


def _file_sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reason_counts(records):
    counts = {}
    for record in records:
        reason_code = record["reason_code"]
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return dict(sorted(counts.items()))


def _quarantine_record(path: Path, status, reason_code, reason, action_taken, digest=None, snapshot_id=None):
    return {
        "input_path": str(path),
        "file_name": path.name,
        "status": status,
        "reason_code": reason_code,
        "reason": reason,
        "digest": digest,
        "snapshot_id": snapshot_id,
        "action_taken": action_taken,
    }


def _extract_snapshot(payload):
    if isinstance(payload, dict) and isinstance(payload.get("snapshot"), dict):
        return payload
    snapshots = payload.get("snapshots") if isinstance(payload, dict) else None
    if isinstance(snapshots, list) and len(snapshots) == 1 and isinstance(snapshots[0], dict):
        candidate = snapshots[0]
        if isinstance(candidate.get("snapshot"), dict):
            return candidate
    return None


def _snapshot_id_from_payload(payload):
    if isinstance(payload, dict):
        value = payload.get("snapshot_id")
        if value is not None:
            return value
        snapshots = payload.get("snapshots")
        if isinstance(snapshots, list) and snapshots and isinstance(snapshots[0], dict):
            return snapshots[0].get("snapshot_id")
    return None


def _classify_inbox(inbox: Path, processed_snapshot_ids):
    accepted = []
    quarantine = []
    seen_snapshot_ids = set()
    processed_ids = set(processed_snapshot_ids)
    entries = sorted(inbox.iterdir(), key=lambda item: item.name) if inbox.exists() else []

    for path in entries:
        digest = None
        snapshot_id = None
        if not path.is_file():
            quarantine.append(_quarantine_record(
                path,
                "quarantined",
                "unreadable_input",
                "Inbox entry is not a regular file.",
                "Skipped before snapshot processing.",
            ))
            continue
        try:
            digest = _file_sha256(path)
        except OSError as exc:
            quarantine.append(_quarantine_record(
                path,
                "quarantined",
                "unreadable_input",
                f"Unable to read inbox entry: {exc}",
                "Skipped before snapshot processing.",
            ))
            continue
        if path.suffix.lower() != ".json":
            quarantine.append(_quarantine_record(
                path,
                "skipped",
                "ignored_non_json_file",
                "Inbox entry is not a JSON file.",
                "Ignored before snapshot processing.",
                digest,
            ))
            continue
        try:
            payload = _load_json(path)
        except json.JSONDecodeError as exc:
            quarantine.append(_quarantine_record(
                path,
                "quarantined",
                "malformed_json",
                f"JSON parse failed at line {exc.lineno}, column {exc.colno}.",
                "Skipped before snapshot processing.",
                digest,
            ))
            continue
        snapshot_id = _snapshot_id_from_payload(payload)
        snapshot = _extract_snapshot(payload)
        if snapshot is None or "snapshot_id" not in snapshot or "observed_at" not in snapshot:
            quarantine.append(_quarantine_record(
                path,
                "quarantined",
                "unsupported_snapshot_shape",
                "JSON payload is not a supported single snapshot file.",
                "Skipped before snapshot processing.",
                digest,
                snapshot_id,
            ))
            continue
        snapshot_id = snapshot["snapshot_id"]
        if snapshot_id in seen_snapshot_ids:
            quarantine.append(_quarantine_record(
                path,
                "skipped",
                "duplicate_snapshot_id_in_inbox",
                "Snapshot ID was already accepted from another inbox file in this run.",
                "Skipped before snapshot processing.",
                digest,
                snapshot_id,
            ))
            continue
        seen_snapshot_ids.add(snapshot_id)
        accepted.append({
            "source": path,
            "file_name": path.name,
            "digest": digest,
            "snapshot_id": snapshot_id,
            "observed_at": snapshot["observed_at"],
            "already_processed": snapshot_id in processed_ids,
        })

    accepted.sort(key=lambda row: (row["observed_at"], row["snapshot_id"], row["file_name"]))
    already_processed = [
        _quarantine_record(
            row["source"],
            "skipped",
            "already_processed_snapshot",
            "Snapshot ID is already present in the input paper state.",
            "Left available to the existing processor for already-processed accounting.",
            row["digest"],
            row["snapshot_id"],
        )
        for row in accepted
        if row["already_processed"]
    ]
    return {
        "input_count": len(entries),
        "valid_snapshots": accepted,
        "accepted_for_processing": [row for row in accepted if not row["already_processed"]],
        "quarantine_records": quarantine + already_processed,
    }


def _filtered_inbox(classification):
    temp_root = Path(tempfile.mkdtemp())
    inbox = temp_root / "inbox"
    inbox.mkdir(parents=True)
    for row in classification["valid_snapshots"]:
        shutil.copyfile(row["source"], inbox / row["file_name"])
    return inbox, temp_root


def _augment_run_ledger(run_dir: Path, classification):
    ledger_path = run_dir / "run_ledger.json"
    if not ledger_path.exists():
        return
    ledger = _load_json(ledger_path)
    by_name = {row["file_name"]: row for row in classification["valid_snapshots"]}
    for row in ledger.get("snapshot_files_discovered", []):
        original = by_name.get(row.get("file_name"))
        if original:
            row["path"] = str(original["source"])
    if classification["valid_snapshots"]:
        ledger["input_inbox_path"] = str(classification["valid_snapshots"][0]["source"].parent)
    ledger["input_files_discovered"] = classification["input_count"]
    ledger["valid_snapshot_files_discovered"] = len(classification["valid_snapshots"])
    ledger["quarantine_count"] = len(classification["quarantine_records"])
    ledger["quarantine_reason_counts"] = _reason_counts(classification["quarantine_records"])
    ledger["quarantine_records"] = classification["quarantine_records"]
    _write_json(ledger_path, ledger)


def _render_run_summary(bundle, classification):
    lines = [
        "# Manual Paper Inbox Run Bundle",
        "",
        f"- Run ID: {bundle['run_id']}",
        f"- Inbox: {bundle['inbox_path']}",
        f"- Input state: {bundle['input_state_path']}",
        f"- Inputs discovered: {classification['input_count']}",
        f"- Valid snapshots discovered: {len(classification['valid_snapshots'])}",
        f"- Snapshots processed: {bundle['snapshots_processed']}",
        f"- Snapshots skipped already processed: {bundle['snapshots_skipped_already_processed']}",
        f"- Quarantine records: {len(classification['quarantine_records'])}",
        f"- Quarantine reason counts: {json.dumps(_reason_counts(classification['quarantine_records']), sort_keys=True)}",
        f"- New paper orders created: {bundle['new_paper_orders_created']}",
        f"- Duplicate orders blocked: {bundle['duplicate_orders_blocked']}",
        f"- Risk-limit orders blocked: {bundle['risk_limit_orders_blocked']}",
        f"- Before exposure: {bundle['before_exposure']:.2f}",
        f"- After exposure: {bundle['exposure_after_run']:.2f}",
        f"- Realized paper PnL delta: {bundle['realized_paper_pnl_delta']:.2f}",
        f"- Final realized paper PnL: {bundle['final_realized_paper_pnl']:.2f}",
        "",
        "## Quarantine",
        "",
    ]
    if classification["quarantine_records"]:
        for record in classification["quarantine_records"]:
            lines.append(f"- {record['file_name']}: {record['status']} {record['reason_code']} ({record['action_taken']})")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Safety",
        "",
        "- Offline/paper only. No live fetcher, API, network, wallet, real order, live trading, runtime wiring, or prompt automation.",
        "",
    ])
    return "\n".join(lines)


def _materialize_run(bundle_runner, root: Path, paths, run_id, run_dir: Path, classification):
    run_dir.mkdir(parents=True, exist_ok=False)
    _copy_state_before(paths["current_state"], run_dir)
    temp_inbox, temp_root = _filtered_inbox(classification)
    try:
        bundle, _summary_md = bundle_runner.build_manual_paper_inbox_bundle(
            root,
            str(temp_inbox),
            str(paths["current_state"]),
            str(run_dir),
            run_id,
        )
    finally:
        shutil.rmtree(temp_root)
    bundle["inbox_path"] = str(paths["inbox"])
    _augment_run_ledger(run_dir, classification)
    (run_dir / "run_summary.md").write_text(_render_run_summary(bundle, classification), encoding="utf-8")
    return bundle


def _build_with_temp(bundle_runner, root: Path, paths, run_id, classification):
    temp_root = Path(tempfile.mkdtemp())
    temp_run = temp_root / run_id
    bundle = _materialize_run(bundle_runner, root, paths, run_id, temp_run, classification)
    return bundle, temp_run, temp_root


def _state_summary(path: Path):
    state = _load_json(path)
    exposure = state["exposure_summary"]
    return {
        "processed_snapshots": len(state.get("processed_snapshot_ids", [])),
        "open_positions": exposure["open_positions"],
        "settled_positions": exposure["settled_positions"],
        "open_paper_notional": exposure["open_paper_notional"],
        "realized_paper_pnl": exposure["realized_paper_pnl"],
    }


def _output_files(run_dir: Path, written: bool):
    if not written:
        return []
    return [
        {"artifact": "state_before", "path": str(run_dir / "state_before.json")},
        {"artifact": "state_after", "path": str(run_dir / "state_after.json")},
        {"artifact": "run_ledger", "path": str(run_dir / "run_ledger.json")},
        {"artifact": "run_summary", "path": str(run_dir / "run_summary.md")},
    ]


def render_markdown(report):
    lines = [
        "# Manual Paper Workspace",
        "",
        f"- Run ID: {report['run_id']}",
        f"- Workspace: {report['workspace_path']}",
        f"- Inbox: {report['inbox_path']}",
        f"- Current state: {report['current_state_path']}",
        f"- Run directory: {report['run_directory_path'] or ''}",
        f"- Run artifacts written: {str(report['run_artifacts_written']).lower()}",
        f"- State committed: {str(report['state_committed']).lower()}",
        f"- Inputs discovered: {report['input_files_discovered']}",
        f"- Valid snapshots discovered: {report['valid_snapshot_files_discovered']}",
        f"- Snapshots discovered: {report['snapshot_files_discovered']}",
        f"- Snapshots processed: {report['snapshots_processed']}",
        f"- Snapshots skipped already processed: {report['snapshots_skipped_already_processed']}",
        f"- Quarantine records: {report['quarantine_count']}",
        f"- Quarantine reason counts: {json.dumps(report['quarantine_reason_counts'], sort_keys=True)}",
        f"- New paper orders created: {report['new_paper_orders_created']}",
        f"- Duplicate orders blocked: {report['duplicate_orders_blocked']}",
        f"- Risk-limit orders blocked: {report['risk_limit_orders_blocked']}",
        f"- Before exposure: {report['exposure_before']:.2f}",
        f"- After exposure: {report['exposure_after_run']:.2f}",
        f"- Realized paper PnL delta: {report['realized_paper_pnl_delta']:.2f}",
        f"- Final realized paper PnL: {report['final_realized_paper_pnl']:.2f}",
        "",
        "## Output Artifacts",
        "",
    ]
    if report["output_files"]:
        for item in report["output_files"]:
            lines.append(f"- {item['artifact']}: {item['path']}")
    else:
        lines.append("- None written")
    lines.extend([
        "",
        "## Quarantine",
        "",
    ])
    if report["quarantine_records"]:
        for record in report["quarantine_records"]:
            lines.append(f"- {record['file_name']}: {record['status']} {record['reason_code']} ({record['action_taken']})")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Safety",
        "",
        "- Offline/paper only. No live fetcher, API, network, wallet, real order, live trading, runtime wiring, or prompt automation.",
        "",
    ])
    return "\n".join(lines)


def build_manual_paper_workspace(root: Path, workspace_path=None, run_id=None, write_run=False, commit_state=False, allow_identical_rerun=False):
    paper_dir = root / "pm_bot" / "paper"
    bundle_runner = _load_module(paper_dir / "run_manual_paper_inbox_bundle.py", "pmbot_workspace_bundle")
    resolved_run_id = run_id or DEFAULT_RUN_ID
    paths = _workspace_paths(root, workspace_path)
    should_write_run = write_run or commit_state
    run_dir = _run_dir(paths, resolved_run_id)
    initial_state = _load_json(paths["current_state"])
    classification = _classify_inbox(paths["inbox"], initial_state.get("processed_snapshot_ids", []))

    if not should_write_run:
        temp_inbox, temp_root = _filtered_inbox(classification)
        try:
            bundle, _summary_md = bundle_runner.build_manual_paper_inbox_bundle(
                root,
                str(temp_inbox),
                str(paths["current_state"]),
                None,
                resolved_run_id,
            )
        finally:
            shutil.rmtree(temp_root)
        bundle["inbox_path"] = str(paths["inbox"])
        run_written = False
    else:
        if run_dir.exists():
            if not allow_identical_rerun:
                raise FileExistsError(f"Run directory already exists: {run_dir}")
            temp_bundle, temp_run, temp_root = _build_with_temp(bundle_runner, root, paths, resolved_run_id, classification)
            try:
                path_replacements = [
                    (str(temp_run), str(run_dir)),
                    (json.dumps(str(temp_run))[1:-1], json.dumps(str(run_dir))[1:-1]),
                ]
                if _existing_files(run_dir) != sorted(RUN_FILES) or not _compare_dirs(run_dir, temp_run, path_replacements):
                    raise FileExistsError(f"Run directory already exists with different content: {run_dir}")
                bundle = temp_bundle
            finally:
                shutil.rmtree(temp_root)
            run_written = True
        else:
            bundle = _materialize_run(bundle_runner, root, paths, resolved_run_id, run_dir, classification)
            run_written = True

    if commit_state:
        shutil.copyfile(paths["current_state"], paths["previous_state"])
        shutil.copyfile(run_dir / "state_after.json", paths["current_state"])

    current_summary = _state_summary(paths["current_state"])
    output_files = _output_files(run_dir, run_written)
    report = {
        "schema_version": "v1",
        "task_id": "PMBOT-BRAIN-025-MANUAL-PAPER-WORKSPACE",
        "workflow": "manual_paper_workspace",
        "deterministic": True,
        "run_id": resolved_run_id,
        "workspace_path": str(paths["workspace"]),
        "inbox_path": str(paths["inbox"]),
        "current_state_path": str(paths["current_state"]),
        "run_directory_path": str(run_dir) if run_written else None,
        "run_artifacts_written": run_written,
        "state_committed": bool(commit_state),
        "output_files": output_files,
        "input_files_discovered": classification["input_count"],
        "valid_snapshot_files_discovered": len(classification["valid_snapshots"]),
        "snapshot_files_discovered": bundle["snapshot_files_discovered"],
        "snapshots_processed": bundle["snapshots_processed"],
        "snapshots_skipped_already_processed": bundle["snapshots_skipped_already_processed"],
        "quarantine_count": len(classification["quarantine_records"]),
        "quarantine_reason_counts": _reason_counts(classification["quarantine_records"]),
        "quarantine_records": classification["quarantine_records"],
        "new_paper_orders_created": bundle["new_paper_orders_created"],
        "duplicate_orders_blocked": bundle["duplicate_orders_blocked"],
        "risk_limit_orders_blocked": bundle["risk_limit_orders_blocked"],
        "open_positions_after_run": bundle["open_positions_after_run"],
        "settled_positions_after_run": bundle["settled_positions_after_run"],
        "exposure_before": bundle["before_exposure"],
        "exposure_after_run": bundle["exposure_after_run"],
        "realized_paper_pnl_delta": bundle["realized_paper_pnl_delta"],
        "final_realized_paper_pnl": bundle["final_realized_paper_pnl"],
        "current_state_after_command": current_summary,
        "offline_only": bundle["offline_only"],
        "paper_only": bundle["paper_only"],
        "live_fetcher_implemented": bundle["live_fetcher_implemented"],
        "execution_allowed": bundle["execution_allowed"],
        "trading_allowed": bundle["trading_allowed"],
        "real_order_created": bundle["real_order_created"],
        "wallet_used": bundle["wallet_used"],
        "api_used": bundle["api_used"],
        "network_used": bundle["network_used"],
    }
    return report


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    try:
        report = build_manual_paper_workspace(
            root,
            args.workspace,
            args.run_id,
            args.write_run,
            args.commit_state,
            args.allow_identical_rerun,
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
