# Codex Local Handoff: PMBOT-REHEARSAL-016-REHEARSAL-SIMULATED-DECISION-REPLAY-LINKS-LOCAL-ONLY

## Task

- task_id: `PMBOT-REHEARSAL-016-REHEARSAL-SIMULATED-DECISION-REPLAY-LINKS-LOCAL-ONLY`
- title: PMBOT rehearsal simulated decision replay links

## Summary

Prepare local PMBOT rehearsal simulated decision replay links for operator review.

## Instructions

- Inspect local PMBOT files under the allowed paths before editing.
- Add deterministic local links between rehearsal artifacts and simulated decision replay records.
- Use only local files, local fixtures, and static samples.
- Keep outputs descriptive, deterministic, and operator-reviewed.
- Do not use network calls.
- Do not call OpenRouter.
- Do not call Polymarket API.
- Do not use authenticated endpoints.
- Do not access wallet files, private keys, secrets, or credential stores.
- Do not create orders or use trading endpoints.
- Do not change runtime, dispatcher, or run_codex wiring.
- Do not add a scheduler, daemon, background worker, resident process, or browser automation.
- Do not produce forecast scoring, action guidance, or selection advice.
- Do not produce market recommendations, probability scores, EV, edge, confidence, or side selection.
- Do not use git add ., git add -A, git add --all, force push, or destructive commands.
- Return a strict result JSON packet that follows the result contract expectations.

## Allowed Paths

- docs/
- pm_bot/readiness/
- pm_bot/simulated_decisions/
- pm_bot/tests/
- tests/

## Forbidden Paths

- .env
- .env.*
- .git/
- .codex/
- runtime/
- dispatcher/
- run_codex/
- pm_bot/llm/
- pm_bot/wallet/
- pm_bot/trading/
- pm_bot/orders/
- agent_tasks/running/

## Safety Boundaries

- Local files and fixtures only.
- No network calls.
- No OpenRouter calls.
- No Polymarket API calls.
- No authenticated endpoints.
- No wallet or private-key access.
- No order placement.
- No trading endpoints.
- No external service calls.
- No sensitive credential or signing material access.
- No transaction endpoint or execution endpoint work.
- No runtime/dispatcher/run_codex changes.
- No core execution wiring changes.
- No timed automation or resident process.
- No scheduler or background worker.
- No browser automation.
- No destructive commands.
- No market recommendation, forecast scoring, action guidance, or selection advice.
- No probability, EV, edge, or confidence scoring.
- No real-money actions.

## Acceptance Checks

- python -m compileall pm_bot tests
- pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py

## Required Result JSON Shape

```json
{
  "task_id": "PMBOT-REHEARSAL-016-REHEARSAL-SIMULATED-DECISION-REPLAY-LINKS-LOCAL-ONLY",
  "status": "completed|partial|blocked",
  "summary": "",
  "files_changed": [],
  "validation_commands_run": [],
  "tests_passed": false,
  "safety_notes": [],
  "remaining_risks": []
}
```

## Explicit Safety Statement

Work only on this task. Do not use network unless explicitly allowed; this MVP does not allow network use. Do not touch credentials, wallet, trading, payment, runtime, dispatcher, run_codex, or Codex app-server code. Do not start background processes, daemons, workers, schedulers, or task scheduler jobs. Return the result JSON and a concise summary for human review.
