# PMBOT Crypto Source Evidence Link Map

Task: `PMBOT-CRYPTO-LIVE-003-CRYPTO-SOURCE-EVIDENCE-LINK-MAP-LOCAL-ONLY`
Map: `pmbot-crypto-source-evidence-link-map-001`
Build: `pmbot-crypto-source-evidence-link-map-001-31b7949e98d1`
Contract: `pmbot_crypto_source_evidence_link_map.v1`
Run mode: `local_static_crypto_source_evidence_link_map`
Operator review: `pending_operator_review`

## Summary

- Source evidence links: 6
- Source artifacts: 6
- Source contracts: 6
- Inventory records linked: 6
- Local references: 14

## Source Inventory

- Inventory: `pmbot-crypto-live-data-source-inventory-001`
- Fixture: `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_live_data_source_inventory.valid.json`
- Documentation: `docs/PMBOT_CRYPTO_LIVE_002_CRYPTO_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- Source records: 6

## Source Evidence Links

- `read_only_crypto_data_contract_fixture` (Read-only crypto data contract fixture)
  - Source artifact: `pm_bot/tests/fixtures/crypto_live/pmbot_read_only_crypto_data_contract.valid.json`
  - Source record: `crypto_live_data_source_inventory_001.read_only_contract_fixture`
  - Source contract: `crypto_live_read_only_crypto_data_contract`
  - Contract documentation: `docs/PMBOT_CRYPTO_LIVE_001_READ_ONLY_CRYPTO_DATA_CONTRACT_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review
- `crypto_market_class_capture_template` (Crypto market class capture template)
  - Source artifact: `pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json`
  - Source record: `crypto_live_data_source_inventory_001.crypto_market_class_capture_template`
  - Source contract: `crypto_market_class_capture_template`
  - Contract documentation: `docs/PMBOT_CRYPTO_PILOT_001_CRYPTO_MARKET_CLASS_CAPTURE_TEMPLATE_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review
- `crypto_operator_review_protocol` (Crypto operator review protocol)
  - Source artifact: `pm_bot/tests/fixtures/crypto_operator_review_protocol/crypto_operator_review_protocol.valid.json`
  - Source record: `crypto_live_data_source_inventory_001.crypto_operator_review_protocol`
  - Source contract: `crypto_operator_review_protocol`
  - Contract documentation: `docs/PMBOT_CRYPTO_PILOT_002_CRYPTO_OPERATOR_REVIEW_PROTOCOL_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review
- `crypto_paperlive_observation_ledger` (Crypto paperlive observation ledger)
  - Source artifact: `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/crypto_paperlive_observation_ledger.valid.json`
  - Source record: `crypto_live_data_source_inventory_001.crypto_paperlive_observation_ledger`
  - Source contract: `crypto_paperlive_observation_ledger`
  - Contract documentation: `docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review
- `crypto_source_quality_capture_surface_sample` (Crypto source quality capture surface sample)
  - Source artifact: `pm_bot/source_quality/samples/crypto_source_quality_capture_surface.fixture.json`
  - Source record: `crypto_live_data_source_inventory_001.crypto_source_quality_capture_surface`
  - Source contract: `crypto_source_quality_capture_surface`
  - Contract documentation: `docs/PMBOT_CRYPTO_PILOT_004_CRYPTO_SOURCE_QUALITY_CAPTURE_SURFACE_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review
- `static_crypto_reference_snapshot_2026_05_09_btc` (Static crypto reference sample)
  - Source artifact: `pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json`
  - Source record: `crypto_live_data_source_inventory_001.static_crypto_reference_snapshot`
  - Source contract: `crypto_paperlive_observation_ledger`
  - Contract documentation: `docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md`
  - Review checks: 4 pending operator review

## Operator Review Steps

- Confirm every crypto source record has a local artifact link, inventory record link, and contract documentation link.
- Confirm linked local references remain static and under allowed paths.
- Record disputes outside this map before any later readiness status change.

## Safety

- Local fixture/static input only.
- Makes no network, LLM, market API, endpoint, wallet, order, transaction, runtime, browser, scheduler, or worker calls.
- Records local references, byte counts, digests, and pending review state only.
- Does not authorize execution and is not runtime input.
