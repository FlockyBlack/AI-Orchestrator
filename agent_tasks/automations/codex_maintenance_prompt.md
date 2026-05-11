# Codex Maintenance Prompt

Report-only maintenance for AI-Orchestrator.

Scope:

- Inspect stale runs.
- Inspect old worktrees.
- Inspect large logs/artifacts.
- Inspect old Codex sessions if available.
- Inspect `memory-bank/` freshness.
- Inspect `.codex-agent/` freshness.
- Inspect whether `AGENTS.md` still matches current safety boundaries.

Hard rule:

- Do not delete automatically.
- Do not modify files automatically.
- Do not create a daemon, scheduler, background worker, or cleanup loop.
- Do not use broad git staging.
- Produce cleanup report only.

Required output:

```json
{
  "status": "report_only",
  "stale_runs": [],
  "old_worktrees": [],
  "large_logs_or_artifacts": [],
  "old_codex_sessions": [],
  "memory_bank_freshness": {},
  "codex_agent_freshness": {},
  "recommended_cleanup_actions": [],
  "automatic_deletion_performed": false,
  "files_modified": false
}
```
