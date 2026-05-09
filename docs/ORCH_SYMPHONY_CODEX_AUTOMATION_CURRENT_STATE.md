# ORCH Symphony Codex Automation Current State

## Built So Far

- ORCH-000 inspected official Symphony as a reference only. No official runtime was installed.
- ORCH-001 created the local file queue shape under `agent_tasks/` with task packet templates, schema expectations, validation, and safety boundaries.
- ORCH-002 added dry-run planning and handoff prompt generation for approved local tasks.
- ORCH-003 added manual result packet schema, validation, ingestion, and proof-of-work checks.
- ORCH-004 added the operator CLI for status, task creation, approval, planning, ingestion, review, done, and blocked transitions.
- ORCH-005 added read-only git safety inspection and workspace/branch/worktree planning reports. It does not create branches or worktrees.
- ORCH-006 added the controlled manual Codex runbook and morning report.
- ORCH-007 added night dry-run planning and scheduler readiness documentation. It does not register a scheduler.
- ORCH-008 completed one real manual docs-only pilot: `ORCH-PILOT-001-REAL-DOCS-HANDOFF`.
- ORCH-009 polished negation-aware safety text scanning, added portability and package readiness reports, added this current-state documentation, and added commit guidance.

## What Works

- Local task packets can be created, validated, approved, planned, and reviewed.
- Safety classification blocks explicit risk flags and non-negated dangerous intent.
- Protective negative wording such as `Do not call OpenRouter`, `No trading`, `Do not touch wallet code`, and `Do not modify dispatcher` no longer blocks by itself.
- Dry-run planning writes task plans and handoff prompts without executing Codex or acceptance checks.
- Workspace planning reports suggested branch/worktree names without creating either.
- Manual result ingestion validates result packets and does not execute result commands.
- Review reports gate the final explicit `mark-done` step.
- Morning report, next-actions, night dry-run, scheduler-plan, portability-check, and package-readiness commands write local reports.

## Command Examples

```powershell
python -m ai_orchestrator.codex_queue.operator_cli status --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli create-demo-task --queue-root agent_tasks --task-id ORCH-DEMO-LOCAL
python -m ai_orchestrator.codex_queue.operator_cli approve --queue-root agent_tasks --task-id ORCH-DEMO-LOCAL
python -m ai_orchestrator.codex_queue.operator_cli plan --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli workspace-plan --queue-root agent_tasks --task-id ORCH-DEMO-LOCAL
python -m ai_orchestrator.codex_queue.operator_cli runbook --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli ingest-result --queue-root agent_tasks --result agent_tasks/review/ORCH-DEMO-LOCAL.result.json
python -m ai_orchestrator.codex_queue.operator_cli review --queue-root agent_tasks --task-id ORCH-DEMO-LOCAL
python -m ai_orchestrator.codex_queue.operator_cli mark-done --queue-root agent_tasks --task-id ORCH-DEMO-LOCAL
python -m ai_orchestrator.codex_queue.operator_cli morning-report --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli next-actions --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli night-dry-run --queue-root agent_tasks --max-tasks 5
python -m ai_orchestrator.codex_queue.operator_cli scheduler-plan --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli portability-check --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli package-readiness --queue-root agent_tasks
```

## Still Manual

- Task packet authoring and approval.
- Reading generated plans, workspace plans, and handoff prompts.
- Running Codex manually with a generated handoff prompt.
- Writing the result JSON into `agent_tasks/review/`.
- Ingesting, reviewing, and marking done.
- Selectively staging and committing package files.
- Any future branch/worktree creation.
- Any future scheduler registration.

## Intentionally Not Enabled

- No autonomous execution.
- No Codex automatic execution.
- No Codex app-server usage.
- No official Symphony runtime integration.
- No Linear or GitHub Issues integration.
- No Telegram/OpenClaw integration.
- No scheduler registration.
- No background worker.
- No network calls.
- No credential access.
- No wallet, trading, order, or payment handling.
- No dispatcher, `run_codex`, or runtime execution changes.

## ORCH-009 Reports

- Portability JSON: `agent_tasks/reports/latest_portability_report.json`
- Portability Markdown: `agent_tasks/reports/latest_portability_report.md`
- Package readiness JSON: `agent_tasks/reports/latest_package_readiness.json`
- Package readiness Markdown: `agent_tasks/reports/latest_package_readiness.md`
- Commit guidance: `docs/ORCH_SYMPHONY_009_COMMIT_PACKAGE_GUIDANCE.md`

## Next Recommended Task

`ORCH-SYMPHONY-010-SELECTIVE-GIT-STAGING-AND-FINAL-REVIEW`

The next task should review the dirty worktree, selectively stage only intended queue/package files, and perform a final pre-commit review. It should still avoid `git add .`.
