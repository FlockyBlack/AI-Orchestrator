# ORCH Symphony 011 Final Staging List

Task: `ORCH-SYMPHONY-011-OPERATOR-APPROVED-SELECTIVE-COMMIT`

Safe to stage: `true`

This list follows `docs/ORCH_SYMPHONY_010_SAFE_STAGING_PLAN.md` and `docs/ORCH_SYMPHONY_010_SAFE_STAGING_PLAN.json`. The recommended commands were checked for forbidden broad staging forms, and no `git add .`, `git add -A`, or `git add --all` command was found.

## Files To Stage

Source files:

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

Tests:

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

Queue docs and templates:

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

Package evidence docs:

- `docs/ORCH_PILOT_001_REAL_DOCS_HANDOFF_OUTPUT.md`
- all ORCH Symphony package docs and result JSON files explicitly listed in the ORCH-010 staging plan, including the ORCH-011 staging and result artifacts.

Total staged-file target: `82`

## Excluded

Runtime queue state remains excluded:

- `agent_tasks/inbox/`
- `agent_tasks/approved/`
- `agent_tasks/planned/`
- `agent_tasks/review/`
- `agent_tasks/done/`
- `agent_tasks/blocked/`
- `agent_tasks/running/`
- `agent_tasks/reports/`

Unrelated workspace files, credentials-adjacent areas, bytecode/cache directories, logs, memory files, runtime folders, merchant/OpenClaw/PMBOT/OpenRouter areas, and temporary scripts remain excluded.

## Validation Gate

The required compile, focused pytest suite, queue CLI checks, and JSON syntax checks passed before staging. Warnings were limited to the expected package-readiness/portability warnings and a pytest Windows temp cleanup warning after the successful pass summary.

## Safety Note

The ORCH-011 result artifact is staged before commit because it matches the allowed `docs/ORCH_SYMPHONY_*.json/md` category. The final commit hash cannot be embedded into the same committed file without an additional amend or second commit, neither of which is approved for this task.
