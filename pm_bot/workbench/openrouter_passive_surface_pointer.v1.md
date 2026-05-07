# PMBOT OpenRouter Passive Surface Pointer v1

- schema_version: openrouter_passive_surface_pointer.v1
- task_id: PMBOT-OPENROUTER-053-WORKBENCH-PASSIVE-SURFACE-MULTI-BATCH-INTEGRATION
- generated_by: pm_bot/workbench/openrouter_passive_surface_pointer.py
- status: passive_surface_pointer_ready
- workbench_integration_mode: read_only_passive_context_multi_batch
- latest_surface_source_batch_task: PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL
- latest_surface_task: PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION

## Surface History

- N=3
  source_batch_task: PMBOT-OPENROUTER-046
  source_baseline_task: PMBOT-OPENROUTER-047
  source_surface_task: PMBOT-OPENROUTER-048-PASSIVE-OPERATOR-SURFACE-046-BATCH
  surfaced_market_ids: 569333, 569334, 569343
  calls: 3
  total_tokens: 18686
  total_cost: 0.125982
  accepted_for_operator_review_count: 3
  blocked_count: 0
- N=5
  source_batch_task: PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL
  source_baseline_task: PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY
  source_surface_task: PMBOT-OPENROUTER-053-PASSIVE-OPERATOR-SURFACE-AND-WORKBENCH-N5-INTEGRATION
  surfaced_market_ids: 569344, 569366, 569368, 569373, 573656
  calls: 5
  total_tokens: 29887
  total_cost: 0.199089
  accepted_for_operator_review_count: 5
  blocked_count: 0

## Combined Summary

- total_markets_successfully_reviewed: 8
- total_openrouter_calls_in_successful_batches: 8
- combined_cost: 0.325071
- combined_tokens: 48573
- total_blocked_in_successful_batches: 0

## Normalization Warnings

- all successful batch responses required fenced JSON normalization
- no clean raw JSON responses observed

## Safety No-Authority Flags

- operator_review_only: true
- passive_context_only: true
- no_trading_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_dispatcher_authority: true
- no_wallet_or_order_authority: true
- acceptance_is_not_trading_approval: true
- analysis_only: true
- manual_review_only: true
- raw_model_responses_included: false
- per_market_response_text_included: false
- network_calls: 0
- orders_created: 0

## Artifact Pointers

- workbench_pointer_json: pm_bot/workbench/openrouter_passive_surface_pointer.v1.json (generated_workbench_pointer)
- workbench_pointer_markdown: pm_bot/workbench/openrouter_passive_surface_pointer.v1.md (generated_workbench_pointer)
- operator_openrouter_review_dashboard_json: pm_bot/workbench/operator_openrouter_review_dashboard.v1.json (generated_static_dashboard)
- operator_openrouter_review_dashboard_markdown: pm_bot/workbench/operator_openrouter_review_dashboard.v1.md (generated_static_dashboard)
- n3_surface_json: pm_bot/llm/operator_openrouter_batch_surface_046.v1.json (read_only_passive_source)
- n3_surface_markdown: pm_bot/llm/operator_openrouter_batch_surface_046.v1.md (read_only_passive_source)
- n5_surface_json: pm_bot/llm/operator_openrouter_batch_surface_051.v1.json (read_only_passive_source)
- n5_surface_markdown: pm_bot/llm/operator_openrouter_batch_surface_051.v1.md (read_only_passive_source)
- source_048_result: docs/PMBOT_OPENROUTER_048_RESULT.json (read_only_source_result)
- source_052_result: docs/PMBOT_OPENROUTER_052_RESULT.json (read_only_source_result)
