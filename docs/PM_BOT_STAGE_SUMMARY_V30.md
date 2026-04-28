# PM Bot Stage Summary V30

Status: `local_snapshot_series_paper_portfolio_ready_for_review`

`PMBOT-BRAIN-018-LOCAL-SNAPSHOT-SERIES-PAPER-PORTFOLIO` adds a deterministic fixture-only replay of repeated local live-shaped snapshot reviews into a carried paper portfolio.

Run JSON:

```powershell
python pm_bot\paper\run_local_snapshot_series_paper_portfolio.py
```

Run Markdown:

```powershell
python pm_bot\paper\run_local_snapshot_series_paper_portfolio.py --markdown
```

## Replay Scope

- reads `pm_bot\paper\local_snapshot_series_fixture.v1.json`
- processes snapshots in chronological order
- adapts each live-shaped snapshot into raw market records
- runs intake, scoring, review table, and paper order planning per snapshot
- carries open paper positions forward across snapshots
- blocks duplicate paper orders for an existing market/side position
- applies fixture settlement data when it appears
- preserves adapter, intake, and scoring rejections with reasons

## Current Fixture Summary

- snapshots processed: 3
- total snapshot markets: 8
- adapted raw markets: 6
- adapter rejections: 2
- paper orders created: 2
- duplicate orders blocked: 1
- open positions: 0
- settled positions: 2
- total paper notional: 200.00
- max exposure: 200.00
- realized paper PnL: 294.99
- unrealized paper PnL: 0.00
- bad entries: 0
- safety flags locked: true

## Safety Boundary

- offline-only
- paper-only
- no live fetcher implemented
- no network/API
- no credentials
- no wallet/private keys/signing
- no real orders
- no live trading
- no runtime wiring
- no dispatcher/run_codex
- no prompt automation

## Verification

- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\paper\run_local_snapshot_series_paper_portfolio.py`
- `python pm_bot\paper\run_local_snapshot_series_paper_portfolio.py --markdown`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

## Next Step

Add a focused offline regression gate for the local snapshot series portfolio replay summary and safety locks.
