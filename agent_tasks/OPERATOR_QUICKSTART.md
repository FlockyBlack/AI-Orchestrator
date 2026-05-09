# Operator Quickstart

Run commands from the repository root.

## 1. Create Or Prepare A Task

Use a template under `agent_tasks/templates/`, or create a safe demo packet:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli create-demo-task --queue-root agent_tasks --task-id ORCH-DEMO-QUICKSTART
```

For the PMBOT weather outcome/source monitoring plan-runner packet, use the local PMBOT bridge:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli create-pmbot-task --queue-root agent_tasks --task-id PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE --template weather-source-monitoring
```

See `agent_tasks/PMBOT_TASK_TEMPLATE_BRIDGE.md` for PMBOT approval, handoff, result JSON, and review-gate details.

Review the task packet in `agent_tasks/inbox/`. Confirm the task is local-only, has safe paths, and does not require network, credentials, wallet/trading/payment code, runtime/dispatcher changes, background workers, schedulers, or Codex app-server.

## 2. Approve

```powershell
python -m ai_orchestrator.codex_queue.operator_cli approve --queue-root agent_tasks --task-id ORCH-DEMO-QUICKSTART
```

## 3. Plan

```powershell
python -m ai_orchestrator.codex_queue.operator_cli plan --queue-root agent_tasks
```

Review:

- `agent_tasks/reports/latest_dry_run_report.md`
- `agent_tasks/planned/<TASK_ID>.plan.json`
- `agent_tasks/planned/<TASK_ID>.handoff_prompt.md`

## 4. Workspace Plan

```powershell
python -m ai_orchestrator.codex_queue.operator_cli workspace-plan --queue-root agent_tasks --task-id ORCH-DEMO-QUICKSTART
```

This only writes a plan. It does not create a branch or worktree.

## 5. Runbook

```powershell
python -m ai_orchestrator.codex_queue.operator_cli runbook --queue-root agent_tasks
```

Review `agent_tasks/reports/latest_controlled_codex_runbook.md`.

## 6. Dry-Run The Codex CLI Command

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-once --queue-root agent_tasks --task-id ORCH-DEMO-QUICKSTART --dry-run
```

Review:

- `agent_tasks/reports/latest_codex_cli_execution_report.md`
- the command shown in the report
- the task packet, plan, handoff prompt, stdout, stderr, and last-message paths

The dry-run does not invoke Codex CLI.

## 7. Run One Supervised Codex CLI Execution

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-once --queue-root agent_tasks --task-id ORCH-DEMO-QUICKSTART --timeout-seconds 3600
```

This invokes exactly one `codex exec` process and passes `agent_tasks/planned/<TASK_ID>.handoff_prompt.md` through stdin. It captures stdout, stderr, the last Codex message, and execution reports under `agent_tasks/reports/codex_cli_runs/<TASK_ID>/<RUN_ID>/`.

The command never marks the task done, never approves review, never ingests the result automatically, never pushes, and never starts a scheduler, daemon, background worker, or multi-task loop.

## 8. Optional Supervised Small Batch

Use this only after multiple tasks are already approved and planned. First inspect the batch:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-batch --queue-root agent_tasks --max-tasks 3 --dry-run
```

Review:

- `agent_tasks/reports/latest_codex_cli_batch_report.md`
- selected task IDs and skipped task IDs
- the exact `run-codex-once` commands shown for each selected task
- any git or queue warnings

Run a supervised three-task batch only after the dry-run is clean:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-batch --queue-root agent_tasks --max-tasks 3 --timeout-seconds 3600
```

The hard cap is five tasks. Optional explicit ordering is repeatable:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-batch --queue-root agent_tasks --task-id TASK_ONE --task-id TASK_TWO --task-id TASK_THREE --dry-run
```

The batch runner calls the one-task runner sequentially, stops on the first failure, and stops before a task if git has unexpected changes. It does not create, approve, mark done, ingest, review, commit, push, schedule, daemonize, or run in the background.

## 9. Put Result JSON Into Review

Confirm the Codex result packet exists as:

```text
agent_tasks/review/<TASK_ID>.result.json
```

Inspect it before ingestion.

## 10. Ingest Result

```powershell
python -m ai_orchestrator.codex_queue.operator_cli ingest-result --queue-root agent_tasks --result agent_tasks/review/<TASK_ID>.result.json
```

## 11. Review

```powershell
python -m ai_orchestrator.codex_queue.operator_cli review --queue-root agent_tasks --task-id <TASK_ID>
```

Inspect `agent_tasks/reports/<TASK_ID>.review.md`.

## 12. Mark Done

Only after the review recommends acceptance:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli mark-done --queue-root agent_tasks --task-id <TASK_ID>
```

## 13. Daily Reports

```powershell
python -m ai_orchestrator.codex_queue.operator_cli morning-report --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli next-actions --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli night-dry-run --queue-root agent_tasks --max-tasks 5
python -m ai_orchestrator.codex_queue.operator_cli scheduler-plan --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli portability-check --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli package-readiness --queue-root agent_tasks
```

All commands above are local and operator-invoked. Only `run-codex-once` without `--dry-run` and `run-codex-batch` without `--dry-run` invoke Codex CLI. The batch command does so only by calling the existing one-task runner sequentially for a bounded selected set. These commands do not commit, push, create branches, create worktrees, register schedulers, start background workers, call Codex app-server, call network services directly, or access credentials.
