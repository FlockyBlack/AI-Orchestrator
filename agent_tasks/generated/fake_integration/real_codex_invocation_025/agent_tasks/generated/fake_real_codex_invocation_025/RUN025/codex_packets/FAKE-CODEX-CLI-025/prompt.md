# Codex Execution Packet: FAKE-CODEX-CLI-025

Return only concise JSON matching the exact result template below. Do not include prose outside the JSON object.

## Packet

- packet_id: `cpkt_RUN025_FAKE-CODEX-CLI-025_20260511T122532Z`
- task_id: `FAKE-CODEX-CLI-025`
- run_id: `RUN025`
- plan_id: `fake_real_codex_invocation_025`
- adapter_mode: `codex_cli_operator_approved`
- requires_operator_approval: `True`

## Repository

- repo_root: `.`
- branch: `master`
- expected HEAD: `69b0d6b324d9106d247901df414a97f24a7dfbcb`

## Queue State

- state_path: `agent_tasks\generated\fake_integration\real_codex_invocation_025\agent_tasks\generated\fake_real_codex_invocation_025\RUN025\state.json`
- queue_manifest_path: `agent_tasks\generated\fake_integration\real_codex_invocation_025\agent_tasks\generated\fake_real_codex_invocation_025\RUN025\manifest.json`
- task_spec_path: `agent_tasks\generated\fake_integration\real_codex_invocation_025\agent_tasks\generated\fake_real_codex_invocation_025\RUN025\tasks\FAKE-CODEX-CLI-025.json`

## Allowed Paths

- agent_tasks/generated/fake_integration/real_codex_invocation_025/

## Forbidden Actions

- Do not use `git add .`, `git add -A`, or `git add --all`.
- Do not force push.
- Do not use wallet files, private keys, signing, orders, trading endpoints, or real-money flows.
- Do not use OpenRouter or Polymarket API.
- Do not use authenticated endpoints.
- Do not use browser automation.
- Do not create daemons, schedulers, or background workers.
- Do not use wallet files, private keys, signing, orders, or trading endpoints.
- Do not use OpenRouter or Polymarket API unless a separate task explicitly approves it.

## Acceptance Gates

- Fake command writes codex_result.json.
- Auto-ingestion marks the task done.
- Dashboard is updated.

## Safety Instructions

- Do not use unsafe git staging. Never run `git add .`, `git add -A`, or `git add --all`.
- Do not use force push.
- Do not use wallet files, private keys, signing, orders, trading endpoints, or real-money flows.
- Do not use OpenRouter or Polymarket API unless a separate task explicitly approves it.
- Do not use authenticated endpoints.
- Do not use browser automation.
- Do not create a daemon, scheduler, background worker, or uncontrolled autonomous loop.
- Work on this task only and report blockers instead of inventing success.

## Expected Artifacts

- packet.json: `agent_tasks\generated\fake_integration\real_codex_invocation_025\agent_tasks\generated\fake_real_codex_invocation_025\RUN025\codex_packets\FAKE-CODEX-CLI-025\packet.json`
- prompt.md: `agent_tasks\generated\fake_integration\real_codex_invocation_025\agent_tasks\generated\fake_real_codex_invocation_025\RUN025\codex_packets\FAKE-CODEX-CLI-025\prompt.md`
- expected_result_template.json: `agent_tasks\generated\fake_integration\real_codex_invocation_025\agent_tasks\generated\fake_real_codex_invocation_025\RUN025\codex_packets\FAKE-CODEX-CLI-025\expected_result_template.json`
- ingestion_report.json: `agent_tasks\generated\fake_integration\real_codex_invocation_025\agent_tasks\generated\fake_real_codex_invocation_025\RUN025\codex_packets\FAKE-CODEX-CLI-025\ingestion_report.json`

## Exact Result JSON Template

```json
{
  "acceptance_reasons": [],
  "acceptance_status": "pending_operator_ingestion",
  "adapter_mode": "codex_cli_operator_approved",
  "artifact_paths": [],
  "packet_id": "cpkt_RUN025_FAKE-CODEX-CLI-025_20260511T122532Z",
  "plan_id": "fake_real_codex_invocation_025",
  "received_at": "<ISO-8601 UTC timestamp>",
  "result_path": "",
  "result_payload": {
    "artifacts": [],
    "authenticated_endpoint_used": false,
    "background_worker_created": false,
    "browser_automation_used": false,
    "commands_run": [],
    "daemon_created": false,
    "force_push_used": false,
    "openrouter_used": false,
    "plan_id": "fake_real_codex_invocation_025",
    "polymarket_api_used": false,
    "real_order_submitted": false,
    "remaining_risks": [],
    "run_id": "RUN025",
    "safety_boundaries_acknowledged": [
      "fake_codex_cli_only: Uses the repository fake Codex command script only; no real Codex, network, auth, wallet, orders, or trading.",
      "operator_approval_required_for_codex_execution",
      "single_task_packet_only",
      "no_uncontrolled_codex_loop",
      "no_daemon_scheduler_or_background_worker",
      "no_wallet_signing_orders_or_trading",
      "no_openrouter_or_polymarket_api_without_separate_approval",
      "no_browser_automation_or_authenticated_endpoints",
      "selective_git_staging_only",
      "adapter_mode:codex_cli_operator_approved"
    ],
    "safety_ok": true,
    "scheduler_created": false,
    "schema_version": "codex_plan_task_result.v1",
    "signing_used": false,
    "status": "completed|blocked|failed|needs_retry",
    "summary": "",
    "task_id": "FAKE-CODEX-CLI-025",
    "trading_endpoint_used": false,
    "unsafe_git_staging_used": false,
    "validation_passed": true,
    "wallet_used": false
  },
  "run_id": "RUN025",
  "safety_ok": true,
  "status": "completed|blocked|failed|needs_retry",
  "task_id": "FAKE-CODEX-CLI-025",
  "validation_passed": true
}
```

## Real Codex CLI Result Contract

- Write the final result JSON file to: `agent_tasks\generated\fake_integration\real_codex_invocation_025\agent_tasks\generated\fake_real_codex_invocation_025\RUN025\codex_packets\FAKE-CODEX-CLI-025\codex_result.json`
- The executor will reject missing, malformed, unsafe, or mismatched result JSON.
- Do not wait for manual copy/paste. Write the JSON file before exiting.
- The same path is also available in `AI_ORCHESTRATOR_CODEX_RESULT_PATH`.
