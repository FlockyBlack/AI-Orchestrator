# PMBOT Packet Evidence Readiness Scores After Source Normalization v1

- schema_version: current_llm_packet_evidence_readiness_scores_after_source_normalization.v1
- task_id: PMBOT-SOURCE-003-RESOLUTION-SOURCE-FIELD-NORMALIZATION
- status: after_source_normalization_readiness_scores_created

## Aggregate

- previous_high_count: 0
- updated_high_count: 0
- previous_medium_count: 10
- updated_medium_count: 10
- previous_low_count: 4
- updated_low_count: 4
- previous_average_score: 75.43
- updated_average_score: 75.43
- score_delta_average: 0.0
- markets_improved: none
- markets_unchanged: 563650, 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 573656, 597964, 598936, 691547, 692258
- markets_worsened: none
- markets_with_source_fields_improved: 569332, 569333, 569334, 569343, 569344, 569366, 569368, 569373, 597964, 598936

## Per-Market Scores

- 563650: previous=84 updated=84 delta=0 band=medium source_fields_improved=none
- 569332: previous=84 updated=84 delta=0 band=medium source_fields_improved=candidate_or_party_if_applicable, jurisdiction
- 569333: previous=84 updated=84 delta=0 band=medium source_fields_improved=candidate_or_party_if_applicable, jurisdiction
- 569334: previous=84 updated=84 delta=0 band=medium source_fields_improved=candidate_or_party_if_applicable, jurisdiction
- 569343: previous=84 updated=84 delta=0 band=medium source_fields_improved=candidate_or_party_if_applicable, jurisdiction
- 569344: previous=84 updated=84 delta=0 band=medium source_fields_improved=candidate_or_party_if_applicable, jurisdiction
- 569366: previous=84 updated=84 delta=0 band=medium source_fields_improved=candidate_or_party_if_applicable, jurisdiction
- 569368: previous=84 updated=84 delta=0 band=medium source_fields_improved=candidate_or_party_if_applicable, jurisdiction
- 569373: previous=84 updated=84 delta=0 band=medium source_fields_improved=candidate_or_party_if_applicable, jurisdiction
- 573656: previous=84 updated=84 delta=0 band=medium source_fields_improved=none
- 597964: previous=54 updated=54 delta=0 band=low source_fields_improved=jurisdiction
- 598936: previous=54 updated=54 delta=0 band=low source_fields_improved=candidate_or_party_if_applicable, jurisdiction
- 691547: previous=54 updated=54 delta=0 band=low source_fields_improved=none
- 692258: previous=54 updated=54 delta=0 band=low source_fields_improved=none

## Remaining Top Missing Fields

- full_market_resolution_criteria_text: 14
- full_resolution_rules: 14
- non_placeholder_evidence_notes: 14
- official_source_references: 14
- official_source_urls_or_rule_references: 14
- reviewed_local_evidence_references: 14
- source_reliability_review: 14
- source_timestamps: 14
- office_or_election_event: 9
- official_election_authority_identifier: 9
- contradiction_checks: 4
- evidence_completeness_audit_status: 4
- operator_checklist: 4
- risk_notes: 4
- event_definition: 3
- entity: 2
- instrument_or_business_action_if_applicable: 2
- case_or_event_definition: 1
- court_or_legal_body: 1
- docket_identifier: 1
- asset_or_ticker: 1
- benchmark_and_timezone_rules: 1
- threshold: 1
- named_person_or_institution: 1
- office_or_public_role: 1

## Recommended Next Enrichment Focus

- full_market_resolution_criteria_text
- full_resolution_rules
- official_source_references
- official_source_urls_or_rule_references
- source_timestamps
- source_reliability_review

## Safety

- no_market_action_guidance: true
- no_probability_ev_edge_confidence_side_selection: true
- openrouter_calls_performed: 0
- polymarket_api_calls_performed: 0
- external_network_calls_performed: 0
