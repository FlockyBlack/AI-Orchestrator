# PMBOT Dossier Draft Skeletons v1

## Summary

- task_id: PMBOT-RESEARCH-012-DOSSIER-DRAFT-SKELETON-EXPORT
- source_merged_packets_path: pm_bot/research/merged_manual_research_packets.v1.json
- source_operator_review_queue_path: pm_bot/research/operator_review_queue.v1.json
- source_review_records_result_path: pm_bot/research/operator_review_records_result.v1.json
- packets_read: 10
- accepted_review_records_seen: 3
- ready_review_records_seen: 1
- dossier_draft_skeletons_exported: 1
- packets_skipped: 9
- skipped_stub_only: 7
- skipped_needs_more_information: 1
- skipped_manual_evidence_added_without_accepted_ready_review: 0
- skipped_watch_only_manual: 1
- skipped_research_quality_rejected: 0
- skipped_invalid: 0
- exported_market_ids:
  - 563650

## Draft Skeletons

### 563650
- title/question: SCOTUS accepts sports event contract case by July 31, 2026?
- category: SCOTUS accepts sports event contract case by...?
- packet_type: legal_event
- current_yes_price: 0.135
- liquidity: 10158.1474
- deadline: 2026-07-31
- draft_status: dossier_draft_skeleton_only
- resolution_criteria_summary: Stub summary only: determine whether the legal/court event in 'SCOTUS accepts sports event contract case by July 31, 2026?' occurs by 2026-07-31; the full market rules and official docket criteria must be copied before completion.

#### Source Coverage Summary

- official_sources_checked_count: 2
- credible_news_sources_checked_count: 1
- evidence_inventory_count: 4
- official_sources_checked:
  - offline-check:563650:market-rules
  - offline-check:563650:official-docket
- credible_news_sources_checked:
  - offline-check:563650:credible-news

#### Evidence Inventory

- item 1
  - source_name: Manual market-rules placeholder
  - source_type: official_resolution_criteria
  - source_url_or_reference: offline-reference:563650:rules
  - captured_claim: Manual entry records a copied resolution-rule source for structural validation only.
  - relevance_to_resolution: Provides the rule text source category needed before operator review.
  - operator_notes: No outcome truth is inferred by this merge fixture.
- item 2
  - source_name: Manual docket placeholder
  - source_type: official_court_source
  - source_url_or_reference: offline-reference:563650:docket
  - captured_claim: Manual entry records an official-source claim for structural validation only.
  - relevance_to_resolution: Maps an official source claim to the market resolution path without evaluating it.
  - operator_notes: Operator must review the claim manually outside this merge tool.
- item 3
  - source_name: Manual credible-news placeholder
  - source_type: credible_news
  - source_url_or_reference: offline-reference:563650:news
  - captured_claim: Manual entry records a credible-news claim for structural validation only.
  - relevance_to_resolution: Adds independent coverage context without scoring the market.
  - operator_notes: Merge tool checks only that the entry is complete.
- item 4
  - source_name: Manual reliability note
  - source_type: operator_context
  - source_url_or_reference: offline-reference:563650:reliability
  - captured_claim: Manual entry records source reliability notes for structural validation only.
  - relevance_to_resolution: Confirms that source reliability was documented before operator review.
  - operator_notes: No recommendation is produced.

#### Missing Information Reviewed

- packet_missing_information:
  - none
- requested_followup_information:
  - none

#### Operator Review Notes

- Structural review completed. Future dossier drafting may start from this packet; no conclusion or order is recorded here.

#### Sections To Fill

- market_overview
- resolution_criteria
- source_coverage
- evidence_inventory
- missing_information_review
- operator_notes
- open_questions

#### Open Questions

- none

## Skipped Packets

### stub_only (7)

- 569332
- 569333
- 569334
- 569343
- 569344
- 569368
- 569373

### needs_more_information (1)

- 569366

### manual_evidence_added_without_accepted_ready_review (0)

- none

### watch_only_manual (1)

- 573656

### research_quality_rejected (0)

- none

### invalid (0)

- none
