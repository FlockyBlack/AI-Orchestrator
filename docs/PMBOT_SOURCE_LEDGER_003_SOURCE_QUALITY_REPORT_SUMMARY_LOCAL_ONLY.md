# PMBOT Source Ledger 003 Source Quality Report Summary

Task: `PMBOT-SOURCE-LEDGER-003-SOURCE-QUALITY-REPORT-SUMMARY-LOCAL-ONLY`

## What Changed

- Added a local source quality report summary builder in `pm_bot/source_quality/source_quality_report_summary.py`.
- Added deterministic JSON and Markdown sample artifacts under `pm_bot/source_quality/samples/`.
- Added focused tests for deterministic output, static sample parity, CLI artifact writing, count drift rejection, operator review status enforcement, and blocked scoring/action fields.

## Summary Contract

Report summaries use contract version `pmbot_source_quality_report_summary.v1`.

Input:

- a JSON source quality ledger with contract version `pmbot_unified_source_quality_ledger.v1`

The builder checks:

- the input ledger validates as a local unified source quality ledger
- local-only safety boundaries remain closed
- every report row remains pending operator review
- summary counts match the row totals
- output remains descriptive source artifact inventory only

## CLI

```powershell
python -m pm_bot.source_quality.source_quality_report_summary `
  --ledger pm_bot\source_quality\samples\unified_source_quality_ledger.fixture.json `
  --output-summary <local-output-path>.json `
  --output-report <local-output-path>.md
```

The command writes:

- a JSON report summary with source row counts, declared field totals, review check totals, and limitation totals
- a Markdown operator report summarizing the same local review surface

## Operator Review Boundary

The report summary is a local inspection artifact. It condenses source quality ledger rows for operator review and keeps source artifact identity, local references, declared fields, and review status visible.

Operators must keep source disputes and any final outcome record separate from this summary.

## Safety

- Local-only fixture/static artifact input.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet, order, trading endpoint, or payment path.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No market scoring metrics, stance selection, or trade action guidance.
- The report summary is not trading approval and is not runtime input.
