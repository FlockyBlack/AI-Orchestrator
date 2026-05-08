# PMBOT SOURCE-008 Read-Only Market Rules Capture Pipeline Protocol

SOURCE-008 creates a protocol-only foundation for a future read-only rules/source capture pipeline. This task does not execute the future pipeline.

## Current Scope

- protocol-only
- local artifacts only
- placeholder CLI only
- no network calls
- no Polymarket API calls
- no OpenRouter calls
- no authenticated endpoints
- no browser automation
- no environment secret reads
- no wallet access
- no private key access
- no orders
- no runtime changes
- no dispatcher changes
- no background workers
- no queue mutation
- no canonical packet mutation

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

## Pipeline Stages

- STAGE 0 - protocol only: current task. Defines contracts and dry-run plans only.
- STAGE 1 - one-market read-only discovery: future task only, explicit network approval required, suggested market_id 597964, public unauthenticated Polymarket or Gamma metadata only.
- STAGE 2 - batch read-only rules capture: future task only, explicit network approval required, current 14 market ids only, raw fetched artifacts only.
- STAGE 3 - normalize fetched metadata: future local-only task, parse question, title, description, rules, resolution source, source references, and end date into normalized candidates.
- STAGE 4 - auto-fill draft capture templates: future local-only task, update only empty or not_started templates, set source_capture_status and capture_status to draft only, run validator plus SOURCE-005 ingest and SOURCE-006 readiness export.
- STAGE 5 - operator review: future human review task, direct Polymarket Rules text must be checked before any capture can become ready_for_local_review.

## Artifact Contracts

- `pm_bot/live_readonly/schemas/market_rules_raw_fetch.schema.v1.json`
- `pm_bot/live_readonly/schemas/market_rules_normalized_candidate.schema.v1.json`
- `pm_bot/live_readonly/schemas/market_rules_auto_fill_plan.schema.v1.json`

## Placeholder CLI

```powershell
python -m pm_bot.live_readonly.market_rules_capture_pipeline --protocol-only
python -m pm_bot.live_readonly.market_rules_capture_pipeline --dry-run --market-id 597964
python -m pm_bot.live_readonly.market_rules_capture_pipeline --dry-run --all-current-markets
```

With `--write`, the CLI writes only protocol status or dry-run plan artifacts:

- `pm_bot/live_readonly/market_rules_capture_protocol_status.v1.json`
- `pm_bot/live_readonly/market_rules_capture_protocol_status.v1.md`
- `pm_bot/live_readonly/market_rules_capture_dry_run_plan.v1.json`
- `pm_bot/live_readonly/market_rules_capture_dry_run_plan.v1.md`

## Draft-Only Gate

- only not_started templates can be future auto-fill targets
- planned_status_after_fill must be draft
- source_capture_status after future fill must be draft
- capture_status after future fill must be draft
- no ready_for_local_review auto-promotion
- no reviewed auto-promotion
- no canonical packet mutation
- operator review is required

## Safety Boundary

- no buy, sell, hold, enter, exit, probability, EV, edge, confidence, or side selection text
- no market action guidance
- no trading authority
- no execution authority
- no wallet or order authority
- no runtime authority
- no dispatcher authority
- no background worker authority
- no queue authority
- no browser automation authority
