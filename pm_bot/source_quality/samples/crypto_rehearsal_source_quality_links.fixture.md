# PMBOT Crypto Rehearsal To Source Quality Links

Task: `PMBOT-CRYPTO-LIVE-019-CRYPTO-REHEARSAL-TO-SOURCE-QUALITY-LINKS-LOCAL-ONLY`
Link set: `pmbot-crypto-rehearsal-source-quality-links-001`
Build: `pmbot-crypto-rehearsal-source-quality-links-001-c47d1d7b9791`
Contract: `pmbot_crypto_rehearsal_source_quality_links.v1`
Run mode: `local_static_crypto_rehearsal_source_quality_links`
Operator review: `pending_operator_review`

## Summary

- Rehearsal source links: 4
- Source quality artifacts: 4
- Source quality record links: 19
- Local references: 7

## Rehearsal Packet

- Packet: `pmbot-crypto-paperlive-rehearsal-packet-001`
- Fixture: `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- Records: 1

## Link Rows

- `crypto_market_class_capture_template`
  - Rehearsal source field: `source_capture_record_id`
  - Rehearsal source record: `crypto_market_class_capture_template_001.sample.btc_threshold`
  - Capture record: `crypto_source_quality_capture_surface_001.crypto_market_class_capture_template_001.quality_capture`
  - Evidence link: `pmbot-crypto-source-evidence-link-map-001.crypto_market_class_capture_template.crypto_source_evidence_link`
  - Staleness check: `pmbot-crypto-source-staleness-check-spec-001.crypto_market_class_capture_template.crypto_source_staleness_check`
  - Contradiction rows: 1
  - Review checks: 4 pending operator review
- `crypto_operator_review_protocol`
  - Rehearsal source field: `source_review_record_id`
  - Rehearsal source record: `crypto_operator_review_protocol_001.sample.btc_threshold.review`
  - Capture record: `crypto_source_quality_capture_surface_001.crypto_operator_review_protocol_001.quality_capture`
  - Evidence link: `pmbot-crypto-source-evidence-link-map-001.crypto_operator_review_protocol.crypto_source_evidence_link`
  - Staleness check: `pmbot-crypto-source-staleness-check-spec-001.crypto_operator_review_protocol.crypto_source_staleness_check`
  - Contradiction rows: 2
  - Review checks: 4 pending operator review
- `crypto_paperlive_observation_ledger`
  - Rehearsal source field: `observation_record_id`
  - Rehearsal source record: `crypto_paperlive_observation_ledger_001.sample.btc_threshold.observation`
  - Capture record: `crypto_source_quality_capture_surface_001.crypto_paperlive_observation_ledger_001.quality_capture`
  - Evidence link: `pmbot-crypto-source-evidence-link-map-001.crypto_paperlive_observation_ledger.crypto_source_evidence_link`
  - Staleness check: `pmbot-crypto-source-staleness-check-spec-001.crypto_paperlive_observation_ledger.crypto_source_staleness_check`
  - Contradiction rows: 2
  - Review checks: 4 pending operator review
- `static_crypto_reference_snapshot_2026_05_09_btc`
  - Rehearsal source field: `local_snapshot_reference`
  - Rehearsal source record: `static_crypto_reference_snapshot_2026_05_09_btc`
  - Capture record: `crypto_source_quality_capture_surface_001.static_crypto_reference_snapshot_2026_05_09_btc.quality_capture`
  - Evidence link: `pmbot-crypto-source-evidence-link-map-001.static_crypto_reference_snapshot_2026_05_09_btc.crypto_source_evidence_link`
  - Staleness check: `pmbot-crypto-source-staleness-check-spec-001.static_crypto_reference_snapshot_2026_05_09_btc.crypto_source_staleness_check`
  - Contradiction rows: 2
  - Review checks: 4 pending operator review

## Operator Review Steps

- Confirm the rehearsal packet record resolves to the listed source quality records.
- Confirm every source quality record remains local, static, and pending operator review.
- Confirm source value fields remain in referenced artifacts and are not copied into this link set.

## Safety

- Local files, local fixtures, and static samples only.
- Makes no network, LLM, market API, endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.
- Records local links and pending review state only; source values remain in referenced artifacts.
- No forecast scoring, action guidance, market ranking, outcome resolution, selection advice, or trade instruction output.
- Not execution approval and not runtime input.
