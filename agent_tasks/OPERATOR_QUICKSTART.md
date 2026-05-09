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

## 6. Manually Run Codex

Open `agent_tasks/planned/<TASK_ID>.handoff_prompt.md`. Paste or run it manually in the controlled Codex environment you choose.

Codex execution is not automatic. The queue does not call Codex app-server.

## 7. Put Result JSON Into Review

Save the manual result packet as:

```text
agent_tasks/review/<TASK_ID>.result.json
```

Inspect it before ingestion.

## 8. Ingest Result

```powershell
python -m ai_orchestrator.codex_queue.operator_cli ingest-result --queue-root agent_tasks --result agent_tasks/review/<TASK_ID>.result.json
```

## 9. Review

```powershell
python -m ai_orchestrator.codex_queue.operator_cli review --queue-root agent_tasks --task-id <TASK_ID>
```

Inspect `agent_tasks/reports/<TASK_ID>.review.md`.

## 10. Mark Done

Only after the review recommends acceptance:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli mark-done --queue-root agent_tasks --task-id <TASK_ID>
```

## 11. Daily Reports

```powershell
python -m ai_orchestrator.codex_queue.operator_cli morning-report --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli next-actions --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli night-dry-run --queue-root agent_tasks --max-tasks 5
python -m ai_orchestrator.codex_queue.operator_cli scheduler-plan --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli portability-check --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli package-readiness --queue-root agent_tasks
```

All commands above are local and operator-invoked. They do not commit, push, create branches, create worktrees, register schedulers, start background workers, execute Codex automatically, call Codex app-server, call network services, or access credentials.
