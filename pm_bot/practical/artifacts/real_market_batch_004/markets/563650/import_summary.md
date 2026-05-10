# PMBOT Local Market Packet Import

- Input: `pm_bot/llm/manual_packet_batch/563650_packet.v1.json`
- Output contract: `pmbot_one_market_input.v1`
- Market ID: `563650`
- Market title: SCOTUS accepts sports event contract case by July 31, 2026?
- Sources preserved: 3
- Missing evidence items: 7
- Source artifact path: `pm_bot/research/final_dossier_drafts.v1.json`
- Normalized JSON: `pm_bot\practical\artifacts\real_market_batch_004\markets\563650\normalized_input.json`

## Missing evidence

- No missing-information item is closed by this gate; human review remains required.
- Confirm the exact docket identifier before any later human decision.
- Court docket terminology may require manual interpretation.
- Source timing should be reviewed by a human before any later workflow.
- Manual draft sections are populated for structural quality review only.
- Reviewer verified checklist coverage for the review pack and approved a later draft-preparation step.
- Referenced source artifact path is not present locally: pm_bot/research/final_dossier_drafts.v1.json

## Source references

- `local_evidence_summary_001` local_evidence_summary - `unknown`
- `local_evidence_summary_002` local_evidence_summary - `unknown`
- `local_evidence_summary_003` local_evidence_summary - `unknown`

## Safety boundary

- Local packet normalization only.
- No live fetch or external API call was performed.
- Missing evidence is preserved instead of invented.
