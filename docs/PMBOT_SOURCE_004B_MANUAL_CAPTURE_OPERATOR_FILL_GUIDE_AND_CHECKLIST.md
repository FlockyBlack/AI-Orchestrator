# PMBOT SOURCE-004B Manual Capture Operator Fill Guide And Checklist

## Executive Summary

SOURCE-004B adds a local-only operator fill guide, checklist, progress summary, validator UX improvements, and static workbench pointers for the SOURCE-004 manual resolution/source capture templates.

Current capture state remains unchanged: 14 templates are `not_started`, 0 are `draft`, 0 are `ready_for_local_review`, 0 are `reviewed`, and 0 are `needs_revision`. No template was filled with external data, no sources were fetched, and no market was approved.

## Why SOURCE-004B Was Needed

SOURCE-004 created the capture schema, 14 JSON templates, 14 Markdown companions, a manifest, and validation. SOURCE-004B makes those templates easier and safer for a human operator to fill by answering which files to open, which fields to fill first, how to move statuses, how to run validation, and what content must stay out of local artifacts.

## Artifacts Created

- Operator fill guide: `docs/PMBOT_SOURCE_004B_MANUAL_CAPTURE_OPERATOR_FILL_GUIDE.md`
- Operator checklist JSON: `pm_bot/llm/manual_resolution_source_capture_operator_checklist.v1.json`
- Operator checklist Markdown: `pm_bot/llm/manual_resolution_source_capture_operator_checklist.v1.md`
- Progress JSON: `pm_bot/llm/manual_resolution_source_capture_progress.v1.json`
- Progress Markdown: `pm_bot/llm/manual_resolution_source_capture_progress.v1.md`
- Result JSON: `docs/PMBOT_SOURCE_004B_RESULT.json`

## How The Operator Should Fill Templates

Open the market JSON template in `pm_bot/llm/manual_resolution_source_capture/` and use its Markdown companion plus the SOURCE-004B checklist. Fill fields in this order:

1. `full_market_resolution_criteria_text`
2. `full_resolution_rules`
3. `official_source_references`
4. `official_source_urls_or_rule_references`
5. `source_timestamps`
6. `source_reliability_review`
7. `reviewed_local_evidence_references`
8. `non_placeholder_evidence_notes`

Move a template from `not_started` to `draft` only after adding substantive local operator source input. Move it to `ready_for_local_review` only after the priority fields are filled, source timing and reliability notes are present, local evidence references are recorded, no-authority flags remain true, and validation passes.

If source data is missing, leave unknown fields blank in `not_started` or `draft`, add specific `unresolved_source_questions`, and do not invent source references, URLs, criteria, rules, timestamps, or reliability conclusions.

## Current Capture Status

- total_templates: 14
- not_started_count: 14
- draft_count: 0
- ready_for_local_review_count: 0
- reviewed_count: 0
- needs_revision_count: 0
- validation_valid_count: 14
- validation_invalid_count: 0

## Validation Command

```powershell
python -m pm_bot.llm.manual_resolution_source_capture_validator --write
```

Optional local views:

```powershell
python -m pm_bot.llm.manual_resolution_source_capture_validator --summary-only
python -m pm_bot.llm.manual_resolution_source_capture_validator --market-id 563650
python -m pm_bot.llm.manual_resolution_source_capture_validator --strict-ready --summary-only
```

## Workbench Updates

The static workbench dashboard, review pack, and export run artifacts now point to:

- guide path
- checklist path
- progress path
- manifest path
- validation path
- total template count
- current status counts
- top fields to fill
- validation command
- next operator action

The workbench remains static and local. No runtime UI, web server, queue item, dispatcher change, background worker, browser automation, wallet access, order handling, or live API path was added.

## Limitations

- The templates are still empty operator templates.
- No real source data was fetched, captured, invented, or approved.
- Validation confirms structure and safety rules only; it does not confirm factual completeness.
- Manual capture improves evidence completeness only and does not approve future live calls.
- Later readiness scoring requires a separate ingest task after a human fills and reviews templates.

## Next Recommended Tasks

Option A: `PMBOT-SOURCE-005-MANUAL-CAPTURE-INGEST-FROM-FILLED-TEMPLATES`

Purpose: after operator fills templates, ingest `ready_for_local_review` or `reviewed` capture data into readiness scoring.

Option B: `PMBOT-SOURCE-006-SOURCE-GAP-NORMALIZATION`

Purpose: normalize source gap notes and reliability fields after manual input.

Option C: `PMBOT-SOURCE-007-UNREVIEWED-PACKET-CHECKLIST-RISK-CONTEXT-BUILDER`

Purpose: improve checklist, risk, and contradiction sections for the 4 unreviewed packets.

Option D: `PMBOT-OPENROUTER-054-REPEAT-N5-READINESS-PROTOCOL-AFTER-SOURCE-GATE`

Purpose: protocol-only repeat N=5 readiness after manual capture review, no live calls.

These are documented as possible future tasks only. SOURCE-004B does not run or approve them.

## Safety Statement

- no OpenRouter calls
- no Polymarket API calls
- no network calls
- no trading
- no wallet/orders
- no runtime/dispatcher/background/browser/queue changes
- no API key access
- no market recommendations
- no probability/EV/edge/confidence/side selection
