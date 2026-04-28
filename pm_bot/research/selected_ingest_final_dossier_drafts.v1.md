# PMBOT Selected-Ingest Final Dossier Drafts v1

## Summary

- task_id: PMBOT-INGEST-014-SELECTED-INGEST-FINAL-DOSSIER-DRAFT-EXPORT
- source_review_pack_path: pm_bot/research/selected_ingest_dossier_human_review_pack.v1.json
- source_review_records_result_path: pm_bot/research/selected_ingest_dossier_human_review_records_result.v1.json
- source_validation_result_path: pm_bot/research/selected_ingest_manual_dossier_draft_validation_result.v1.json
- source_dossier_skeletons_path: pm_bot/research/selected_ingest_dossier_draft_skeletons.v1.json
- source_merged_packets_path: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json
- selected_market_ids:
  - 692258
  - 824952
  - 691547
  - 597964
  - 598936
- approved_review_records_seen: 1
- final_dossier_drafts_exported: 1
- review_records_skipped: 9
- completed_dossiers_created: 0
- exported_market_ids:
  - 824952

## Final Dossier Drafts

### 824952
- title/question: MicroStrategy sells any Bitcoin by December 31, 2026?
- event_id: 16167
- event_title: MicroStrategy sells any Bitcoin by ___ ?
- category: Finance / Economy / Business / 2025 Predictions / Crypto / MicroStrategy / Stocks
- packet_type: selected_ingest_market_research_stub
- deadline: 2026-07-01T04:00:00Z
- current_yes_price: 0.095
- liquidity: 33862.5213
- volume: 574606.4678400013
- final_draft_status: final_dossier_draft_only

#### Market Overview

- market_context_notes: Manual context notes summarize the local packet and market question for human review.

#### Resolution Rules

- resolution_criteria_summary: Stub-only local market description excerpt for 'MicroStrategy sells any Bitcoin by December 31, 2026?': This market will resolve to "Yes" if MicroStrategy sells any of its Bitcoin by 11:59 PM ET on the date specified in the title. Otherwise, this market will resolve to "No". Manual completion must review the full local criteria before use.
- resolution_criteria_notes: Manual notes restate local resolution criteria boundaries for later human review.

#### Evidence Inventory

- Local rule reference was copied into the packet for structural review.
- Official source placeholder was documented as source coverage context.
- Credible news placeholder was documented as source coverage context.

#### Uncertainty Notes

- Manual review still needs human judgment on source completeness.
- Artifact validation does not determine the market outcome.

#### Source Coverage Notes

- official_sources_to_check:
  - Manual check template: local Polymarket rules and resolution criteria for market_id 824952
  - Manual check template: official primary source named in the local market description for 'MicroStrategy sells any Bitcoin by December 31, 2026?'
  - Manual check template: original issuer, government, court, exchange, or company source relevant to 'MicroStrategy sells any Bitcoin by December 31, 2026?'
- credible_news_sources_to_check:
  - Manual check template: Reuters coverage query for 'MicroStrategy sells any Bitcoin by December 31, 2026?'
  - Manual check template: Associated Press coverage query for 'MicroStrategy sells any Bitcoin by December 31, 2026?'
  - Manual check template: major credible outlet query for 'Finance / Economy / Business / 2025 Predictions / Crypto / MicroStrategy / Stocks' and 'MicroStrategy sells any Bitcoin by December 31, 2026?'
- official_sources_checked:
  - offline-check:824952:local-market-rules
  - offline-check:824952:official-source-placeholder
- credible_news_sources_checked:
  - offline-check:824952:credible-news-placeholder
- official_sources_checked_count: 2
- credible_news_sources_checked_count: 1
- evidence_inventory_count: 4

#### Unresolved Questions

- missing_information_review: No structural gaps were flagged by the selected-ingest operator review result.
- none

#### Human Review Summary

- human_review_notes: Reviewer verified selected-ingest human review pack checklist coverage and approved a later draft-preparation step.

#### Source Ingest Artifacts

- normalized_market_preview: pm_bot/ingest/normalized_market_preview.v1.json
- normalized_source_snapshot_artifact_id: polymarket_gamma_events_20260427T231234Z_c6373d103a2e
- normalized_source_snapshot_path: pm_bot/ingest/raw_snapshots/polymarket_gamma_events_20260427T231234Z_c6373d103a2e.json
- operator_candidate_selection_index: pm_bot/ingest/operator_candidate_selection_index.v1.json
- operator_candidate_selection_overlay: pm_bot/ingest/operator_candidate_selection_overlay_selected_first5.v1.json
