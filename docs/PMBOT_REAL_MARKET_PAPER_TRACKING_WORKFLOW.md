# PMBOT Real Market Paper Tracking Workflow

## Purpose

This workflow keeps real/local PMBOT market analysis in paper-only tracking mode. It exists to compare analysis quality across saved market packets over time, not to perform live trading or autonomous execution.

## PRACTICAL-003

PRACTICAL-003 proved the one-market path using saved packet `pm_bot/llm/manual_packet_batch/692258_packet.v1.json`. It normalized one real/local packet, ran one-market analysis, created one paper-only hypothesis, created one unresolved outcome record, and surfaced it in a local operator console.

## PRACTICAL-004

PRACTICAL-004 repeats the same local workflow for multiple saved packets and builds batch-level artifacts for queue review, active hypotheses, outcome checks, source-learning pending records, source dependency mapping, operator next actions, safety scanning, and quality-pending review.

## Artifact Locations

- Normalized inputs: `pm_bot/practical/artifacts/real_market_batch_004/markets/<market_id>/normalized_input.json`
- Analysis cards: `pm_bot/practical/artifacts/real_market_batch_004/markets/<market_id>/analysis.md`
- Analysis JSON: `pm_bot/practical/artifacts/real_market_batch_004/markets/<market_id>/analysis.result.json`
- Paper hypotheses: `pm_bot/practical/artifacts/real_market_batch_004/markets/<market_id>/paper_hypothesis.json` and `.md`
- Outcome records: `pm_bot/practical/artifacts/real_market_batch_004/markets/<market_id>/outcome_record.unresolved.json` and `.md`
- Batch queue: `pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json`
- Operator console: `pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.operator_console.md`

## Updating Outcome Records Later

When a market has saved local resolution evidence, copy the unresolved outcome record to a resolved local record, set `outcome_status` to the appropriate resolved state, fill `actual_outcome_summary`, set `resolved_at`, and preserve the exact local resolution source reference. Then update the market queue item to point to the resolved outcome record.

## Feedback After Resolution

After a resolved local outcome record exists, run the local paper feedback workflow against the analysis result and outcome record. The feedback result can then feed source-learning records with observed usefulness and gaps.

## Source Learning

Before outcomes resolve, source learning remains pending. After feedback exists, update source-learning records with whether each saved source row was useful, stale, missing, contradictory, insufficient, or unknown.

## Manual Work Remaining

- Attach saved local resolution evidence when available.
- Fill missing local source evidence without live fetches unless a later controlled read-only fetch task explicitly permits it.
- Review contradictions and stale source notes manually.
- Run feedback only after outcomes are locally resolved.

## Prohibited

- Scheduler, daemon, watcher, background worker, infinite loop, or unattended automation.
- OpenRouter calls, Polymarket API calls, authenticated endpoints, wallet/private-key access, signing, orders, or real-money activity.
- Runtime, dispatcher, run_codex, browser automation, or autonomous execution changes.
- Executable market instructions or quantitative market-output used for execution.
