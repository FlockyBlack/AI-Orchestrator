# ORCH-PMBOT-PRACTICAL-003-REAL-MARKET-LOCAL-PACKET-IMPORT-AND-ANALYSIS-RUN

## Summary

This run used an existing saved PMBOT market packet instead of a synthetic practical fixture. The selected packet was normalized into `pmbot_one_market_input.v1`, analyzed with the local one-market practical workflow, placed into an active paper-only queue item, and checked by the practical safety scanner.

No live market fetch, OpenRouter call, Polymarket API call, authenticated endpoint, wallet access, order path, trading action, runtime change, dispatcher change, scheduler, or automation was used.

## Selected Real/Local Market Artifact

- Selected artifact: `pm_bot/llm/manual_packet_batch/692258_packet.v1.json`
- Market ID: `692258`
- Market title: MicroStrategy sells any Bitcoin by June 30, 2026?
- Known historical market `824952`: not found locally.
- Source pointer: `pm_bot/practical/artifacts/real_market_003/selected_real_market_source_pointer.json`
- Candidate inventory: `pm_bot/practical/artifacts/real_market_003/candidate_market_artifact_inventory.md`

## Why It Was Selected

Selected because it has the clearest concrete market question, a local rules excerpt, binary outcomes, the richest saved evidence-placeholder set, fewer missing-evidence rows than similar rich packets, and no live fetch requirement.

The packet has a concrete market question, binary outcomes, a saved local rules excerpt, ten local source-placeholder rows, and explicit missing evidence. Its referenced upstream selected-ingest artifact is absent from this checkout, so that limitation is preserved in the normalized missing-evidence list instead of filled in.

## Import And Normalization Result

- Normalized input: `pm_bot/practical/artifacts/real_market_003/real_market_003.normalized_input.json`
- Import summary: `pm_bot/practical/artifacts/real_market_003/real_market_003.import_summary.md`
- Contract: `pmbot_one_market_input.v1`
- Sources preserved: 10
- Missing evidence items: 6

## Analysis Result

- Analysis JSON: `pm_bot/practical/artifacts/real_market_003/real_market_003.analysis.result.json`
- Analysis Markdown: `pm_bot/practical/artifacts/real_market_003/real_market_003.analysis.md`
- Analysis ID: `692258.analysis.bed289c1494d`
- Used sources: 10
- Stale source notes: 0
- Contradiction notes: 3

## Sources Used

- `official_source_checked_001` official_source_checked - `unknown`
- `official_source_checked_002` official_source_checked - `unknown`
- `official_source_placeholder_003` official_source_placeholder - `unknown`
- `official_source_placeholder_004` official_source_placeholder - `unknown`
- `official_source_placeholder_005` official_source_placeholder - `unknown`
- `news_source_checked_006` news_source_checked - `unknown`
- `news_source_placeholder_007` news_source_placeholder - `unknown`
- `news_source_placeholder_008` news_source_placeholder - `unknown`
- `news_source_placeholder_009` news_source_placeholder - `unknown`
- `source_plan_010` source_plan - `unknown`

## Missing Evidence

- full_official_source_reference
- credible_news_source_references
- official_yes_or_no_evidence
- source_reliability_review
- Valid partial selected-ingest overlay used to prove deterministic merge behavior.
- Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json

## Paper-Only Hypothesis

- Paper hypothesis JSON: `pm_bot/practical/artifacts/real_market_003/real_market_003.paper_hypothesis.json`
- Paper hypothesis Markdown: `pm_bot/practical/artifacts/real_market_003/real_market_003.paper_hypothesis.md`
- Hypothesis ID: `692258.analysis.bed289c1494d.paper_hypothesis`
- Safety label: `paper_only_non_executable_analysis_tracking`
- Purpose: analysis-quality tracking only.

## Active Hypothesis And Outcome Queue Status

- Market queue: `pm_bot/practical/artifacts/real_market_003/real_market_003.market_queue.json`
- Queue summary: `pm_bot/practical/artifacts/real_market_003/real_market_003.market_queue.summary.md`
- Active hypotheses: `pm_bot/practical/artifacts/real_market_003/real_market_003.active_paper_hypotheses.md`
- Outcome queue: `pm_bot/practical/artifacts/real_market_003/real_market_003.outcome_check_queue.md`
- Queue statuses: `{'hypothesis_active': 1}`
- Active hypotheses: 1
- Outcome check status: `due_now`

## Operator Console Artifact

- Console JSON: `pm_bot/practical/artifacts/real_market_003/real_market_003.operator_console.result.json`
- Console Markdown: `pm_bot/practical/artifacts/real_market_003/real_market_003.operator_console.md`
- Market review details surfaced: 1

## Source Learning Placeholder

- Pending JSON: `pm_bot/practical/artifacts/real_market_003/real_market_003.source_learning_pending.json`
- Pending Markdown: `pm_bot/practical/artifacts/real_market_003/real_market_003.source_learning_pending.md`
- Pending dependency: A resolved local outcome record is required before source usefulness can be judged.

## Safety Scan Result

- Safety scan JSON: `pm_bot/practical/artifacts/real_market_003/real_market_003.practical_safety_scan.result.json`
- Safety scan Markdown: `pm_bot/practical/artifacts/real_market_003/real_market_003.practical_safety_scan.md`
- Safety OK: `true`
- Issues: 0
- Live network used: false.
- OpenRouter calls performed: 0.
- Polymarket API calls performed: 0.
- Authenticated endpoints used: false.
- Wallet/private-key access: false.
- Orders or trading actions: false.
- Runtime or dispatcher changes: false.
- Market recommendation generated: false.
- Quantitative market-output generated: false.

## What This Proves

- The practical importer can normalize a saved manual PMBOT market packet into the one-market input contract.
- The one-market analyzer can produce operator-review Markdown and JSON from that concrete local packet.
- The paper-only hypothesis tracker, outcome queue, operator console, source-learning placeholder, and safety scan can operate on a real saved market packet without live services.

## What This Does Not Prove

- It does not prove the market outcome.
- It does not prove the missing upstream selected-ingest artifact is recoverable.
- It does not prove readiness for autonomous execution or real-money activity.
- It does not produce an executable market instruction.

## Repeat With Another Market

1. Put or identify a saved local market packet with title, rules/context, outcomes, missing evidence, and source rows.
2. Run `python -m pm_bot.practical.local_market_packet_import --input <packet> --out-json <normalized.json> --out-md <summary.md>`.
3. Run `python -m pm_bot.practical.one_market_analysis --input <normalized.json> --out-json <analysis.json> --out-md <analysis.md>`.
4. Create an unresolved outcome record and a one-item local market queue.
5. Run the queue summary, active hypothesis tracker, outcome queue, operator console, source-learning pending record, and safety scan.

## Next Recommended Action

`ORCH-PMBOT-PRACTICAL-004-REAL-MARKET-MULTI-PACKET-PAPER-TRACKING-BATCH`
