# PMBOT LLM Market Packet Completeness Contract v1

- schema_version: llm_market_packet_completeness_contract.v1
- task_id: PMBOT-SOURCE-001-EVIDENCE-ENRICHMENT-DESIGN-FROM-INVENTORY
- status: completeness_contract_created
- contract_version: llm_market_packet_completeness_contract.v1

## Minimum For Batch Eligibility

- market_id
- market_title_or_question
- category
- local_packet_provenance
- operator_review_only_safety_contract
- local_context_for_missing_evidence_risk_and_checklist_sections
- no_runtime_trading_or_queue_authority

## Minimum For High Evidence Completeness

- full_market_resolution_criteria_text
- official_source_or_rule_reference_notes
- explicit_source_gap_notes
- contradiction_check_context
- risk_notes_context
- operator_checklist
- category_specific_key_fields

## Blocked Conditions

- missing_market_id
- missing_market_title_or_question
- missing_category
- missing_local_packet_provenance
- missing_operator_review_only_safety_contract
- packet_requires_live_fetch_to_be_understood
- runtime_trading_queue_wallet_or_dispatcher_authority_present
- market_action_guidance_present
- probability_ev_edge_confidence_or_side_selection_present

## Safety Constraints

- local packet readiness only
- no live external source fetching required or allowed
- no trading, wallet, order, queue, runtime, dispatcher, background, or browser authority
