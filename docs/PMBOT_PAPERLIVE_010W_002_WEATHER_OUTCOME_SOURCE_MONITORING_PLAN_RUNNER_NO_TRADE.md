# PMBOT Paperlive 010W 002 Weather Outcome Source Monitoring Plan Runner

Task: `PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE`

## What Changed

- Added a local weather source monitoring plan contract in `pm_bot/weather/source_monitoring_plan_runner.py`.
- Added a deterministic plan runner that reads a local JSON plan and writes an operator review report.
- Added static fixtures under `pm_bot/tests/fixtures/`.
- Added focused tests for the valid plan, deterministic report output, CLI behavior, local source enforcement, unknown source rejection, and blocked scoring/action fields.

## Plan Contract

Plans use contract version `pmbot_weather_source_monitoring_plan.v1`.

Required fields:

- `contract_version`
- `plan_id`
- `scope`
- `local_only`
- `operator_review_required`
- `sources`
- `outcome_checks`

Optional field:

- `market_context`

Each source must identify a local fixture or static artifact. Network-like source references are rejected.

Each outcome check must name existing source ids, evidence fields, and operator review steps. The runner assembles the checklist only; it does not decide the weather outcome.

## CLI

```powershell
python -m pm_bot.weather.source_monitoring_plan_runner `
  --plan pm_bot\tests\fixtures\weather_source_monitoring_plan.valid.json `
  --output <local-output-path>
```

The command writes a JSON report with contract version `pmbot_weather_source_monitoring_run.v1`.

## Operator Review Boundary

The run report is a local review checklist. It inventories source snapshots and evidence fields, then marks each source and monitoring item as `pending_operator_review`.

The operator must review source identity, target date, target station, and evidence completeness outside this runner before recording any final weather outcome elsewhere.

## Safety

- Local-only fixture/static artifact input.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet, order, trading endpoint, or payment path.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No market scoring metrics, stance selection, or trade action guidance.
- The report is not trading approval and is not runtime input.
