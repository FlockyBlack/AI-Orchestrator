# PMBOT Daily Operator Summary

- Tracked markets: 5
- Unresolved outcomes: 5
- Feedback ready: 0
- Public evidence packets: 2
- Source URL backlog: 3

## What changed recently

- PRACTICAL-014 prepared pending manual feedback packets for all five tracked markets.
- PRACTICAL-013 created the outcome recheck queue and source learning scorecard update.
- PRACTICAL-012 applied one operator-approved paper tracking update to a versioned snapshot.
- PRACTICAL-011 merged two saved public evidence packets into the dashboard.

## Markets being tracked

- `563650` `generic` - SCOTUS accepts sports event contract case by July 31, 2026? (hypothesis_active)
- `597964` `politics` - Macron out by June 30, 2026? (hypothesis_active)
- `598936` `politics` - Will the next UK election be called by June 30, 2026? (hypothesis_active)
- `691547` `crypto` - Kraken IPO by December 31, 2026? (hypothesis_active)
- `692258` `crypto` - MicroStrategy sells any Bitcoin by June 30, 2026? (hypothesis_active)

## Evidence and source status

- Saved public evidence packets: 2
- Source records: 5
- Source URLs needing manual repair: 3

## Paper updates

- Applied paper updates: 1
- `563650` - `applied-paper-update-012-paper-hypothesis-update-candidate-009`

## Outcome recheck status

- Unresolved outcomes: 5
- Outcome status stays unresolved until saved local resolution evidence exists.

## Feedback readiness

- Feedback-ready packets: 0
- Feedback packets are pending because every tracked outcome remains unresolved.

## What to open first

- `pm_bot/practical/artifacts/daily_workflow_015/operator_quickstart_card_015.md` - One-screen daily entry point.
- `pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.md` - Current counts, blockers, and next safe actions.
- `pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.md` - Shows which feedback packets are pending or ready.
- `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.md` - Shows unresolved markets and recheck priority.
- `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_operator_view_013.md` - Shows reachable, repaired, missing, and blocked source records.
- `pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.md` - Shows active paper hypotheses and applied paper updates.
- `pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.md` - Shows saved public evidence packets and source status.

## Next safe actions

- Open the operator quickstart card, daily summary, feedback readiness dashboard, and outcome recheck queue.
- Check unresolved outcome count, feedback-ready count, and source URL backlog count.
- Leave outcomes unresolved unless saved local resolution evidence exists.
- Collect replacement source URLs manually before a separate approved source task.
- Use `ORCH-PMBOT-PRACTICAL-016-ADD-NEXT-REAL-MARKET-PACKET-AND-RUN-DAILY-WORKFLOW` for the next local-only expansion task.

## Prohibited actions

- No wallet, private key, signing, or real-money path access.
- No order placement, trading endpoint, or authenticated endpoint.
- No OpenRouter call unless a separate approved task explicitly allows it.
- No Polymarket API call unless a separate approved task explicitly allows it.
- No scheduler, daemon, background worker, watcher, polling loop, or unattended automation.
- No market recommendation, probability, EV, edge, confidence, or side-selection output.
- No invented outcomes and no resolved status for unresolved markets.
- No runtime, dispatcher, browser automation, or autonomous execution path changes.
