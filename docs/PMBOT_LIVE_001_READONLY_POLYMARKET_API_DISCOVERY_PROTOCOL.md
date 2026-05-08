# PMBOT LIVE-001 Read-Only Polymarket API Discovery Protocol

LIVE-001 creates the future read-only discovery contract only. It performs no network calls and implements no live client.

## Current Scope

- protocol-only
- local artifacts only
- no Polymarket API calls
- no OpenRouter calls
- no external network calls
- no runtime wiring
- no dispatcher changes
- no background workers
- no queue mutation
- no browser automation

## Future Read-Only Categories

- public read-only market metadata discovery
- public read-only market snapshot fetch
- public read-only orderbook/liquidity snapshot fetch

## Future Task Separation

- LIVE-001: protocol-only, no calls.
- LIVE-002: read-only API discovery dry-run; explicit network approval required.
- LIVE-003: read-only snapshot ingest; explicit network approval required.
- LIVE-004: local packet bridge from read-only snapshots; explicit network approval required.

## Required Future Safety Fields

- network_allowed_explicitly
- polymarket_api_calls_performed
- authenticated_endpoints_used
- wallet_or_private_key_accessed
- orders_created
- runtime_wiring_changed
- dispatcher_changed
- background_worker_created
- queue_mutated
- browser_automation_used
- trading_recommendations_generated
- probability_ev_edge_confidence_generated
- side_selection_generated
- operator_review_only
- analysis_only

## Readiness Gate

Future LIVE-002 remains blocked until:

- source/evidence readiness report exists
- manual capture ingest report exists
- at least one real filled capture template is ingested, or an explicit operator override document exists
- the safety protocol remains read-only
- tests pass

## Placeholder Command

The only implemented command is local protocol status:

```powershell
python -m pm_bot.live_readonly.polymarket_readonly_discovery --protocol-only
```

It exits with `protocol_only_no_network`.

## Safety Boundary

- no authenticated endpoints
- no wallet access
- no private key access
- no order creation
- no trading authority
- no market action guidance
- no probability, EV, edge, confidence, or side selection
