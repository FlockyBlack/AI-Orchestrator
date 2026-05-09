# ORCH-SYMPHONY-005 Workspace Worktree Planner and Git Safety

Task: `ORCH-SYMPHONY-005-WORKSPACE-WORKTREE-PLANNER-AND-GIT-SAFETY`

Status: `completed`

## What Git Safety Adds

Added `ai_orchestrator/codex_queue/git_safety.py`, a local-only read-only git inspection layer.

It records:

- repository root
- current branch
- current HEAD
- `git status --short` lines
- clean/dirty state
- tracked change count
- untracked file count
- warnings
- blocking errors

It also adds branch-name validation and safe branch-name construction for `codex/<task-id>` branches. Suggested branch names are lowercase and restricted to letters, numbers, dash, and slash.

Conflict-like status lines such as `UU`, `AA`, `DU`, and related unmerged states block workspace planning. Tracked local changes warn and require operator review. Many untracked files warn but do not block by default.

## What Workspace Planning Adds

Added `ai_orchestrator/codex_queue/workspace_planner.py`, which creates a no-execution workspace plan for one approved or planned task packet.

The plan includes:

- suggested safe branch name
- suggested worktree path outside the repository root
- allowed paths
- forbidden paths
- acceptance checks
- expected outputs
- git state
- human review requirement
- proof-of-work requirement
- warnings and blocking errors

The plan explicitly records:

- `branch_created: false`
- `worktree_created: false`
- `codex_execution_enabled: false`
- `codex_app_server_used: false`

## Why No Real Worktree Was Created

This task is deliberately dry-run only. It prepares the operator review layer before any branch or worktree operation is allowed.

The new planner suggests:

```text
../AI-Orchestrator-worktrees/<sanitized-task-id>
```

but it does not create that path, does not call `git worktree add`, and does not create a branch.

## Operator Usage

New command:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli workspace-plan --queue-root agent_tasks --task-id <TASK_ID>
```

For a planned task, it writes:

```text
agent_tasks/planned/<TASK_ID>.workspace_plan.json
agent_tasks/reports/<TASK_ID>.workspace_plan.md
agent_tasks/reports/latest_workspace_plan.json
agent_tasks/reports/latest_workspace_plan.md
```

It exits zero when the plan status is `planned` and non-zero when the plan status is `blocked`.

It does not move task status, run tests, run Codex, call Codex app-server, create branches, create worktrees, commit, push, or call network services.

## Handoff Prompt Context

Handoff prompt generation now checks for:

```text
agent_tasks/planned/<TASK_ID>.workspace_plan.json
```

When present, future generated handoff prompts include:

- suggested branch name
- suggested worktree path
- workspace allowed paths
- workspace forbidden paths
- a note that branch/worktree creation is still manual unless separately approved
- a note that Codex must not work outside allowed paths

The demo handoff was regenerated after the workspace plan existed and verified to include this context.

## Demo Flow

Demo task:

```text
ORCH-DEMO-003-WORKSPACE-PLAN
```

Commands:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli create-demo-task --queue-root agent_tasks --task-id ORCH-DEMO-003-WORKSPACE-PLAN
# status: ok

python -m ai_orchestrator.codex_queue.operator_cli approve --queue-root agent_tasks --task-id ORCH-DEMO-003-WORKSPACE-PLAN
# status: ok

python -m ai_orchestrator.codex_queue.operator_cli plan --queue-root agent_tasks
# status: ok

python -m ai_orchestrator.codex_queue.operator_cli status --queue-root agent_tasks
# status: ok

python -m ai_orchestrator.codex_queue.operator_cli workspace-plan --queue-root agent_tasks --task-id ORCH-DEMO-003-WORKSPACE-PLAN
# status: ok
# warning: working tree has many untracked files: 370

python -m json.tool agent_tasks/reports/latest_workspace_plan.json
# passed

python -m ai_orchestrator.codex_queue.operator_cli plan --queue-root agent_tasks
# status: ok; regenerated handoff prompt after workspace plan existed
```

Workspace plan result:

```text
agent_tasks/planned/ORCH-DEMO-003-WORKSPACE-PLAN.workspace_plan.json
agent_tasks/reports/ORCH-DEMO-003-WORKSPACE-PLAN.workspace_plan.md
agent_tasks/reports/latest_workspace_plan.json
agent_tasks/reports/latest_workspace_plan.md
```

Suggested demo branch:

```text
codex/orch-demo-003-workspace-plan
```

Suggested demo worktree:

```text
C:\Users\OpenC\.openclaw\AI-Orchestrator-worktrees\orch-demo-003-workspace-plan
```

This path was suggested only. It was not created.

## Validation

Passed:

```powershell
python -m compileall ai_orchestrator tests
```

Passed:

```powershell
pytest tests/test_codex_queue_schema.py tests/test_codex_queue_validator.py tests/test_codex_queue_safety.py tests/test_codex_queue_planner.py tests/test_codex_queue_dry_run_runner.py tests/test_codex_queue_result_schema.py tests/test_codex_queue_result_validator.py tests/test_codex_queue_result_ingestor.py tests/test_codex_queue_operator_cli.py tests/test_codex_queue_git_safety.py tests/test_codex_queue_workspace_planner.py
# 70 passed
```

Pytest emitted an ignored Windows temp cleanup warning after success, but exited successfully.

Passed:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli status --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli workspace-plan --queue-root agent_tasks --task-id ORCH-DEMO-003-WORKSPACE-PLAN
python -m json.tool agent_tasks/reports/latest_workspace_plan.json
```

## How This Prepares Controlled Codex Execution

The queue now has a separate operator-reviewed planning stage for local workspace preparation. Before any future manual Codex run, the operator can inspect the current git state, suggested branch, suggested worktree path, allowed paths, forbidden paths, acceptance checks, and safety warnings.

This creates the missing review artifact needed before a later controlled manual Codex runbook. The next task should define the operator-approved manual execution procedure without adding autonomous workers or schedulers.

## Recommended Next Task

`ORCH-SYMPHONY-006-CONTROLLED-MANUAL-CODEX-RUNBOOK-AND-MORNING-REPORT`

## Safety Confirmation

No real git branch was created. No real git worktree was created. No git commit was performed. No git push was performed. No Codex automatic execution was added. No Codex app-server was used. No official Symphony runtime was integrated. No Linear/GitHub Issues integration was added. No background worker was added. No scheduler was added. No Telegram/OpenClaw integration was added. No OpenRouter calls were performed. No Polymarket API calls were performed. No network calls were performed. No credentials were accessed. No wallet/trading/payment code was touched. No dispatcher/run_codex/runtime code was modified. No destructive commands were used.
