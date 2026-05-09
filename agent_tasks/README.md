# Local Codex Task Queue

This directory is a local, file-based, Symphony-spec-inspired task queue for AI-Orchestrator / PMBOT Codex automation.

Official OpenAI Symphony was inspected as a reference in `docs/ORCH_SYMPHONY_000_REFERENCE_SPIKE.md`. This queue is not the official Symphony runtime, does not install Symphony, and does not run the Elixir/OTP reference implementation.

The MVP shape is:

- task packet
- local queue
- validation
- safety gate
- workspace and handoff planning
- proof-of-work report
- human review

There is no autonomous execution in this MVP. The dry-run runner only validates approved JSON packets, classifies safety, writes non-executing plans, writes handoff prompts, and writes reports.

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

## Runner

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

