# ORCH-CODEX-AUTOMATION-025 Real Codex Invocation And Auto-Ingestion

## Summary

Implemented a gated, operator-invoked `codex_cli` executor for plan runs. The executor creates the existing Codex execution packet, writes the prompt, invokes a configured Codex command, captures stdout/stderr/invocation logs, requires the result JSON at the configured path, validates the Codex result envelope, automatically ingests accepted results, refreshes state/dashboard, and continues within the operator's `--max-steps` limit.

## Operator Command

```powershell
python -m ai_orchestrator.codex_queue.operator_cli continue-plan ^
  --run-id <RUN_ID> ^
  --queue-root agent_tasks ^
  --executor codex_cli ^
  --max-steps 3 ^
  --auto-ingest ^
  --allow-real-codex-invocation ^
  --continue-until blocked_or_done
```

## Safety Gates

- Real invocation requires `--executor codex_cli`.
- Real invocation requires `--allow-real-codex-invocation`.
- The `codex_cli` executor requires `--auto-ingest`.
- Config must exist at `agent_tasks/config/codex_executor_config.json` or an explicit `--codex-config` path.
- Config must set `enabled: true`.
- Config validation rejects network, browser, auth, real-trading, disabled logging, and multi-step Codex invocations.
- Missing executable, non-zero exit, missing result JSON, invalid result JSON, safety failures, and ingestion rejection stop the run.

## Added Surfaces

- `ai_orchestrator/codex_queue/codex_cli_executor.py`
- `RealCodexCliExecutor` in `ai_orchestrator/codex_queue/task_executor.py`
- `codex_cli` executor mode in `LongRunController`
- `run-plan` and `continue-plan` flags:
  - `--executor codex_cli`
  - `--auto-ingest`
  - `--allow-real-codex-invocation`
  - `--codex-config`
  - `--codex-timeout-seconds`
- Operator CLI commands:
  - `test-codex-cli-config`
  - `print-codex-cli-command`
- Operator panel Codex CLI page and run controls with explicit approval text.
- Disabled-by-default example config at `agent_tasks/config/codex_executor_config.example.json`.

## Fake Integration

The integration artifact is under:

`agent_tasks/generated/fake_integration/real_codex_invocation_025/`

It uses `tests/fake_codex_command.py` as the configured command and demonstrates:

- queue creation
- `continue-plan --executor codex_cli --auto-ingest --allow-real-codex-invocation`
- automatic prompt delivery by stdin/env/path contract
- fake command writing `codex_result.json`
- automatic result validation and ingestion
- state/dashboard update
- no manual prompt or result copy/paste

## Validation

Commands run:

```powershell
python -m compileall ai_orchestrator
python -m pytest tests/test_codex_cli_executor_config.py tests/test_codex_cli_executor_invocation.py tests/test_operator_cli_real_codex_executor.py tests/test_operator_panel_real_codex_executor.py
python -m pytest tests/test_codex_automation_dashboard.py tests/test_codex_cli_dry_run_executor.py tests/test_codex_cli_executor_config.py tests/test_codex_cli_executor_invocation.py tests/test_codex_commit_push_verify.py tests/test_codex_controller_recovery.py tests/test_codex_controller_resume.py tests/test_codex_execution_lock.py tests/test_codex_execution_packet.py tests/test_codex_executor_contract.py tests/test_codex_handoff_loop.py tests/test_codex_long_run_controller.py tests/test_codex_memory_hooks.py tests/test_codex_operator_cli_plan_runner.py tests/test_codex_operator_cli_resume_recovery.py tests/test_codex_packet_executor.py
python -m pytest tests/test_codex_plan_contract.py tests/test_codex_plan_decomposer.py tests/test_codex_plan_recovery.py tests/test_codex_plan_run_state.py tests/test_codex_plan_to_queue.py tests/test_codex_queue_codex_cli_batch_runner.py tests/test_codex_queue_codex_cli_postprocessor.py tests/test_codex_queue_codex_cli_runner.py tests/test_codex_queue_dry_run_runner.py tests/test_codex_queue_git_safety.py tests/test_codex_queue_manifest_resume.py tests/test_codex_queue_morning_report.py tests/test_codex_queue_night_runner.py tests/test_codex_queue_operator_cli.py tests/test_codex_queue_planner.py
python -m pytest tests/test_codex_queue_pmbot_templates.py tests/test_codex_queue_queue_health.py tests/test_codex_queue_result_ingestor.py tests/test_codex_queue_result_schema.py tests/test_codex_queue_result_validator.py tests/test_codex_queue_runbook.py tests/test_codex_queue_safety.py tests/test_codex_queue_scheduler_plan.py tests/test_codex_queue_schema.py tests/test_codex_queue_validator.py tests/test_codex_queue_workspace_planner.py tests/test_codex_result_acceptance_policy.py tests/test_codex_result_ingestion.py tests/test_codex_selective_staging_planner.py tests/test_codex_state_consistency.py tests/test_codex_task_executor.py tests/test_codex_worktree_lane_manager.py tests/test_operator_cli_codex_adapter.py tests/test_operator_cli_real_codex_executor.py tests/test_operator_panel_actions.py tests/test_operator_panel_app_smoke.py tests/test_operator_panel_codex_adapter.py tests/test_operator_panel_continue_recover.py tests/test_operator_panel_real_codex_executor.py tests/test_operator_panel_renderer.py tests/test_operator_panel_run_detail.py tests/test_operator_panel_state.py
```

Result: all targeted and relevant Codex queue/operator panel tests passed.
