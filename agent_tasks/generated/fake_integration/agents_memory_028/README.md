# Fake Integration: Agents Memory 028

This fake integration artifact demonstrates the 028 operator context without invoking Codex, browser automation, authenticated endpoints, app-server sessions, OpenRouter, Polymarket API, wallet/signing, orders, daemons, schedulers, or background workers.

Checklist:

1. `AGENTS.md` discovered: yes.
2. `memory-bank/` discovered: yes.
3. `agent_tasks/agents/` subagent profiles discovered: yes.
4. `.codex-agent/` phase memory discovered: yes.
5. Sample Codex execution packet includes subagent plan: `sample_packet.json`.
6. Idempotency key generated for sample task: `idempotency.json`.
7. Maintenance prompt exists and is report-only: `agent_tasks/automations/codex_maintenance_prompt.md`.
8. Result JSON written: `result.json`.
