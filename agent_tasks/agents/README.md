# Subagent Role Profiles

These profiles define bounded working modes for AI-Orchestrator Codex runs.
Main Codex remains responsible for final judgment, result JSON, and safety.

## How to Use

1. Read `AGENTS.md` first.
2. Select only the roles needed for the current task.
3. Keep every role within allowed paths and the task scope.
4. Treat role outputs as evidence, not automatic approval.
5. Integrator aggregates role outputs and checks acceptance gates before selective staging.

## Default Sequence

- Scout: discover relevant files and risks.
- Planner: create the bounded implementation plan.
- Builder: implement only approved scoped changes.
- Tester: add or update tests and run targeted validation.
- Reviewer: inspect diff, safety boundaries, and git staging plan.
- Docs: update operator-facing docs and result JSON.
- Integrator: decide whether the task is completed, blocked, or needs retry.

Do not use these profiles to bypass operator approval or safety boundaries.
