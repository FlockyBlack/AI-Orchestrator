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

## Execution Guardrails

The command is not a scheduler, daemon, background worker, or infinite loop. It runs once, stops on the first failed task, git preflight error, or out-of-band git state change, and writes JSON and Markdown batch reports.

The batch runner does not create tasks, approve tasks, ingest results, review results, mark tasks done, commit, push, call network services directly, access credentials, call OpenRouter, call Polymarket APIs, access wallets or private keys, place orders, or change runtime/dispatcher wiring.

## Morning Inspection

After a night run, inspect:

- `agent_tasks/reports/latest_codex_cli_batch_report.json`
- `agent_tasks/reports/latest_codex_cli_batch_report.md`
- per-task execution reports linked from the batch report
- result packets under `agent_tasks/review/`

What remains manual after execution: inspect each result, run `ingest-result`, run `review`, decide whether to `mark-done`, then selectively commit and push accepted task outputs.
