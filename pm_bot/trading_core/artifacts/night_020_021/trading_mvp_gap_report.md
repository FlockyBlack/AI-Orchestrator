# PMBOT Trading MVP Gap Report

## What now works

- local paper trade intent candidate generation from practical artifacts
- paper risk limits and risk gate checks
- paper execution simulation with explicit fixture fills
- paper position ledger and portfolio exposure state
- post-execution consistency audit
- paper trading dashboard and safety scan
- one-shot local operator runner boundary

## What is still simulated

- paper side labels
- fixture fill price
- paper position units
- paper portfolio capital and exposure accounting
- all execution results

## What is missing before supervised real trading

- separate explicit approval task
- real data adapter design
- wallet isolation design
- signing isolation design
- disabled real execution adapter boundary
- kill switch
- post-order reconciliation
- manual approval workflow
- risk engine upgrade

## Risk engine gaps

- no dynamic volatility or liquidity cap
- no per-market halt state
- no real price validation
- no stale-data enforcement beyond local evidence completeness

## Kill switch gaps

- no global runtime halt control
- no adapter-level emergency stop
- no reconciliation-triggered halt

## Wallet isolation gaps

- no wallet module exists
- no signing module exists
- no key isolation design is approved

## Real execution adapter gaps

- no order adapter exists
- no authenticated endpoint is implemented
- no idempotency or order-state reconciliation exists

## Reconciliation gaps

- no external fill reconciliation
- no cash/share reconciliation
- no exception queue for mismatched state

## Approval gaps

- operator review is recorded as required but no approval UI exists
- no dual-control approval record exists
- no real-trade approval workflow is implemented
