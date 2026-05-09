# Local Queue Operator Workflow

1. Create a JSON task packet in `agent_tasks/inbox/` using a template from `agent_tasks/templates/`.
2. Manually inspect the task packet for scope, safety, allowed paths, forbidden paths, and acceptance checks.
3. Move the packet to `agent_tasks/approved/` only when an operator explicitly approves planning.
4. Run the dry-run runner:

```powershell
python -m ai_orchestrator.codex_queue.dry_run_runner --queue-root agent_tasks --dry-run
```

5. Inspect `agent_tasks/reports/latest_dry_run_report.json` and `agent_tasks/reports/latest_dry_run_report.md`.
6. Inspect the generated handoff prompt in `agent_tasks/planned/<TASK_ID>.handoff_prompt.md`.
7. Manually execute Codex separately only if the operator approves that handoff.
8. Place the Codex result into `agent_tasks/review/` later for human review.
9. Manually move accepted completed work to `agent_tasks/done/`.

No automatic execution exists in this MVP. The dry-run runner only plans and reports. It does not run Codex, does not start a worker, does not schedule future work, does not call network services, and does not modify runtime, dispatcher, wallet, trading, payment, or credential code.

