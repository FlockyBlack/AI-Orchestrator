# PAPER-012 Paper Fill Simulation From Manual Fixture

- task_id: PMBOT-PAPER-BATCH-011-013-FILL-SETTLEMENT-PNL-MVP
- fill_source_records_accepted: 1
- fill_source_records_rejected: 2
- paper_fill_events_written: 1
- real_orders_created: 0
- live_orders_created: 0

## Accepted Fill Sources

- paper-fill-source-operator-manual-001: market_id=824952 type=operator_manual_fill_fixture

## Rejected Fill Sources

- paper-fill-source-rejected-live-bot: market_id=824952 reasons=generated_by_bot_false_required,live_order_created_false_required,prohibited_or_execution_field_present,unexpected_field_present,blocked_language_present
- paper-fill-source-rejected-unknown-market: market_id=000000 reasons=unknown_market_id,unknown_source_manual_intent_id

## Paper Fill Events

- paper-fill-event-001: market_id=824952 status=paper_fill_recorded_from_operator_manual_fixture fill_price=0.4 fill_size=10

## Safety

- Fill events are generated only from accepted operator manual fill fixtures.
- No real, live, or autonomous paper order artifact is created.
