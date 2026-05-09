# PMBOT Dashboard 004 Paper Accounting Dashboard Summary

Task: `PMBOT-DASHBOARD-004-PAPER-ACCOUNTING-DASHBOARD-SUMMARY`

Contract: `pmbot_local_paper_accounting_dashboard_summary.v1`
Run mode: `local_static_paper_accounting_dashboard_summary`
Operator review: `pending_operator_review`

## Purpose

This dashboard summary provides a local, deterministic inventory of PMBOT paper accounting artifacts for operator review. It uses static local fixtures and documentation references only.

## Local Artifacts

- Request fixture: `pm_bot/tests/fixtures/dashboard/local_paper_accounting_dashboard_request.valid.json`
- Static dashboard sample: `pm_bot/dashboard/samples/local_paper_accounting_dashboard_summary.fixture.json`
- Static report sample: `pm_bot/dashboard/samples/local_paper_accounting_dashboard_summary.fixture.md`
- Builder: `pm_bot/dashboard/local_paper_accounting_dashboard_summary.py`
- Tests: `pm_bot/tests/test_local_paper_accounting_dashboard_summary.py`

## Dashboard Sections

- Queue rows for the dashboard task and paper accounting PMBOT tasks.
- Paper accounting artifact rows for the ledger, validation, and session summary samples.
- Balance rows copied from the local paper accounting ledger sample.
- Validation status rows for the acceptance commands listed by the handoff.

## CLI

```powershell
python -m pm_bot.dashboard.local_paper_accounting_dashboard_summary `
  --request pm_bot/tests/fixtures/dashboard/local_paper_accounting_dashboard_request.valid.json `
  --output-dashboard pm_bot/dashboard/samples/local_paper_accounting_dashboard_summary.fixture.json `
  --output-report pm_bot/dashboard/samples/local_paper_accounting_dashboard_summary.fixture.md
```

## Operator Review Boundary

Operators review whether each paper accounting artifact row points to the expected local sample or documentation reference and whether the displayed counts match the named static artifacts. Every row remains `pending_operator_review` until a human updates a later artifact.

This dashboard summary is not execution approval and is not runtime input.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet access, signing material access, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
