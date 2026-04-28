# One-Shot External Codex Execution Gate

This directory contains a manual-run-only execution gate for `PMBOT-BATCH-001`.

The gate does not execute Codex, does not invoke external Codex CLI, and does not execute the generated prompt. It only materializes a validated gate record and a final command preview for later human use.

The final command preview must be run manually only after final human confirmation. For this non-git workspace it uses a non-interactive editable Codex command with `--full-auto` and `--skip-git-repo-check`. The preview file is not permission to bypass validation, policy checks, or preserved execution flags.

Post-execution Flocky validation is mandatory. A manual run is still incomplete until the separate post-execution Flocky validation step succeeds.

Runtime wiring remains forbidden. This gate does not authorize runtime wiring, dispatcher changes, `run_codex` changes, active task mutation, or any second runtime source of truth.

Wallet usage, API usage, live Polymarket access, trading behavior, live APIs, and real orders are forbidden. The gate exists to preserve a constrained paper-only workflow.

Files:

- `prepare_one_shot_execution.py`: validates local approval artifacts and writes the one-shot gate plus the final command preview.
- `validate_one_shot_execution_gate.py`: validates the generated gate and rejects execution-enabling flags or unsafe claims.
- `PMBOT-BATCH-001.one_shot_execution_gate.json`: generated gate record.
- `PMBOT-BATCH-001.final_command_preview.txt`: generated manual command preview.
