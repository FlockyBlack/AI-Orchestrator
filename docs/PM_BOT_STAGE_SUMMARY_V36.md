# PM Bot Stage Summary V36

## PMBOT-BRAIN-024

Added deterministic offline manual paper run bundle output for the local snapshot inbox portfolio workflow.

- Command: `python pm_bot\paper\run_manual_paper_inbox_bundle.py`
- Optional bundle output directory: `--out-dir <dir>`
- Deterministic run ID override: `--run-id <id>`
- Default behavior remains read-only: no files are written unless `--out-dir` is provided
- Bundle files: `state_after.json`, `run_ledger.json`, `run_summary.md`

## Bundle Result

- Run ID tested: `fixture-run-001`
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
- `python pm_bot\paper\run_manual_paper_inbox_bundle.py`
- `python pm_bot\paper\run_manual_paper_inbox_bundle.py --markdown`
- `python pm_bot\paper\run_manual_paper_inbox_bundle.py --run-id fixture-run-001 --out-dir pm_bot\paper\manual_paper_run_fixture_output`
- `python pm_bot\paper\run_local_snapshot_inbox_paper_portfolio.py`
- `python pm_bot\paper\run_local_snapshot_paper_portfolio_state.py`
- `python pm_bot\paper\run_local_snapshot_series_risk_scenarios.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`
