# PMBOT Paperlive 010W 005 Weather Operator Review Surface

Task: `PMBOT-PAPERLIVE-010W-005-WEATHER-OPERATOR-REVIEW-SURFACE-UPDATE-NO-TRADE`

## What Changed

- Added a local weather operator review surface contract in `pm_bot/weather/operator_review_surface.py`.
- Added deterministic JSON and Markdown output builders that combine a local observation ledger with a local reconciliation record.
- Added cross-artifact validation so reconciliation inventory and referenced records must match the ledger records they cite.
- Added focused tests for deterministic output, CLI artifact writing, local path rejection, cross-artifact mismatch rejection, and blocked scoring/selection fields.

## Surface Contract

Review surfaces use contract version `pmbot_weather_operator_review_surface.v1`.

Inputs:

- a JSON weather observation ledger with contract version `pmbot_weather_observation_ledger.v1`
- a JSON weather outcome reconciliation record with contract version `pmbot_weather_outcome_reconciliation_record.v1`

The builder checks:

- both inputs are local-only and operator-review-gated
- input safety boundaries remain closed for network, LLM, market API, wallet/order, runtime, scheduler, and trade guidance paths
- reconciliation inventory records match ledger records on source, snapshot, station, date, value, unit, timestamp, and review status
- reconciliation referenced records match the same ledger records
- automated outcome status remains `not_performed`

## CLI

```powershell
python -m pm_bot.weather.operator_review_surface `
  --ledger <local-weather-observation-ledger>.json `
  --reconciliation-record <local-weather-reconciliation-record>.json `
  --output-surface <local-output-path>.json `
  --output-report <local-output-path>.md
```

The command writes:

- a JSON review surface with ledger record panels, record link panels, and reconciliation review panels
- a Markdown operator report summarizing the same inspection surface

## Operator Review Boundary

The review surface is a local inspection artifact. It makes ledger records and reconciliation records easier to inspect together, but it does not set a final weather outcome.

Operators must keep any final weather outcome record separate from this artifact.

## Safety

- Local-only fixture/static artifact input.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet, order, trading endpoint, or payment path.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No market scoring metrics, stance selection, or trade action guidance.
- The review surface and Markdown report are not trading approval and are not runtime input.
