# Operator Quickstart Card 015

## Open this first

- pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.md
- pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.md
- pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.md

## Check these 3 numbers

- unresolved_outcome_count: 5
- feedback_ready_count: 0
- source_url_backlog_count: 3

## If outcome resolved, do this

- Open that market's manual outcome packet under manual_outcome_feedback_014/markets/<market_id>/.
- Fill only from saved local resolution evidence.
- Run the feedback evaluator in a separate paper-only task after review.

## If source broken, do this

- Open source_url_backlog_011.md.
- Collect a replacement public source manually in local notes.
- Use a later approved public-source task before any fetch.

## If new market needed, do this

- Prepare a local market packet under pm_bot/llm/manual_packet_batch/.
- Run local packet normalization and local analysis only.
- Prefer next task `ORCH-PMBOT-PRACTICAL-016-ADD-NEXT-REAL-MARKET-PACKET-AND-RUN-DAILY-WORKFLOW`.

## Never do this

- No wallet, private key, signing, or real-money path access.
- No order placement, trading endpoint, or authenticated endpoint.
- No OpenRouter call unless a separate approved task explicitly allows it.
- No Polymarket API call unless a separate approved task explicitly allows it.
- No scheduler, daemon, background worker, watcher, polling loop, or unattended automation.
- No market recommendation, probability, EV, edge, confidence, or side-selection output.
