# Selected Ingest Dossier Draft Skeletons v1

## Summary

- task_id: PMBOT-INGEST-010-SELECTED-INGEST-DOSSIER-DRAFT-SKELETON-EXPORT
- source_merged_packets_path: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json
- source_operator_review_queue_path: pm_bot/research/selected_ingest_operator_review_queue.v1.json
- source_review_records_result_path: pm_bot/research/selected_ingest_operator_review_records_result.v1.json
- ready_review_records_seen: 1
- dossier_draft_skeletons_exported: 1
- records_skipped: 5
- completed_dossiers_created: 0
- skipped_needs_more_information: 1
- skipped_watch_only_manual: 1
- skipped_research_quality_rejected: 0
- skipped_stub_only: 0
- skipped_invalid: 0
- skipped_rejected_record: 3
- exported_market_ids:
  - 824952

## Selected Market IDs

- 692258
- 824952
- 691547
- 597964
- 598936

## Draft Skeletons

### 824952
- title/question: MicroStrategy sells any Bitcoin by December 31, 2026?
- event_id: 16167
- event_title: MicroStrategy sells any Bitcoin by ___ ?
- category: Finance / Economy / Business / 2025 Predictions / Crypto / MicroStrategy / Stocks
- packet_type: selected_ingest_market_research_stub
- current_yes_price: 0.095
- liquidity: 33862.5213
- volume: 574606.4678400013
- deadline: 2026-07-01T04:00:00Z
- draft_status: dossier_draft_skeleton_only
- resolution_criteria_summary: Stub-only local market description excerpt for 'MicroStrategy sells any Bitcoin by December 31, 2026?': This market will resolve to "Yes" if MicroStrategy sells any of its Bitcoin by 11:59 PM ET on the date specified in the title. Otherwise, this market will resolve to "No". Manual completion must review the full local criteria before use.

#### Source Coverage Summary

- official_sources_checked_count: 2
- credible_news_sources_checked_count: 1
- evidence_inventory_count: 4
- official_sources_checked:
  - offline-check:824952:local-market-rules
  - offline-check:824952:official-source-placeholder
- credible_news_sources_checked:
  - offline-check:824952:credible-news-placeholder

#### Evidence Inventory

- item 1
  - source_name: Manual selected-ingest rule placeholder
  - source_type: official_resolution_criteria
  - source_url_or_reference: offline-reference:824952:rules
  - captured_claim: Manual entry records a copied resolution-rule source for structural validation only.
  - relevance_to_resolution: Provides the rule source category needed before operator review.
  - operator_notes: No outcome truth is inferred by this merge fixture.
- item 2
  - source_name: Manual official-source placeholder
  - source_type: official_company_source
  - source_url_or_reference: offline-reference:824952:official-source
  - captured_claim: Manual entry records an operator-copied official source claim for structural validation only.
  - relevance_to_resolution: Maps a manual source claim to the market resolution path without evaluating it.
  - operator_notes: Operator must review the claim manually outside this merge tool.
- item 3
  - source_name: Manual credible-news placeholder
  - source_type: credible_news
  - source_url_or_reference: offline-reference:824952:news
  - captured_claim: Manual entry records a credible-news claim for structural validation only.
  - relevance_to_resolution: Adds independent coverage context without scoring the market.
  - operator_notes: Merge tool checks only that the entry is complete.
- item 4
  - source_name: Manual reliability note
  - source_type: operator_context
  - source_url_or_reference: offline-reference:824952:reliability
  - captured_claim: Manual entry records source reliability notes for structural validation only.
  - relevance_to_resolution: Confirms that source reliability was documented before operator review.
  - operator_notes: No recommendation is produced.

#### Missing Information Reviewed

- packet_missing_information:
  - none
- requested_followup_information:
  - none

#### Operator Review Notes

- Structural review completed. A future draft skeleton may be prepared from this packet only; no conclusion or action is recorded here.

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

#### Source Ingest Artifacts

- normalized_market_preview: pm_bot/ingest/normalized_market_preview.v1.json
- normalized_source_snapshot_artifact_id: polymarket_gamma_events_20260427T231234Z_c6373d103a2e
- normalized_source_snapshot_path: pm_bot/ingest/raw_snapshots/polymarket_gamma_events_20260427T231234Z_c6373d103a2e.json
- operator_candidate_selection_index: pm_bot/ingest/operator_candidate_selection_index.v1.json
- operator_candidate_selection_overlay: pm_bot/ingest/operator_candidate_selection_overlay_selected_first5.v1.json

## Skipped Records

### needs_more_information (1)

- 692258

### watch_only_manual (1)

- 598936

### research_quality_rejected (0)

- none

### stub_only (0)

- none

### invalid (0)

- none

### rejected_record (3)

- 691547
- 597964
- unknown-market-id
