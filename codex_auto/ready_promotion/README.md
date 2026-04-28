# Ready Promotion

Candidate-to-ready promotion here is codex_auto-local only. It copies validated PMBOT candidate tasks into `codex_auto/tasks/ready/` so they are visible to local preview flows without becoming executable runtime work.

PMBOT ready tasks are ready for human and Flocky review, not execution. `approved_for_execution` remains false, external Codex CLI remains disabled, and the generated prompt is not executed automatically by this layer.

Runtime wiring stays forbidden. Any future PMBOT execution still requires a separate human approval step, Flocky validation, and an explicit execution gate. These ready tasks do not claim final Flocky/OpenClaw completion.
