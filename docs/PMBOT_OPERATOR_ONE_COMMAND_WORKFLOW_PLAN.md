# PMBOT Operator One-Command Workflow Plan

## Problem

The current practical PMBOT workflow asks the operator to paste a new prompt every 10 to 20 minutes. That creates avoidable drift:

- context gets lost between prompts
- artifacts are easy to refresh in the wrong order
- safety checks can be skipped by accident
- the operator has to manually connect daily state, market dashboards, paper tracking, and next actions

## What the one-shot runner now does

The new command runs one local workflow and exits:

```bash
python -m pm_bot.operator_runner.run_operator_workflow_once --out-dir pm_bot/operator_runner/artifacts/night_020_021/run_001 --include-trading-core --no-live-fetch --no-real-trading
```

It performs these local steps:

- loads the latest practical state
- copies the latest daily summary
- refreshes the tracked market dashboard from local artifacts
- builds paper trade intent candidates
- applies paper risk limits and risk gate checks
- runs the execution simulator
- builds the paper position ledger
- builds paper portfolio state
- runs post-execution audit
- builds the paper trading dashboard
- writes the future real-adapter boundary
- runs trading-core and operator-workflow safety scans
- writes one final operator report

## Why this is not scheduler or background automation

The runner has no loop, no watcher, no daemon, no scheduler, no automatic repeat, and no polling. It runs only when the operator executes the command. The result includes `run_once: true` and `repeat_count: 1`.

## How to extend later

Good next extensions:

- add better local freshness checks for saved evidence
- add a paper-only daily run snapshot directory per date
- add a task packet queue that requires explicit approval before execution
- add richer dashboard summaries for stalled markets

## Still requires explicit Codex task prompts

- any live public fetch
- any OpenRouter call
- any Polymarket API call
- any real adapter design work
- any wallet/signing/order discussion
- any scheduler or task queue implementation

## Future work for true task queue autonomy

The project still needs a safe task packet model, approval records, finite runner boundaries, dashboard state, failure recovery, and a clear list of tasks that are never eligible for unattended automation.
