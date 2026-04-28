# Codex Approval Guardrails

Approval artifacts in this directory are offline guardrails only.

They do not enable execution.
They do not modify runner execution behavior.
Execution remains disabled by default.

## Future Execution Requirements

1. valid Codex task JSON
2. valid execution approval JSON
3. dry-run preview
4. explicit human approval
5. controlled execution
6. execution envelope
7. OpenClaw read-only validation

## Forbidden

- runtime wiring
- dispatcher or run_codex changes
- active task mutation
- network usage
- API usage
- wallet usage
- private key usage
- trading behavior
- live Polymarket API usage
- real orders

## Scope

This directory adds approval metadata and validation only. It does not alter `codex_auto/runner/run_codex_task.py`, does not unlock `--execute`, and does not create a new runtime source of truth.
