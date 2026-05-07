# PMBOT Operator OpenRouter Review Dashboard v1

- schema_version: operator_openrouter_review_dashboard.v1
- task_id: PMBOT-OPENROUTER-053-N5-SURFACE-WORKBENCH-INVENTORY-UX-AND-CONTOUR-AUDIT
- status: operator_openrouter_review_dashboard_created
- dashboard_mode: local_static_read_only
- latest_batch: N=5 / PMBOT-OPENROUTER-051
- latest_surface: PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION
- latest_baseline: PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY
- latest_workbench_integration_status: multi_batch_passive_surface_pointer_ready

## Batch Summaries

- N3 markets: 569333, 569334, 569343
- N3 cost: 0.125982
- N3 tokens: 18686
- N5 markets: 569344, 569366, 569368, 569373, 573656
- N5 cost: 0.199089
- N5 tokens: 29887

## Combined OpenRouter Review Contour

- total_markets_successfully_reviewed: 8
- total_openrouter_calls_in_successful_batches: 8
- combined_cost: 0.325071
- combined_tokens: 48573
- total_blocked_in_successful_batches: 0

## Normalization

- successful_batch_responses_requiring_fenced_normalization: 8/8
- clean_raw_json_responses: 0
- policy: fenced_json_normalization.v1

## Safety

- operator_review_only: true
- passive_context_only: true
- no_trading_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_wallet_or_order_authority: true

## Inventory Summary

- total_markets_found: 14
- total_reviewed_by_openrouter: 10
- unknown_category_count: 0
- markets_with_low_packet_completeness: 563650, 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 573656, 597964, 598936, 691547, 692258

## Category Counts

- company/business: 2
- crypto: 1
- elections: 9
- legal/courts: 1
- politics: 1

## Evidence Completeness

- medium: 10

## Operator Next Engineering Actions

- category/source inventory review
- source/evidence enrichment design
- repeat N=5 or protocol-only N=10 only after review
- model comparison and cost optimization later

## Artifact Pointers

- n3_surface_json: pm_bot/llm/operator_openrouter_batch_surface_046.v1.json
- n3_surface_md: pm_bot/llm/operator_openrouter_batch_surface_046.v1.md
- n5_surface_json: pm_bot/llm/operator_openrouter_batch_surface_051.v1.json
- n5_surface_md: pm_bot/llm/operator_openrouter_batch_surface_051.v1.md
- contour_audit_json: pm_bot/llm/openrouter_operator_review_contour_046_053_audit.v1.json
- contour_audit_md: pm_bot/llm/openrouter_operator_review_contour_046_053_audit.v1.md
- inventory_json: pm_bot/llm/current_llm_market_packet_inventory.v1.json
- inventory_md: pm_bot/llm/current_llm_market_packet_inventory.v1.md
- evidence_audit_json: pm_bot/llm/current_llm_source_evidence_completeness_audit.v1.json
- evidence_audit_md: pm_bot/llm/current_llm_source_evidence_completeness_audit.v1.md
- operator_review_pack_json: pm_bot/workbench/operator_review_pack.v1.json
- operator_review_pack_md: pm_bot/workbench/operator_review_pack.v1.md
- workbench_export_run_json: pm_bot/workbench/operator_workbench_export_run.v1.json
- workbench_export_run_md: pm_bot/workbench/operator_workbench_export_run.v1.md
- runbook: docs/PMBOT_OPENROUTER_OPERATOR_REVIEW_RUNBOOK.md
- decision_matrix_json: pm_bot/llm/openrouter_next_step_decision_matrix.v1.json
- decision_matrix_md: docs/PMBOT_OPENROUTER_NEXT_STEP_DECISION_MATRIX.md
