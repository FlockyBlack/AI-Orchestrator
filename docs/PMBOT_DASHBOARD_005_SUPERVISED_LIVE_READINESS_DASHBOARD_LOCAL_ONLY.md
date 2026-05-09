# PMBOT Dashboard 005 Supervised Live Readiness Dashboard Local Only

Task: `PMBOT-DASHBOARD-005-SUPERVISED-LIVE-READINESS-DASHBOARD-LOCAL-ONLY`

Contract: `pmbot_local_supervised_live_readiness_dashboard.v1`
Run mode: `local_static_supervised_live_readiness_dashboard`
Operator review: `pending_operator_review`

## Purpose

This dashboard provides a local, deterministic inventory of PMBOT supervised-live readiness artifacts for operator review. It uses static local fixtures and documentation references only.

The dashboard is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Local Artifacts

- Request fixture: `pm_bot/tests/fixtures/dashboard/local_supervised_live_readiness_dashboard_request.valid.json`
- Static dashboard sample: `pm_bot/dashboard/samples/local_supervised_live_readiness_dashboard.fixture.json`
- Static report sample: `pm_bot/dashboard/samples/local_supervised_live_readiness_dashboard.fixture.md`
- Builder: `pm_bot/dashboard/local_supervised_live_readiness_dashboard.py`
- Tests: `pm_bot/tests/test_local_supervised_live_readiness_dashboard.py`

## Dashboard Sections

- Queue rows for the dashboard task and supervised-live readiness PMBOT tasks.
- Readiness artifact rows for read-only data, source inventory, operator gate, stop condition, readiness evidence bundle, and gap matrix artifacts.
- Validation status rows for the acceptance commands listed by the handoff.

## CLI

```powershell
python -m pm_bot.dashboard.local_supervised_live_readiness_dashboard `
  --request pm_bot/tests/fixtures/dashboard/local_supervised_live_readiness_dashboard_request.valid.json `
  --output-dashboard pm_bot/dashboard/samples/local_supervised_live_readiness_dashboard.fixture.json `
  --output-report pm_bot/dashboard/samples/local_supervised_live_readiness_dashboard.fixture.md
```

## Operator Review Boundary

Operators review whether each readiness row points to the expected local sample or documentation reference and whether displayed counts match the named static artifacts. Every row remains `pending_operator_review` until a human updates a later artifact.

This dashboard is not execution approval and is not runtime input.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external service calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, stance selection, or trade action guidance.
