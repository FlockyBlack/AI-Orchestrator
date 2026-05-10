# PMBOT Real Market Batch 004 Operator Console

- Generated at: `2026-05-10T00:00:00Z`
- Selected real/local markets: 5
- Active paper hypotheses: 5
- Unresolved outcomes: 5
- Sources used: 34
- Missing evidence items: 34

## Selected Real/Local Markets

- `563650` SCOTUS accepts sports event contract case by July 31, 2026?
  Analysis: `analysis_result_loaded`
  Paper hypothesis: `563650.analysis.adc53630aa1f.paper_hypothesis`
  Outcome: `unresolved`
  Sources used: 3
  Missing evidence: 7
- `597964` Macron out by June 30, 2026?
  Analysis: `analysis_result_loaded`
  Paper hypothesis: `597964.analysis.33643849e5db.paper_hypothesis`
  Outcome: `unresolved`
  Sources used: 7
  Missing evidence: 7
- `598936` Will the next UK election be called by June 30, 2026?
  Analysis: `analysis_result_loaded`
  Paper hypothesis: `598936.analysis.dceea0f50063.paper_hypothesis`
  Outcome: `unresolved`
  Sources used: 7
  Missing evidence: 7
- `691547` Kraken IPO by December 31, 2026?
  Analysis: `analysis_result_loaded`
  Paper hypothesis: `691547.analysis.56b3a68b9b94.paper_hypothesis`
  Outcome: `unresolved`
  Sources used: 7
  Missing evidence: 7
- `692258` MicroStrategy sells any Bitcoin by June 30, 2026?
  Analysis: `analysis_result_loaded`
  Paper hypothesis: `692258.analysis.bed289c1494d.paper_hypothesis`
  Outcome: `unresolved`
  Sources used: 10
  Missing evidence: 6

## Missing Evidence

- `563650` SCOTUS accepts sports event contract case by July 31, 2026?
  - No missing-information item is closed by this gate; human review remains required.
  - Confirm the exact docket identifier before any later human decision.
  - Court docket terminology may require manual interpretation.
  - Source timing should be reviewed by a human before any later workflow.
  - Manual draft sections are populated for structural quality review only.
  - Reviewer verified checklist coverage for the review pack and approved a later draft-preparation step.
  - Referenced source artifact path is not present locally: pm_bot/research/final_dossier_drafts.v1.json
- `597964` Macron out by June 30, 2026?
  - manual_research_not_started
  - full_market_resolution_criteria_review
  - official_source_references
  - credible_news_source_references
  - empty_evidence_slots
  - operator_human_review_required
  - Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json
- `598936` Will the next UK election be called by June 30, 2026?
  - manual_research_not_started
  - full_market_resolution_criteria_review
  - official_source_references
  - credible_news_source_references
  - empty_evidence_slots
  - operator_human_review_required
  - Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json
- `691547` Kraken IPO by December 31, 2026?
  - manual_research_not_started
  - full_market_resolution_criteria_review
  - official_source_references
  - credible_news_source_references
  - empty_evidence_slots
  - operator_human_review_required
  - Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json
- `692258` MicroStrategy sells any Bitcoin by June 30, 2026?
  - full_official_source_reference
  - credible_news_source_references
  - official_yes_or_no_evidence
  - source_reliability_review
  - Valid partial selected-ingest overlay used to prove deterministic merge behavior.
  - Referenced source artifact path is not present locally: pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json

## Sources Used

- `563650`
  - local_evidence_summary_001 - local_evidence_summary (unknown)
  - local_evidence_summary_002 - local_evidence_summary (unknown)
  - local_evidence_summary_003 - local_evidence_summary (unknown)
- `597964`
  - official_source_placeholder_001 - official_source_placeholder (unknown)
  - official_source_placeholder_002 - official_source_placeholder (unknown)
  - official_source_placeholder_003 - official_source_placeholder (unknown)
  - news_source_placeholder_004 - news_source_placeholder (unknown)
  - news_source_placeholder_005 - news_source_placeholder (unknown)
  - news_source_placeholder_006 - news_source_placeholder (unknown)
  - source_plan_007 - source_plan (unknown)
- `598936`
  - official_source_placeholder_001 - official_source_placeholder (unknown)
  - official_source_placeholder_002 - official_source_placeholder (unknown)
  - official_source_placeholder_003 - official_source_placeholder (unknown)
  - news_source_placeholder_004 - news_source_placeholder (unknown)
  - news_source_placeholder_005 - news_source_placeholder (unknown)
  - news_source_placeholder_006 - news_source_placeholder (unknown)
  - source_plan_007 - source_plan (unknown)
- `691547`
  - official_source_placeholder_001 - official_source_placeholder (unknown)
  - official_source_placeholder_002 - official_source_placeholder (unknown)
  - official_source_placeholder_003 - official_source_placeholder (unknown)
  - news_source_placeholder_004 - news_source_placeholder (unknown)
  - news_source_placeholder_005 - news_source_placeholder (unknown)
  - news_source_placeholder_006 - news_source_placeholder (unknown)
  - source_plan_007 - source_plan (unknown)
- `692258`
  - official_source_checked_001 - official_source_checked (unknown)
  - official_source_checked_002 - official_source_checked (unknown)
  - official_source_placeholder_003 - official_source_placeholder (unknown)
  - official_source_placeholder_004 - official_source_placeholder (unknown)
  - official_source_placeholder_005 - official_source_placeholder (unknown)
  - news_source_checked_006 - news_source_checked (unknown)
  - news_source_placeholder_007 - news_source_placeholder (unknown)
  - news_source_placeholder_008 - news_source_placeholder (unknown)
  - news_source_placeholder_009 - news_source_placeholder (unknown)
  - source_plan_010 - source_plan (unknown)

## Blockers

- none

## Next Operator Actions

- `563650` - Wait for a local outcome record or add one when the outcome is known.
- `597964` - Wait for a local outcome record or add one when the outcome is known.
- `598936` - Wait for a local outcome record or add one when the outcome is known.
- `691547` - Wait for a local outcome record or add one when the outcome is known.
- `692258` - Wait for a local outcome record or add one when the outcome is known.

## Safety Boundary

- Local artifacts only.
- Paper-only analysis-quality tracking.
- No live fetch, OpenRouter call, Polymarket API call, authenticated endpoint, wallet access, order, trading action, runtime change, or dispatcher change.
