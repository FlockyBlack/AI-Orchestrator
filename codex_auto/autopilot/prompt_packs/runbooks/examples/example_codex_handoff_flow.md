# Example Codex Handoff Flow

1. Operator selects `codex_code_changing.template.txt` for task `<TASK_ID_CODEX_PATCH>`.
2. Operator creates render request at `<PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/requests/<REQUEST_FILE>.json`.
3. Operator runs:
   `python <PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/render_prompt_pack.py --request-path <PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/requests/<REQUEST_FILE>.json --out -`
4. Operator checks that preflight stays safe for `Codex` and that the renderer does not execute or send prompts.
5. Operator manually sends the rendered prompt to `Codex`.
6. Operator copies the Codex response into `<PROJECT_ROOT>/docs/reviews/<RESULT_NOTE>.md`.
7. Operator sends the copied Codex output to Flocky for read-only validation before acceptance review.
