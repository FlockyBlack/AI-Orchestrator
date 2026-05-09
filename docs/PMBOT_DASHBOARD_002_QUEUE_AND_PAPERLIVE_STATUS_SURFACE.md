# PMBOT Dashboard 002 Queue And Paperlive Status Surface

Task: `PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE`

Contract: `pmbot_local_queue_paperlive_status_surface.v1`
Run mode: `local_static_queue_paperlive_status_surface`
Operator review: `pending_operator_review`

## Purpose

This dashboard surface provides a local, deterministic status inventory for selected PMBOT queue rows and paperlive artifacts. It is for operator review only and uses local static files.

## Local Artifacts

- Request fixture: `pm_bot/tests/fixtures/dashboard/local_queue_paperlive_status_request.valid.json`
- Static status sample: `pm_bot/dashboard/samples/local_queue_paperlive_status_surface.fixture.json`
- Static report sample: `pm_bot/dashboard/samples/local_queue_paperlive_status_surface.fixture.md`
- Builder: `pm_bot/dashboard/local_queue_paperlive_status_surface.py`
- Tests: `pm_bot/tests/test_local_queue_paperlive_status_surface.py`

## Surface Sections

- Queue status rows for the dashboard task, weather paperlive review surface, and crypto paperlive observation ledger.
- Paperlive status rows for the local weather review surface documentation and the crypto paperlive observation ledger fixture.
- Validation status rows for the acceptance commands listed by the handoff.

## CLI

```powershell
python -m pm_bot.dashboard.local_queue_paperlive_status_surface `
  --request pm_bot/tests/fixtures/dashboard/local_queue_paperlive_status_request.valid.json `
  --output-surface pm_bot/dashboard/samples/local_queue_paperlive_status_surface.fixture.json `
  --output-report pm_bot/dashboard/samples/local_queue_paperlive_status_surface.fixture.md
```

## Operator Review Boundary

Operators review whether the queue rows and paperlive rows point to expected local fixtures or documentation. All rows remain `pending_operator_review` until a human updates a later artifact.

This status surface is not execution approval and is not runtime input.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet access, signing material access, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, or selection advice.
