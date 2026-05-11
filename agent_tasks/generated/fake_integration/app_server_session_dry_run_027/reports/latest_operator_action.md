# Latest Operator Action

- command: `app-server-dry-run`
- status: `ok`
- task_id: ``
- queue_root: `agent_tasks\generated\fake_integration\app_server_session_dry_run_027`
- source_path: ``
- destination_path: `agent_tasks\generated\fake_integration\app_server_session_dry_run_027\generated\manual_app_server_dry_run\20260511T132652Z\app_server_dry_runs\20260511T132652Z`
- next_operator_action: Review app-server dry-run artifacts and protocol probe status.

## Safety

This operator action starts Codex app-server only when exact operator approval is supplied through --operator-approved. Any approved run is short-lived, local-only, dry-run-only, captures logs, and stops the process; it does not create a daemon, scheduler, background worker, browser automation flow, authenticated flow, or trading action.
