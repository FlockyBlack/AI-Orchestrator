# ORCH-SYMPHONY-004 Task Lifecycle and Operator CLI

Task: `ORCH-SYMPHONY-004-TASK-LIFECYCLE-AND-OPERATOR-CLI`

Status: `completed`

## What Was Added

Added a local-only operator CLI:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli <command> [args]
```

The CLI adds queue inspection, safe demo task creation, manual approval, dry-run planning, manual result ingestion, review reporting, explicit mark-done, and explicit mark-blocked commands.

Also added shared safe file helpers in `ai_orchestrator/codex_queue/files.py` for queue directory creation, JSON reads/writes, queue-root path safety, task lookup, and safe task packet moves between queue states.

## Queue Lifecycle Now

The local queue can now be operated without manually moving task JSON files:

1. `create-demo-task` creates a safe docs-only packet in `agent_tasks/inbox/`.
2. `approve` validates and safety-classifies an inbox task, then moves it to `agent_tasks/approved/`.
3. `plan` wraps the existing dry-run runner and writes plans and handoff prompts under `agent_tasks/planned/`.
4. A human/manual process creates a result packet under `agent_tasks/review/`.
5. `ingest-result` wraps the existing ingestor and writes ingestion reports.
6. `review` writes task-specific JSON and Markdown review reports.
7. `mark-done` explicitly moves the task packet to `agent_tasks/done/` only after review, result, and ingestion preconditions pass.
8. `mark-blocked` explicitly moves a task packet to `agent_tasks/blocked/` with an operator reason.

Ingestion remains review-only. It does not automatically mark tasks done.

## Operator Commands

```powershell
python -m ai_orchestrator.codex_queue.operator_cli status --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli create-demo-task --queue-root agent_tasks --task-id ORCH-DEMO-002-CLI-DOCS-TASK
python -m ai_orchestrator.codex_queue.operator_cli approve --queue-root agent_tasks --task-id ORCH-DEMO-002-CLI-DOCS-TASK
python -m ai_orchestrator.codex_queue.operator_cli plan --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli ingest-result --queue-root agent_tasks --result agent_tasks/review/ORCH-DEMO-002-CLI-DOCS-TASK.result.json
python -m ai_orchestrator.codex_queue.operator_cli review --queue-root agent_tasks --task-id ORCH-DEMO-002-CLI-DOCS-TASK
python -m ai_orchestrator.codex_queue.operator_cli mark-done --queue-root agent_tasks --task-id ORCH-DEMO-002-CLI-DOCS-TASK
python -m ai_orchestrator.codex_queue.operator_cli mark-blocked --queue-root agent_tasks --task-id <TASK_ID> --reason "reason"
```

## Demo Lifecycle Completed

Completed the safe demo lifecycle for:

`ORCH-DEMO-002-CLI-DOCS-TASK`

Commands/results:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli create-demo-task --queue-root agent_tasks --task-id ORCH-DEMO-002-CLI-DOCS-TASK
# status: ok

python -m ai_orchestrator.codex_queue.operator_cli approve --queue-root agent_tasks --task-id ORCH-DEMO-002-CLI-DOCS-TASK
# status: ok

python -m ai_orchestrator.codex_queue.operator_cli plan --queue-root agent_tasks
# status: ok
```

Created manual result packet:

```text
agent_tasks/review/ORCH-DEMO-002-CLI-DOCS-TASK.result.json
```

Then ran:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli ingest-result --queue-root agent_tasks --result agent_tasks/review/ORCH-DEMO-002-CLI-DOCS-TASK.result.json
# status: ok

python -m ai_orchestrator.codex_queue.operator_cli review --queue-root agent_tasks --task-id ORCH-DEMO-002-CLI-DOCS-TASK
# status: ok, recommendation: ready_for_operator_done

python -m ai_orchestrator.codex_queue.operator_cli mark-done --queue-root agent_tasks --task-id ORCH-DEMO-002-CLI-DOCS-TASK
# status: ok
```

The demo task packet now exists under:

```text
agent_tasks/done/ORCH-DEMO-002-CLI-DOCS-TASK.task.json
```

The declared demo docs output was intentionally not created:

```powershell
Test-Path docs\ORCH_DEMO_002_CLI_DOCS_TASK_OUTPUT.md
# False
```

## Reports Written

Queue and operator reports:

```text
agent_tasks/reports/latest_queue_status.json
agent_tasks/reports/latest_queue_status.md
agent_tasks/reports/latest_operator_action.json
agent_tasks/reports/latest_operator_action.md
```

Dry-run reports:

```text
agent_tasks/reports/latest_dry_run_report.json
agent_tasks/reports/latest_dry_run_report.md
agent_tasks/reports/dry_run_report_<run_id>.json
```

Result ingestion reports:

```text
agent_tasks/reports/latest_result_ingestion_report.json
agent_tasks/reports/latest_result_ingestion_report.md
agent_tasks/reports/result_ingestion_report_<run_id>.json
```

Task review reports:

```text
agent_tasks/reports/ORCH-DEMO-002-CLI-DOCS-TASK.review.json
agent_tasks/reports/ORCH-DEMO-002-CLI-DOCS-TASK.review.md
```

Task result artifacts:

```text
docs/ORCH_SYMPHONY_004_TASK_LIFECYCLE_AND_OPERATOR_CLI_RESULT.json
docs/ORCH_SYMPHONY_004_TASK_LIFECYCLE_AND_OPERATOR_CLI.md
```

## What Remains Manual

The operator still manually decides when to run Codex outside this queue system, manually creates or supplies result packets, manually reviews ingestion and review reports, and manually invokes `mark-done` or `mark-blocked`.

There is no autonomous execution, no background worker, no scheduler, no Codex app-server call, and no automatic done marking.

## Validation

Passed:

```powershell
python -m compileall ai_orchestrator tests
pytest tests/test_codex_queue_schema.py tests/test_codex_queue_validator.py tests/test_codex_queue_safety.py tests/test_codex_queue_planner.py tests/test_codex_queue_dry_run_runner.py tests/test_codex_queue_result_schema.py tests/test_codex_queue_result_validator.py tests/test_codex_queue_result_ingestor.py tests/test_codex_queue_operator_cli.py
python -m ai_orchestrator.codex_queue.operator_cli status --queue-root agent_tasks
python -m json.tool agent_tasks/reports/latest_queue_status.json
python -m json.tool agent_tasks/reports/latest_operator_action.json
```

Focused operator CLI tests also passed:

```powershell
pytest tests/test_codex_queue_operator_cli.py
```

Pytest completed successfully. Windows emitted a temp-directory cleanup warning after test completion, but pytest exited with success.

## Safety Confirmation

No Codex automatic execution was added. No Codex app-server was used. No official Symphony runtime was integrated. No Linear/GitHub Issues integration was added. No background worker was added. No scheduler was added. No Telegram/OpenClaw integration was added. No OpenRouter calls were performed. No Polymarket API calls were performed. No network calls were performed. No credentials were accessed. No wallet/trading/payment code was touched. No dispatcher/run_codex/runtime code was modified. No destructive commands were used. Only the explicit demo task was marked done by the operator CLI demo lifecycle.

## Recommended Next Task

`ORCH-SYMPHONY-005-WORKSPACE-WORKTREE-PLANNER-AND-GIT-SAFETY`
