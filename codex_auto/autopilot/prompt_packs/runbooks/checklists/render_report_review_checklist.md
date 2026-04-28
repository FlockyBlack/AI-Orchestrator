# Render Report Review Checklist

- Confirm `render_only` is true.
- Confirm `original_prompt_executed` is false.
- Confirm `rendered_prompt_executed` is false.
- Confirm `runtime_wiring_allowed` is false.
- Confirm `queue_mutation_allowed` is false.
- Confirm `active_flocky_tool_integration` is false.
- Confirm the renderer does not execute or send prompts.
- Stop if the report claims runtime done, execution approval, or final acceptance.
- Stop if the report implies queue bridge, dispatcher integration, or `run_codex` integration.
