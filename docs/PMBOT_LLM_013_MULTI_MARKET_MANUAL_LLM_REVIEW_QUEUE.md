# PMBOT Manual LLM Review Queue v1

- task_id: PMBOT-LLM-013-MULTI-MARKET-MANUAL-LLM-REVIEW-QUEUE
- queue_items_total: 1
- generated_at: deterministic-manual-llm-review-queue.v1
- network_calls: 0
- llm_api_calls: 0
- browser_automation: false
- prompt_automation: false
- runtime_wiring: false

## Queue Status Counts

- ready_for_manual_prompt_export: 0
- waiting_for_operator_pasted_response: 0
- response_accepted_for_operator_review: 1
- response_rejected_needs_operator_fix: 0
- blocked_missing_packet: 0
- blocked_invalid_artifact: 0

## Queue Items

- market_id: 824952
  status: response_accepted_for_operator_review
  source_artifact_path: pm_bot/research/selected_ingest_final_dossier_drafts.v1.json
  packet_path: pm_bot/llm/real_local_market_llm_trial_packet.v1.json
  packet_present: true
  prompt_path: pm_bot/llm/real_local_market_llm_trial_prompt.v1.md
  prompt_present: true
  operator_response_path: pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json
  response_present: true
  validation_status: accepted
  quality_gate_status: quality_passed
  operator_surface_review_status: operator_surface_review_passed
  next_safe_operator_action: Review the accepted local response context in the offline operator surface only.

## Candidate Discovery

- selected_ingest_markets_seen: 5
- final_dossier_drafts_seen: 1
- additional_ready_candidates_found: 0
- candidate_policy: Only markets with an existing local LLM packet or accepted actual manual response artifact become queue items.

## Safety Boundary

- offline_manual_only: true
- not_truth_source: true
- not_trading_advice: true
- not_execution_authority: true

## Warnings

- no_additional_ready_candidates_found: No additional safe local packet candidates were found beyond existing queue items.

## Errors

- none
