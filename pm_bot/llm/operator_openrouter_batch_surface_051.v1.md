# PMBOT OpenRouter N5 Passive Operator Surface v1

- surface_version: operator_openrouter_batch_surface.v1
- task_id: PMBOT-OPENROUTER-053-N5-SURFACE-WORKBENCH-INVENTORY-UX-AND-CONTOUR-AUDIT
- source_protocol_task: PMBOT-OPENROUTER-050-CONTROLLED-N5-BATCH-READINESS-PROTOCOL
- source_batch_task: PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL
- source_baseline_task: PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY
- status: passive_operator_surface_created
- model: anthropic/claude-sonnet-4.5
- surfaced_market_ids: 569344, 569366, 569368, 569373, 573656
- accepted_for_operator_review_count: 5
- blocked_count: 0
- source_openrouter_calls: 5

## Usage And Cost

- prompt_tokens: 20768
- completion_tokens: 9119
- total_tokens: 29887
- average_tokens_per_market: 5977.4
- total_cost: 0.199089
- average_cost_per_market: 0.0398178
- max_total_cost_allowed: 0.35
- cost_cap_exceeded: false

## Normalization

- policy: fenced_json_normalization.v1
- fenced_response_count: 5
- normalized_response_count: 5
- clean_raw_json_response_count: 0
- raw_response_preserved: true
- semantic_repair_allowed: false

## Safety

- operator_review_only: true
- passive_context_only: true
- analysis_only: true
- manual_review_only: true
- no_trading_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_dispatcher_authority: true
- no_wallet_or_order_authority: true
- acceptance_is_not_trading_approval: true
- no_market_action_guidance: true

## Per-Market Passive Entries

- market_id: 569344
  accepted_for_operator_review: true
  total_tokens: 6203
  cost: 0.041745
  normalized: true
  note: Required operator-review fields are populated, validation accepted the normalized JSON, and the content includes explicit evidence-gap/source-gap, contradiction-check, risk-note, and checklist sections. Counts: source_gap=10, missing_evidence=11, contradiction_checks=4, risk_notes=8, operator_checklist=13. Passive context only.
- market_id: 569366
  accepted_for_operator_review: true
  total_tokens: 5944
  cost: 0.037236
  normalized: true
  note: Required operator-review fields are populated, validation accepted the normalized JSON, and the content includes explicit evidence-gap/source-gap, contradiction-check, risk-note, and checklist sections. Counts: source_gap=9, missing_evidence=10, contradiction_checks=3, risk_notes=6, operator_checklist=10. Passive context only.
- market_id: 569368
  accepted_for_operator_review: true
  total_tokens: 5965
  cost: 0.040647
  normalized: true
  note: Required operator-review fields are populated, validation accepted the normalized JSON, and the content includes explicit evidence-gap/source-gap, contradiction-check, risk-note, and checklist sections. Counts: source_gap=12, missing_evidence=12, contradiction_checks=3, risk_notes=10, operator_checklist=13. Passive context only.
- market_id: 569373
  accepted_for_operator_review: true
  total_tokens: 6079
  cost: 0.042765
  normalized: true
  note: Required operator-review fields are populated, validation accepted the normalized JSON, and the content includes explicit evidence-gap/source-gap, contradiction-check, risk-note, and checklist sections. Counts: source_gap=12, missing_evidence=13, contradiction_checks=4, risk_notes=10, operator_checklist=15. Passive context only.
- market_id: 573656
  accepted_for_operator_review: true
  total_tokens: 5696
  cost: 0.036696
  normalized: true
  note: Required operator-review fields are populated, validation accepted the normalized JSON, and the content includes explicit evidence-gap/source-gap, contradiction-check, risk-note, and checklist sections. Counts: source_gap=10, missing_evidence=10, contradiction_checks=3, risk_notes=7, operator_checklist=12. Passive context only.

## Artifact Pointers

- source_050_result: docs/PMBOT_OPENROUTER_050_RESULT.json (read_only_input)
- source_051_result: docs/PMBOT_OPENROUTER_051_RESULT.json (read_only_input)
- source_052_result: docs/PMBOT_OPENROUTER_052_RESULT.json (read_only_input)
- source_052_baseline_json: pm_bot/llm/openrouter_051_n5_batch_quality_baseline.v1.json (read_only_input)
- source_052_baseline_markdown: pm_bot/llm/openrouter_051_n5_batch_quality_baseline.v1.md (read_only_input)
- source_052_operator_summary: pm_bot/llm/openrouter_051_n5_batch_operator_summary.v1.md (read_only_input)
- surface_json: pm_bot/llm/operator_openrouter_batch_surface_051.v1.json (generated_passive_surface)
- surface_markdown: pm_bot/llm/operator_openrouter_batch_surface_051.v1.md (generated_passive_surface)

## Warnings

- all five responses required fenced JSON normalization
- no clean raw JSON responses observed
