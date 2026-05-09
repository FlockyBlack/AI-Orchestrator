# ORCH-PMBOT-PRACTICAL-001 One-Market Analysis Source Learning Loop

Task: `ORCH-PMBOT-PRACTICAL-001-ONE-MARKET-ANALYSIS-SOURCE-LEARNING-LOOP`

## Summary

This task shifts PMBOT work from abstract rehearsal hardening toward practical analysis usefulness. The new loop takes one local market packet, produces a compact operator analysis card, records a paper-only hypothesis for later review, accepts a local outcome record, and updates a transparent source-learning ledger from feedback.

The loop remains local-only and deterministic. It does not fetch live data, call OpenRouter, call Polymarket APIs, use authenticated endpoints, touch wallet/signing/order paths, modify runtime/dispatcher code, or create unattended automation.

## Why This Shift Matters

The previous rehearsal milestone proved that static failure modes fail closed. That is necessary but not enough to judge whether PMBOT analysis is useful on concrete markets.

This practical loop lets an operator test analysis quality on one market at a time:

- Did PMBOT identify the main question?
- Which sources were used or ignored?
- What evidence was missing, stale, or contradictory?
- Was the paper-only hypothesis later useful, incomplete, or wrong?
- Which source types helped and which created review problems?

## Local Commands

Run one-market analysis:

```powershell
python -m pm_bot.practical.one_market_analysis `
  --input pm_bot\tests\fixtures\practical_one_market\one_market_input.valid.json `
  --out-json pm_bot\practical\artifacts\one_market_analysis_sample_001.result.json `
  --out-md pm_bot\practical\artifacts\one_market_analysis_sample_001.md
```

Run paper feedback:

```powershell
python -m pm_bot.practical.paper_feedback `
  --analysis pm_bot\practical\artifacts\one_market_analysis_sample_001.result.json `
  --outcome pm_bot\tests\fixtures\practical_one_market\one_market_outcome_record.resolved_aligned.json `
  --out-json pm_bot\practical\artifacts\one_market_feedback_sample_001.result.json `
  --out-md pm_bot\practical\artifacts\one_market_feedback_sample_001.md
```

Update the source learning ledger:

```powershell
python -m pm_bot.practical.source_learning `
  --feedback pm_bot\practical\artifacts\one_market_feedback_sample_001.result.json `
  --out-json pm_bot\practical\artifacts\source_learning_ledger_sample_001.result.json `
  --out-md pm_bot\practical\artifacts\source_learning_ledger_sample_001.md
```

## Artifacts Produced

- `pm_bot/practical/one_market_analysis.py`
- `pm_bot/practical/paper_feedback.py`
- `pm_bot/practical/source_learning.py`
- `pm_bot/practical/artifacts/one_market_analysis_sample_001.result.json`
- `pm_bot/practical/artifacts/one_market_analysis_sample_001.md`
- `pm_bot/practical/artifacts/one_market_feedback_sample_001.result.json`
- `pm_bot/practical/artifacts/one_market_feedback_sample_001.md`
- `pm_bot/practical/artifacts/source_learning_ledger_sample_001.result.json`
- `pm_bot/practical/artifacts/source_learning_ledger_sample_001.md`
- `pm_bot/tests/fixtures/practical_one_market/`
- `pm_bot/tests/test_practical_one_market_analysis.py`
- `pm_bot/tests/test_practical_paper_feedback.py`
- `pm_bot/tests/test_practical_source_learning.py`

## Input Contract

The one-market input fixture uses contract version `pmbot_one_market_input.v1`.

It records local market metadata, outcomes, rules, current context, available evidence, missing evidence, known uncertainty, operator notes, and source packets. Source packets include source identity, type, local reference or source reference, capture time, evidence summary, claim type/value, freshness status, known limitations, and whether the source was used in analysis.

No source packet is fetched by the runner. Source references are attribution strings only.

## What The Analysis Produces

The analysis result uses contract version `pmbot_one_market_analysis_result.v1`.

It includes:

- source attribution
- sources used and not used
- missing evidence
- uncertainty notes
- stale source notes
- contradiction notes
- compact operator summary
- paper-only hypothesis for analysis-quality tracking
- outcome tracking placeholder
- next research questions
- safety flags proving local-only behavior

The Markdown card mirrors the JSON in operator-readable form.

## Paper Feedback

The feedback runner consumes an analysis result and an outcome record with contract version `pmbot_one_market_outcome_record.v1`.

It produces `pmbot_one_market_paper_feedback_result.v1` with:

- qualitative paper hypothesis review
- analysis quality label
- source contribution review
- missing evidence lessons
- reasoning lessons
- source quality lessons
- next prompt improvements

Supported analysis quality labels are `useful`, `incomplete`, `wrong_due_to_missing_evidence`, `wrong_due_to_bad_reasoning`, `unresolved`, and `ambiguous`.

## Source Learning Ledger

The source learning ledger uses contract version `pmbot_source_learning_ledger.v1`.

This is not ML training. It is a transparent local ledger that aggregates feedback records into source records labeled `useful`, `stale`, `misleading`, `contradictory`, `insufficient`, `unused`, or `unknown`.

Each source record stores:

- source ID and name
- markets used
- usefulness label
- evidence role
- observed issue
- suggested future handling

The ledger also records source failure patterns, source handling updates, and prompt improvement notes.

## What This Proves

This proves PMBOT can run a practical one-market local analysis loop end to end from deterministic fixtures:

- local market packet in
- attributed JSON analysis out
- Markdown operator card out
- paper-only hypothesis recorded
- outcome feedback generated
- source usefulness ledger updated
- safety flags preserved

It also proves stale sources, contradictory source claims, malformed inputs, unresolved outcomes, aligned outcomes, and missed-evidence outcomes are covered by targeted tests.

## What This Does Not Prove

This does not prove live data fetching is ready. It does not validate public source availability, live parsing, network controls, authenticated endpoint safety, latency, operator timing, or production readiness.

It does not approve autonomous trading, real-money activity, wallet access, signing, order placement, execution routing, side selection, market instruction output, or unattended automation.

## Source Tracking Over Time

Each feedback result carries source contribution rows. The source learning runner aggregates those rows across one or more feedback files, preserving source IDs, market IDs, labels, issues, and suggested future handling.

Over time this lets the operator see whether a source tends to be useful, stale, contradictory, misleading, insufficient, unused, or still unknown.

## Before Real Live Public Read-Only Fetch

Remaining work before any live public read-only fetch:

- explicit approved public source inventory
- local-to-public source mapping
- read-only network boundary checks
- parser fixtures for each source type
- failure behavior for unavailable or changed pages
- operator approval gate for any live read-only test

## Before Any Real-Money Trading

Remaining work before any real-money trading is much larger and remains out of scope:

- separate explicit operator approval task
- wallet/signing safety design
- order and execution path review
- supervised controls and stop conditions
- auditability and reconciliation
- legal, operational, and financial risk review
- proof that analysis quality is reliable over many resolved paper-only cases

PMBOT is not ready for autonomous trading.

## Next Recommended Practical Step

`ORCH-PMBOT-PRACTICAL-002-OPERATOR-CONSOLE-MARKET-QUEUE-AND-ACTIVE-PAPER-HYPOTHESES`
