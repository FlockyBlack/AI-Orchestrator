# PMBOT Crypto Source Quality Capture Surface

Task: `PMBOT-CRYPTO-PILOT-004-CRYPTO-SOURCE-QUALITY-CAPTURE-SURFACE-LOCAL-ONLY`
Surface: `crypto_source_quality_capture_surface_001`
Build: `crypto_source_quality_capture_surface_001-e3588b6b1073`
Contract: `pmbot_crypto_source_quality_capture_surface.v1`
Run mode: `local_descriptive_crypto_source_quality_capture_surface`
Operator review: `pending_operator_review`

## Summary

- Input artifacts: 4
- Capture records: 4
- Required fields: 35
- Present fields: 35
- Missing fields: 0

## Capture Records

- `crypto_market_class_capture_template_001` (Crypto market class capture template)
  - Role: `market_class_capture_template`
  - Local artifact: `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
  - Contract: `pmbot_crypto_market_class_capture_template.v1`
  - Required fields visible: 8/8
  - Review status: `pending_operator_review`
- `crypto_operator_review_protocol_001` (Crypto operator review protocol)
  - Role: `operator_review_protocol`
  - Local artifact: `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
  - Contract: `pmbot_crypto_operator_review_protocol.v1`
  - Required fields visible: 9/9
  - Review status: `pending_operator_review`
- `crypto_paperlive_observation_ledger_001` (Crypto paperlive observation ledger)
  - Role: `paperlive_observation_ledger`
  - Local artifact: `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
  - Contract: `pmbot_crypto_paperlive_observation_ledger.v1`
  - Required fields visible: 8/8
  - Review status: `pending_operator_review`
- `static_crypto_reference_snapshot_2026_05_09_btc` (Static crypto reference snapshot)
  - Role: `static_reference_snapshot`
  - Local artifact: `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
  - Contract: `pmbot_static_crypto_reference_snapshot.v1`
  - Required fields visible: 10/10
  - Review status: `pending_operator_review`

## Operator Review Steps

- Confirm each listed local fixture opens as a static JSON artifact.
- Confirm required fields are visible in each artifact.
- Confirm every capture row remains pending operator review.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive source quality capture only; no outcome resolution or trade instruction output.
- Not execution approval and not runtime input.
