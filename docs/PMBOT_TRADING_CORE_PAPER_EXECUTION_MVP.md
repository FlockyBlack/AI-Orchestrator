# PMBOT Trading Core Paper Execution MVP

## Scope

This milestone adds a paper-only trading core under `pm_bot/trading_core/`.

The core transforms local practical PMBOT artifacts into:

- paper trade intent candidates
- paper risk gate results
- simulated execution results
- paper position ledger
- paper portfolio state
- post-execution audit
- paper trading dashboard
- future real-adapter boundary
- safety scan

## Paper-only pipeline

The pipeline is deterministic and local:

1. Load six tracked markets and active paper hypotheses.
2. Link saved local public evidence where available.
3. Create one paper intent candidate per market.
4. Apply paper risk limits.
5. Simulate execution only for risk-allowed paper candidates.
6. Create ledger records from simulated fills.
7. Build portfolio exposure.
8. Audit consistency across intent, risk, execution, ledger, and portfolio.
9. Run safety scans.

## Current output

- Paper intents: 6
- Risk allowed: 6
- Risk blocked: 0
- Simulated execution results: 6
- Paper fixture fills: 2
- Skipped observe-only results: 4
- Open paper positions: 2
- Total paper exposure: `$50.0`

## Safety boundary

The trading core does not implement wallet access, signing, orders, authenticated endpoints, live prices, live fetch, OpenRouter, Polymarket API calls, scheduler, daemon, watcher, background worker, polling loop, or real-money execution.

`future_real_adapter_boundary.py` exists only to document what is missing before any supervised real execution milestone can be considered.
