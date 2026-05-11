# Codex Handoff: ORCH-CODEX-AUTOMATION-026-SELECTIVE-COMMIT-PUSH-HARDENING

Return only JSON matching the expected result shape. Do not include prose outside the JSON object.

- task_id: `ORCH-CODEX-AUTOMATION-026-SELECTIVE-COMMIT-PUSH-HARDENING`
- repo_root: `C:\Users\OpenC\.openclaw\workspace`
- branch: `master`
- expected_current_head: `acfc63531d76d4e9c30456a41c960a17ca04988c`
- execution_lane: `orch_automation`
- max_retries: `2`

## Compact Run State

```json
{
  "blocked_task_ids": [],
  "completed_count": 4,
  "failed_task_ids": [],
  "latest_checkpoint": {
    "artifact_paths": [
      "C:\\Users\\OpenC\\.openclaw\\workspace\\agent_tasks\\generated\\fake_integration\\operator_panel_023_resume_recovery\\generated\\pmbot_master_plan_to_050\\O23B\\artifacts\\ORCH-CODEX-AUTOMATION-022-OPERATOR-PANEL-AND-PLAN-RUNNER-CONTROL_fake_103345104757.json",
      "C:\\Users\\OpenC\\.openclaw\\workspace\\agent_tasks\\generated\\fake_integration\\operator_panel_023_resume_recovery\\generated\\pmbot_master_plan_to_050\\O23B\\artifacts\\ORCH-CODEX-AUTOMATION-023-QUEUE-STATE-RESUME-AND-PANEL-HARDENING_fake_103345738350.json",
      "C:\\Users\\OpenC\\.openclaw\\workspace\\agent_tasks\\generated\\fake_integration\\operator_panel_023_resume_recovery\\generated\\pmbot_master_plan_to_050\\O23B\\artifacts\\ORCH-CODEX-AUTOMATION-024-CODEX-EXECUTOR-ADAPTER-BOUNDARY_fake_103346437687.json",
      "C:\\Users\\OpenC\\.openclaw\\workspace\\agent_tasks\\generated\\fake_integration\\operator_panel_023_resume_recovery\\generated\\pmbot_master_plan_to_050\\O23B\\artifacts\\ORCH-CODEX-AUTOMATION-025-WORKTREE-LANE-MANAGER_fake_103346592505.json"
    ],
    "blocked_task_ids": [],
    "checkpoint_created_at": "2026-05-11T10:33:46Z",
    "checkpoint_id": "cp_0006_20260511T103346Z",
    "checkpoint_reason": "recovery_result",
    "completed_task_ids": [
      "ORCH-CODEX-AUTOMATION-022-OPERATOR-PANEL-AND-PLAN-RUNNER-CONTROL",
      "ORCH-CODEX-AUTOMATION-023-QUEUE-STATE-RESUME-AND-PANEL-HARDENING",
      "ORCH-CODEX-AUTOMATION-024-CODEX-EXECUTOR-ADAPTER-BOUNDARY",
      "ORCH-CODEX-AUTOMATION-025-WORKTREE-LANE-MANAGER"
    ],
    "failed_task_ids": [],
    "latest_handoff_prompt_path": "",
    "latest_recovery_report_path": "C:\\Users\\OpenC\\.openclaw\\workspace\\agent_tasks\\generated\\fake_integration\\operator_panel_023_resume_recovery\\generated\\pmbot_master_plan_to_050\\O23B\\recovery\\recovery_report_20260511T103346987430Z.json",
    "retry_counts": {},
    "skipped_task_ids": [],
    "status": "recovered",
    "task_id": ""
  },
  "plan_id": "pmbot_master_plan_to_050",
  "retry_counts": {},
  "run_id": "O23B",
  "run_status": "running"
}
```

## Previously Completed Tasks

- ORCH-CODEX-AUTOMATION-022-OPERATOR-PANEL-AND-PLAN-RUNNER-CONTROL
- ORCH-CODEX-AUTOMATION-023-QUEUE-STATE-RESUME-AND-PANEL-HARDENING
- ORCH-CODEX-AUTOMATION-024-CODEX-EXECUTOR-ADAPTER-BOUNDARY
- ORCH-CODEX-AUTOMATION-025-WORKTREE-LANE-MANAGER

## Next Task Only

Title: Selective commit/push hardening

Harden selective commit and push flow with explicit paths, dry-run support, and remote HEAD verification.

Dependencies:
- ORCH-CODEX-AUTOMATION-025-WORKTREE-LANE-MANAGER

## Allowed Paths

- ai_orchestrator/codex_queue/
- docs/
- tests/

## Forbidden Actions

- git add dot
- git add all
- force push

## Expected Artifacts

- selective staging hardening tests
- commit push verify docs

## Acceptance Gates

- unsafe staging is rejected
- dry-run commit/push verification works
- remote verification path is documented

## Required Result JSON Shape

```json
{
  "artifacts": [],
  "commands_run": [],
  "remaining_risks": [],
  "safety_ok": true,
  "status": "completed|blocked|failed",
  "summary": "",
  "task_id": "ORCH-CODEX-AUTOMATION-026-SELECTIVE-COMMIT-PUSH-HARDENING",
  "validation_passed": true
}
```

## Safety Reminders

- Do not use unsafe git staging. Never run `git add .`, `git add -A`, or `git add --all`.
- Do not use wallet files, private keys, signing, orders, trading endpoints, or real-money flows.
- Do not use OpenRouter or Polymarket API unless a separate task explicitly approves it.
- Do not start daemons, schedulers, uncontrolled background workers, or browser automation.
