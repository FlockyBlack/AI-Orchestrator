# PMBOT Task Template Bridge

This bridge creates local-only PMBOT task packets in `agent_tasks/inbox/` for operator review. It does not approve, plan, execute, schedule, or hand off work by itself.

## Supported Template

- `weather-source-monitoring`: creates the PMBOT weather outcome/source monitoring plan-runner packet for `PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE`.

The generated packet uses the normal `codex_task_packet.v1` schema with PMBOT metadata:

- `project`: `PMBOT`
- `task_template.name`: `weather-source-monitoring`
- `task_type`: `local_code_tests`
- local allowed paths for PMBOT weather code, docs, and tests
- explicit forbidden actions and safety boundaries
- validation commands mirrored in `acceptance_checks` and `validation_commands`
- result contract expectations for `codex_task_result.v1`

## Create The Weather Task Packet

Run from the repository root:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli create-pmbot-task --queue-root agent_tasks --task-id PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE --template weather-source-monitoring
```

Optional fields:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli create-pmbot-task --queue-root agent_tasks --task-id PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE --template weather-source-monitoring --repo-root . --branch master --expected-head <HEAD>
```

Review `agent_tasks/inbox/<TASK_ID>.task.json` before approval.

## Approve

Approve only after confirming the packet is local-only and keeps all PMBOT boundaries:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli approve --queue-root agent_tasks --task-id PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE
```

Approval moves the packet from `inbox/` to `approved/` and runs the existing schema and safety classifier gates.

## Generate The Handoff Prompt

Generate the non-executing dry-run plan and handoff prompt:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli plan --queue-root agent_tasks
```

Review:

- `agent_tasks/planned/<TASK_ID>.plan.json`
- `agent_tasks/planned/<TASK_ID>.handoff_prompt.md`
- `agent_tasks/reports/latest_dry_run_report.md`

The plan command does not run Codex, execute validation commands, create branches, create worktrees, call network services, or start any worker.

## Dry-Run The Supervised Codex CLI Runner

Review the generated handoff prompt first, then run the supervised runner dry-run:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-once --queue-root agent_tasks --task-id PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE --dry-run
```

Inspect:

- `agent_tasks/reports/latest_codex_cli_execution_report.md`
- the exact `codex exec` command
- the task packet, plan, handoff prompt, stdout, stderr, and last-message paths

The dry-run does not invoke Codex CLI.

## Run One Supervised Codex CLI Execution

Run exactly one supervised execution:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-codex-once --queue-root agent_tasks --task-id PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE --timeout-seconds 3600
```

The runner passes `agent_tasks/planned/<TASK_ID>.handoff_prompt.md` to `codex exec` through stdin, captures stdout and stderr under `agent_tasks/reports/codex_cli_runs/<TASK_ID>/<RUN_ID>/`, and writes JSON/Markdown execution reports.

This command never approves review, never marks the task done, never ingests the result automatically, never pushes git changes, and never starts a scheduler, daemon, background worker, or multi-task loop.

## Result JSON

Codex should return a `codex_task_result.v1` JSON packet and place it under:

```text
agent_tasks/review/<TASK_ID>.result.json
```

Required shape:

```json
{
  "schema_version": "codex_task_result.v1",
  "task_id": "PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE",
  "status": "completed",
  "completed_by": "manual_codex_handoff",
  "completed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "summary": "",
  "files_created": [],
  "files_modified": [],
  "files_deleted": [],
  "commands_run": [],
  "validation_results": [],
  "acceptance_checks_passed": false,
  "safety_confirmation": {
    "network_calls_performed": 0,
    "credentials_accessed": false,
    "wallet_or_trading_touched": false,
    "runtime_or_dispatcher_touched": false,
    "background_worker_added": false,
    "scheduler_added": false,
    "telegram_or_openclaw_added": false,
    "openrouter_calls_performed": 0,
    "polymarket_api_calls_performed": 0,
    "codex_app_server_used": false,
    "destructive_commands_used": false
  },
  "operator_review_notes": "",
  "next_recommended_action": ""
}
```

Use `partial`, `blocked`, or `failed` instead of `completed` when the work cannot satisfy the acceptance checks or a safety boundary stops progress.

## Review Gate

Ingest the result packet:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli ingest-result --queue-root agent_tasks --result agent_tasks/review/PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE.result.json
```

Generate the review report:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli review --queue-root agent_tasks --task-id PMBOT-PAPERLIVE-010W-002-WEATHER-OUTCOME-SOURCE-MONITORING-PLAN-RUNNER-NO-TRADE
```

Inspect `agent_tasks/reports/<TASK_ID>.review.md`. Run `mark-done` only if the review recommendation is `ready_for_operator_done`.

## Safety Boundaries

The PMBOT template preserves these operator-review limits:

- No wallet/private keys
- No orders
- No trading endpoints
- No OpenRouter calls
- No Polymarket API calls
- No authenticated endpoints
- No runtime/dispatcher/run_codex changes
- No background worker
- No scheduler execution
- No browser automation
- No destructive commands
- No git add .
- No git add -A
- No git add --all
- No force push
- No probability / EV / edge / confidence / side selection
- No buy/sell/hold/enter/exit recommendations
- No market-action guidance
