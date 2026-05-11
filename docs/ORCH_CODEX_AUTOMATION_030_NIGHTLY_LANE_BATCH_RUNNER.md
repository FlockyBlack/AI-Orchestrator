# ORCH-CODEX-AUTOMATION-030 Nightly Lane Batch Runner

This task adds an operator-started nightly lane batch runner for controlled Codex task execution. It is not a scheduler, daemon, background worker, or autonomous loop.

## Batch Plan Contract

The deterministic plan contract is `nightly_lane_batch_plan.v1`, with JSON Schema at `contracts/nightly_lane_batch_plan.schema.json`.

Required top-level fields:

- `batch_id`
- `tasks`
- `expected_base_head`
- `lane_mode`
- `max_steps_per_task`
- `executor_mode`
- `safety_flags`
- `stop_policy`
- `allow_real_codex_invocation`

Supported modes:

- `lane_mode`: `plan_only`, `create_or_reuse`
- `executor_mode`: `fake`, `codex_cli_dry_run`, `codex_cli`
- `stop_policy`: `stop_on_first_blocker`, `continue_on_task_blocker`

The safe default is fake execution. Real Codex CLI execution requires both:

- plan field `allow_real_codex_invocation: true`
- CLI flag `--allow-real-codex-invocation`

## CLI

Dry-run example:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-nightly-lane-batch `
  --queue-root agent_tasks `
  --plan-file agent_tasks/plans/nightly_lane_batch_plan.json `
  --dry-run
```

Fake lane execution example:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-nightly-lane-batch `
  --queue-root agent_tasks `
  --plan-file agent_tasks/plans/nightly_lane_batch_plan.json
```

The runner validates the repo branch, expected base head, and dirty-tree state before lane creation or execution.

## Reports

The runner writes:

- `agent_tasks/reports/latest_nightly_lane_batch_report.json`
- `agent_tasks/reports/latest_nightly_lane_batch_report.md`
- timestamped JSON and Markdown reports

Reports include per-task status, lane path, branch, selected subagent profile, test summary placeholder, blocker reason, next action, and overall safety summary.

## Safety

The runner does not:

- register schedulers
- create daemons
- start background workers
- use browser automation
- call external APIs directly
- access credentials
- touch wallets, signing, orders, or trading endpoints
- enable autonomous trading
- stage, commit, push, ingest results, review results, or mark tasks done automatically
