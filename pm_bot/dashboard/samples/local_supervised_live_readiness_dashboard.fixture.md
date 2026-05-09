# PMBOT Supervised Live Readiness Dashboard

Dashboard: `local_supervised_live_readiness_dashboard_fixture_001`
Build: `local_supervised_live_readiness_dashboard_fixture_001-94f18392f00c`
Label: `PMBOT local supervised-live readiness dashboard`
Run mode: `local_static_supervised_live_readiness_dashboard`
Operator review: `pending_operator_review`

## Summary Counts

- Queue records: 7
- Readiness artifacts: 6
- Readiness rows: 38
- Supporting artifacts: 21
- Operator review checks: 28
- Validation commands: 12
- Validation records: 2
- Pending operator review records: 15
- Warnings: 0

## Queue Records

- `PMBOT-DASHBOARD-005-SUPERVISED-LIVE-READINESS-DASHBOARD-LOCAL-ONLY`: group `supervised_live_readiness_template`, template `supervised_live_readiness_dashboard`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_DASHBOARD_005_SUPERVISED_LIVE_READINESS_DASHBOARD_LOCAL_ONLY.md`
- `PMBOT-SUPERVISED-LIVE-001-READ-ONLY-LIVE-DATA-CONTRACT-LOCAL-ONLY`: group `supervised_live_readiness_template`, template `read_only_live_data_contract`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_SUPERVISED_LIVE_001_READ_ONLY_LIVE_DATA_CONTRACT_LOCAL_ONLY.md`
- `PMBOT-SUPERVISED-LIVE-002-LIVE-DATA-SOURCE-INVENTORY-LOCAL-ONLY`: group `supervised_live_readiness_template`, template `live_data_source_inventory`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_SUPERVISED_LIVE_002_LIVE_DATA_SOURCE_INVENTORY_LOCAL_ONLY.md`
- `PMBOT-SUPERVISED-LIVE-003-OPERATOR-APPROVAL-GATE-RECORD-LOCAL-ONLY`: group `supervised_live_readiness_template`, template `operator_approval_gate_record`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_SUPERVISED_LIVE_003_OPERATOR_APPROVAL_GATE_RECORD_LOCAL_ONLY.md`
- `PMBOT-SUPERVISED-LIVE-004-SUPERVISED-LIVE-STOP-CONDITION-SPEC-LOCAL-ONLY`: group `supervised_live_readiness_template`, template `supervised_live_stop_condition_spec`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_SUPERVISED_LIVE_004_SUPERVISED_LIVE_STOP_CONDITION_SPEC_LOCAL_ONLY.md`
- `PMBOT-SUPERVISED-LIVE-005-LIVE-READINESS-EVIDENCE-BUNDLE-LOCAL-ONLY`: group `supervised_live_readiness_template`, template `supervised_live_readiness_evidence_bundle`, state `template_listed_static_record`, review `pending_operator_review`, reference `docs/PMBOT_SUPERVISED_LIVE_005_LIVE_READINESS_EVIDENCE_BUNDLE_LOCAL_ONLY.md`
- `PMBOT-ROADMAP-002-PMBOT-LOCAL-TO-SUPERVISED-LIVE-GAP-MATRIX`: group `next_twenty_template`, template `local_to_supervised_live_gap_matrix`, state `template_listed_static_record`, review `pending_operator_review`, reference `pm_bot/readiness/PMBOT_ROADMAP_002_PMBOT_LOCAL_TO_SUPERVISED_LIVE_GAP_MATRIX.md`

## Readiness Artifacts

- `read_only_live_data_contract`: type `supervised_live_contract`, rows 5, supporting artifacts 3, review `pending_operator_review`, fixture `pm_bot/tests/fixtures/readiness/pmbot_read_only_live_data_contract.valid.json`
- `live_data_source_inventory`: type `supervised_live_inventory`, rows 4, supporting artifacts 3, review `pending_operator_review`, fixture `pm_bot/tests/fixtures/readiness/pmbot_live_data_source_inventory.valid.json`
- `operator_approval_gate_record`: type `supervised_live_gate_record`, rows 6, supporting artifacts 5, review `pending_operator_review`, fixture `pm_bot/tests/fixtures/readiness/pmbot_operator_approval_gate_record.valid.json`
- `supervised_live_stop_condition_spec`: type `supervised_live_stop_spec`, rows 6, supporting artifacts 5, review `pending_operator_review`, fixture `pm_bot/tests/fixtures/readiness/pmbot_supervised_live_stop_condition_spec.valid.json`
- `supervised_live_readiness_evidence_bundle`: type `supervised_live_readiness_evidence_bundle`, rows 8, supporting artifacts 5, review `pending_operator_review`, fixture `pm_bot/tests/fixtures/readiness/pmbot_supervised_live_readiness_evidence_bundle.valid.json`
- `local_to_supervised_live_gap_matrix`: type `readiness_gap_matrix`, rows 9, supporting artifacts 0, review `pending_operator_review`, fixture `pm_bot/tests/fixtures/readiness/pmbot_local_to_supervised_live_gap_matrix.valid.json`

## Validation Status Records

- `compileall.pm_bot.tests`: status `not_run_static_record`, command `python -m compileall pm_bot tests`, reference `tests/test_codex_queue_pmbot_templates.py`
- `pytest.pm_bot_tests.queue_templates`: status `not_run_static_record`, command `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py`, reference `tests/test_codex_queue_pmbot_templates.py`

## Operator Review Steps

- Confirm each readiness artifact row points to an expected local sample or documentation reference.
- Confirm dashboard counts match the named static readiness artifacts.
- Confirm all rows remain pending operator review before any later status update.
- Confirm this dashboard remains descriptive readiness inventory only.

## Safety

- Local fixture/static input only.
- Makes no network, LLM provider, external service, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.
- Descriptive readiness dashboard only; no live transition, data refresh, transaction endpoint, or execution output.
- Not execution approval and not runtime input.
