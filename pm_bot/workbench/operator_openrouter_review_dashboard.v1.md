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
- no_dispatcher_authority: true
- no_wallet_or_order_authority: true
- acceptance_is_not_trading_approval: true
- no_market_action_guidance: true

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

## Evidence Readiness

- integration_status: source_001_context_ready
- high_count: 0
- medium_count: 10
- low_count: 4
- blocked_count: 0
- average_evidence_readiness_score: 75.43
- reviewed_market_ids: 563650, 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 573656
- unreviewed_market_ids: 597964, 598936, 691547, 692258
- markets_with_medium_evidence_completeness: 563650, 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 573656

## Category Gap Summary

- company/business: priority=high, effort=medium, markets=691547, 692258
- crypto: priority=high, effort=small, markets=573656
- elections: priority=high, effort=large, markets=569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 598936
- legal/courts: priority=high, effort=small, markets=563650
- politics: priority=high, effort=small, markets=597964

## Batch Readiness Gate

- integration_status: source_002_gate_ready
- artifact_pointer: pm_bot/llm/current_llm_batch_readiness_gate.v1.json
- artifact_markdown_pointer: pm_bot/llm/current_llm_batch_readiness_gate.v1.md
- total_markets: 14
- high_count: 0
- medium_count: 10
- low_count: 4
- blocked_count: 0
- eligible_for_future_llm_review_count: 10
- eligible_for_future_openrouter_batch_count: 10
- needs_local_enrichment_count: 14
- needs_local_enrichment_before_future_openrouter_batch_count: 4
- low_readiness_market_ids: 597964, 598936, 691547, 692258
- unreviewed_market_ids: 597964, 598936, 691547, 692258
- future_live_batch_scheduled: false
- future_openrouter_batch_approved: false
- no_market_action_guidance: true

## Top Missing Fields

- full_market_resolution_criteria_text: 14
- full_resolution_rules: 14
- non_placeholder_evidence_notes: 14
- official_source_references: 14
- official_source_urls_or_rule_references: 14
- reviewed_local_evidence_references: 14
- source_reliability_review: 14
- source_timestamps: 14
- jurisdiction: 10
- candidate_or_party_if_applicable: 9

## Recommended Next Local Enrichment Focus

- resolution source extraction
- source gap normalization
- operator checklist standardization for unreviewed packets
- contradiction and risk context builder for unreviewed packets
- packet completeness readiness gate review before future LLM batches

## Resolution Source Normalization

- integration_status: source_003_context_ready
- artifact_pointer: pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json
- artifact_markdown_pointer: pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.md
- total_markets_audited: 14
- markets_missing_resolution_criteria_text: 14
- markets_missing_full_resolution_rules: 14
- markets_missing_official_source_references: 14
- markets_needing_manual_resolution_source_review: 14

## Readiness After Source Normalization

- artifact_pointer: pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json
- artifact_markdown_pointer: pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.md
- previous_average_score: 75.43
- updated_average_score: 75.43
- score_delta_average: 0.0
- markets_improved: none
- remaining_top_missing_fields: full_market_resolution_criteria_text, full_resolution_rules, non_placeholder_evidence_notes, official_source_references, official_source_urls_or_rule_references, reviewed_local_evidence_references

## Batch Gate After Source Normalization

- artifact_pointer: pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.json
- artifact_markdown_pointer: pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.md
- total_markets: 14
- high_count: 0
- medium_count: 10
- low_count: 4
- blocked_count: 0
- eligible_for_future_openrouter_batch_count: 10
- markets_still_missing_resolution_sources: 563650, 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 573656, 597964, 598936, 691547, 692258
- manual_review_needed_markets: 563650, 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 573656, 597964, 598936, 691547, 692258
- future_openrouter_batch_approved: false
- no_market_action_guidance: true

## Local Source Enrichment Action Plan

- artifact_pointer: pm_bot/llm/local_source_enrichment_action_plan.v1.json
- artifact_markdown_pointer: pm_bot/llm/local_source_enrichment_action_plan.v1.md
- high_priority_local_actions: 4
- high_priority_local_action_market_ids: 597964, 598936, 691547, 692258
- fields_to_fix_first: full_market_resolution_criteria_text, full_resolution_rules, official_source_references, official_source_urls_or_rule_references, source_timestamps, source_reliability_review
- passive_only: true
- queue_items_created: 0
- queue_state_mutated: false

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
- batch_readiness_gate_json: pm_bot/llm/current_llm_batch_readiness_gate.v1.json
- batch_readiness_gate_md: pm_bot/llm/current_llm_batch_readiness_gate.v1.md
- resolution_source_audit_json: pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json
- resolution_source_audit_md: pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.md
- readiness_after_source_normalization_json: pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json
- readiness_after_source_normalization_md: pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.md
- batch_gate_after_source_normalization_json: pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.json
- batch_gate_after_source_normalization_md: pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.md
- local_source_enrichment_action_plan_json: pm_bot/llm/local_source_enrichment_action_plan.v1.json
- local_source_enrichment_action_plan_md: pm_bot/llm/local_source_enrichment_action_plan.v1.md
- operator_review_pack_json: pm_bot/workbench/operator_review_pack.v1.json
- operator_review_pack_md: pm_bot/workbench/operator_review_pack.v1.md
- workbench_export_run_json: pm_bot/workbench/operator_workbench_export_run.v1.json
- workbench_export_run_md: pm_bot/workbench/operator_workbench_export_run.v1.md
- runbook: docs/PMBOT_OPENROUTER_OPERATOR_REVIEW_RUNBOOK.md
- decision_matrix_json: pm_bot/llm/openrouter_next_step_decision_matrix.v1.json
- decision_matrix_md: docs/PMBOT_OPENROUTER_NEXT_STEP_DECISION_MATRIX.md
- requirements_json: pm_bot/llm/source_evidence_enrichment_requirements.v1.json
- requirements_md: pm_bot/llm/source_evidence_enrichment_requirements.v1.md
- readiness_scores_json: pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.json
- readiness_scores_md: pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.md
- gap_plan_json: pm_bot/llm/source_evidence_gap_plan_by_category.v1.json
- gap_plan_md: pm_bot/llm/source_evidence_gap_plan_by_category.v1.md
- completeness_contract_json: pm_bot/llm/llm_market_packet_completeness_contract.v1.json
- completeness_contract_md: pm_bot/llm/llm_market_packet_completeness_contract.v1.md
- enrichment_design_json: pm_bot/llm/source_evidence_enrichment_design.v1.json
- enrichment_design_md: docs/PMBOT_SOURCE_EVIDENCE_ENRICHMENT_DESIGN.md
- after_source_normalization_readiness_scores_json: pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json
- after_source_normalization_readiness_scores_md: pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.md
- batch_readiness_gate_after_source_normalization_json: pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.json
- batch_readiness_gate_after_source_normalization_md: pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.md
