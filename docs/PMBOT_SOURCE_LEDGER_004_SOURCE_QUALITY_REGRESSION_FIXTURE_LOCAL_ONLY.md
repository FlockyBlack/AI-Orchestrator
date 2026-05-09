# PMBOT Source Ledger 004 Source Quality Regression Fixture

Task: `PMBOT-SOURCE-LEDGER-004-SOURCE-QUALITY-REGRESSION-FIXTURE-LOCAL-ONLY`

## What Changed

- Added a local source quality regression fixture builder in `pm_bot/source_quality/source_quality_regression_fixture.py`.
- Added a deterministic JSON sample artifact at `pm_bot/source_quality/samples/source_quality_regression.fixture.json`.
- Added focused tests for static sample parity, deterministic build identity, validation drift rejection, operator review state enforcement, and CLI artifact writing.

## Fixture Contract

Regression fixtures use contract version `pmbot_source_quality_regression_fixture.v1`.

Input:

- a JSON source quality ledger with contract version `pmbot_unified_source_quality_ledger.v1`
- a JSON source quality report summary with contract version `pmbot_source_quality_report_summary.v1`

The builder checks:

- both inputs validate under the existing local source quality contracts
- the report summary references the ledger build
- source artifact totals, declared field totals, present field totals, missing field totals, warning totals, and row identities remain aligned
- all regression rows remain pending operator review
- local-only safety boundaries remain closed

## CLI

```powershell
python -m pm_bot.source_quality.source_quality_regression_fixture `
  --ledger pm_bot\source_quality\samples\unified_source_quality_ledger.fixture.json `
  --report-summary pm_bot\source_quality\samples\source_quality_report_summary.fixture.json `
  --output-fixture <local-output-path>.json
```

The command writes a deterministic JSON fixture that captures cross-artifact invariants for repeatable local review.

## Operator Review Boundary

The fixture is a descriptive regression artifact. It records static sample references, row alignment, field totals, review assertion parity, and pending review status.

Operators must keep source disputes and any final outcome record separate from this fixture.

## Safety

- Local-only fixture/static artifact input.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet, order, trading endpoint, payment, runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No market ranking metrics, stance choice, or trade instruction output.
- The fixture is not trading approval and is not runtime input.
