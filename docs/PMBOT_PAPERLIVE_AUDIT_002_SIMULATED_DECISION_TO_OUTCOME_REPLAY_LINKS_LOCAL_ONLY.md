# PMBOT Paperlive Audit 002 Simulated Decision To Outcome Replay Links

Task: `PMBOT-PAPERLIVE-AUDIT-002-SIMULATED-DECISION-TO-OUTCOME-REPLAY-LINKS-LOCAL-ONLY`

Artifact: `pmbot-simulated-decision-outcome-replay-links`
Contract: `pmbot_simulated_decision_outcome_replay_links.v1`
Run mode: `offline_recordkeeping`
Operator review: `pending_operator_review`

## Purpose

This artifact defines deterministic local replay links from a static simulated decision replay summary to a static outcome-review request fixture. It uses only local fixtures and static samples, and it is built for operator review.

The replay links are descriptive only. They are not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Inputs

- Request fixture: `pm_bot/tests/fixtures/simulated_decisions/simulated_decision_outcome_replay_links_request.valid.json`
- Simulated decision replay summary sample: `pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json`
- Weather outcome review request fixture: `pm_bot/tests/fixtures/weather_outcome_reconciliation_request.valid.json`

## Static Outputs

- Replay links sample: `pm_bot/simulated_decisions/samples/simulated_decision_outcome_replay_links.fixture.json`
- Operator report sample: `pm_bot/simulated_decisions/samples/simulated_decision_outcome_replay_links.fixture.md`
- Schema: `pm_bot/simulated_decisions/schemas/simulated_decision_outcome_replay_links.schema.v1.json`
- Builder: `pm_bot/simulated_decisions/outcome_replay_links.py`
- Tests: `pm_bot/tests/test_simulated_decision_outcome_replay_links.py`

## Static Sample Command

```powershell
python -m pm_bot.simulated_decisions.outcome_replay_links `
  --request pm_bot\tests\fixtures\simulated_decisions\simulated_decision_outcome_replay_links_request.valid.json `
  --output-links pm_bot\simulated_decisions\samples\simulated_decision_outcome_replay_links.fixture.json `
  --output-report pm_bot\simulated_decisions\samples\simulated_decision_outcome_replay_links.fixture.md
```

## Operator Review Boundary

Operators review whether the replay summary identity, source packet identity, outcome artifact identity, local references, record IDs, and safety flags are reproduced from local static files.

All rows remain `pending_operator_review` and `recorded_for_operator_review`. Any final outcome record remains outside this artifact.

## Safety

- Local files, local fixtures, and static samples only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, or selection advice.
- This artifact is not execution approval and is not runtime input.

## Validation

Required local validation commands:

- `python -m compileall pm_bot tests`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`
