# PMBOT Current LLM Batch Readiness Gate v1

- gate_version: current_llm_batch_readiness_gate.v1
- task_id: PMBOT-SOURCE-002-LOCAL-PACKET-COMPLETENESS-SCORER-INTEGRATION
- status: batch_readiness_gate_created
- generated_by: pm_bot/llm/packet_completeness_scorer.py
- inventory_source: pm_bot/llm/current_llm_market_packet_inventory.v1.json
- readiness_source: pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.json
- contract_source: pm_bot/llm/llm_market_packet_completeness_contract.v1.json

## Summary

- total_markets: 14
- high_count: 0
- medium_count: 10
- low_count: 4
- blocked_count: 0
- eligible_for_future_llm_review_count: 10
- eligible_for_future_openrouter_batch_count: 10
- needs_local_enrichment_count: 14
- needs_local_enrichment_before_future_openrouter_batch_count: 4
- reviewed_count: 10
- unreviewed_count: 4
- average_evidence_readiness_score: 75.43

## Gate Logic

- high: eligible_for_future_openrouter_batch_if_other_safety_constraints_pass
- medium: eligible_only_with_warning_or_manual_operator_approval
- low: needs_local_enrichment_before_future_openrouter_batch
- blocked: not_eligible

## Low Readiness Markets

- 597964
- 598936
- 691547
- 692258

## Unreviewed Markets

- 597964
- 598936
- 691547
- 692258

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

## Per-Market Readiness

- 563650: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 569332: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 569333: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 569334: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 569343: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 569344: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 569366: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 569368: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 569373: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 573656: band=medium; score=84; future_llm_review=true; future_openrouter_batch=true; needs_local_enrichment_before_future_batch=false
- 597964: band=low; score=54; future_llm_review=false; future_openrouter_batch=false; needs_local_enrichment_before_future_batch=true
- 598936: band=low; score=54; future_llm_review=false; future_openrouter_batch=false; needs_local_enrichment_before_future_batch=true
- 691547: band=low; score=54; future_llm_review=false; future_openrouter_batch=false; needs_local_enrichment_before_future_batch=true
- 692258: band=low; score=54; future_llm_review=false; future_openrouter_batch=false; needs_local_enrichment_before_future_batch=true

## Safety Flags

- local_only: true
- no_live_calls: true
- no_trading_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_dispatcher_authority: true
- no_wallet_or_order_authority: true
- operator_review_only: true
- passive_context_only: true
- acceptance_is_not_trading_approval: true
- no_market_action_guidance: true
- future_live_batch_scheduled: false
- future_openrouter_batch_approved: false
- future_llm_review_approved: false
- openrouter_calls_performed: 0
- polymarket_api_calls_performed: 0
- external_network_calls_performed: 0
