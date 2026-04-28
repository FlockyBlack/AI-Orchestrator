# Example Repair Loop Flow

1. Flocky read-only validation finds a bounded issue in task `<TASK_ID_REPAIR_LOOP>`.
2. Operator creates a new repair render request at `<PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/requests/<REPAIR_REQUEST>.json`.
3. Operator runs:
   `python <PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/render_prompt_pack.py --request-path <PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/requests/<REPAIR_REQUEST>.json --out -`
4. Operator checks that the repair prompt stays within approved write scope and remains safe for `Codex`.
5. Operator manually sends the repair prompt to `Codex`.
6. Operator copies the repair result into `<PROJECT_ROOT>/docs/reviews/<REPAIR_NOTE>.md`.
7. Operator requires another Flocky read-only validation pass before acceptance review resumes.
