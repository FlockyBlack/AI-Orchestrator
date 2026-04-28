# Safe Batch

This is isolated `codex_auto` automation only.

The batch runner coordinates local queue execution and local Flocky review bookkeeping.
The `done` state it can write is codex_auto-local only and is not final OpenClaw or final Flocky done.
External Codex CLI is not invoked.
Runtime wiring is forbidden.
Only `CODEX-AUTO-TINY-001` is supported in this batch scaffold.
Future expansion requires separate approval.
