# PMBOT Codex Automation Recovery And Multi-Task Plan

## Current broken workflow

The operator gives a high-level direction, but the system still depends on repeated manual prompt chaining. That means each small refresh, dashboard update, paper-state check, or safety scan often requires a separate prompt.

## Desired workflow

The intended workflow is:

- operator gives one high-level approved plan
- the system expands it into finite task packets
- the operator reviews the packets and approves safe local work
- a local runner executes approved safe tasks one at a time
- dashboard state tracks progress, failures, and next actions
- no manual copy/paste loop every 10 minutes

## Required modules

- task packet schema with task id, scope, inputs, outputs, and safety flags
- approval record schema
- finite local runner for approved packets
- artifact registry and dashboard
- safety scanner for packet content and produced artifacts
- failure recovery and retry plan
- task result ingestion back into the dashboard

## Risks

- accidental live network use
- accidental OpenRouter or Polymarket API use
- unsafe expansion into wallet, signing, order, or real-money scope
- hidden background execution
- stale task state causing repeated or duplicate runs
- operator approval becoming unclear or implicit

## Safe next milestone

`ORCH-PMBOT-TRADING-MVP-022-PAPER-TRADING-LOOP-DAILY-RUN-AND-CODEX-AUTOMATION-RECOVERY`

Recommended scope:

- add dated paper run directories
- add task packet drafts for the paper-only workflow
- add packet validation
- add dashboard status for packet state
- keep execution explicit and one-shot

## Must not be automated yet

- real trading
- wallet access
- private key access
- signing
- orders
- authenticated endpoints
- Polymarket API calls
- OpenRouter calls
- schedulers, daemons, watchers, background workers, or infinite polling loops
