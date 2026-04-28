# Codex Auto Queue

This queue is isolated under `codex_auto`.

It is not AI-Orchestrator runtime.
The `ready`, `running`, `done`, `failed`, `needs_flocky_review`, and `quarantine` directories are codex_auto-local states only.
Flocky validation is required after controlled execution.
`--execute-next-controlled` is currently limited to `CODEX-AUTO-TINY-001`.
External Codex CLI is not invoked by this queue scaffold.
Runtime wiring remains forbidden.
