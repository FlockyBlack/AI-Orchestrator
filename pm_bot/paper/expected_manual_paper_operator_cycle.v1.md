# Manual Paper Operator Cycle

- Run ID: manual-paper-operator-cycle-fixture-v1
- Source: <REPO_ROOT>\pm_bot\paper\manual_snapshot_import_source
- Workspace: <REPO_ROOT>\pm_bot\paper\manual_paper_workspace
- Inbox: <REPO_ROOT>\pm_bot\paper\manual_paper_workspace\inbox
- Write inbox: false
- Manifest written: false
- Run artifacts written: false
- State committed: false
- Workspace note: Importable snapshots were previewed but not added to the workspace inbox because --write-inbox was not provided.

## Import Phase

- Inputs discovered: 7
- Importable snapshots: 2
- Imported snapshots: 0
- Skipped/quarantined inputs: 5
- Reason counts: {"already_present_in_workspace_inbox": 1, "duplicate_snapshot_id_in_source_batch": 1, "ignored_non_json_file": 1, "malformed_json": 1, "unsupported_snapshot_shape": 1}

## Workspace Phase

- Input files discovered: 3
- Valid snapshots discovered: 3
- Snapshots discovered: 3
- Snapshots processed: 2
- Snapshots skipped already processed: 1
- Quarantine records: 1
- Quarantine reason counts: {"already_processed_snapshot": 1}
- New paper orders created: 0
- Duplicate orders blocked: 1
- Risk-limit orders blocked: 1
- Before exposure: 100.00
- After exposure: 0.00
- Realized paper PnL delta: 72.41
- Final realized paper PnL: 72.41

## Output Artifacts

- None written

## Safety

- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false
