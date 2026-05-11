# Codex Handoff: ORCH-CODEX-AUTOMATION-025-WORKTREE-LANE-MANAGER

- task_id: `ORCH-CODEX-AUTOMATION-025-WORKTREE-LANE-MANAGER`
- repo_root: `.`
- branch: `master`
- expected_current_head: `acfc63531d76d4e9c30456a41c960a17ca04988c`
- execution_lane: `orch_automation`

## Task

Improve worktree lane planning for future parallel Codex agents while remaining dry-run-safe.

## Allowed Paths

- ai_orchestrator/codex_queue/
- docs/
- tests/

## Forbidden Actions

- automatic merge
- destructive git
- force operation

## Expected Artifacts

- lane plan tests
- dry-run command renderer

## Acceptance Gates

- lane isolation validation covers overlap
- rendered worktree commands are dry-run only
- no merge or destructive command emitted

## Required Result JSON Shape

```json
{
  "artifacts": [],
  "commands_run": [],
  "remaining_risks": [],
  "safety_ok": true,
  "status": "completed|blocked|failed",
  "summary": "",
  "task_id": "ORCH-CODEX-AUTOMATION-025-WORKTREE-LANE-MANAGER",
  "validation_passed": true
}
```

## Safety Reminders

- Do not use unsafe git staging. Never run `git add .`, `git add -A`, or `git add --all`.
- Do not use wallet files, private keys, signing, orders, trading endpoints, or real-money flows.
- Do not use OpenRouter or Polymarket API unless a separate task explicitly approves it.
- Do not start daemons, schedulers, uncontrolled background workers, or browser automation.
