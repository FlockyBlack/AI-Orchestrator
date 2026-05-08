# PMBOT LIVE-001 Read-Only Polymarket API Discovery Protocol

- schema_version: polymarket_readonly_api_discovery_protocol.v1
- task_id: PMBOT-LIVE-001-READONLY-POLYMARKET-API-DISCOVERY-PROTOCOL-ONLY
- status: protocol_only_no_network
- network_allowed_explicitly: false
- polymarket_api_calls_performed: 0
- external_network_calls_performed: 0

## Allowed Future Endpoint Categories

- public read-only market metadata discovery
- public read-only market snapshot fetch
- public read-only orderbook/liquidity snapshot fetch

## Prohibited Scope

- no authenticated endpoints
- no wallet access
- no private key access
- no order creation
- no runtime wiring
- no dispatcher changes
- no background workers
- no queue mutation
- no browser automation
- no market action guidance
- no probability, EV, edge, confidence, or side selection

## Future Task Separation

- LIVE-001: protocol-only, no calls.
- LIVE-002: read-only API discovery dry-run; explicit network approval required.
- LIVE-003: read-only snapshot ingest; explicit network approval required.
- LIVE-004: local packet bridge from read-only snapshots; explicit network approval required.

## Required Before Future LIVE-002

- source/evidence readiness report exists
- manual capture ingest report exists
- at least one real filled capture template is ingested, or an explicit operator override document exists
- safety protocol remains read-only
- tests pass

## Current Status

LIVE-001 is protocol-only. The placeholder command reports local status only:

```powershell
python -m pm_bot.live_readonly.polymarket_readonly_discovery --protocol-only
```

## Safety Boundary

- no OpenRouter calls
- no Polymarket API calls
- no network calls
- no trading authority
- no queue, runtime, dispatcher, background, browser, wallet, or order authority
- no market action guidance
- no probability, EV, edge, confidence, or side selection
