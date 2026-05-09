# Scheduler Plan

This document describes a future Windows Task Scheduler integration concept for the local Codex queue. No scheduler is registered by the current implementation.

The current scheduler-plan command is report-only:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli scheduler-plan --queue-root agent_tasks
```

It writes:

- `agent_tasks/reports/latest_scheduler_plan.json`
- `agent_tasks/reports/latest_scheduler_plan.md`

## Required Approval Gates

Before any real scheduler can be registered, these gates must be satisfied and reviewed:

- queue health available;
- night dry-run available;
- git safety available;
- result ingestion available;
- morning report available;
- max task cap;
- lock file discipline;
- no network by default;
- no credentials;
- no automatic Codex execution unless separately approved;
- explicit operator approval.

The current scheduler plan always reports `scheduler_registered: false`. It is documentation, not activation.

## Future Staged Activation

1. Dry-run manually.
   Run `night-dry-run` by hand and inspect the JSON and Markdown reports.

2. Dry-run through scheduler, but no Codex execution.
   Only after a separate explicit approval task, register a scheduler entry that runs `night-dry-run` and writes reports. It must still not execute Codex or mutate queue states.

3. Scheduled morning report only.
   After dry-run scheduling proves stable, consider a schedule for the morning report only.

4. Later controlled execution only after explicit approval.
   Controlled execution is a separate future task. It must not be inferred from this scheduler plan.

## FUTURE ONLY / DO NOT RUN YET

The following is an outline for a future manually approved scheduler registration. It is not a command to run now:

```powershell
schtasks /Create /TN "AI-Orchestrator Night Dry Run" /SC DAILY /ST 02:00 /TR "powershell.exe -NoProfile -Command 'Set-Location C:\Users\OpenC\.openclaw\workspace; python -m ai_orchestrator.codex_queue.operator_cli night-dry-run --queue-root agent_tasks --max-tasks 5'"
```

Do not run that outline until a separate operator-approved scheduler activation task exists.

## Why No Scheduler Is Registered Yet

This task only adds readiness reporting and documentation. Registering a scheduler would create an automated entry outside the local report-only queue flow, so it remains blocked until a later task explicitly approves and scopes scheduler activation.
