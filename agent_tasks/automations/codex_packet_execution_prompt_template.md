# Codex Packet Execution Prompt Template

Use this template only for a future Codex app automation profile after operator approval.

Runtime profile:

- Use worktree mode.
- Prefer workspace-write sandbox.
- Do not use full filesystem access unless the operator explicitly approves it for that run.
- Do not use network, authenticated endpoints, browser automation, wallet files, private keys, signing, orders, trading endpoints, or real-money actions.
- Do not use OpenRouter or Polymarket API unless a separate future task explicitly approves it.
- Do not start a daemon, scheduler, background worker, or uncontrolled autonomous loop.
- Do not use unsafe git staging. Never run `git add .`, `git add -A`, or `git add --all`.
- Do not force push.

Packet instructions:

1. Read `packet.json`.
2. Read `prompt.md`.
3. Work only on the packet's single `task_id`.
4. Stay inside `allowed_paths`.
5. Treat `forbidden_actions` as hard stop conditions.
6. Run only the smallest relevant validation.
7. Return result JSON only, matching `expected_result_template.json`.
8. Do not claim success unless acceptance gates are satisfied.
9. Report to Triage only for blocker, failure, rejected validation, or diff needing review.

Result contract:

- Return a single JSON object.
- Include the original `packet_id`, `run_id`, `plan_id`, `task_id`, and `adapter_mode`.
- Set all safety flags truthfully.
- Set `wallet_used`, `signing_used`, `trading_endpoint_used`, `authenticated_endpoint_used`, `browser_automation_used`, `openrouter_used`, `polymarket_api_used`, `unsafe_git_staging_used`, and `force_push_used` to `false` unless a future separately approved packet explicitly allows otherwise.
