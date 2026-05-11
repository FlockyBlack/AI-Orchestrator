# ORCH PMBOT Trading MVP Night 020/021 Implementation Map

Task: `ORCH-PMBOT-TRADING-MVP-NIGHT-020-021-PAPER-TRADING-CORE-AND-ONE-COMMAND-OPERATOR-RUNNER`

## Active market sources

The trading MVP reads only local practical artifacts:

- `pm_bot/practical/artifacts/add_market_016/market_queue_6_016.json`
- `pm_bot/practical/artifacts/add_market_016/active_paper_hypotheses_6_016.json`
- `pm_bot/practical/artifacts/add_market_016/daily_workflow_summary_after_add_016.json`
- `pm_bot/practical/artifacts/manual_url_collection_017c/public_evidence_dashboard_url_filled_pending_approval_017c.json`
- `pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.json`
- `pm_bot/practical/artifacts/paper_update_application_012/paper_tracking_state_snapshot_012.json`

The six tracked markets are `563650`, `573656`, `597964`, `598936`, `691547`, and `692258`. All remain unresolved.

## Active hypotheses

`active_paper_hypotheses_6_016.json` provides one active paper hypothesis per tracked market. These are analysis-tracking hypotheses only. They are not real trading decisions and do not resolve outcomes.

## Public evidence sources

Saved local public evidence packets currently exist for:

- `563650` through the PRACTICAL-008 SCOTUS saved evidence packet.
- `691547` through the PRACTICAL-010 Kraken saved evidence packet.

The BTC market `573656` has a filled manual URL packet from PRACTICAL-017C, but no live fetch was performed and operator approval remains separate.

## Available paper tracking state

Paper tracking state comes from:

- active market queue and hypotheses from PRACTICAL-016
- saved evidence links and paper update snapshot from PRACTICAL-011/012
- unresolved outcome and feedback readiness counts from PRACTICAL-014/016
- manual URL readiness from PRACTICAL-017C

## Paper trade intent candidate inputs

The new intent generator creates one `paper_trade_intent` candidate per tracked market. Markets with saved local public evidence can produce a `simulated_entry` candidate for testing ledger plumbing. Markets without saved evidence default to `observe_only`.

Side labels such as `track_yes` and `no_action` are paper tracking labels only. They are not real market-side instructions.

## Still fake or simulated

- Paper intent candidates are non-executable.
- Simulated fills use an explicit fixture placeholder price.
- Paper positions are local ledger records only.
- Portfolio capital and exposure are local paper accounting values.
- No wallet, signing, order adapter, authenticated endpoint, live price, scheduler, daemon, watcher, background worker, or autonomous real-money path exists.
