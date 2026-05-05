# Manual Snapshot Workspace Import

- Source: /pm_bot/paper/manual_snapshot_import_source
- Workspace: /pm_bot/paper/manual_paper_workspace
- Inbox: /pm_bot/paper/manual_paper_workspace/inbox
- Write inbox: false
- Manifest path: 
- Manifest written: false
- Inputs discovered: 7
- Importable snapshots: 2
- Imported snapshots: 0
- Skipped/quarantined inputs: 5
- Reason counts: {"already_present_in_workspace_inbox": 1, "duplicate_snapshot_id_in_source_batch": 1, "ignored_non_json_file": 1, "malformed_json": 1, "unsupported_snapshot_shape": 1}

## Importable

- 001_series_snapshot_004.json: series_snapshot_004 -> 004_series_snapshot_004.json written=false
- 002_series_snapshot_005.json: series_snapshot_005 -> 005_series_snapshot_005.json written=false

## Skipped And Quarantined

- 003_duplicate_series_snapshot_004.json: skipped duplicate_snapshot_id_in_source_batch (No inbox file written.)
- 004_already_present_series_snapshot_002.json: skipped already_present_in_workspace_inbox (No inbox file written.)
- 005_malformed.json: quarantined malformed_json (No inbox file written.)
- 006_unsupported.json: quarantined unsupported_snapshot_shape (No inbox file written.)
- 007_operator_note.txt: skipped ignored_non_json_file (Ignored before import.)

## Output Inbox Files

- None written

## Safety

- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; prompt_automation_added=false
