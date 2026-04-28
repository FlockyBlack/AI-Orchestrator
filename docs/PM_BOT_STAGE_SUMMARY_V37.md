# PM Bot Stage Summary V37

## PMBOT-BRAIN-025

Added deterministic offline manual paper workspace command around the existing inbox bundle workflow.

- Command: `python pm_bot\paper\run_manual_paper_workspace.py`
- Default workspace: `pm_bot\paper\manual_paper_workspace`
- Default behavior: read-only preview, no run folder, no state mutation
- `--write-run`: writes `runs/<run_id>/state_before.json`, `state_after.json`, `run_ledger.json`, and `run_summary.md`
- `--commit-state`: writes run artifacts and promotes `state_after.json` to `state/current_state.json`
- Existing run IDs fail cleanly unless `--allow-identical-rerun` is provided

## Workspace Result

- Run artifacts write tested: true
- State commit tested: true
- Snapshot files discovered: 3
- Snapshots skipped already processed: 1
- Snapshots processed: 2
- New paper orders created: 0
- Duplicate orders blocked: 1
- Risk-limit orders blocked: 1
- Open positions after run: 0
- Settled positions after run: 1
- Exposure after run: 0.00
- Realized paper PnL delta: 72.41
- Final realized paper PnL: 72.41

## Safety

- Offline only: true
- Paper only: true
- Live fetcher implemented: false
- API used: false
- Network used: false
- Wallet used: false
- Real order created: false
- Trading allowed: false
- Runtime wiring changed: false
- Dispatcher touched: false
- Prompt automation added: false

## Checks

- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\paper\run_manual_paper_workspace.py`
- `python pm_bot\paper\run_manual_paper_workspace.py --markdown`
- `python pm_bot\paper\run_manual_paper_workspace.py --run-id fixture-run-001 --write-run`
- `python pm_bot\paper\run_manual_paper_workspace.py --run-id fixture-run-002 --commit-state`
- `python pm_bot\paper\run_manual_paper_inbox_bundle.py`
- `python pm_bot\paper\run_local_snapshot_inbox_paper_portfolio.py`
- `python pm_bot\paper\run_local_snapshot_series_risk_scenarios.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`
