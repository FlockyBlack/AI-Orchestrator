# Selected Ingest Dossier Human Review Pack v1

## Summary

- task_id: PMBOT-INGEST-012-SELECTED-INGEST-DOSSIER-HUMAN-REVIEW-PACK
- source_validation_result_path: pm_bot/research/selected_ingest_manual_dossier_draft_validation_result.v1.json
- source_dossier_skeletons_path: pm_bot/research/selected_ingest_dossier_draft_skeletons.v1.json
- source_merged_packets_path: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json
- source_review_records_result_path: pm_bot/research/selected_ingest_operator_review_records_result.v1.json
- accepted_drafts_seen: 1
- human_review_packs_exported: 1
- draft_records_skipped: 6
- completed_dossiers_created: 0
- exported_market_ids:
  - 824952

## Selected Market IDs

- 692258
- 824952
- 691547
- 597964
- 598936

## Human Review Packs

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
- resolution_criteria_summary: Stub-only local market description excerpt for 'MicroStrategy sells any Bitcoin by December 31, 2026?': This market will resolve to "Yes" if MicroStrategy sells any of its Bitcoin by 11:59 PM ET on the date specified in the title. Otherwise, this market will resolve to "No". Manual completion must review the full local criteria before use.
- review_pack_status: human_review_pack_only

#### Review Notes

- market_context_notes: Manual context notes summarize the local packet and market question for human review.
- resolution_criteria_notes: Manual notes restate local resolution criteria boundaries for later human review.
- missing_information_review: No structural gaps were flagged by the selected-ingest operator review result.
- operator_review_notes: Operator review marked the packet ready for dossier drafting; this draft only records structural notes.

#### Evidence Summary By Source

- Local rule reference was copied into the packet for structural review.
- Official source placeholder was documented as source coverage context.
- Credible news placeholder was documented as source coverage context.

#### Uncertainty Register

- Manual review still needs human judgment on source completeness.
- Artifact validation does not determine the market outcome.

#### Open Questions

- none

#### Human Review Checklist

- evidence_matches_resolution_criteria
- uncertainty_register_reviewed
- missing_information_reviewed
- no_trading_recommendation_present
- no_probability_or_ev_present
- no_side_recommendation_present
- no_market_decision_present

#### Allowed Review Outcomes

- approved_for_final_dossier_draft
- needs_draft_revision
- rejected_for_research_quality
- watch_only

#### Prohibited Review Outputs

- bet recommendation
- trade recommendation
- YES/NO side selection
- probability estimate
- expected value calculation
- score/signal
- market decision
- order/paper order

#### Source Ingest Artifacts

- normalized_market_preview: pm_bot/ingest/normalized_market_preview.v1.json
- normalized_source_snapshot_artifact_id: polymarket_gamma_events_20260427T231234Z_c6373d103a2e
- normalized_source_snapshot_path: pm_bot/ingest/raw_snapshots/polymarket_gamma_events_20260427T231234Z_c6373d103a2e.json
- operator_candidate_selection_index: pm_bot/ingest/operator_candidate_selection_index.v1.json
- operator_candidate_selection_overlay: pm_bot/ingest/operator_candidate_selection_overlay_selected_first5.v1.json
