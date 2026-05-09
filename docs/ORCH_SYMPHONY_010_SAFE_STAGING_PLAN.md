# ORCH Symphony 010 Safe Staging Plan

## Status

Safe to stage: `true`, after operator review.

No staging was performed by this task. The plan below is the approved shape for a later operator-authorized staging task.

## Forbidden Commands

Do not run:

```powershell
git add .
git add -A
git add --all
```

These commands would sweep in the large pre-existing untracked workspace, generated queue state, Python bytecode, logs, memory files, unrelated project drafts, and runtime artifacts.

## Recommended Explicit Staging Commands

Run only after reviewing `git status --short`, the inventory, and the validation results:

```powershell
git add -- ai_orchestrator/codex_queue/__init__.py ai_orchestrator/codex_queue/dry_run_runner.py ai_orchestrator/codex_queue/files.py ai_orchestrator/codex_queue/git_safety.py ai_orchestrator/codex_queue/morning_report.py ai_orchestrator/codex_queue/night_runner.py ai_orchestrator/codex_queue/operator_cli.py ai_orchestrator/codex_queue/package_readiness.py ai_orchestrator/codex_queue/planner.py ai_orchestrator/codex_queue/portability.py ai_orchestrator/codex_queue/queue_health.py ai_orchestrator/codex_queue/report_writer.py ai_orchestrator/codex_queue/result_ingestor.py ai_orchestrator/codex_queue/result_schema.py ai_orchestrator/codex_queue/result_validator.py ai_orchestrator/codex_queue/runbook.py ai_orchestrator/codex_queue/safety.py ai_orchestrator/codex_queue/scheduler_plan.py ai_orchestrator/codex_queue/schema.py ai_orchestrator/codex_queue/validator.py ai_orchestrator/codex_queue/workspace_planner.py
```

```powershell
git add -- tests/conftest.py tests/test_codex_queue_dry_run_runner.py tests/test_codex_queue_git_safety.py tests/test_codex_queue_morning_report.py tests/test_codex_queue_night_runner.py tests/test_codex_queue_operator_cli.py tests/test_codex_queue_planner.py tests/test_codex_queue_queue_health.py tests/test_codex_queue_result_ingestor.py tests/test_codex_queue_result_schema.py tests/test_codex_queue_result_validator.py tests/test_codex_queue_runbook.py tests/test_codex_queue_safety.py tests/test_codex_queue_scheduler_plan.py tests/test_codex_queue_schema.py tests/test_codex_queue_validator.py tests/test_codex_queue_workspace_planner.py
```

```powershell
git add -- agent_tasks/ARTIFACT_POLICY.md agent_tasks/NIGHT_RUNNER_WORKFLOW.md agent_tasks/OPERATOR_QUICKSTART.md agent_tasks/README.md agent_tasks/SCHEDULER_PLAN.md agent_tasks/WORKFLOW.md agent_tasks/templates/blocked_trading.example.task.json agent_tasks/templates/codex_task_packet.v1.template.json agent_tasks/templates/local_code_tests.example.task.json agent_tasks/templates/local_docs_only.example.task.json
```

```powershell
git add -- docs/ORCH_PILOT_001_REAL_DOCS_HANDOFF_OUTPUT.md docs/ORCH_SYMPHONY_000_REFERENCE_SPIKE.md docs/ORCH_SYMPHONY_000_REFERENCE_SPIKE_RESULT.json docs/ORCH_SYMPHONY_001_ADAPT_SPEC_LOCAL_QUEUE.md docs/ORCH_SYMPHONY_001_ADAPT_SPEC_LOCAL_QUEUE_RESULT.json docs/ORCH_SYMPHONY_002_FIRST_LOCAL_HANDOFF_DRY_RUN.md docs/ORCH_SYMPHONY_002_FIRST_LOCAL_HANDOFF_DRY_RUN_RESULT.json docs/ORCH_SYMPHONY_003_MANUAL_HANDOFF_RESULT_INGESTION.md docs/ORCH_SYMPHONY_003_MANUAL_HANDOFF_RESULT_INGESTION_RESULT.json docs/ORCH_SYMPHONY_004_TASK_LIFECYCLE_AND_OPERATOR_CLI.md docs/ORCH_SYMPHONY_004_TASK_LIFECYCLE_AND_OPERATOR_CLI_RESULT.json
```

```powershell
git add -- docs/ORCH_SYMPHONY_005_WORKSPACE_WORKTREE_PLANNER_AND_GIT_SAFETY.md docs/ORCH_SYMPHONY_005_WORKSPACE_WORKTREE_PLANNER_AND_GIT_SAFETY_RESULT.json docs/ORCH_SYMPHONY_006_CONTROLLED_MANUAL_CODEX_RUNBOOK_AND_MORNING_REPORT.md docs/ORCH_SYMPHONY_006_CONTROLLED_MANUAL_CODEX_RUNBOOK_AND_MORNING_REPORT_RESULT.json docs/ORCH_SYMPHONY_007_NIGHT_RUNNER_DRY_RUN_AND_SCHEDULER_PLAN.md docs/ORCH_SYMPHONY_007_NIGHT_RUNNER_DRY_RUN_AND_SCHEDULER_PLAN_RESULT.json docs/ORCH_SYMPHONY_008_REAL_MANUAL_CODEX_TASK_PILOT_NO_AUTONOMY.md docs/ORCH_SYMPHONY_008_REAL_MANUAL_CODEX_TASK_PILOT_NO_AUTONOMY_RESULT.json docs/ORCH_SYMPHONY_009_COMMIT_PACKAGE_GUIDANCE.md docs/ORCH_SYMPHONY_009_COMMIT_PACKAGE_PORTABILITY_AND_SAFETY_CLASSIFIER_POLISH.md docs/ORCH_SYMPHONY_009_COMMIT_PACKAGE_PORTABILITY_AND_SAFETY_CLASSIFIER_POLISH_RESULT.json docs/ORCH_SYMPHONY_CODEX_AUTOMATION_CURRENT_STATE.md
```

```powershell
git add -- docs/ORCH_SYMPHONY_010_INTENDED_STAGING_INVENTORY.md docs/ORCH_SYMPHONY_010_INTENDED_STAGING_INVENTORY.json docs/ORCH_SYMPHONY_010_SAFE_STAGING_PLAN.md docs/ORCH_SYMPHONY_010_SAFE_STAGING_PLAN.json docs/ORCH_SYMPHONY_010_SELECTIVE_GIT_STAGING_AND_FINAL_REVIEW.md docs/ORCH_SYMPHONY_010_SELECTIVE_GIT_STAGING_AND_FINAL_REVIEW_RESULT.json docs/ORCH_SYMPHONY_CODEX_AUTOMATION_FINAL_REVIEW.md
```

## Pre-Commit Validation

Run before staging or immediately after staging and before committing:

```powershell
python -m compileall ai_orchestrator tests
pytest tests/test_codex_queue_schema.py tests/test_codex_queue_validator.py tests/test_codex_queue_safety.py tests/test_codex_queue_planner.py tests/test_codex_queue_dry_run_runner.py tests/test_codex_queue_result_schema.py tests/test_codex_queue_result_validator.py tests/test_codex_queue_result_ingestor.py tests/test_codex_queue_operator_cli.py tests/test_codex_queue_git_safety.py tests/test_codex_queue_workspace_planner.py tests/test_codex_queue_queue_health.py tests/test_codex_queue_runbook.py tests/test_codex_queue_morning_report.py tests/test_codex_queue_night_runner.py tests/test_codex_queue_scheduler_plan.py
python -m ai_orchestrator.codex_queue.operator_cli status --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli package-readiness --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli portability-check --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli morning-report --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli night-dry-run --queue-root agent_tasks --max-tasks 5
python -m json.tool docs/ORCH_SYMPHONY_009_COMMIT_PACKAGE_PORTABILITY_AND_SAFETY_CLASSIFIER_POLISH_RESULT.json
python -m json.tool agent_tasks/reports/latest_package_readiness.json
python -m json.tool agent_tasks/reports/latest_portability_report.json
```

## Pre-Commit Review

After explicit staging, inspect the staged set:

```powershell
git status --short
git diff --cached --name-only
git diff --cached --stat
```

Confirm that no file under `agent_tasks/reports/`, `agent_tasks/inbox/`, `agent_tasks/approved/`, `agent_tasks/planned/`, `agent_tasks/review/`, `agent_tasks/done/`, `agent_tasks/blocked/`, `agent_tasks/running/`, `__pycache__/`, unrelated docs, wallet/trading/payment code, dispatcher/runtime code, Telegram/OpenClaw integration, OpenRouter integration, or Polymarket code is staged.

## Commit

Suggested commit message:

```text
Add local Symphony-style Codex automation queue
```

Commit only after the operator confirms the staged diff:

```powershell
git commit -m "Add local Symphony-style Codex automation queue"
```

## Post-Commit Verification

Run after the commit:

```powershell
git status --short
git show --stat --name-status HEAD
```

Do not push until the operator separately approves a push.
