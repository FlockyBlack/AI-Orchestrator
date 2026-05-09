# PMBOT Crypto Operator Review Protocol

Task: `PMBOT-CRYPTO-PILOT-002-CRYPTO-OPERATOR-REVIEW-PROTOCOL-LOCAL-ONLY`

Protocol: `crypto-operator-review-protocol`
Contract: `pmbot_crypto_operator_review_protocol.v1`
Run mode: `local_descriptive_operator_review_protocol`
Operator review: `pending_operator_review`

## Purpose

This protocol defines a local, deterministic operator review shape for crypto pilot records. It is for descriptive record checks only and uses local static samples.

## Review Inputs

The initial protocol uses this local capture fixture:

`pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`

The protocol checks whether a local review record preserves copied market text, copied deadline text, copied threshold fields, local source reference, and pending operator review state.

## Review Record Fields

Each review record keeps these fields in a fixed contract:

- `review_record_id`
- `source_record_id`
- `market_class`
- `market_slug`
- `market_title`
- `asset_symbol`
- `asset_name`
- `quote_currency`
- `metric_type`
- `threshold_value`
- `threshold_unit`
- `comparison_rule`
- `deadline_utc`
- `local_source_reference`
- `copied_text_check`
- `timestamp_check`
- `field_presence_check`
- `operator_notes`
- `review_status`

## Protocol Steps

The static fixture defines four deterministic inspection steps:

- Field presence check.
- Copied text check.
- Timestamp check.
- Pending state check.

Each step records only whether the expected local fields are visible for later human review. The protocol does not compute a market outcome, rank records, or choose an operator path.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`

It contains one static review record copied from the crypto market class capture template sample. The sample is not live market data and is not runtime input.

## Operator Review Boundary

Operators review whether the descriptive fields in the local review record match the local static capture fixture. Review status remains `pending_operator_review` until a human updates a later artifact.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet access, signing material access, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, market ranking, or selection advice.
- This protocol is not execution approval and is not runtime input.
