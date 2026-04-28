# Render Request Review Checklist

- Confirm the template matches the intended receiver and task type.
- Confirm task ID and paths use the planned placeholder or approved local values for the operator flow.
- Confirm allowed write paths are minimal and explicitly approved.
- Confirm forbidden behavior blocks runtime wiring, queue mutation, prompt sending, and session spawning.
- Confirm the request does not treat `codex_auto` as runtime authority or source of truth.
- Stop if the request would require dispatcher or `run_codex` integration.
- Stop if the request implies execution approval or final acceptance.
