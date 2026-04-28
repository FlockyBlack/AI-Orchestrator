# External Codex Plan

The external Codex plan is a preview-only artifact for a future execution path. It records which prompt pack and candidate bundle would be used later, plus a clearly labeled command preview that is not executed by these tools.

`build_external_codex_plan.py` writes only a plan JSON and a command preview text file under `codex_auto/external_cli/plans/`. It does not invoke external Codex CLI, does not execute the generated prompt, and does not authorize runtime wiring.

Human approval and Flocky validation are required before any future execution step. This planning layer does not claim final Flocky/OpenClaw completion and does not promote candidates into runtime state.
