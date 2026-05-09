# ORCH Symphony Codex Automation Final Review

## What Works Now

The local Codex automation layer is implemented as a manual, file-backed queue. It supports task packet templates, schema validation, safety classification, dry-run planning, handoff prompt generation, manual result ingestion, review gating, operator CLI reporting, git safety inspection, workspace/worktree dry-run planning, runbooks, morning reports, night dry-runs, scheduler plan documentation, portability checks, package readiness checks, and one successful real docs-only pilot.

Safety remains manual and conservative:

- no automatic Codex execution
- no Codex app-server calls
- no scheduler registration
- no background worker
- no branch or worktree creation by the queue
- no network calls
- no credential access
- no wallet, trading, order, or payment handling
- no dispatcher or runtime execution changes

## Operator Commands

Run from repository root:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli status --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli package-readiness --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli portability-check --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli morning-report --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli next-actions --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli night-dry-run --queue-root agent_tasks --max-tasks 5
python -m ai_orchestrator.codex_queue.operator_cli scheduler-plan --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli runbook --queue-root agent_tasks
```

## Manual Queue Flow

Use a template from `agent_tasks/templates/`, or create a local demo packet:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli create-demo-task --queue-root agent_tasks --task-id ORCH-DEMO-MANUAL
```

Review the task in `agent_tasks/inbox/`, then explicitly approve and plan it:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli approve --queue-root agent_tasks --task-id ORCH-DEMO-MANUAL
python -m ai_orchestrator.codex_queue.operator_cli plan --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli workspace-plan --queue-root agent_tasks --task-id ORCH-DEMO-MANUAL
python -m ai_orchestrator.codex_queue.operator_cli runbook --queue-root agent_tasks
```

Open and review the generated handoff prompt:

```text
agent_tasks/planned/<TASK_ID>.handoff_prompt.md
```

Run Codex manually in the operator-selected environment. The queue does not execute Codex. Put the returned result packet at:

```text
agent_tasks/review/<TASK_ID>.result.json
```

Then ingest, review, and mark done only if the review gate recommends acceptance:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli ingest-result --queue-root agent_tasks --result agent_tasks/review/<TASK_ID>.result.json
python -m ai_orchestrator.codex_queue.operator_cli review --queue-root agent_tasks --task-id <TASK_ID>
python -m ai_orchestrator.codex_queue.operator_cli mark-done --queue-root agent_tasks --task-id <TASK_ID>
```

## Reports

Generated reports are local runtime state:

- `agent_tasks/reports/latest_queue_status.*`
- `agent_tasks/reports/latest_package_readiness.*`
- `agent_tasks/reports/latest_portability_report.*`
- `agent_tasks/reports/latest_morning_report.*`
- `agent_tasks/reports/latest_night_dry_run_plan.*`
- `agent_tasks/reports/latest_controlled_codex_runbook.*`
- `agent_tasks/reports/latest_scheduler_plan.*`

These reports are useful for operation, but they should usually remain untracked. They can contain local absolute paths.

## Review Before Commit

Use the inventory and staging plan:

- `docs/ORCH_SYMPHONY_010_INTENDED_STAGING_INVENTORY.md`
- `docs/ORCH_SYMPHONY_010_SAFE_STAGING_PLAN.md`

Run:

```powershell
git status --short
python -m compileall ai_orchestrator tests
pytest tests/test_codex_queue_schema.py tests/test_codex_queue_validator.py tests/test_codex_queue_safety.py tests/test_codex_queue_planner.py tests/test_codex_queue_dry_run_runner.py tests/test_codex_queue_result_schema.py tests/test_codex_queue_result_validator.py tests/test_codex_queue_result_ingestor.py tests/test_codex_queue_operator_cli.py tests/test_codex_queue_git_safety.py tests/test_codex_queue_workspace_planner.py tests/test_codex_queue_queue_health.py tests/test_codex_queue_runbook.py tests/test_codex_queue_morning_report.py tests/test_codex_queue_night_runner.py tests/test_codex_queue_scheduler_plan.py
python -m ai_orchestrator.codex_queue.operator_cli package-readiness --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli portability-check --queue-root agent_tasks
```

If the operator approves staging, use only the explicit `git add -- <file>` commands in `docs/ORCH_SYMPHONY_010_SAFE_STAGING_PLAN.md`. Then inspect:

```powershell
git diff --cached --name-only
git diff --cached --stat
```

## Still Required Before Real Scheduler Or Controlled Execution

Before enabling real unattended execution, create separate approved design and implementation tasks for:

- scheduler registration policy
- background worker design
- execution lock and cancellation behavior
- unattended credential and network policy
- branch/worktree creation policy
- result retention and report cleanup policy
- CI or repeatable validation in a clean checkout
- minimal `.gitignore` policy for bytecode and queue runtime state

## Must Not Be Enabled Without Explicit Approval

Do not enable any of the following without a separate operator-approved task:

- real scheduler registration
- background worker
- automatic Codex execution
- Codex app-server
- official Symphony runtime integration
- Linear or GitHub Issues integration
- Telegram/OpenClaw integration
- OpenRouter calls
- Polymarket API calls
- credential access
- wallet, trading, order, or payment handling
- dispatcher, `run_codex`, or runtime execution code changes
- broad git staging, cleanup, reset, commit, push, branch creation, or worktree creation
