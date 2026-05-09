# ORCH Codex Reliability 001 - Batch Evidence And Report Persistence

Task ID: `ORCH-CODEX-RELIABILITY-001-BATCH-EVIDENCE-AND-REPORT-PERSISTENCE`

Date: `2026-05-09`

Scope: harden the Codex queue evidence layer for large post-batch review runs. This task does not add PMBOT product modules, does not execute Codex, does not run batches, does not mark tasks done, and does not touch runtime, dispatcher, wallet, private-key, order, or trading paths.

## Problem

The 20-task post-batch review exposed a report-persistence weakness. Result ingestion used second-level run IDs, so multiple tasks created the same `result_ingestion_report_<RUN_ID>.json` name in the same second. That made per-task ingestion evidence collide while the mutable `latest_result_ingestion_report.json` pointer kept moving.

The result was operationally confusing:

- Stable per-task ingestion reports were overwritten.
- `latest_result_ingestion_report.json` represented only the most recent ingestion.
- Post-batch summaries needed stronger per-task traceability.
- Operators needed a clear rule for what evidence should be committed and what should stay untracked.

## Implementation

Result ingestion report filenames are generated in `ai_orchestrator/codex_queue/result_ingestor.py`.

The stable report path now uses a collision-resistant report ID:

```text
agent_tasks/reports/result_ingestion_report_<task-slug>_<UTC-high-resolution-timestamp>_<uuid8>.json
```

The ID is created before report persistence and includes:

- a safe task slug,
- a UTC timestamp with microseconds,
- an 8-character UUID suffix.

The mutable convenience files still exist:

```text
agent_tasks/reports/latest_result_ingestion_report.json
agent_tasks/reports/latest_result_ingestion_report.md
```

They are explicitly documented and tagged as mutable pointers. Stable ingestion evidence is the task-specific `result_ingestion_report_*.json` file, not `latest_result_ingestion_report.*`.

## Batch Review Ledger

Post-batch processing now writes a batch-wide ledger alongside the summary:

```text
agent_tasks/reports/batch_review_ledger_<RUN_ID>.json
agent_tasks/reports/latest_batch_review_ledger.json
```

The timestamped ledger is stable evidence. The `latest_batch_review_ledger.json` file is a mutable pointer.

The ledger records:

- batch report path,
- batch run ID and status,
- task IDs,
- per-task execution report paths,
- bridged result JSON paths,
- result validation status,
- stable ingestion report paths,
- review report paths,
- review recommendation per task,
- blocked and failed task IDs,
- next operator action,
- safety booleans confirming no mark-done, commit, push, scheduler, daemon, or background worker was performed by postprocess.

Post-batch task rows also expose direct `ingestion_report_json`, `ingestion_latest_report_json`, and `review_report_json` fields for faster operator inspection.

## Latest Pointer Policy

`latest_*` files are convenience pointers only. They are useful for dashboards, quick local inspection, and CLI summaries, but they are not authoritative evidence for a batch or task.

Authoritative evidence is stable, timestamped, task-specific, or batch-specific:

- `agent_tasks/reports/result_ingestion_report_<task-slug>_<timestamp>_<uuid8>.json`
- `agent_tasks/reports/post_batch_review_summary_<run-id>.json`
- `agent_tasks/reports/batch_review_ledger_<run-id>.json`
- `agent_tasks/reports/<TASK_ID>.review.json`
- `agent_tasks/review/<TASK_ID>.result.json`
- per-task execution reports linked from the batch report

`operator_cli.find_allowed_ingestion_report()` and queue health ingestion checks now use stable `result_ingestion_report_*.json` files for allowance decisions. They still surface the latest pointer as metadata, but do not treat it as authorization evidence.

## Report Retention

Keep stable evidence for any committed or reviewed batch:

- batch execution JSON and Markdown report,
- post-batch review summary JSON and Markdown report,
- batch review ledger JSON,
- per-task execution report JSON,
- per-task bridged result JSON,
- per-task ingestion report JSON,
- per-task review JSON and Markdown report.

Mutable pointers may remain in the local workspace but should not be used as proof:

- `latest_result_ingestion_report.*`
- `latest_post_batch_review_summary.*`
- `latest_batch_review_ledger.json`
- other `latest_*` queue reports

Commit policy:

- Commit source code, tests, documentation, and intentionally curated stable evidence for the task being finalized.
- Do not commit `latest_*` files as proof unless a task explicitly asks for a local pointer snapshot.
- Do not commit bulk generated run histories, `.pyc` files, temporary test output, local logs, or unrelated task artifacts.

## Untracked Artifact Policy

This workspace has many pre-existing untracked files because prior local operator runs, drafts, PMBOT artifacts, generated queue reports, and temporary validation output were created in the working tree before this task.

Because of that, broad staging is forbidden:

```text
git add .
git add -A
git add --all
```

Use selective staging only. Stage exact files that belong to the current task. Generated artifacts are safe to commit only when they are stable evidence for the current task, intentionally reviewed, and listed in the task report.

Keep these untracked unless a task explicitly approves them:

- `agent_tasks/reports/latest_*`
- ad hoc batch reports not needed as stable evidence,
- local logs,
- temp files,
- cache directories,
- `__pycache__/`,
- draft PMBOT/OpenRouter/LLM files outside the task scope,
- any credential, wallet, auth, profile, or runtime files.

## Validation Replay

A full replay command is still a follow-up. The natural next command should read a saved `batch_review_ledger_<RUN_ID>.json`, confirm every referenced stable evidence file exists, re-run result schema validation against bridged result JSON, re-check ingestion/review recommendations, and emit a local-only replay report.

This task deliberately documents that next step instead of adding a broader replay engine.

## Operator Rule

Queue `done/` means the automation task lifecycle completed. It does not mean PMBOT product artifact approval. PMBOT product artifacts still need explicit human/operator review records before their product status should be trusted.
