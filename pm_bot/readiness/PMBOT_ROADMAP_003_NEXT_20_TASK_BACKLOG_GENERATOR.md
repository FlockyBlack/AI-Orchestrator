# PMBOT Roadmap 003 Next 20 Task Backlog Generator

Task: `PMBOT-ROADMAP-003-NEXT-20-TASK-BACKLOG-GENERATOR`
Backlog: `pmbot-next-20-task-backlog`
Contract: `pmbot_next_20_task_backlog.v1`
Run mode: `local_static_next_20_task_backlog_generator`
Operator review: `pending_operator_review`

## Purpose

This artifact defines a deterministic local generator for the PMBOT next 20 task backlog. It records fixed task IDs, local references, source artifacts, validation commands, and closed safety boundaries for operator review.

The backlog is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Local Artifacts

- Generator: `pm_bot/readiness/next_20_task_backlog_generator.py`
- Static fixture: `pm_bot/tests/fixtures/readiness/pmbot_next_20_task_backlog.valid.json`
- Tests: `pm_bot/tests/test_next_20_task_backlog_generator.py`

## Source Basis

Reviewed local PMBOT artifacts:

- `tests/test_codex_queue_pmbot_templates.py`
- `pm_bot/readiness/PMBOT_ROADMAP_001_REAL_WALLET_READINESS_BLOCKER_MATRIX.md`
- `pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `docs/PMBOT_DASHBOARD_002_QUEUE_AND_PAPERLIVE_STATUS_SURFACE.md`

These sources keep the backlog local-only, deterministic, and pending operator review.

## Generator Contract

The generator emits:

- a fixed contract version and run mode
- exactly 20 task records
- fixed record indexes from 1 through 20
- local references under allowed PMBOT paths
- pending operator review status for every task and source artifact row
- closed safety boundaries for credentials, wallet access, endpoints, runtime, scheduler, worker, browser, network, and transaction surfaces
- the acceptance validation commands from the handoff

The generator does not inspect live queues, call services, read secrets, read wallets, start processes, or write runtime state.

## CLI

```powershell
python -m pm_bot.readiness.next_20_task_backlog_generator `
  --output-backlog pm_bot\tests\fixtures\readiness\pmbot_next_20_task_backlog.valid.json `
  --output-report <local-output-path>.md
```

The CLI writes a JSON backlog artifact and, when requested, a Markdown operator report. Both outputs are deterministic for the same code version.

## Operator Review Boundary

Operators review whether the fixed task records and local references match the intended PMBOT backlog. The artifact does not approve any task, choose the next task to run, change review status, resolve any gate, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, stance selection, or trade action guidance.
- This backlog is not execution approval and is not runtime input.
