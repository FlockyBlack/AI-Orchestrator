# PAPER-011 Fill Source Contract

- task_id: PMBOT-PAPER-BATCH-011-013-FILL-SETTLEMENT-PNL-MVP
- source_manual_paper_intent_ledger_path: pm_bot/paper/manual_paper_intent_ledger.v1.json
- source_paper_workbench_preview_path: pm_bot/paper/paper_workbench_preview.v1.json
- market_ids: 824952
- fixture_records: 3

## Allowed Fill Source Types

- operator_manual_fill_fixture
- no_fill_source_available
- blocked_by_policy

## Required Fields

- fill_source_id
- market_id
- source_manual_intent_id
- source_ledger_entry_id
- fill_source_type
- operator_manual_fill_status
- operator_manual_fill_price
- operator_manual_fill_size
- operator_manual_fill_notes
- paper_only
- inert_only
- generated_by_bot
- live_order_created
- real_order_created

## Safety

- Contract requires local operator manual fill fixture fields only.
- Contract requires paper_only true and inert_only true.
- Contract requires generated_by_bot false, live_order_created false, and real_order_created false.
- Contract has no external data requirement.
