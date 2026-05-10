# ORCH PMBOT PRACTICAL 015 Practical Operator Daily Workflow Runbook

## Summary

PRACTICAL-015 creates a daily operator workflow layer for PMBOT's current practical analysis system. It consolidates the current state from PRACTICAL-011 through PRACTICAL-014 into a summary, command catalog, workflow index, checklist, quickstart card, decision matrix, status snapshot, and safety boundary reference.

The work is documentation plus local operator UX. It performs no new public fetch, no OpenRouter call, no Polymarket API call, no authenticated endpoint access, no trading action, and no scheduler or background automation.

## Relation to PRACTICAL-014

PRACTICAL-014 created manual outcome feedback packets for five unresolved markets. PRACTICAL-015 explains how to operate those packets day to day:

- which files to open first
- which counts to check
- which outcomes are unresolved
- which feedback packets are pending
- which source URLs still need manual repair
- which safe local commands can run
- which tasks remain blocked

## Modules created

- `pm_bot/practical/daily_workflow_summary.py`
- `pm_bot/practical/practical_command_catalog.py`
- `pm_bot/practical/practical_workflow_index.py`
- `pm_bot/practical/practical_daily_checklist.py`

## Artifacts generated

- `pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.json`
- `pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.md`
- `pm_bot/practical/artifacts/daily_workflow_015/practical_command_catalog_015.json`
- `pm_bot/practical/artifacts/daily_workflow_015/practical_command_catalog_015.md`
- `pm_bot/practical/artifacts/daily_workflow_015/practical_workflow_index_015.json`
- `pm_bot/practical/artifacts/daily_workflow_015/practical_workflow_index_015.md`
- `pm_bot/practical/artifacts/daily_workflow_015/practical_daily_checklist_015.json`
- `pm_bot/practical/artifacts/daily_workflow_015/practical_daily_checklist_015.md`
- `pm_bot/practical/artifacts/daily_workflow_015/operator_quickstart_card_015.json`
- `pm_bot/practical/artifacts/daily_workflow_015/operator_quickstart_card_015.md`
- `pm_bot/practical/artifacts/daily_workflow_015/next_task_decision_matrix_015.json`
- `pm_bot/practical/artifacts/daily_workflow_015/next_task_decision_matrix_015.md`
- `pm_bot/practical/artifacts/daily_workflow_015/current_practical_status_snapshot_015.json`
- `pm_bot/practical/artifacts/daily_workflow_015/current_practical_status_snapshot_015.md`
- `pm_bot/practical/artifacts/daily_workflow_015/practical_safety_boundary_reference_015.json`
- `pm_bot/practical/artifacts/daily_workflow_015/practical_safety_boundary_reference_015.md`
- `pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_safety_scan_015.result.json`
- `pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_safety_scan_015.md`

## How operator uses this daily

1. Open `operator_quickstart_card_015.md`.
2. Open `daily_workflow_summary_015.md`.
3. Check unresolved outcomes, feedback-ready packets, and source URL backlog count.
4. Open feedback readiness, outcome recheck, and source learning dashboards.
5. If no outcome is resolved, keep all feedback packets pending.
6. If a source is broken, record the manual repair need.
7. Use `next_task_decision_matrix_015.md` before starting another Codex task.

## What this proves

- The current practical PMBOT workflow can be operated from local artifacts.
- The operator can see the five tracked markets and current unresolved status.
- The operator can identify pending feedback packets and source URL backlog.
- The safe local command surface is explicit and finite.
- The runbook separates paper tracking from trading.

## What this does not prove

- It does not prove outcome accuracy.
- It does not prove source accuracy.
- It does not prove PMBOT is ready for autonomous operation.
- It does not prove any real-money readiness.
- It does not validate live data fetching, OpenRouter use, Polymarket APIs, wallets, orders, or trading endpoints.

## Remaining gaps before real trading

- Resolved outcome feedback packets are missing.
- Source accuracy has not been validated against resolved outcomes.
- Source URL backlog remains open.
- Risk design is not approved.
- Execution mock and accounting gates are not approved.
- No wallet, signing, order, or autonomous execution approval exists.

## Next recommended action

`ORCH-PMBOT-PRACTICAL-016-ADD-NEXT-REAL-MARKET-PACKET-AND-RUN-DAILY-WORKFLOW`
