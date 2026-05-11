# Codex Multi-Agent Continue Plan Prompt

Continue the current AI-Orchestrator plan using the governed subagent workflow.

Required context:

- Read `AGENTS.md`.
- Read relevant `memory-bank/` files.
- Read relevant `.codex-agent/` phase memory.
- Use worktree/session isolation when available.

Execution bounds:

- Use bounded max steps from the operator request or plan state.
- Work only on the next runnable task.
- Keep Scout, Planner, Builder, Tester, Reviewer, Docs, and Integrator responsibilities separate.
- Persist useful outputs as artifacts or result JSON.
- Stop on safety failure, validation failure, missing approval, state inconsistency, or ambiguous PMBOT market outcome.

Safety:

- PMBOT remains paper-only.
- No real-money flows, wallet/signing, orders, trading endpoints, authenticated endpoints, browser automation, OpenRouter, or Polymarket API unless separately approved.
- No daemon, scheduler, background worker, or uncontrolled loop.
- Selective staging only.

Report only when useful:

- Return concise JSON.
- Include changed files, tests, artifacts, safety flags, blockers, and next recommended task.
