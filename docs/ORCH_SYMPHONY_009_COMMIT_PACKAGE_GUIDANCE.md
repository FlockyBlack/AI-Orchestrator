# ORCH-009 Commit Package Guidance

No commit was performed by ORCH-009. No files were staged.

## Safe Git Status Checklist

Before committing, inspect:

```powershell
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
```

Confirm:

- The branch is the expected operator branch.
- HEAD did not move unexpectedly.
- There are no merge or rebase conflict markers.
- The large pre-existing untracked workspace tree is understood.
- Only intended ORCH/Symphony queue package files are selected for staging.

## Review These Files And Directories

- `ai_orchestrator/codex_queue/safety.py`
- `ai_orchestrator/codex_queue/portability.py`
- `ai_orchestrator/codex_queue/package_readiness.py`
- `ai_orchestrator/codex_queue/operator_cli.py`
- `tests/test_codex_queue_safety.py`
- `tests/test_codex_queue_operator_cli.py`
- `agent_tasks/README.md`
- `agent_tasks/WORKFLOW.md`
- `agent_tasks/OPERATOR_QUICKSTART.md`
- `agent_tasks/NIGHT_RUNNER_WORKFLOW.md`
- `agent_tasks/SCHEDULER_PLAN.md`
- `agent_tasks/templates/`
- selected `agent_tasks/reports/latest_*.json`
- selected `agent_tasks/reports/latest_*.md`
- `docs/ORCH_SYMPHONY_000_REFERENCE_SPIKE.md` through `docs/ORCH_SYMPHONY_009_*`
- `docs/ORCH_SYMPHONY_CODEX_AUTOMATION_CURRENT_STATE.md`
- `docs/ORCH_PILOT_001_REAL_DOCS_HANDOFF_OUTPUT.md`

## Important Warning

This workspace has many pre-existing untracked files. Do not run:

```powershell
git add .
```

Do not use broad recursive staging from the repository root. Review and stage selectively.

## Suggested Selective Add Pattern

Review first, then stage only intended paths. A safe pattern is:

```powershell
git add -- ai_orchestrator/codex_queue/safety.py
git add -- ai_orchestrator/codex_queue/portability.py
git add -- ai_orchestrator/codex_queue/package_readiness.py
git add -- ai_orchestrator/codex_queue/operator_cli.py
git add -- tests/test_codex_queue_safety.py
git add -- tests/test_codex_queue_operator_cli.py
git add -- agent_tasks/OPERATOR_QUICKSTART.md
git add -- agent_tasks/reports/latest_portability_report.json
git add -- agent_tasks/reports/latest_portability_report.md
git add -- agent_tasks/reports/latest_package_readiness.json
git add -- agent_tasks/reports/latest_package_readiness.md
git add -- docs/ORCH_SYMPHONY_CODEX_AUTOMATION_CURRENT_STATE.md
git add -- docs/ORCH_SYMPHONY_009_COMMIT_PACKAGE_GUIDANCE.md
git add -- docs/ORCH_SYMPHONY_009_COMMIT_PACKAGE_PORTABILITY_AND_SAFETY_CLASSIFIER_POLISH_RESULT.json
git add -- docs/ORCH_SYMPHONY_009_COMMIT_PACKAGE_PORTABILITY_AND_SAFETY_CLASSIFIER_POLISH.md
```

Add any earlier ORCH artifacts only after reviewing them individually.

## Suggested Commit Message

```text
Add local Symphony-style Codex automation queue
```

## Not Performed

- No `git add` was run.
- No `git commit` was run.
- No `git push` was run.
- No branch was created.
- No worktree was created.
- No cleanup, reset, or destructive git command was run.
