# PMBOT SOURCE-008B Market Class Pilot Protocol

SOURCE-008B adds a protocol-only market-class pilot layer for future source capture work. The first classes are esports, weather, and crypto, and the future testing order is fixed in that same order.

## Scope

- protocol-only
- local artifacts only
- placeholder CLI only
- no network calls
- no Polymarket API calls
- no OpenRouter calls
- no authenticated endpoints
- no wallet or private key access
- no orders
- no runtime wiring
- no dispatcher changes
- no background workers
- no queue mutation
- no browser automation
- no canonical packet mutation

## Artifacts

- `pm_bot/llm/market_class_pilot_taxonomy.v1.json`
- `pm_bot/llm/market_class_pilot_taxonomy.v1.md`
- `pm_bot/llm/market_class_pilot_selection_criteria.v1.json`
- `pm_bot/llm/market_class_pilot_selection_criteria.v1.md`
- `pm_bot/llm/market_class_pilot_candidate_contract.v1.json`
- `pm_bot/llm/market_class_source_capture_candidate_contract.v1.json`
- `pm_bot/llm/market_class_operator_review_contract.v1.json`
- `pm_bot/llm/market_class_pilot_pipeline.py`
- `pm_bot/llm/market_class_pilot_protocol_status.v1.json`
- `pm_bot/llm/market_class_pilot_protocol_status.v1.md`
- `pm_bot/llm/market_class_pilot_dry_run_plan.v1.json`
- `pm_bot/llm/market_class_pilot_dry_run_plan.v1.md`

## CLI

```powershell
python -m pm_bot.llm.market_class_pilot_pipeline --protocol-only
python -m pm_bot.llm.market_class_pilot_pipeline --dry-run --class esports
python -m pm_bot.llm.market_class_pilot_pipeline --dry-run --class weather
python -m pm_bot.llm.market_class_pilot_pipeline --dry-run --class crypto
python -m pm_bot.llm.market_class_pilot_pipeline --write --all-classes
```

The CLI imports only local standard-library modules used for argument parsing, JSON, and filesystem paths. It writes only protocol status and dry-run plan artifacts.

## Selection Criteria

- prefer clear resolution wording
- prefer identifiable official source
- prefer near/mid-term markets
- avoid ambiguous/meme/private-person/legal/medical rumor-driven markets for first pilots
- order: esports, weather, crypto

## State Preservation

SOURCE-007 and SOURCE-008 state remains unchanged:

- real_ingested_template_count: 1
- draft_ingested_template_count: 1
- ready_ingested_template_count: 0
- future_live_002_allowed: false

## Safety Boundary

- no probability, EV, edge, confidence, side selection, trade recommendation, buy, sell, hold, enter, exit, guaranteed win, free money, or sure bet labels
- no market action guidance
- no trading authority
- no execution authority
- no wallet or order authority
- no runtime authority
- no dispatcher authority
- no background worker authority
- no queue authority
- no browser automation authority
