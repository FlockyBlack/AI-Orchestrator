# PMBOT Rehearsal Readiness Dashboard Card

Task: `PMBOT-REHEARSAL-011-REHEARSAL-READINESS-DASHBOARD-CARD-LOCAL-ONLY`
Card: `pmbot-rehearsal-readiness-dashboard-card-001`
Build: `pmbot-rehearsal-readiness-dashboard-card-001-878530e0029e`
Contract: `pmbot_rehearsal_readiness_dashboard_card.v1`
Run mode: `local_static_rehearsal_readiness_dashboard_card`
Review date: `2026-05-09`
Operator review: `pending_operator_review`

## Sections
- `rehearsal_control_record_section`: role `control_artifact_review`, records 4, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_001_READ_ONLY_REHEARSAL_SCENARIO_CONTRACT_LOCAL_ONLY.md`
- `source_review_case_section`: role `source_artifact_review`, records 4, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_003_REHEARSAL_SOURCE_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `validation_runner_section`: role `validation_artifact_review`, records 2, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_010_REHEARSAL_CI_SAFE_VALIDATION_RUNNER_LOCAL_ONLY.md`
- `dashboard_context_section`: role `dashboard_context_review`, records 1, review `pending_operator_review`, reference `pm_bot/dashboard/samples/local_supervised_live_readiness_dashboard.fixture.json`

## Readiness Records
- `rehearsal_readiness_dashboard_card_document`: type `markdown_document`, state `pending_operator_review`, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_011_REHEARSAL_READINESS_DASHBOARD_CARD_LOCAL_ONLY.md`
- `rehearsal_readiness_dashboard_card_builder`: type `python_module`, state `local_validation_reference`, review `pending_operator_review`, reference `pm_bot/dashboard/local_rehearsal_readiness_dashboard_card.py`
- `rehearsal_readiness_dashboard_card_contract_test`: type `python_test_reference`, state `local_validation_reference`, review `pending_operator_review`, reference `pm_bot/tests/test_rehearsal_readiness_dashboard_card.py`
- `queue_template_validation_test`: type `python_test_reference`, state `local_validation_reference`, review `pending_operator_review`, reference `tests/test_codex_queue_pmbot_templates.py`
- `rehearsal_ci_safe_validation_runner`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json`
- `rehearsal_validation_replay_packet`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_validation_replay_packet.valid.json`
- `read_only_rehearsal_scenario_contract`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_read_only_rehearsal_scenario_contract.valid.json`
- `rehearsal_market_packet_schema`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_market_packet_schema.valid.json`
- `rehearsal_source_evidence_bundle`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_source_evidence_bundle.valid.json`
- `rehearsal_operator_approval_record`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_operator_approval_record.valid.json`
- `rehearsal_stop_condition_trigger_matrix`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_stop_condition_trigger_matrix.valid.json`
- `rehearsal_staleness_case_set`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_staleness_case_set.valid.json`
- `rehearsal_contradiction_case_set`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_contradiction_case_set.valid.json`
- `rehearsal_evidence_retention_ledger`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_evidence_retention_ledger.valid.json`
- `local_supervised_live_readiness_dashboard_sample`: type `json_fixture`, state `pending_operator_review`, review `pending_operator_review`, reference `pm_bot/dashboard/samples/local_supervised_live_readiness_dashboard.fixture.json`

## Safety Records
- `local_static_material_boundary`: state `closed`, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_011_REHEARSAL_READINESS_DASHBOARD_CARD_LOCAL_ONLY.md`
- `endpoint_and_service_boundary`: state `closed`, review `pending_operator_review`, reference `docs/PMBOT_REHEARSAL_010_REHEARSAL_CI_SAFE_VALIDATION_RUNNER_LOCAL_ONLY.md`
- `sensitive_path_boundary`: state `closed`, review `pending_operator_review`, reference `pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json`
- `execution_wiring_boundary`: state `closed`, review `pending_operator_review`, reference `tests/test_codex_queue_pmbot_templates.py`

## Validation
- `python -m compileall pm_bot tests`: status `not_run_static_record`, review `pending_operator_review`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`: status `not_run_static_record`, review `pending_operator_review`, reference `tests/test_codex_queue_pmbot_templates.py`

## Summary Counts
- Card sections: `4`
- Readiness records: `15`
- Safety records: `4`
- Validation records: `2`
- Local references: `18`
- Pending operator review records: `25`

## Operator Review Boundary
- Descriptive readiness dashboard card only; no live data refresh, endpoint use, transaction output, or execution output.
- Human review remains required before any later operational use.
