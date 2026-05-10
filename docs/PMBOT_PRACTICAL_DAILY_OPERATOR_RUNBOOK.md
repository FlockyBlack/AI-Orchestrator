# PMBOT Practical Daily Operator Runbook

This is the daily guide for PMBOT's current practical analysis system. It is local-only, paper-only, and meant to help an operator understand the current state without asking a model to reconstruct the workflow.

## What PMBOT can do now

- Track 5 saved local Polymarket-style market packets in paper-only mode.
- Show active paper hypotheses and unresolved outcome placeholders.
- Show saved public evidence from prior approved public read-only tasks.
- Show which source URLs worked, failed, or still need manual repair.
- Show one applied paper tracking update in a versioned snapshot.
- Prepare manual feedback packets for later outcome resolution.
- Generate a daily local summary, command catalog, workflow index, checklist, quickstart card, decision matrix, status snapshot, and safety boundary reference.

## What PMBOT cannot do

- It cannot resolve outcomes by guessing.
- It cannot fetch new live data in this daily workflow.
- It cannot call OpenRouter or Polymarket APIs in this task.
- It cannot use authenticated endpoints, cookies, API keys, browser profiles, or browser automation.
- It cannot access wallets, private keys, signing paths, trading endpoints, or real-money flows.
- It cannot create schedulers, daemons, background workers, watchers, polling loops, or unattended automation.
- It cannot produce market-side recommendation output, quantitative side-selection output, or real trading actions.

## What to open first each day

1. `pm_bot/practical/artifacts/daily_workflow_015/operator_quickstart_card_015.md`
2. `pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.md`
3. `pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.md`
4. `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.md`
5. `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_operator_view_013.md`

## Daily workflow in 10 minutes

1. Open the quickstart card and daily summary.
2. Check `unresolved_outcome_count`, `feedback_ready_count`, and `source_url_backlog_count`.
3. Open the feedback readiness dashboard. Current expected state is 5 unresolved, 0 feedback-ready.
4. Open the outcome recheck queue. Keep every market unresolved unless saved local resolution evidence exists.
5. Open the source learning scorecard. Note which sources are reachable, repaired, missing, or blocked.
6. If a source URL is broken, record the manual repair need. Do not fetch from the daily runbook.
7. If an outcome is actually resolved, follow `docs/PMBOT_HOW_TO_PROCESS_A_RESOLVED_MARKET_OUTCOME.md`.
8. If no outcome is resolved, choose the next safe task from `next_task_decision_matrix_015.md`.
9. Run only the safe local commands from `practical_command_catalog_015.md`.
10. End by checking `daily_workflow_safety_scan_015.md` after artifact changes.

## Where the 5 tracked markets live

The selected batch lives at:

- `pm_bot/practical/artifacts/real_market_batch_004/selected_real_market_batch.md`
- `pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json`

Tracked markets:

- `563650` - SCOTUS accepts sports event contract case by July 31, 2026?
- `597964` - Macron out by June 30, 2026?
- `598936` - Will the next UK election be called by June 30, 2026?
- `691547` - Kraken IPO by December 31, 2026?
- `692258` - MicroStrategy sells any Bitcoin by June 30, 2026?

## Where public evidence dashboard lives

- Dashboard: `pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.md`
- Source URL backlog: `pm_bot/practical/artifacts/public_evidence_dashboard_011/source_url_backlog_011.md`
- Source status board: `pm_bot/practical/artifacts/public_evidence_dashboard_011/merged_source_status_board_011.md`

The current dashboard has 2 saved public evidence packets from prior approved tasks and 3 source URL backlog items.

## Where paper tracking snapshot lives

- Snapshot: `pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.md`
- Applied update: `pm_bot/practical/artifacts/paper_update_application_012/applied_paper_update_012.md`
- Operator morning card: `pm_bot/practical/artifacts/paper_update_application_012/operator_morning_card_after_update_012.md`

There is 1 applied paper update, for market `563650`. It does not resolve the outcome.

## Where outcome recheck queue lives

- Queue: `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.md`
- Operator dashboard: `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/operator_dashboard_outcome_recheck_013.md`
- Manual update template: `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/manual_outcome_resolution_update_template_013.md`

All 5 tracked markets remain unresolved.

## Where manual feedback packets live

- Dashboard: `pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.md`
- Operator guide: `pm_bot/practical/artifacts/manual_outcome_feedback_014/manual_outcome_operator_guide_014.md`
- Per-market packets: `pm_bot/practical/artifacts/manual_outcome_feedback_014/markets/<market_id>/`

Each market has a pending manual outcome packet, pending paper feedback packet, pending source feedback packet, and pending manual feedback packet.

## How to handle a market that resolves

Use `docs/PMBOT_HOW_TO_PROCESS_A_RESOLVED_MARKET_OUTCOME.md`.

The short version:

- Open that market's pending manual outcome packet.
- Fill only from saved local resolution evidence.
- Set `actual_outcome_summary`, `resolved_at`, and `resolution_source_reference`.
- Choose one of `aligned`, `not_aligned`, `ambiguous`, or `void` after manual review.
- Run feedback generation in a separate paper-only task.
- Update source learning only from approved local feedback artifacts.

Never invent outcome fields. Never treat feedback as trading proof.

## How to inspect source learning

Open:

- `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_operator_view_013.md`
- `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_update_013.md`
- `pm_bot/practical/artifacts/public_evidence_dashboard_011/source_url_backlog_011.md`

Current source state:

- SCOTUS source is reachable and supported the paper tracking update.
- Kraken source was repaired and has a saved public evidence packet.
- Macron, UK election, and MicroStrategy source paths need manual repair or alternate official public sources.

## How to decide next safe Codex task

Open:

- `pm_bot/practical/artifacts/daily_workflow_015/next_task_decision_matrix_015.md`

Default next action:

- `ORCH-PMBOT-PRACTICAL-016-ADD-NEXT-REAL-MARKET-PACKET-AND-RUN-DAILY-WORKFLOW`

Choose a different task only when a concrete condition is true, such as a saved local outcome record existing or a manually curated replacement source URL being ready.

## What is prohibited

- No wallet, private key, signing, or real-money path access.
- No order placement, trading endpoint, or authenticated endpoint.
- No OpenRouter call unless separately approved.
- No Polymarket API call unless separately approved.
- No scheduler, daemon, background worker, watcher, polling loop, or unattended automation.
- No market-side recommendation output or quantitative side-selection output.
- No invented outcomes.
- No resolved status for unresolved markets.
- No runtime, dispatcher, browser automation, or autonomous execution path changes.

## Troubleshooting

- If a dashboard count looks wrong, validate the JSON with `python -m json.tool <path>`.
- If a file is missing, open `pm_bot/practical/artifacts/daily_workflow_015/practical_workflow_index_015.md`.
- If feedback is still zero, check whether any local outcome packet is actually resolved. Current expected value is zero.
- If source repair is needed, record manual URL work locally and create a separate source repair task.
- If a command asks for API keys, cookies, profiles, wallet access, network polling, or model calls, it is not part of this runbook.

## Do not confuse paper tracking with trading

Paper tracking records what the analysis system believed and what evidence was saved. It is not trading, not execution readiness, not a market-side instruction, and not proof that the system can operate autonomously.
