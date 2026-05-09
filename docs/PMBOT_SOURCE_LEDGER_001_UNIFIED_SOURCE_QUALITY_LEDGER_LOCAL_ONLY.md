# PMBOT Source Ledger 001 Unified Source Quality Ledger

Task: `PMBOT-SOURCE-LEDGER-001-UNIFIED-SOURCE-QUALITY-LEDGER-LOCAL-ONLY`

## What Changed

- Added a local source-quality ledger builder in `pm_bot/source_quality/unified_source_quality_ledger.py`.
- Added a deterministic fixture request under `pm_bot/tests/fixtures/source_quality/`.
- Added a static sample output under `pm_bot/source_quality/samples/`.
- Added focused tests for deterministic output, CLI artifact writing, local path enforcement, missing fields, and blocked scoring/action fields.

## Ledger Contract

Requests use contract version `pmbot_unified_source_quality_ledger_request.v1`.

Required fields:

- `contract_version`
- `ledger_id`
- `scope`
- `local_only`
- `operator_review_required`
- `source_artifacts`
- `operator_review_steps`

Each source artifact must identify a relative local fixture or static artifact path under an allowed local path. Network-like references, path traversal, forbidden operational paths, and undeclared local scopes are rejected.

Each source artifact lists declared fields, review checks, and known limitations. The builder verifies the declared fields exist in the local JSON artifact and emits descriptive review rows only.

## CLI

```powershell
python -m pm_bot.source_quality.unified_source_quality_ledger `
  --request pm_bot\tests\fixtures\source_quality\unified_source_quality_ledger_request.valid.json `
  --output-ledger <local-output-path>.json `
  --output-report <local-output-path>.md
```

The command writes:

- a JSON ledger with contract version `pmbot_unified_source_quality_ledger.v1`
- a Markdown operator report summarizing the same local review surface

## Operator Review Boundary

The ledger is a descriptive local review artifact. It inventories local source artifacts, declared fields, field presence, limitations, and review prompts.

It does not resolve outcomes, rank sources, provide market guidance, or approve runtime use. Operators must review source disputes outside this ledger.

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
