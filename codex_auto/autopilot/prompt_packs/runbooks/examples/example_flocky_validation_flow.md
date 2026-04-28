# Example Flocky Validation Flow

1. Operator selects `flocky_read_only_validation.template.txt` for task `<TASK_ID_VALIDATION>`.
2. Operator creates render request at `<PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/requests/<VALIDATION_REQUEST>.json`.
3. Operator runs:
   `python <PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/render_prompt_pack.py --request-path <PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/requests/<VALIDATION_REQUEST>.json --out -`
4. Operator confirms the report remains render-only and preflight says `PROCEED_READ_ONLY_VALIDATION`.
5. Operator manually sends the rendered prompt to `Flocky`.
6. Operator copies the Flocky validation result into `<PROJECT_ROOT>/docs/reviews/<VALIDATION_NOTE>.md`.
7. Operator keeps the validation result as review evidence only, not runtime state.
