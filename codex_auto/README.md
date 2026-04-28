# Codex Automation Scaffold

This directory contains an isolated Codex automation scaffold for AI-Orchestrator. It is a local task-envelope, validation, and dry-run layer only.

It is not runtime wiring.
It does not replace AI-Orchestrator as the execution source of truth.
It does not modify `scripts/dispatcher.py`.
It does not modify `scripts/run_codex.py`.
It defaults to dry-run.
Future real execution requires explicit human approval and `--execute`.

## Safe Flow

1. Create a task JSON file that matches `codex_auto/schemas/codex_task.schema.v1.json`.
2. Validate the task JSON with `python codex_auto\runner\validate_codex_task.py <task.json>`.
3. Preview the future command with `python codex_auto\runner\run_codex_task.py <task.json>`.
4. Human approves the task in a separate controlled step.
5. Execute only the safe task with an explicit future approval path and `--execute`.
6. Validate the result through OpenClaw before any final governance completion.

## Forbidden

- runtime wiring
- dispatcher or run_codex mutation
- active task mutation
- network usage
- API usage
- wallet usage
- private key usage
- trading behavior
- live Polymarket API usage
- real orders

## Scope

The current scaffold only validates local task envelopes and prepares a dry-run command preview. It does not call Codex during this implementation task, does not read active task queues, and does not create a second runtime source of truth.
