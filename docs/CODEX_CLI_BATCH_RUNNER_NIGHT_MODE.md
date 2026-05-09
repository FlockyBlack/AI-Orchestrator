# Codex CLI Batch Runner Night Mode

The supervised Codex CLI batch runner is a manually invoked queue command for bounded local batches:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-batch --queue-root agent_tasks --dry-run
```

It selects approved or planned tasks that already have matching plan and handoff prompt artifacts, then either reports the selected order in dry-run mode or invokes the existing one-task runner sequentially.

## Modes

Small batch mode is for a short supervised check. Pass an explicit smaller cap, for example:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-batch --queue-root agent_tasks --max-tasks 3 --dry-run
```

Night mode is the default bounded batch size. Omitting `--max-tasks` selects up to 10 eligible tasks:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-batch --queue-root agent_tasks --dry-run
```

The hard cap is 20 tasks. Values above 20 are rejected before any task execution.

For a larger supervised night batch, explicitly set the cap up to 20 after reviewing the dry-run:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-batch --queue-root agent_tasks --max-tasks 20 --dry-run
python -m ai_orchestrator.codex_queue.operator_cli run-codex-batch --queue-root agent_tasks --max-tasks 20 --timeout-seconds 3600
```

## Execution Guardrails

The command is not a scheduler, daemon, background worker, or infinite loop. It runs once, stops on the first failed task, git preflight error, or out-of-band git state change, and writes JSON and Markdown batch reports.

The batch runner does not create tasks, approve tasks, ingest results, review results, mark tasks done, commit, push, call network services directly, access credentials, call OpenRouter, call Polymarket APIs, access wallets or private keys, place orders, or change runtime/dispatcher wiring.

## Post-Batch Result Bridge

Completed Codex executions write their final message under:

```text
agent_tasks/reports/codex_cli_runs/<TASK_ID>/<RUN_ID>/last_message.md
```

Bridge completed task outputs into queue-compatible result packets with an explicit postprocess command:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli postprocess-codex-batch --queue-root agent_tasks --batch-report agent_tasks/reports/latest_codex_cli_batch_report.json --bridge-results
```

The bridge reads the batch report, each completed execution report, and each `last_message.md`. It writes:

```text
agent_tasks/review/<TASK_ID>.result.json
```

If a task cannot be bridged safely, the postprocess summary records it as blocked and continues with the other completed executions. It does not fake a successful result.

The bridge does not mark tasks done, approve review, commit, push, execute Codex, schedule work, start daemons, or start background workers.

## Optional Post-Batch Review

To bridge results and then run the existing ingestion and review helpers for each successfully bridged task:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli postprocess-codex-batch --queue-root agent_tasks --batch-report agent_tasks/reports/latest_codex_cli_batch_report.json --bridge-results --review-results
```

Review mode still does not run `mark-done`. It only writes ingestion reports and task review reports. The operator must inspect those reports before deciding what to finalize.

Post-batch summaries are written to:

```text
agent_tasks/reports/latest_post_batch_review_summary.json
agent_tasks/reports/latest_post_batch_review_summary.md
```

## Morning Inspection

After a night run, inspect:

- `agent_tasks/reports/latest_codex_cli_batch_report.json`
- `agent_tasks/reports/latest_codex_cli_batch_report.md`
- per-task execution reports linked from the batch report
- result packets under `agent_tasks/review/`
- `agent_tasks/reports/latest_post_batch_review_summary.md` after bridge/review postprocessing

What remains manual after execution: inspect each result and review report, decide whether to `mark-done`, then selectively commit and push accepted task outputs. The bridge/review postprocess step prepares 20-task night batches by removing the manual copy step from `last_message.md` to `agent_tasks/review/`, while keeping final acceptance and git publication explicit.
