# PMBOT Paper Trading Dashboard

## Intent candidates

- Paper intents: 6
- `563650` `simulated_entry` `track_yes` - SCOTUS accepts sports event contract case by July 31, 2026?
- `573656` `observe_only` `no_action` - Will Bitcoin hit $150k by December 31, 2026?
- `597964` `observe_only` `no_action` - Macron out by June 30, 2026?
- `598936` `observe_only` `no_action` - Will the next UK election be called by June 30, 2026?
- `691547` `simulated_entry` `track_yes` - Kraken IPO by December 31, 2026?
- `692258` `observe_only` `no_action` - MicroStrategy sells any Bitcoin by June 30, 2026?

## Risk gate results

- Allowed: 6
- Blocked: 0
- `563650` `allowed_for_paper_simulation`
- `573656` `allowed_for_paper_simulation`
- `597964` `allowed_for_paper_simulation`
- `598936` `allowed_for_paper_simulation`
- `691547` `allowed_for_paper_simulation`
- `692258` `allowed_for_paper_simulation`

## Simulated executions

- Simulated results: 6
- Paper fixture fills: 2
- Skipped: 4
- Rejected: 0
- `563650` `immediate_fill`
- `573656` `skipped`
- `597964` `skipped`
- `598936` `skipped`
- `691547` `immediate_fill`
- `692258` `skipped`

## Paper positions

- Open paper positions: 2
- `563650` `$25.0` unresolved
- `691547` `$25.0` unresolved

## Portfolio exposure

- Total paper capital: `$1000.0`
- Total paper exposure: `$50.0`
- Available paper capital: `$950.0`

## Audit status

- Audit passed: `true`
- Violations: 0
- Warnings: 0

## Next operator actions

- Review the dashboard and audit before treating any paper position as useful state.
- Collect or approve saved public evidence for observe-only markets before future paper simulation.
- Keep all six outcomes unresolved until saved local outcome evidence exists.
- Use the one-shot operator runner for the next explicit local refresh.

## What is still not real trading

- No wallet, signing, order placement, authenticated endpoint, live price, or trading endpoint exists here.
- Paper side labels are tracking labels only and are not real trading instructions.
- Fixture fills exist only to test ledger, portfolio, and audit plumbing.
- Real adapter, kill switch, reconciliation, and manual approval infrastructure remain missing.
