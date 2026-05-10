# PMBOT Practical Operator Workflow

This workflow is local-only and paper-only. It exists to test market analysis quality against concrete saved packets and outcome records.

## Import a local market packet

```powershell
python -m pm_bot.practical.local_market_packet_import --input pm_bot/tests/fixtures/practical_market_queue_batch/seeds/weather.seed.json --out-json pm_bot/practical/artifacts/night_002/local_packet_import_sample.result.json --out-md pm_bot/practical/artifacts/night_002/local_packet_import_sample.md
```

The importer preserves source references and missing evidence. It does not fetch live data or invent evidence.

## Run one-market analysis

```powershell
python -m pm_bot.practical.one_market_analysis --input pm_bot/tests/fixtures/practical_market_queue_batch/inputs/weather.one_market_input.json --out-json pm_bot/practical/artifacts/night_002/analyses/weather.analysis.result.json --out-md pm_bot/practical/artifacts/night_002/analyses/weather.analysis.md
```

The output is a paper-only analysis card with source attribution and an outcome-tracking placeholder.

## Run finite batch local analysis

```powershell
python -m pm_bot.practical.batch_local_analysis --queue pm_bot/tests/fixtures/practical_market_queue_batch/market_queue_5.valid.json --out-dir pm_bot/practical/artifacts/night_002/batch_analysis --out-summary-json pm_bot/practical/artifacts/night_002/batch_local_analysis_5.summary.json --out-summary-md pm_bot/practical/artifacts/night_002/batch_local_analysis_5.summary.md
```

This processes eligible queued items once and exits. It does not mutate the original queue unless `--out-queue` is provided.

## Inspect active paper hypotheses

```powershell
python -m pm_bot.practical.active_paper_hypotheses --queue pm_bot/tests/fixtures/practical_market_queue_batch/market_queue_5.valid.json --out-json pm_bot/practical/artifacts/night_002/active_paper_hypotheses_5.result.json --out-md pm_bot/practical/artifacts/night_002/active_paper_hypotheses_5.md
```

Use this to see unresolved outcomes, feedback pending, blocked items, and the next outcome checks.

## Run paper feedback after an outcome is known

```powershell
python -m pm_bot.practical.batch_paper_feedback --queue pm_bot/tests/fixtures/practical_market_queue_batch/market_queue_feedback_ready.valid.json --out-dir pm_bot/practical/artifacts/night_002/feedback_batch --out-summary-json pm_bot/practical/artifacts/night_002/batch_paper_feedback_5.summary.json --out-summary-md pm_bot/practical/artifacts/night_002/batch_paper_feedback_5.summary.md
```

Feedback uses local analysis and outcome JSON pairs only.

## Update source learning

```powershell
python -m pm_bot.practical.source_learning_batch --feedback pm_bot/practical/artifacts/night_002/feedback_batch/queue-feedback-weather-001-synthetic-weather-rain-001.feedback.result.json --out-json pm_bot/practical/artifacts/night_002/source_learning_batch_5.result.json --out-md pm_bot/practical/artifacts/night_002/source_learning_batch_5.md
```

Source learning is a transparent ledger update. It is not autonomous ML training.

## Open operator console artifacts

- `pm_bot/practical/artifacts/night_002/operator_console_5.md`
- `pm_bot/practical/artifacts/night_002/operator_next_actions_5.md`
- `pm_bot/practical/artifacts/night_002/practical_dashboard_index_5.md`

## Still manual

- Creating or exporting local market packets.
- Deciding whether missing evidence is acceptable for analysis-quality testing.
- Attaching resolved local outcome records.
- Reviewing feedback and source-learning notes.

## Prohibited

- Live market fetching in this local workflow.
- OpenRouter calls.
- Polymarket API calls.
- Authenticated endpoints.
- Wallet, private-key, signing, order, or real-money actions.
- Autonomous scheduling or background execution.
- Treating paper hypotheses as executable market instructions.
