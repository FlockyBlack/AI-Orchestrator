# PMBOT Paperlive 010W 003 Weather Observation Refresh Ledger

Task: `PMBOT-PAPERLIVE-010W-003-WEATHER-OBSERVATION-REFRESH-LEDGER-NO-TRADE`

## What Changed

- Added a local weather observation ledger refresh contract in `pm_bot/weather/observation_ledger_refresher.py`.
- Added deterministic static weather observation snapshot fixtures under `pm_bot/tests/fixtures/weather/`.
- Added a refresh request fixture that maps named snapshot fields into ledger records.
- Added focused tests for deterministic ledger output, CLI artifacts, local path enforcement, missing snapshot fields, and blocked scoring/action fields.

## Refresh Contract

Refresh requests use contract version `pmbot_weather_observation_ledger_refresh_request.v1`.

Required fields:

- `contract_version`
- `ledger_id`
- `scope`
- `local_only`
- `operator_review_required`
- `source_snapshots`
- `record_specs`
- `operator_review_steps`

Optional field:

- `market_context`

Each source snapshot must identify a relative local fixture/static artifact path under an allowed fixture/static path. Network-like references and path traversal are rejected.

Each record spec names the source id, snapshot field names, measurement name, unit, and operator review label. The refresher copies only those named fields from the local snapshot into a ledger record.

## CLI

```powershell
python -m pm_bot.weather.observation_ledger_refresher `
  --request pm_bot\tests\fixtures\weather_observation_ledger_refresh_request.valid.json `
  --output-ledger <local-output-path>.json `
  --output-report <local-output-path>.md
```

The command writes:

- a JSON ledger with contract version `pmbot_weather_observation_ledger.v1`
- a Markdown operator report summarizing the refresh and review steps

## Operator Review Boundary

The refreshed ledger is a local observation artifact. Each record is marked `pending_operator_review`.

The operator must review snapshot identity, station, date, and copied fields before using the ledger in any downstream human process. Any weather outcome review remains outside this refresher.

## Safety

- Local-only fixture/static artifact input.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet, order, trading endpoint, or payment path.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No market scoring metrics, stance selection, or trade action guidance.
- The ledger and Markdown report are not trading approval and are not runtime input.
