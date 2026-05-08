# PMBOT SOURCE-008 Read-Only Market Rules Capture Pipeline Protocol

- schema_version: market_rules_capture_protocol.v1
- task_id: PMBOT-SOURCE-008-READONLY-MARKET-RULES-CAPTURE-PIPELINE-PROTOCOL
- status: protocol_only_no_network
- current_stage: STAGE_0_PROTOCOL_ONLY
- current_market_count: 14
- network_allowed_explicitly: false
- polymarket_api_calls_performed: 0
- openrouter_calls_performed: 0
- external_network_calls_performed: 0

## Purpose

SOURCE-008 defines the contract for a future read-only market rules and source capture pipeline. It does not fetch data, call APIs, open browsers, read secrets, mutate capture templates, mutate canonical packets, or connect to runtime systems.

## Pipeline Stages

- STAGE 0 - protocol only: current task. No network, API calls, data fetching, browser automation, wallet access, orders, runtime changes, dispatcher changes, background workers, queue mutation, or canonical packet mutation.
- STAGE 1 - one-market read-only discovery: future task only. Requires explicit network approval. Fetch one market only, suggested 597964, from public unauthenticated Polymarket or Gamma metadata.
- STAGE 2 - batch read-only rules capture: future task only. Requires explicit network approval. Fetch only the current 14 market ids and write raw fetched artifacts. No capture template mutation yet.
- STAGE 3 - normalize fetched metadata: future local-only task. Parse question, title, description, rules, resolution source, source references, and end date into normalized candidates. No final operator approval.
- STAGE 4 - auto-fill draft capture templates: future local-only task. Update only empty or not_started templates, set source_capture_status and capture_status to draft only, then run validator, ingest, and readiness export.
- STAGE 5 - operator review: future human review task. Human checks direct Polymarket Rules text and may promote selected captures to ready_for_local_review if appropriate.

## Current Market Set

- 563650
- 569332
- 569333
- 569334
- 569343
- 569344
- 569366
- 569368
- 569373
- 573656
- 597964
- 598936
- 691547
- 692258

## Future Artifact Contracts

- raw fetch schema: `pm_bot/live_readonly/schemas/market_rules_raw_fetch.schema.v1.json`
- normalized candidate schema: `pm_bot/live_readonly/schemas/market_rules_normalized_candidate.schema.v1.json`
- auto-fill plan schema: `pm_bot/live_readonly/schemas/market_rules_auto_fill_plan.schema.v1.json`

## Placeholder CLI

```powershell
python -m pm_bot.live_readonly.market_rules_capture_pipeline --protocol-only
python -m pm_bot.live_readonly.market_rules_capture_pipeline --dry-run --market-id 597964
python -m pm_bot.live_readonly.market_rules_capture_pipeline --dry-run --all-current-markets
```

With `--write`, the CLI writes only protocol status or dry-run plan artifacts. It does not import network client libraries and does not read environment secrets.

## Auto-Fill Guardrails

- only not_started templates are eligible in a future auto-fill task
- planned_status_after_fill: draft
- source_capture_status_after_fill: draft
- capture_status_after_fill: draft
- no ready_for_local_review auto-promotion
- no reviewed auto-promotion
- no canonical packet mutation
- operator review is required

## Required Safety Fields

- network_allowed_explicitly
- polymarket_api_calls_performed
- authenticated_endpoints_used
- wallet_or_private_key_accessed
- orders_created
- trading_runtime_changed
- dispatcher_changed
- background_worker_created
- queue_mutated
- browser_automation_used
- canonical_packets_mutated
- probability_ev_edge_confidence_generated
- side_selection_generated
- market_action_guidance_generated
- operator_review_only
- analysis_only

## Safety Boundary

- no OpenRouter calls
- no Polymarket API calls
- no external network calls
- no authenticated endpoints
- no wallet access
- no private key access
- no orders
- no trading endpoints
- no trading runtime changes
- no dispatcher changes
- no background workers
- no queue mutation
- no browser automation
- no canonical packet mutation
- no buy, sell, hold, enter, exit, probability, EV, edge, confidence, or side selection text
- no market action guidance
