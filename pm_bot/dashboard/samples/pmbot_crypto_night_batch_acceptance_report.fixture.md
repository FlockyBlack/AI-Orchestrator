# PMBOT Crypto Night Batch Acceptance Report

Report: `pmbot-crypto-night-batch-acceptance-report-001`
Run mode: `local_static_crypto_night_batch_acceptance_report`
Operator review: `pending_operator_review`

## Summary Counts

- Acceptance sections: 6
- Readiness records: 25
- Supporting artifacts: 23
- Source artifacts: 28
- Operator review checks: 8
- Validation command records: 2
- Pending acceptance sections: 6
- Warnings: 0

## Acceptance Sections

- `crypto_night_batch_inventory_review`: type `night_batch_inventory_review`, records 3, supporting artifacts 3, review `pending_operator_review`, reference `tests/test_codex_queue_pmbot_templates.py`
- `crypto_dashboard_readiness_review`: type `dashboard_readiness_review`, records 6, supporting artifacts 4, review `pending_operator_review`, reference `pm_bot/dashboard/samples/pmbot_crypto_dashboard_readiness_summary.fixture.json`
- `crypto_morning_card_review`: type `morning_card_review`, records 6, supporting artifacts 4, review `pending_operator_review`, reference `pm_bot/dashboard/samples/pmbot_crypto_morning_review_card.fixture.json`
- `crypto_rehearsal_and_gate_review`: type `rehearsal_gate_review`, records 6, supporting artifacts 6, review `pending_operator_review`, reference `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json`
- `crypto_validation_review`: type `validation_review`, records 2, supporting artifacts 3, review `pending_operator_review`, reference `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_validation_replay_bundle.valid.json`
- `crypto_safety_review`: type `safety_review`, records 2, supporting artifacts 3, review `pending_operator_review`, reference `pm_bot/tests/fixtures/crypto_live/pmbot_crypto_sensitive_path_exclusion_audit.valid.json`

## Validation Status Records

- `python -m compileall pm_bot tests`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`: status `not_run_static_record`, reference `tests/test_codex_queue_pmbot_templates.py`

## Operator Review

- Confirm acceptance sections have primary local references.
- Confirm source artifact references resolve inside allowed local paths.
- Confirm dashboard readiness and morning card samples are included.
- Confirm crypto rehearsal, gate, stop, and gap records remain pending review.
- Confirm validation command records are captured for operator review.
- Confirm sensitive path and execution wiring boundaries remain closed.
- Confirm the markdown report mirrors the static JSON report.
- Confirm the report remains descriptive review material only.

## Safety

- Local files, local fixtures, and static samples only.
- Makes no network, LLM provider, external service, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive crypto night batch acceptance report only; no live transition, data refresh, outcome resolution, market ranking, numeric prediction metric, threshold comparison output, or trade instruction output.
- Not execution approval and not runtime input.
