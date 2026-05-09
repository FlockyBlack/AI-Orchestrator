# PMBOT Crypto Market Class Capture Template

Task: `PMBOT-CRYPTO-PILOT-001-CRYPTO-MARKET-CLASS-CAPTURE-TEMPLATE-LOCAL-ONLY`

Template: `crypto-market-class-capture`
Contract: `pmbot_crypto_market_class_capture_template.v1`
Run mode: `local_descriptive_capture_template`
Operator review: `pending_operator_review`

## Purpose

This template defines a local, deterministic capture shape for crypto market class records. It is for descriptive recordkeeping only and uses local static samples.

## Capture Fields

Each captured record keeps these fields in a fixed contract:

- `record_id`
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
- `source_snapshot_reference`
- `operator_notes`
- `capture_status`

## Market Class Catalog

Initial class: `crypto_threshold_event`

This class records a crypto asset threshold condition, copied market title, copied local source reference, measurement label, comparison rule, and deadline. The class does not rank markets, compute values, or choose an operator action.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`

It contains one static sample record for the capture shape. The sample is not live market data and is not runtime input.

## Operator Review Boundary

Operators review whether the captured market class fields were copied accurately from a local static source. Review status remains `pending_operator_review` until a human updates a later artifact.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No wallet access, signing material access, or transaction endpoint use.
- No runtime, dispatcher, scheduler, worker, browser, or app-server wiring.
- No forecast scoring, action guidance, market ranking, or selection advice.
- This template is not execution approval and is not runtime input.
