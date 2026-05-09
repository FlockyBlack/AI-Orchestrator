# PMBOT Crypto Source Contradiction Ledger

Task: `PMBOT-CRYPTO-LIVE-005-CRYPTO-SOURCE-CONTRADICTION-LEDGER-LOCAL-ONLY`
Ledger: `pmbot-crypto-source-contradiction-ledger-001`
Build: `pmbot-crypto-source-contradiction-ledger-001-7caf57862990`
Contract: `pmbot_crypto_source_contradiction_ledger.v1`
Run mode: `local_static_crypto_source_contradiction_ledger`
Operator review: `pending_operator_review`

## Summary

- Source contradiction rows: 4
- Source staleness checks: 5
- Source artifact references: 5
- Subject key comparisons: 6
- Subject key differences: 0
- Field comparisons: 33
- Static value differences: 0
- Local references: 8

## Source Staleness Spec

- Spec: `pm_bot/source_quality/samples/crypto_source_staleness_check_spec.fixture.json`
- Spec id: `pmbot-crypto-source-staleness-check-spec-001`
- Build: `pmbot-crypto-source-staleness-check-spec-001-8d78439513d2`
- Rows: 6

## Source Contradiction Rows

- `read_only_contract_to_reference_snapshot_static_copy` (Read-only contract static sample to reference snapshot copy review)
  - Left source: `read_only_crypto_data_contract_fixture` -> `pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`
  - Right source: `static_crypto_reference_snapshot_2026_05_09_btc` -> `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
  - Contradiction state: `no_static_difference_recorded`
  - Review checks: 4 pending operator review
  - asset_name: `asset_name`=`Bitcoin`; `asset_name`=`Bitcoin`; state `matching_static_values`
  - measurement_source_label: `measurement_source_label`=`local fixture index close label`; `measurement_source_label`=`local fixture index close label`; state `matching_static_values`
  - reported_at_utc: `reported_at_utc`=`2026-05-09T00:00:00Z`; `reported_at_utc`=`2026-05-09T00:00:00Z`; state `matching_static_values`
  - reported_reference_unit: `reported_reference_unit`=`USD`; `reported_reference_unit`=`USD`; state `matching_static_values`
  - source_label: `source_label`=`Static crypto reference sample`; `source_label`=`Static crypto reference sample`; state `matching_static_values`
- `market_capture_to_operator_review_static_copy` (Market capture sample to operator review record copy review)
  - Left source: `crypto_market_class_capture_template` -> `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
  - Right source: `crypto_operator_review_protocol` -> `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
  - Contradiction state: `no_static_difference_recorded`
  - Review checks: 4 pending operator review
  - market_class: `market_class`=`crypto_threshold_event`; `market_class`=`crypto_threshold_event`; state `matching_static_values`
  - market_slug: `market_slug`=`static-sample-btc-threshold-2026`; `market_slug`=`static-sample-btc-threshold-2026`; state `matching_static_values`
  - market_title: `market_title`=`Static sample BTC threshold market`; `market_title`=`Static sample BTC threshold market`; state `matching_static_values`
  - asset_symbol: `asset_symbol`=`BTC`; `asset_symbol`=`BTC`; state `matching_static_values`
  - asset_name: `asset_name`=`Bitcoin`; `asset_name`=`Bitcoin`; state `matching_static_values`
  - quote_currency: `quote_currency`=`USD`; `quote_currency`=`USD`; state `matching_static_values`
  - metric_type: `metric_type`=`spot_index_threshold`; `metric_type`=`spot_index_threshold`; state `matching_static_values`
  - threshold_value: `threshold_value`=`150000.00`; `threshold_value`=`150000.00`; state `matching_static_values`
  - threshold_unit: `threshold_unit`=`USD`; `threshold_unit`=`USD`; state `matching_static_values`
  - comparison_rule: `comparison_rule`=`at_or_above_threshold_by_deadline`; `comparison_rule`=`at_or_above_threshold_by_deadline`; state `matching_static_values`
  - deadline_utc: `deadline_utc`=`2026-12-31T23:59:59Z`; `deadline_utc`=`2026-12-31T23:59:59Z`; state `matching_static_values`
- `operator_review_to_observation_static_copy` (Operator review record to observation ledger copy review)
  - Left source: `crypto_operator_review_protocol` -> `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
  - Right source: `crypto_paperlive_observation_ledger` -> `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
  - Contradiction state: `no_static_difference_recorded`
  - Review checks: 4 pending operator review
  - market_class: `market_class`=`crypto_threshold_event`; `market_class`=`crypto_threshold_event`; state `matching_static_values`
  - market_slug: `market_slug`=`static-sample-btc-threshold-2026`; `market_slug`=`static-sample-btc-threshold-2026`; state `matching_static_values`
  - market_title: `market_title`=`Static sample BTC threshold market`; `market_title`=`Static sample BTC threshold market`; state `matching_static_values`
  - asset_symbol: `asset_symbol`=`BTC`; `asset_symbol`=`BTC`; state `matching_static_values`
  - asset_name: `asset_name`=`Bitcoin`; `asset_name`=`Bitcoin`; state `matching_static_values`
  - quote_currency: `quote_currency`=`USD`; `quote_currency`=`USD`; state `matching_static_values`
  - metric_type: `metric_type`=`spot_index_threshold`; `metric_type`=`spot_index_threshold`; state `matching_static_values`
  - threshold_value: `threshold_value`=`150000.00`; `threshold_value`=`150000.00`; state `matching_static_values`
  - threshold_unit: `threshold_unit`=`USD`; `threshold_unit`=`USD`; state `matching_static_values`
  - comparison_rule: `comparison_rule`=`at_or_above_threshold_by_deadline`; `comparison_rule`=`at_or_above_threshold_by_deadline`; state `matching_static_values`
  - deadline_utc: `deadline_utc`=`2026-12-31T23:59:59Z`; `deadline_utc`=`2026-12-31T23:59:59Z`; state `matching_static_values`
- `observation_to_reference_snapshot_static_copy` (Observation ledger to reference snapshot copy review)
  - Left source: `crypto_paperlive_observation_ledger` -> `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
  - Right source: `static_crypto_reference_snapshot_2026_05_09_btc` -> `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
  - Contradiction state: `no_static_difference_recorded`
  - Review checks: 4 pending operator review
  - asset_name: `asset_name`=`Bitcoin`; `asset_name`=`Bitcoin`; state `matching_static_values`
  - measurement_source_label: `measurement_source_label`=`local fixture index close label`; `measurement_source_label`=`local fixture index close label`; state `matching_static_values`
  - reported_at_utc: `reported_at_utc`=`2026-05-09T00:00:00Z`; `reported_at_utc`=`2026-05-09T00:00:00Z`; state `matching_static_values`
  - reported_reference_unit: `reported_reference_unit`=`USD`; `reported_reference_unit`=`USD`; state `matching_static_values`
  - reported_reference_value: `reported_reference_value`=`102500.00`; `reported_reference_value`=`102500.00`; state `matching_static_values`
  - source_label: `observation_source_label`=`Static crypto reference sample`; `source_label`=`Static crypto reference sample`; state `matching_static_values`

## Operator Review Steps

- Confirm each crypto source pair resolves to local static artifacts and expected nested records.
- Confirm static copy fields and source keys match or remain pending operator review when they differ.
- Record disputes outside this ledger before any later readiness status change.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, market API, endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.
- Records descriptive source copy checks and pending review state only.
- Not execution approval and not runtime input.
