# PMBOT SOURCE-004B Manual Capture Operator Fill Guide

## Purpose

Manual resolution/source capture is a local-only evidence completeness step for PMBOT operator review. It helps a human operator fill missing resolution criteria, rules, official source references, timestamps, and reliability notes in SOURCE-004 capture templates.

This process improves evidence completeness only. It does not approve trading, actions, queues, runtime behavior, wallets, orders, market decisions, or future live calls.

## Files To Open

Capture templates live in:

- JSON templates: `pm_bot/llm/manual_resolution_source_capture/`
- Markdown companions: `pm_bot/llm/manual_resolution_source_capture/`
- Manifest: `pm_bot/llm/manual_resolution_source_capture_manifest.v1.json`
- Validation report: `pm_bot/llm/manual_resolution_source_capture_validation.v1.json`
- Operator checklist: `pm_bot/llm/manual_resolution_source_capture_operator_checklist.v1.json`
- Progress summary: `pm_bot/llm/manual_resolution_source_capture_progress.v1.json`

Open the JSON file when editing. Use the Markdown companion as a readable checklist.

## Market IDs

- `563650`
- `569332`
- `569333`
- `569334`
- `569343`
- `569344`
- `569366`
- `569368`
- `569373`
- `573656`
- `597964`
- `598936`
- `691547`
- `692258`

## Recommended Fill Order

1. `full_market_resolution_criteria_text`
2. `full_resolution_rules`
3. `official_source_references`
4. `official_source_urls_or_rule_references`
5. `source_timestamps`
6. `source_reliability_review`
7. `reviewed_local_evidence_references`
8. `non_placeholder_evidence_notes`

Fill the highest-priority field first. Do not move a template to `ready_for_local_review` while the first four fields are empty.

## Field Guide

`full_market_resolution_criteria_text`

- Means: the complete local text that defines how the market resolves.
- Good: exact local criteria text, or a faithful operator summary that says where it came from.
- Bad: a guess, prediction, partial headline, unsupported paraphrase, or placeholder.
- If unknown: leave blank while `not_started` or `draft`, and add a specific unresolved source question.

`full_resolution_rules`

- Means: the rule clauses needed to understand valid resolution conditions and edge cases.
- Good: locally reviewed rule text or a neutral summary of all relevant clauses.
- Bad: a short excerpt that omits important conditions, opinion, or unsupported inference.
- If unknown: leave blank in `not_started` or `draft`, and note which rule text is missing.

`official_source_references`

- Means: names of official source documents, systems, publications, or rule sources manually checked by the operator.
- Good: a generic source label such as official rules document, official filing, official results page, or official notice.
- Bad: commentary, social chatter, search snippets, unverifiable claims, or invented source names.
- If unknown: keep the array empty and write the missing-source question in `unresolved_source_questions`.

`official_source_urls_or_rule_references`

- Means: manually verified URLs or rule identifiers already known from local operator review.
- Good: a verified URL string, local document reference, rule identifier, docket identifier, or official source section label.
- Bad: guessed URLs, links not opened by the operator, stale placeholders, or source references invented from memory.
- If unknown: keep the array empty until manually verified. Do not invent a URL.

`source_timestamps`

- Means: when each source was checked or captured.
- Good: local timestamp plus source label, such as a timestamped note that a named local source was checked.
- Bad: no timestamp, future timestamp, copied timestamp from unrelated context, or ambiguous date.
- If unknown: add the timestamp when the operator checks the source.

`source_reliability_review`

- Means: a neutral operator note on whether the cited sources are official, complete, current, and sufficient.
- Good: states why the source is official or names specific unresolved gaps.
- Bad: outcome speculation, certainty language, or a conclusion without source basis.
- If unknown: state that reliability remains unresolved and list what verification is missing.

`reviewed_local_evidence_references`

- Means: repo-relative files, local packet sections, or captured documents the operator actually reviewed.
- Good: local file path plus section label.
- Bad: broad claims like checked sources, external claims not present locally, or unverifiable references.
- If unknown: leave empty until local evidence is reviewed.

`non_placeholder_evidence_notes`

- Means: substantive notes about what the local evidence contains or lacks.
- Good: a concise note describing source coverage, missing fields, contradictions, or pending checks.
- Bad: `TODO`, placeholder text, prediction, recommendation, or market decision text.
- If unknown: after review starts, write a clear missing-data note instead of pretending the field is complete.

## Status Flow

`not_started`

- Use when the template has not received substantive operator source input.
- Empty priority fields are allowed.

`draft`

- Use after the operator starts filling real local source content.
- Some fields may still be incomplete.

`ready_for_local_review`

- Use only after the priority fields are filled, timestamps and reliability notes are present, no-authority flags remain true, and validation passes.
- This status means ready for local human review only.

`reviewed`

- Use only after a separate local review confirms the filled source fields are complete enough for evidence readiness work.
- This still does not approve trading or market actions.

`needs_revision`

- Use when local review finds missing, contradictory, stale, unclear, or unsupported source content.

## Moving From Not Started To Draft

1. Open the market JSON template.
2. Add substantive local operator input to at least one priority field.
3. Keep all no-authority flags set to `true`.
4. Set both `capture_status` and `source_capture_status` to `draft`.
5. Run validation.

Do not move to `draft` just because the file was opened.

## Moving To Ready For Local Review

Before setting both status fields to `ready_for_local_review`, confirm:

- `full_market_resolution_criteria_text` is filled.
- `full_resolution_rules` is filled.
- `official_source_references` has manually verified content.
- `official_source_urls_or_rule_references` has manually verified content or a rule reference.
- `source_timestamps` records source check timing.
- `source_reliability_review` explains reliability or remaining gaps.
- `reviewed_local_evidence_references` points to local evidence reviewed.
- `non_placeholder_evidence_notes` is substantive.
- `unresolved_source_questions` does not hide a blocker.
- No forbidden market-action language is present.
- Validation passes.

## If Source Data Is Missing

- Do not invent criteria, rules, sources, URLs, timestamps, or reliability conclusions.
- Leave unknown fields blank while `not_started` or `draft`.
- Record specific missing items in `unresolved_source_questions`.
- Use `manual_operator_notes` for neutral process notes.
- Use `needs_revision` if a packet was reviewed and the missing source data blocks review readiness.

## What Must Not Be Written

- no predictions
- no trading recommendations
- no probability
- no EV
- no edge
- no confidence score
- no side selection
- no buy/sell/hold/enter/exit
- no wallet, order, runtime, dispatcher, background, browser, or queue instructions
- no API keys, private keys, secrets, credentials, or account material

## Run Validation

After editing templates:

```powershell
python -m pm_bot.llm.manual_resolution_source_capture_validator --write
```

Optional local views:

```powershell
python -m pm_bot.llm.manual_resolution_source_capture_validator --summary-only
python -m pm_bot.llm.manual_resolution_source_capture_validator --market-id 563650
python -m pm_bot.llm.manual_resolution_source_capture_validator --strict-ready --summary-only
```

## Interpreting Validation

- `valid_count: 14` and `invalid_count: 0` means the templates pass structural and safety validation.
- `packets_not_started` lists templates still awaiting operator input.
- `packets_ready_for_local_review` lists templates marked for local review.
- `missing_fields_by_priority` shows the highest-priority evidence fields still empty.
- `operator_next_steps` gives the next safe local operator action.

Validation passing does not mean the market is approved. It only means the local capture packet conforms to the template and safety rules.

## When Validation Fails

1. Read `pm_bot/llm/manual_resolution_source_capture_validation.v1.md`.
2. Find the market ID and error.
3. Fix missing required fields, invalid status values, mismatched status fields, missing no-authority flags, or forbidden market-action language.
4. Rerun validation with `--write`.
5. Keep the template in `draft` or `needs_revision` until the error is fixed.

## Later Readiness Scoring

Filled templates can later feed evidence readiness scoring after a separate ingest task. Manual capture does not itself change readiness scoring, approve future OpenRouter calls, create queue items, schedule work, or authorize runtime behavior.

Manual capture improves evidence completeness only and does not approve trading.
