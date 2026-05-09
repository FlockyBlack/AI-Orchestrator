# Night Runner Dry-Run Workflow

`night-dry-run` is an operator-invoked planning command for the local Codex queue. It reads queue state, reads local git state, checks the night-runner lock file, classifies task readiness, and writes JSON/Markdown reports for review.

Run it manually from the repository root:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli night-dry-run --queue-root agent_tasks --max-tasks 5
```

## What It Does

- Inspects queue health across `inbox`, `approved`, `planned`, `running`, `review`, `done`, and `blocked`.
- Inspects local git state with read-only git commands.
- Checks `agent_tasks/running/night_runner.lock.json`.
- Classifies tasks into manual handoff ready, needs plan, needs workspace plan, needs result ingestion, needs review, ready for mark-done, and blocked.
- Applies `--max-tasks` as a dry-run planning cap.
- Writes:
  - `agent_tasks/reports/latest_night_dry_run_plan.json`
  - `agent_tasks/reports/latest_night_dry_run_plan.md`
  - `agent_tasks/reports/night_dry_run_plan_<timestamp>.json`
  - `agent_tasks/reports/latest_night_runner_lock_check.json`
  - `agent_tasks/reports/latest_night_runner_lock_check.md`

## What It Does Not Do

- It does not execute Codex.
- It does not call Codex app-server.
- It does not create branches.
- It does not create worktrees.
- It does not register schedulers.
- It does not start background workers.
- It does not move task packets.
- It does not mark tasks done.
- It does not call network services.
- It does not access credentials.

## Reading The Report

Start with `latest_night_dry_run_plan.md`. The operator-facing sections are:

- Queue Snapshot: current queue counts.
- Batch Evaluation: how many tasks are ready or need action, capped by `--max-tasks`.
- Ordered Next Actions: explicit local operator commands where a command applies.
- Errors and Warnings: lock, git, or queue concerns that need review.

The JSON report has the same information plus safety booleans. The key safety fields must remain false:

- `would_execute_codex`
- `would_create_branch`
- `would_create_worktree`
- `would_register_scheduler`

## Lock Check

The lock check only inspects `agent_tasks/running/night_runner.lock.json`. If that file exists, `night-dry-run` reports `blocked` unless the operator passes `--ignore-stale-lock`.

Ignoring a lock is only a reporting override. The command still does not create a long-running lock, remove a lock, sleep, wait, or start any background process.

## Before Any Real Scheduler Activation

A future scheduler must not be enabled until all of these are true:

- queue health reports are available;
- night dry-run reports are available;
- git safety inspection is available;
- result ingestion is available;
- morning report generation is available;
- a max task cap is enforced;
- lock file discipline is defined;
- no network is used by default;
- no credentials are accessed;
- Codex automatic execution is not enabled unless separately approved;
- the operator explicitly approves scheduler activation in a separate task.

The scheduler is not registered yet because this layer is only the local dry-run planning and readiness-reporting stage.
