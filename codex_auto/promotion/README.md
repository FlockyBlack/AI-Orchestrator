# Promotion Gate

Promotion requests in this directory are review-only artifacts. They package candidate-task references, the generated prompt pack, and the materialization report so Flocky-local review can assess whether the bundle is safe to consider for a later promotion step.

The promotion decision produced by `review_candidate_bundle.py` can approve ready promotion only. It does not execute prompts, does not invoke external Codex CLI, does not authorize runtime wiring, and does not claim final Flocky/OpenClaw completion.

Human approval and Flocky validation remain required before any execution path. Runtime wiring stays forbidden in this phase, and candidate tasks remain non-executable until a separate approved task promotes them.
