# Practical Command Catalog 015

## Safe local commands

### view dashboard

- Command: `python -m json.tool pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.json`
- Purpose: Print the daily summary JSON in a stable local format.
- Writes files: `false`

### summarize daily state

- Command: `python -m pm_bot.practical.daily_workflow_summary --out-json pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.json --out-md pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.md`
- Purpose: Regenerate the local daily workflow summary from known artifact paths.
- Writes files: `true`

### inspect active paper hypotheses

- Command: `python -m pm_bot.practical.active_paper_hypotheses --queue pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json --out-json pm_bot/practical/artifacts/daily_workflow_015/active_paper_hypotheses_local_view.json --out-md pm_bot/practical/artifacts/daily_workflow_015/active_paper_hypotheses_local_view.md`
- Purpose: Create a local view of active paper hypotheses from the saved market queue.
- Writes files: `true`

### inspect outcome recheck queue

- Command: `python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.json`
- Purpose: View unresolved outcome status and recheck priority.
- Writes files: `false`

### inspect source learning scorecard

- Command: `python -m json.tool pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_update_013.json`
- Purpose: View saved source status and source handling notes.
- Writes files: `false`

### inspect manual feedback packets

- Command: `python -m json.tool pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.json`
- Purpose: View pending manual feedback readiness across tracked markets.
- Writes files: `false`

### validate artifacts

- Command: `python -m json.tool pm_bot/practical/artifacts/daily_workflow_015/practical_workflow_index_015.json`
- Purpose: Validate the workflow index JSON shape.
- Writes files: `false`

### run safety scan

- Command: `python -m pm_bot.practical.practical_safety_scan --artifact-dir pm_bot/practical/artifacts/daily_workflow_015 --out-json pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_safety_scan_015.result.json --out-md pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_safety_scan_015.md`
- Purpose: Scan daily workflow artifacts for unsafe action wording and unsafe flags.
- Writes files: `true`

### prepare future outcome feedback

- Command: `python -m json.tool pm_bot/practical/artifacts/manual_outcome_feedback_014/manual_outcome_operator_guide_014.json`
- Purpose: Open the manual outcome guide before filling any future resolved outcome packet.
- Writes files: `false`

## Manual-only steps

- Collect actual outcome evidence outside PMBOT, then save it locally before any packet update.
- Curate replacement public source URLs manually before a separate approved source task.
- Review paper labels manually before generating feedback from a resolved packet.

## Prohibited commands

- run-codex-once
- run-codex-batch
- Any OpenRouter command without separate approval.
- Any Polymarket API command without separate approval.
- Any wallet, signing, order, trading endpoint, scheduler, daemon, watcher, or polling command.

## Notes

- The daily catalog is local-only and finite.
- Public fetch commands are intentionally excluded from the daily runbook.
- Commands that write files target versioned local artifacts only.
- No command in safe_commands needs API keys, cookies, browser profiles, or authenticated endpoints.
