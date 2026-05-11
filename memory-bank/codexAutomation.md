# Codex Automation

Current stack:

- panel: local operator panel for plans, runs, artifacts, Codex handoff, Codex CLI, and app-server dry-run controls.
- runner: long-run controller with queue state, checkpoints, resume, recovery, dashboard writing, and acceptance gates.
- codex_cli executor: supervised real Codex CLI path with operator approval, command preview, captured stdout/stderr, and auto-ingestion.
- app-server dry-run: short-lived Codex app-server protocol probe and dry-run artifacts.
- auto-ingestion: Codex result envelope validation and state update.
- Symphony-style workspaces: workspace/session/task contract mapping and app-server schema boundary.

028 additions:

- durable `AGENTS.md`
- `agent_tasks/agents/` role profiles
- `memory-bank/` context
- `.codex-agent/` phase memory
- Goal Maker-style board and receipt template
- maintenance automation prompt
- idempotency foundation
- execution packet subagent metadata

Next automation goals:

- route worktree lanes through explicit role metadata
- persist subagent outputs as receipts
- add retry/restart idempotency checks around packet execution
- improve operator acceptance gates before long supervised PMBOT runs
