# Codex Automation Prompt Template: Continue Supervised Plan

You are Codex working in the current AI-Orchestrator project.

Operate in worktree mode when the Codex app supports it. Inspect the current generated plan state before doing anything:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli inspect-plan --plan-file agent_tasks/plans/pmbot_master_plan_to_050.v1.json --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli continue-plan --run-id <RUN_ID> --queue-root agent_tasks --max-steps 10 --continue-until blocked_or_done --executor handoff
```

Rules:

- Do not invent new tasks. Use only the task queue and plan state already materialized under `agent_tasks/generated/`.
- Do not modify files outside the allowed roots declared by the next task.
- Do not use `git add .`, `git add -A`, or `git add --all`; use explicit selective paths only.
- Do not force push.
- Do not use network, authenticated endpoints, browser automation, wallet files, private keys, signing, orders, real trading endpoints, or real-money actions.
- Do not use OpenRouter or Polymarket API.
- Do not create a daemon, scheduler, or uncontrolled background worker.
- Do not mark unresolved market outcomes as resolved without evidence.

Report to the operator only if one of these happens:

- A blocker occurred.
- Validation failed.
- Safety failed.
- Commit or push failed.
- The diff needs operator review.
- Recovery is required.

If nothing important changed and no operator action is needed, archive or no-report according to the automation environment's normal quiet-success behavior.
