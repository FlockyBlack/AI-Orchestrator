# Operator Quickstart

1. Choose the template that matches the intended receiver and task type.
2. Create the render request with explicit scope, validation commands, and forbidden behavior.
3. Run the renderer and capture the rendered prompt plus preflight report.
4. Inspect preflight and confirm the report stays render-only, non-executing, and non-routing.
5. Send the rendered prompt only to the correct agent named by the template and preflight result.
6. Copy the resulting agent output back into approved review artifacts only.
7. Require Flocky read-only validation after any Codex output.
8. Stop on misroute, unsafe output, missing approval, wrong receiver, or any blocked preflight result.

Stop conditions:
- Stop if the renderer report implies prompt execution or prompt sending.
- Stop if preflight shows mismatch, unsafe scope, or approval-required behavior.
- Stop if the flow would mutate runtime, queue, dispatcher, or `run_codex` surfaces.
