# PMBOT OpenRouter Operator Review Runbook

## Current Architecture

PMBOT keeps local market packets, prompts, OpenRouter analysis artifacts, passive surfaces, and workbench exports as separate static files. The OpenRouter contour is analysis-only and exists to help a human operator review local evidence gaps.

PMBOT does local packet preparation, controlled readiness protocols, controlled analysis-only live batches when separately approved, baseline quality summaries, passive operator surfaces, and static workbench exports.

PMBOT does not trade, mutate queues, wire runtime services, place orders, access wallets, sign anything, or call Polymarket APIs inside the OpenRouter batch flow.

## Safety Boundaries

- operator-review-only artifacts
- passive context only
- no queue authority
- no runtime or dispatcher authority
- no wallet, order, or private-key authority
- no browser automation
- no API key value should be read, printed, written, or committed
- accepted_for_operator_review means the artifact passed local review gates; it is not trading approval

## Supported Flow

1. Local packets and prompts exist under pm_bot/llm/manual_packet_batch.
2. A readiness protocol defines market IDs, cost cap, fail-fast gates, and safety constraints.
3. A controlled live batch may run only when separately approved.
4. A baseline quality summary checks local artifact completeness and warnings.
5. A passive operator surface summarizes accepted artifacts without raw response text.
6. The workbench pointer/export includes passive context for manual review.
7. A human operator reviews sources, gaps, and checklist items manually.

## Validation Commands

- python -m compileall pm_bot
- python -m pytest tests pm_bot\llm\tests -q
- python -m pytest tests\test_openrouter_prompt_test.py -q
- python -m pytest tests\test_openrouter_result_artifacts.py -q
- python -m pytest tests\test_openrouter_fenced_json_normalization.py -q
- python -m pytest tests\test_openrouter_n5_batch_readiness_protocol.py -q
- python -m pytest pm_bot\workbench\tests -q
- python -m pm_bot.workbench.run_operator_workbench_export
- JSON parse checks for source and generated artifacts
- secret scan over changed files
- generated Markdown scan for market-action guidance

## Reading The Workbench

Start with pm_bot/workbench/operator_openrouter_review_dashboard.v1.md for the 8-market contour summary. Use pm_bot/workbench/openrouter_passive_surface_pointer.v1.md to inspect N=3 and N=5 surface history. Use pm_bot/workbench/operator_review_pack.v1.md for the broader local operator review context.

## Normalization Warnings

The current model/provider route returned Markdown-fenced JSON in all successful N=3 and N=5 batch responses. The normalization policy is local fence extraction only; raw responses remain preserved and semantic repair is not allowed.

## Cost Tracking

N=3 cost was 0.125982. N=5 cost was 0.199089. The combined successful-batch contour cost is 0.325071. The N=5 batch stayed below its 0.35 cap.

## If A Batch Blocks

Stop at the first diagnostic. Preserve raw, content, validation, summary, and result artifacts. Do not retry until the failure class is documented and a protocol or prompt-hardening fix is reviewed.

## Do Not Do

- no retries without diagnostic review
- no queue mutation
- no runtime wiring
- no trading
- no wallet or order access
- no Polymarket API call inside the OpenRouter batch flow
- no future live calls from this task

## Recommended Next Tasks

- review the category/source inventory
- design source/evidence enrichment for local packets
- refine static operator UX
- repeat N=5 only after review and separate approval
- create N=10 readiness as protocol-only after review
