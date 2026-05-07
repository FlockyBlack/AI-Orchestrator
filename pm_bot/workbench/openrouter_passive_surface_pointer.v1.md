# PMBOT OpenRouter Passive Surface Pointer v1

- schema_version: openrouter_passive_surface_pointer.v1
- task_id: PMBOT-OPENROUTER-049-WORKBENCH-PASSIVE-SURFACE-INTEGRATION
- generated_by: pm_bot/workbench/openrouter_passive_surface_pointer.py
- status: passive_surface_pointer_ready
- workbench_integration_mode: read_only_passive_context
- source_batch_task: PMBOT-OPENROUTER-046
- source_baseline_task: PMBOT-OPENROUTER-047
- source_surface_task: PMBOT-OPENROUTER-048
- source_048_status: completed_pushed
- surfaced_market_ids: 569333, 569334, 569343
- model: anthropic/claude-sonnet-4.5
- total_calls: 3

## Aggregate Usage

- prompt_tokens: 12859
- completion_tokens: 5827
- total_tokens: 18686

## Aggregate Cost

- total_cost: 0.125982
- average_cost_per_market: 0.041994

## Normalization Summary

- fenced_response_count: 3
- normalized_response_count: 3
- clean_raw_json_response_count: 0
- policy: fenced_json_normalization.v1
- raw_response_preserved: true
- semantic_repair_allowed: false

## Quality Summary

- accepted_for_operator_review_count: 3
- blocked_count: 0
- schema_validation_accepted_count: 3
- acceptance_gate_passed_count: 3
- all_required_artifacts_present: true
- all_json_artifacts_parse: true
- baseline_suitable_for_future_controlled_expansion: true

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
- source_surface_json: pm_bot/llm/operator_openrouter_batch_surface_046.v1.json (read_only_passive_source)
- source_surface_markdown: pm_bot/llm/operator_openrouter_batch_surface_046.v1.md (read_only_passive_source)
- source_048_result: docs/PMBOT_OPENROUTER_048_RESULT.json (read_only_source_result)
- source_048_report: docs/PMBOT_OPENROUTER_048_PASSIVE_OPERATOR_SURFACE_046_BATCH.md (read_only_source_report)

## Source Artifact Pointers

- source_046_result: docs/PMBOT_OPENROUTER_046_RESULT.json (read_only_source_summary)
- source_046_report: docs/PMBOT_OPENROUTER_046_RETRY_SMALL_MANUAL_BATCH_AFTER_ACCEPTANCE_PHRASE_HARDENING.md (read_only_source_summary)
- source_047_result: docs/PMBOT_OPENROUTER_047_RESULT.json (read_only_source_summary)
- source_047_report: docs/PMBOT_OPENROUTER_047_SMALL_BATCH_BASELINE_QUALITY_AND_OPERATOR_SUMMARY.md (read_only_source_summary)
- source_047_baseline_json: pm_bot/llm/openrouter_046_small_batch_quality_baseline.v1.json (read_only_source_summary)
- source_047_baseline_markdown: pm_bot/llm/openrouter_046_small_batch_quality_baseline.v1.md (read_only_source_summary)
- source_047_operator_summary: pm_bot/llm/openrouter_046_small_batch_operator_summary.v1.md (read_only_source_summary)
- source_046_batch_summary: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_046_retry_small_manual_batch_after_acceptance_phrase_hardening/openrouter_batch_summary.v1.json (read_only_source_summary)
- source_046_batch_cost_report_json: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_046_retry_small_manual_batch_after_acceptance_phrase_hardening/openrouter_batch_cost_report.v1.json (read_only_source_summary)
- source_046_batch_cost_report_markdown: pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_046_retry_small_manual_batch_after_acceptance_phrase_hardening/openrouter_batch_cost_report.v1.md (read_only_source_summary)

## Known Warnings

- all_3_source_responses_required_fenced_json_normalization
- no_clean_raw_json_responses_observed_in_046

## Future Readiness Note

- options_documented_only: true
- option_a: PMBOT-OPENROUTER-050-CONTROLLED-N5-BATCH-READINESS-PROTOCOL - Protocol-only readiness for a future 5-market controlled batch, no live calls.
- option_b: PMBOT-OPENROUTER-050-OPERATOR-WORKBENCH-OPENROUTER-UX-REFINEMENT - Improve local presentation of passive OpenRouter review data in workbench artifacts, no live calls.
