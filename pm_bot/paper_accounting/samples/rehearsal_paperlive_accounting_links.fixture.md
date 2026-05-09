# PMBOT Rehearsal Paperlive Accounting Links

Link set: `pmbot-rehearsal-paperlive-accounting-links-001`
Build ID: `pmbot-rehearsal-paperlive-accounting-links-001-43d69351f7da`
Run mode: `local_static_rehearsal_paperlive_accounting_links`
Operator review: `pending_operator_review`

## Summary

- Rehearsal artifacts: 2
- Accounting artifacts: 4
- Paperlive accounting links: 1
- Accounting entry links: 0
- Local references: 8
- Warnings: 0

## Rehearsal Artifacts

- `crypto_paperlive_rehearsal_packet_fixture`: 1 records from `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`.
- `crypto_paperlive_observation_replay_fixture`: 1 records from `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_observation_replay.valid.json`.

## Accounting Artifacts

- `paperlive_accounting_reconciliation_sample`: 1 records from `pm_bot/paper_accounting/samples/paperlive_accounting_reconciliation.fixture.json`.
- `paper_accounting_ledger_sample`: 3 records from `pm_bot/paper_accounting/samples/paper_accounting_ledger.fixture.json`.
- `paper_accounting_validation_sample`: 3 records from `pm_bot/paper_accounting/samples/paper_accounting_validation.fixture.json`.
- `paper_accounting_session_summary_sample`: 3 records from `pm_bot/paper_accounting/samples/paper_accounting_session_summary.fixture.json`.

## Links

- `pmbot-rehearsal-paperlive-accounting-links-001.sample.btc_threshold.paperlive_accounting` connects packet `pmbot-crypto-paperlive-rehearsal-packet-001.sample.btc_threshold.rehearsal` to reconciliation row `crypto_paperlive_observation_ledger_001.sample.btc_threshold.to.paper_accounting.paperlive_accounting_reconciliation` with 0 accounting entry links.

## Safety

- Local fixtures and static paper accounting samples only.
- No network, provider, external market API, authenticated endpoint, wallet, order, transaction, runtime, worker, scheduler, or browser use.
- Values remain in referenced local artifacts; this link set records identifiers for operator review.
- Not execution approval and not runtime input.
