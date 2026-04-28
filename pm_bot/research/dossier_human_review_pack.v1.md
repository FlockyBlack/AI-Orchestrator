# PMBOT Dossier Human Review Pack v1

## Summary

- task_id: PMBOT-RESEARCH-014-DOSSIER-HUMAN-REVIEW-PACK-EXPORT
- source_validation_result_path: pm_bot/research/manual_dossier_draft_validation_result.v1.json
- source_dossier_skeletons_path: pm_bot/research/dossier_draft_skeletons.v1.json
- source_merged_packets_path: pm_bot/research/merged_manual_research_packets.v1.json
- source_review_records_result_path: pm_bot/research/operator_review_records_result.v1.json
- accepted_drafts_seen: 1
- human_review_packs_exported: 1
- draft_records_skipped: 7
- completed_dossiers_created: 0
- exported_market_ids:
  - 563650

## Human Review Packs

### 563650
- title/question: SCOTUS accepts sports event contract case by July 31, 2026?
- category: SCOTUS accepts sports event contract case by...?
- packet_type: legal_event
- deadline: 2026-07-31
- current_yes_price: 0.135
- liquidity: 10158.1474
- resolution_criteria_summary: Stub summary only: determine whether the legal/court event in 'SCOTUS accepts sports event contract case by July 31, 2026?' occurs by 2026-07-31; the full market rules and official docket criteria must be copied before completion.
- review_pack_status: human_review_pack_only

#### Review Notes

- market_context_notes: Manual context note records the market subject and timing for human review only.
- resolution_criteria_notes: Resolution criteria note records the source categories and unresolved manual review points.
- missing_information_review: No missing-information item is closed by this gate; human review remains required.
- operator_review_notes: Manual draft sections are populated for structural quality review only.

#### Evidence Summary By Source

- offline-reference:563650:rules - records the rule source category used for structural review.
- offline-reference:563650:docket - records a court-source claim without resolving the outcome.
- offline-reference:563650:news - records external context for later human review.

#### Uncertainty Register

- Court docket terminology may require manual interpretation.
- Source timing should be reviewed by a human before any later workflow.

#### Open Questions

- Confirm the exact docket identifier before any later human decision.

#### Human Review Checklist

- evidence_matches_resolution_criteria
- uncertainty_register_reviewed
- missing_information_reviewed
- no_trading_recommendation_present
- no_probability_or_ev_present
- no_side_recommendation_present

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
- order/paper order
