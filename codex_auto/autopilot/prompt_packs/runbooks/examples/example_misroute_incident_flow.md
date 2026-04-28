# Example Misroute Incident Flow

1. Operator notices that task `<TASK_ID_MISROUTE>` was sent to the wrong agent after review.
2. Operator preserves the rendered prompt and preflight report in `<PROJECT_ROOT>/docs/incidents/<INCIDENT_NOTE>.md`.
3. Operator stops any further prompt sending for that task.
4. Operator records that wrong-agent execution triggered containment.
5. Operator requests human review before any new render request is created.
6. Operator prepares a corrected request at `<PROJECT_ROOT>/codex_auto/autopilot/prompt_packs/requests/<CORRECTED_REQUEST>.json` only after containment review closes.
