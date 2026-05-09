# PMBOT Crypto Paperlive Observation Ledger

Task: `PMBOT-CRYPTO-PILOT-003-CRYPTO-PAPERLIVE-OBSERVATION-LEDGER-LOCAL-ONLY`

Ledger: `crypto-paperlive-observation-ledger`
Contract: `pmbot_crypto_paperlive_observation_ledger.v1`
Run mode: `local_descriptive_crypto_paperlive_observation_ledger`
Operator review: `pending_operator_review`

## Purpose

This ledger defines a local, deterministic record shape for crypto paperlive observation records. It is for descriptive recordkeeping only and uses local static samples.

## Ledger Record Fields

Each observation record keeps these fields in a fixed contract:

- `record_id`
- `source_review_record_id`
- `market_class`
- `market_slug`
- `market_title`
- `asset_symbol`
- `asset_name`
- `quote_currency`
- `metric_type`
- `measurement_source_label`
- `threshold_value`
- `threshold_unit`
- `comparison_rule`
- `deadline_utc`
- `observation_window_start_utc`
- `observation_window_end_utc`
- `reported_reference_value`
- `reported_reference_unit`
- `reported_at_utc`
- `observation_source_label`
- `local_source_reference`
- `copied_text_check`
- `operator_notes`
- `review_status`

## Static Fixtures

The local ledger fixture is:

`pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`

The local static observation sample is:

`pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`

The ledger also references the earlier local crypto capture and operator review fixtures:

- `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
- `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`

## Operator Review Boundary

Operators review whether the observation row copies static fixture labels, timestamps, reference values, and market text accurately. Review status remains `pending_operator_review` until a human updates a later artifact.

This ledger does not compute market outcomes, compare thresholds, rank records, choose an operator path, or approve runtime use.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet access, signing material access, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, market ranking, or selection advice.
- This ledger is not execution approval and is not runtime input.
