# PMBOT Manual Command Contract Examples

These examples define inert local command records for human review only. They are not a Telegram bot, dispatcher, command executor, order engine, scoring layer, or trading interface.

## Contract Boundaries

- Command records do not execute actions.
- Command records do not place orders.
- Command records do not select sides, prices, sizes, outcomes, or markets.
- Command records do not calculate probability, EV, edge, score, rank, truth, or recommendations.
- Command records do not call APIs, read credentials, load wallet keys, open webhooks, or start polling.
- Telegram wording is limited to static transcript placeholders.
- Runtime use requires a later explicit approved implementation.

## Allowed Command Types

- `request_status_summary`
- `request_dashboard_state_export`
- `record_manual_review_note`
- `record_manual_paper_intent_reference`
- `request_artifact_pointer`
- `mark_needs_human_review`

## Allowed Source Types

- `manual_json`
- `manual_markdown`
- `telegram_transcript_placeholder`

## Forbidden Source Types

- `telegram_live_bot`
- `webhook`
- `polling_runtime`
- `authenticated_api`

## Local Validation

Validate the fixture examples with:

```powershell
python pm_bot\operator\validate_manual_command_contract.py pm_bot\operator\manual_command_examples.v1.json --examples
```

Validate one local command record with:

```powershell
python pm_bot\operator\validate_manual_command_contract.py path\to\command.json
```

The validator only reads local JSON files and reports validation results. It does not dispatch, execute, call a network service, or mutate PMBOT runtime state.
