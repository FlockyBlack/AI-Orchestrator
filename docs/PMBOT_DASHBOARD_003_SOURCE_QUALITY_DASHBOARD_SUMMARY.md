# PMBOT Dashboard 003 Source Quality Dashboard Summary

Task: `PMBOT-DASHBOARD-003-SOURCE-QUALITY-DASHBOARD-SUMMARY`

Contract: `pmbot_local_source_quality_dashboard_summary.v1`
Run mode: `local_static_source_quality_dashboard_summary`
Operator review: `pending_operator_review`

## Purpose

This dashboard summary provides a local, deterministic inventory of PMBOT source quality artifacts for operator review. It uses static local fixtures and documentation references only.

## Local Artifacts

- Request fixture: `pm_bot/tests/fixtures/dashboard/local_source_quality_dashboard_request.valid.json`
- Static dashboard sample: `pm_bot/dashboard/samples/local_source_quality_dashboard_summary.fixture.json`
- Static report sample: `pm_bot/dashboard/samples/local_source_quality_dashboard_summary.fixture.md`
- Builder: `pm_bot/dashboard/local_source_quality_dashboard_summary.py`
- Tests: `pm_bot/tests/test_local_source_quality_dashboard_summary.py`

## Dashboard Sections

- Queue rows for the dashboard task and selected source quality PMBOT tasks.
- Source quality artifact rows for the unified ledger, report summary, regression fixture, and crypto source quality capture surface.
- Validation status rows for the acceptance commands listed by the handoff.

## CLI

```powershell
python -m pm_bot.dashboard.local_source_quality_dashboard_summary `
  --request pm_bot/tests/fixtures/dashboard/local_source_quality_dashboard_request.valid.json `
  --output-dashboard pm_bot/dashboard/samples/local_source_quality_dashboard_summary.fixture.json `
  --output-report pm_bot/dashboard/samples/local_source_quality_dashboard_summary.fixture.md
```

## Operator Review Boundary

Operators review whether each source quality row points to the expected local sample or documentation reference and whether the summary counts match the named static artifacts. Every row remains `pending_operator_review` until a human updates a later artifact.

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
