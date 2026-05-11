# Active Context

- current_head: `8e6f19f2fcff5165b8505e3788be148c4b544b83`
- current_branch: `master`
- latest_completed_milestone: `ORCH-CODEX-AUTOMATION-027-ACTUAL-APP-SERVER-SESSION-DRY-RUN`
- next_milestone: `ORCH-CODEX-AUTOMATION-028-AGENTS-MD-SUBAGENTS-MEMORY-BANK-AND-MAINTENANCE`
- next_recommended_after_028: `ORCH-CODEX-AUTOMATION-029-WORKTREE-LANE-REAL-EXECUTION-AND-SUBAGENT-ROUTING`

Current blockers/risks:

- Long supervised runs can still lose role/context discipline without durable project instructions.
- Multi-role workflow is metadata/template based in 028; real routing is deferred to 029.
- Result JSON cannot include the final commit hash inside the same commit without a follow-up mutation; final response carries the verified `head_after`.
- PMBOT tracked markets remain unresolved and must not be guessed.
