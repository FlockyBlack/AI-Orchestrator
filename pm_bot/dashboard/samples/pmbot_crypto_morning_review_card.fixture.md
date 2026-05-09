# PMBOT Crypto Morning Review Card

Card: `pmbot-crypto-morning-review-card-001`
Run mode: `local_static_crypto_morning_review_card`
Operator review: `pending_operator_review`

## Summary Counts

- Card sections: 6
- Readiness records: 20
- Supporting artifacts: 19
- Source artifacts: 24
- Operator review checks: 7
- Validation command records: 2
- Pending card sections: 6
- Warnings: 0

## Card Sections

- `crypto_dashboard_readiness_snapshot`: type `dashboard_readiness_snapshot`, records 6, supporting artifacts 3, review `pending_operator_review`, reference `pm_bot/dashboard/samples/pmbot_crypto_dashboard_readiness_summary.fixture.json`
- `crypto_source_review_snapshot`: type `source_review_snapshot`, records 4, supporting artifacts 4, review `pending_operator_review`, reference `docs/PMBOT_CRYPTO_LIVE_003_CRYPTO_SOURCE_EVIDENCE_LINK_MAP_LOCAL_ONLY.md`
- `crypto_rehearsal_review_snapshot`: type `rehearsal_review_snapshot`, records 3, supporting artifacts 3, review `pending_operator_review`, reference `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `crypto_gate_review_snapshot`: type `gate_review_snapshot`, records 3, supporting artifacts 3, review `pending_operator_review`, reference `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_operator_approval_gate_record.valid.json`
- `crypto_validation_review_snapshot`: type `validation_review_snapshot`, records 2, supporting artifacts 3, review `pending_operator_review`, reference `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_validation_replay_bundle.valid.json`
- `crypto_safety_review_snapshot`: type `safety_review_snapshot`, records 2, supporting artifacts 3, review `pending_operator_review`, reference `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_sensitive_path_exclusion_audit.valid.json`

## Validation Status Records

- `python -m compileall pm_bot tests`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`

## Operator Review

- Confirm each card section has one primary local reference.
- Confirm source artifact references resolve inside allowed local paths.
- Confirm the crypto dashboard summary is included as the morning snapshot basis.
- Confirm crypto gate records remain pending operator review.
- Confirm local validation command records are captured for operator review.
- Confirm sensitive path and execution wiring boundaries remain closed.
- Confirm this report mirrors the static morning card.

## Safety

- Local files, local fixtures, and static samples only.
- Makes no network, LLM provider, external service, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive crypto morning review card only; no live transition, data refresh, outcome resolution, or trade instruction output.
- Not execution approval and not runtime input.
