# PMBOT Codex Parallel Worktree Guide

## Summary

This guide defines the local-only Git branch and worktree rules for running multiple Codex tasks against AI-Orchestrator without overlapping writes or changing runtime behavior accidentally.

The default operating model is:

- create one local branch per Codex slot/task
- create one Git worktree per branch
- keep each task inside its assigned write scope
- produce a result JSON for integration review
- merge only through an explicit integration task

No task may add a remote, push, touch secrets, enable wallet signing, or introduce live execution unless a separate approved task explicitly allows it.

## Slot Roles

- `CODEX_A`: core PMBOT feature writer
- `CODEX_B`: dashboard/data contract writer
- `CODEX_C`: Telegram/operator contract writer
- `CODEX_D`: coordination/safety/docs writer
- `CODEX_INTEGRATION`: merge/review only

## Branch Naming

Use a branch name that includes the slot and task id:

- `codex/a-<task-id>`
- `codex/b-<task-id>`
- `codex/c-<task-id>`
- `codex/d-<task-id>`
- `integration/<task-id>`

Branches are local-only unless a later approved GitHub task changes that policy.

## Worktree Path Convention

Use this parent directory:

```text
C:\Users\OpenC\Documents\AI-Orchestrator-worktrees
```

Use this worktree path pattern:

```text
C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\<slot>-<task-id>
```

Examples:

- `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\codex-a-core-paper-pilot`
- `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\codex-b-dashboard-contract-pilot`
- `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\codex-c-telegram-contract-pilot`

Create worktrees with `git worktree add`. Do not manually copy the repository.

## One-Writer-Per-Directory Rule

Only one Codex slot may write to a directory family at a time.

If two tasks need the same directory family, split the work into explicit serial tasks or assign the overlap to `CODEX_INTEGRATION`.

Directory family examples:

- `pm_bot/paper/`
- `pm_bot/dashboard_contracts/`
- `pm_bot/operator_contracts/`
- `docs/`
- `.agents/skills/`
- `scripts/`
- `runtime` or queue/state directories

## Write-Scope Examples

- `CODEX_A` may write `pm_bot/paper/` only if the prompt assigns that scope.
- `CODEX_B` may write `pm_bot/dashboard_contracts/` and dashboard docs only if assigned.
- `CODEX_C` may write `pm_bot/operator_contracts/` and Telegram/operator docs only if assigned.
- `CODEX_D` may write `docs/` and `.agents/skills/` only if assigned.
- `CODEX_INTEGRATION` may merge, review, and resolve conflicts only when the prompt assigns integration authority.

Prompts must name the allowed write scope. If the prompt does not assign a directory, the task must treat it as read-only.

## Forbidden Shared Files Without Explicit Integration Task

Do not edit these shared files unless an explicit integration or infrastructure task assigns them:

- `scripts/dispatcher.py`
- `scripts/run_codex.py`
- runtime files and queue/state files
- `.gitignore`
- shared config
- PMBOT source files outside the assigned scope

When a task needs one of these files, stop and request a dedicated integration/safety task.

## Result Contract

Each Codex task must produce a machine-readable result artifact:

```text
docs/<TASK_ID>_RESULT.json
```

If a different result path is required, it must be named in the task prompt before implementation.

The result JSON should include:

- slot and task id
- status
- summary
- files created or modified
- tests run
- safety flags
- warnings
- blockers
- recommended next task

## Integration Flow

Feature branches do not merge themselves.

The integration task must:

- read each accepted task result JSON
- check changed files against assigned write scopes
- check for overlapping writes
- check tests and safety findings
- verify no secrets or credential files were introduced
- verify no remote, push, live execution, wallet signing, or automation behavior was introduced unless explicitly approved
- merge only after the result is accepted

If conflicts or scope overlap exist, the integration task records the issue and stops unless the prompt explicitly authorizes resolution.

## Flocky/OpenClaw Required

Escalate to Flocky/OpenClaw before implementation when a task touches any of these boundaries:

- network/API boundary changes
- wallet/auth/trading boundary changes
- runtime, dispatcher, or `run_codex` changes
- automation changes
- live execution changes
- broad refactor

These boundaries require explicit safety review before code edits.

## Stop Conditions

Stop and report blocked if any of these occur:

- dirty main branch before worktree creation
- worktree creation conflict
- pilot or task worktree is dirty unexpectedly
- branch mismatch
- overlapping write scopes
- secrets found
- failed tests that cannot be explained as unrelated
- PMBOT source files need edits outside the assigned scope
- GitHub remote or push is required
- network/API/live/trading behavior is needed without approval
- dispatcher or `run_codex` changes are needed without approval
- unsafe boundary expansion

## Cleanup Policy

Keep task worktrees while review or integration is pending.

Before removing a worktree, record:

- worktree path
- branch
- status
- whether changes were merged or intentionally abandoned

Remove only with `git worktree remove <path>` after confirming the worktree is clean or the changes are no longer needed. Do not delete worktree directories manually.

