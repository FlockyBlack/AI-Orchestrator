# Local Codex Task Queue

This directory is a local, file-based, Symphony-spec-inspired task queue for AI-Orchestrator / PMBOT Codex automation.

Official OpenAI Symphony was inspected as a reference in `docs/ORCH_SYMPHONY_000_REFERENCE_SPIKE.md`. This queue is not the official Symphony runtime, does not install Symphony, and does not run the Elixir/OTP reference implementation.

The MVP shape is:

- task packet
- local queue
- validation
- safety gate
- workspace and handoff planning
- supervised one-task Codex CLI execution
- proof-of-work report
- human review

There is no autonomous multi-task execution in this MVP. The dry-run runner validates approved JSON packets, classifies safety, writes non-executing plans, writes handoff prompts, and writes reports. The supervised Codex CLI runner executes only one explicit approved/planned task per operator command.

Manual approval is required. Proposed tasks start in `inbox/`; an operator must inspect and move a task packet to `approved/` before the dry-run runner will plan it.

PMBOT operator-review packets can be created through the safe template bridge documented in `agent_tasks/PMBOT_TASK_TEMPLATE_BRIDGE.md`. The first supported PMBOT template is `weather-source-monitoring`.

## Directories

- `inbox/`: proposed tasks not yet approved.
- `approved/`: tasks manually approved by the operator.
- `planned/`: dry-run plans and generated handoff prompts.
- `running/`: reserved for future controlled execution; unused for execution in this MVP.
- `review/`: completed task outputs awaiting human review.
- `done/`: manually accepted completed tasks.
- `blocked/`: tasks rejected by schema or safety gate.
- `templates/`: example task packets.
- `reports/`: dry-run and queue reports.

## Planning Runner

Run from the repository root:

```powershell
python -m ai_orchestrator.codex_queue.dry_run_runner --queue-root agent_tasks --dry-run
```

The runner does not:

- invoke Codex
- call Codex app-server
- execute acceptance checks
- call network services
- create branches or worktrees
- move packets between queue directories
- start daemons, background workers, schedulers, or task scheduler jobs

## Supervised Codex CLI Runner

After a task is approved and planned, inspect the handoff prompt and run a dry-run preflight:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-once --queue-root agent_tasks --task-id <TASK_ID> --dry-run
```

For one supervised execution:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-once --queue-root agent_tasks --task-id <TASK_ID> --timeout-seconds 3600
```

The runner:

- requires an explicit `--task-id`
- accepts only approved/planned tasks with an existing plan and handoff prompt
- checks local git state and blocks on `expected_head` mismatches
- invokes exactly one `codex exec` process when not in dry-run mode
- passes the handoff prompt through stdin
- captures stdout, stderr, the last Codex message, and JSON/Markdown execution reports under `agent_tasks/reports/codex_cli_runs/<TASK_ID>/<RUN_ID>/`

It does not mark tasks done, approve review, ingest results, push git changes, create schedulers, start daemons, start background workers, or run a multi-task loop.
