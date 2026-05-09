# ORCH Symphony 010 Intended Staging Inventory

## Scope

This inventory defines the intended commit package for the local Symphony-style Codex automation queue. It is intentionally narrow because the repository has a large pre-existing untracked workspace.

Track only these package areas:

- `ai_orchestrator/codex_queue/*.py`
- `tests/test_codex_queue_*.py`
- `tests/conftest.py`
- queue documentation under `agent_tasks/*.md`
- queue templates under `agent_tasks/templates/*.json`
- ORCH Symphony package documentation under `docs/ORCH_SYMPHONY_*.md` and `docs/ORCH_SYMPHONY_*.json`
- the pilot evidence document `docs/ORCH_PILOT_001_REAL_DOCS_HANDOFF_OUTPUT.md`

Do not use broad staging from the repository root.

## Recommended To Track

### Source

- `ai_orchestrator/codex_queue/__init__.py`
- `ai_orchestrator/codex_queue/dry_run_runner.py`
- `ai_orchestrator/codex_queue/files.py`
- `ai_orchestrator/codex_queue/git_safety.py`
- `ai_orchestrator/codex_queue/morning_report.py`
- `ai_orchestrator/codex_queue/night_runner.py`
- `ai_orchestrator/codex_queue/operator_cli.py`
- `ai_orchestrator/codex_queue/package_readiness.py`
- `ai_orchestrator/codex_queue/planner.py`
- `ai_orchestrator/codex_queue/portability.py`
- `ai_orchestrator/codex_queue/queue_health.py`
- `ai_orchestrator/codex_queue/report_writer.py`
- `ai_orchestrator/codex_queue/result_ingestor.py`
- `ai_orchestrator/codex_queue/result_schema.py`
- `ai_orchestrator/codex_queue/result_validator.py`
- `ai_orchestrator/codex_queue/runbook.py`
- `ai_orchestrator/codex_queue/safety.py`
- `ai_orchestrator/codex_queue/scheduler_plan.py`
- `ai_orchestrator/codex_queue/schema.py`
- `ai_orchestrator/codex_queue/validator.py`
- `ai_orchestrator/codex_queue/workspace_planner.py`

### Tests

- `tests/conftest.py`
- `tests/test_codex_queue_dry_run_runner.py`
- `tests/test_codex_queue_git_safety.py`
- `tests/test_codex_queue_morning_report.py`
- `tests/test_codex_queue_night_runner.py`
- `tests/test_codex_queue_operator_cli.py`
- `tests/test_codex_queue_planner.py`
- `tests/test_codex_queue_queue_health.py`
- `tests/test_codex_queue_result_ingestor.py`
- `tests/test_codex_queue_result_schema.py`
- `tests/test_codex_queue_result_validator.py`
- `tests/test_codex_queue_runbook.py`
- `tests/test_codex_queue_safety.py`
- `tests/test_codex_queue_scheduler_plan.py`
- `tests/test_codex_queue_schema.py`
- `tests/test_codex_queue_validator.py`
- `tests/test_codex_queue_workspace_planner.py`

### Queue Docs And Templates

- `agent_tasks/ARTIFACT_POLICY.md`
- `agent_tasks/NIGHT_RUNNER_WORKFLOW.md`
- `agent_tasks/OPERATOR_QUICKSTART.md`
- `agent_tasks/README.md`
- `agent_tasks/SCHEDULER_PLAN.md`
- `agent_tasks/WORKFLOW.md`
- `agent_tasks/templates/blocked_trading.example.task.json`
- `agent_tasks/templates/codex_task_packet.v1.template.json`
- `agent_tasks/templates/local_code_tests.example.task.json`
- `agent_tasks/templates/local_docs_only.example.task.json`

### Package Docs

- `docs/ORCH_PILOT_001_REAL_DOCS_HANDOFF_OUTPUT.md`
- all current `docs/ORCH_SYMPHONY_*.md`
- all current `docs/ORCH_SYMPHONY_*.json`
- `docs/ORCH_SYMPHONY_CODEX_AUTOMATION_CURRENT_STATE.md`
- `docs/ORCH_SYMPHONY_CODEX_AUTOMATION_FINAL_REVIEW.md`

## Excluded Runtime State

The following queue areas are generated runtime state and should stay untracked unless an operator deliberately chooses a small sample fixture or milestone evidence file:

- `agent_tasks/inbox/`
- `agent_tasks/approved/`
- `agent_tasks/planned/`
- `agent_tasks/review/`
- `agent_tasks/done/`
- `agent_tasks/blocked/`
- `agent_tasks/reports/`
- `agent_tasks/running/`

Current generated examples in those directories include task packets, handoff prompts, dry-run plans, workspace plans, review packets, status reports, morning reports, night dry-run plans, package-readiness reports, and portability reports. They are useful operational evidence, but they are not source package files.

## Excluded Unknown Workspace Material

The root status includes many unrelated pre-existing untracked files and directories: workspace memory files, OpenClaw and merchant pipeline files, PMBOT/OpenRouter docs, AUTOPILOT/FLOCKY docs, temporary scripts, logs, state, schemas, and Python bytecode. These are outside the ORCH Symphony package boundary and should not be staged as part of this task.

`ai_orchestrator/__init__.py` is also left out because the requested package boundary is `ai_orchestrator/codex_queue/`. If the operator wants the parent package marker in the commit, add that explicitly in a later approved commit task.

## Warnings

- `git add .`, `git add -A`, and `git add --all` are forbidden for this workspace.
- Directory adds are risky because untracked bytecode and unrelated files exist under package-adjacent directories.
- There is no root `.gitignore` file. This task does not modify `.gitignore`; any ignore policy should be reviewed separately.
- Historical ORCH Symphony docs include local absolute paths as audit evidence. That is acceptable for the docs package, but review them before committing.
