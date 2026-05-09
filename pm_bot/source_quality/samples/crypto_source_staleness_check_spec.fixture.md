# PMBOT Crypto Source Staleness Check Spec

Task: `PMBOT-CRYPTO-LIVE-004-CRYPTO-SOURCE-STALENESS-CHECK-SPEC-LOCAL-ONLY`
Spec: `pmbot-crypto-source-staleness-check-spec-001`
Build: `pmbot-crypto-source-staleness-check-spec-001-8d78439513d2`
Contract: `pmbot_crypto_source_staleness_check_spec.v1`
Run mode: `local_static_crypto_source_staleness_check_spec`
Operator review: `pending_operator_review`

## Static Reference Clock

- Reference timestamp: `2026-05-09T01:30:00Z`
- Reference source: `static_fixture_reference_time`
- System clock used: `false`

## Summary

- Source staleness checks: 6
- Source evidence links: 6
- Source artifacts: 6
- Source contracts: 6
- Timestamp fields present: 6
- Timestamp fields missing: 0
- Local references: 15

## Source Evidence Link Map

- Link map: `pm_bot/source_quality/samples/crypto_source_evidence_link_map.fixture.json`
- Map: `pmbot-crypto-source-evidence-link-map-001`
- Build: `pmbot-crypto-source-evidence-link-map-001-31b7949e98d1`
- Rows: 6

## Source Staleness Checks

- `read_only_crypto_data_contract_fixture` (Read-only crypto data contract fixture)
  - Source artifact: `pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`
  - Source evidence link: `pmbot-crypto-source-evidence-link-map-001.read_only_crypto_data_contract_fixture.crypto_source_evidence_link`
  - Timestamp field path: `$.created_at`
  - Observed timestamp: `2026-05-09T00:40:00Z`
  - Age seconds: `3000`
  - Staleness state: `within_static_review_window`
  - Review checks: 4 pending operator review
- `crypto_market_class_capture_template` (Crypto market class capture template)
  - Source artifact: `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
  - Source evidence link: `pmbot-crypto-source-evidence-link-map-001.crypto_market_class_capture_template.crypto_source_evidence_link`
  - Timestamp field path: `$.created_at`
  - Observed timestamp: `2026-05-09T00:00:00Z`
  - Age seconds: `5400`
  - Staleness state: `within_static_review_window`
  - Review checks: 4 pending operator review
- `crypto_operator_review_protocol` (Crypto operator review protocol)
  - Source artifact: `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
  - Source evidence link: `pmbot-crypto-source-evidence-link-map-001.crypto_operator_review_protocol.crypto_source_evidence_link`
  - Timestamp field path: `$.created_at`
  - Observed timestamp: `2026-05-09T00:00:00Z`
  - Age seconds: `5400`
  - Staleness state: `within_static_review_window`
  - Review checks: 4 pending operator review
- `crypto_paperlive_observation_ledger` (Crypto paperlive observation ledger)
  - Source artifact: `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
  - Source evidence link: `pmbot-crypto-source-evidence-link-map-001.crypto_paperlive_observation_ledger.crypto_source_evidence_link`
  - Timestamp field path: `$.created_at`
  - Observed timestamp: `2026-05-09T00:20:00Z`
  - Age seconds: `4200`
  - Staleness state: `within_static_review_window`
  - Review checks: 4 pending operator review
- `crypto_source_quality_capture_surface_sample` (Crypto source quality capture surface sample)
  - Source artifact: `pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json`
  - Source evidence link: `pmbot-crypto-source-evidence-link-map-001.crypto_source_quality_capture_surface_sample.crypto_source_evidence_link`
  - Timestamp field path: `$.created_at`
  - Observed timestamp: `2026-05-09T00:30:00Z`
  - Age seconds: `3600`
  - Staleness state: `within_static_review_window`
  - Review checks: 4 pending operator review
- `static_crypto_reference_snapshot_2026_05_09_btc` (Static crypto reference sample)
  - Source artifact: `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
  - Source evidence link: `pmbot-crypto-source-evidence-link-map-001.static_crypto_reference_snapshot_2026_05_09_btc.crypto_source_evidence_link`
  - Timestamp field path: `$.reported_at_utc`
  - Observed timestamp: `2026-05-09T00:00:00Z`
  - Age seconds: `5400`
  - Staleness state: `within_static_review_window`
  - Review checks: 4 pending operator review

## Operator Review Steps

- Confirm every crypto source evidence link row has one local staleness check row.
- Confirm timestamp field paths, age windows, and digests match local static artifacts.
- Record disputes outside this spec before any later readiness status change.

## Safety

- Local fixture/static input only.
- Uses the fixed fixture reference timestamp, not the system clock.
- Makes no network, LLM, market API, endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.
- Records descriptive age windows, digests, and pending review state only.
- Does not authorize execution and is not runtime input.
