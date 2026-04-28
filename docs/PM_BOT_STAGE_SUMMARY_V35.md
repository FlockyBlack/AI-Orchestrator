# PM Bot Stage Summary V35

## PMBOT-BRAIN-023

Added deterministic offline run ledger artifact output for the local snapshot inbox paper portfolio workflow.

- Command: `python pm_bot\paper\run_local_snapshot_inbox_paper_portfolio.py`
- Run ledger write: `--out-run-ledger <path>`
- Deterministic run ID override: `--run-id <id>`
- Default behavior remains read-only: no state write without `--out-state`, no ledger write without `--out-run-ledger`

## Run Ledger Result

- Run ID tested: `fixture-run-001`
- Snapshot files discovered: 3
- Snapshots skipped already processed: 1
- Snapshots processed: 2
- New paper orders created: 0
- Duplicate orders blocked: 1
- Risk-limit orders blocked: 1
- Realized paper PnL delta: 72.41
- Final realized paper PnL: 72.41
- Snapshot content digests included: true
- Before/after state summaries included: true

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
- `python pm_bot\paper\run_local_snapshot_inbox_paper_portfolio.py`
- `python pm_bot\paper\run_local_snapshot_inbox_paper_portfolio.py --markdown`
- `python pm_bot\paper\run_local_snapshot_inbox_paper_portfolio.py --run-id fixture-run-001 --out-run-ledger pm_bot\paper\expected_local_snapshot_inbox_run_ledger.v1.json`
- `python pm_bot\paper\run_local_snapshot_paper_portfolio_state.py`
- `python pm_bot\paper\run_local_snapshot_series_risk_scenarios.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`
