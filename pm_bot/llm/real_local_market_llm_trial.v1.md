# PMBOT Real Local Market LLM Trial v1

- Trial status: accepted
- Packet source: real_local_market_artifact
- Source artifact: pm_bot/research/selected_ingest_final_dossier_drafts.v1.json
- Market ID: 824952
- Packet path: pm_bot/llm/real_local_market_llm_trial_packet.v1.json
- Prompt path: pm_bot/llm/real_local_market_llm_trial_prompt.v1.md
- Response path: pm_bot/llm/real_local_market_llm_trial_response_example.v1.json
- Manual review status: accepted
- Quality gate status: quality_passed

## Boundary

No API calls, LLM API calls, browser automation, prompt automation, runtime integration, live trading, real orders, autonomous paper orders, trading advice, truth evaluation, outcome estimates, value scoring, advantage claims, side selection, or market decisions.

## Errors

- none

## Warnings

- none

## Manual Operator Steps For A Real Trial

1. Open pm_bot/llm/real_local_market_llm_trial_prompt.v1.md.
2. Paste into ChatGPT, Claude, or Gemini manually.
3. Ask for strict JSON only, with no Markdown wrapper or extra prose.
4. Save the response to a local JSON file matching llm_analysis_response_schema.v1.json.
5. Rerun python pm_bot/llm/export_real_local_market_llm_trial.py --response path/to/manual_response.json.
6. Review accepted/rejected and quality gate status in the JSON, Markdown, or workbench surface.

## Current Example Response Status

- Packet validation: accepted
- Response validation: accepted
- Manual review: accepted
- Quality gate: quality_passed

## Source Notes

The packet is built from an existing local PMBOT market/research artifact and is labeled `real_local_market_artifact` when a suitable source is selected. It does not use `example_llm_analysis_packet.v1.json` as the market source.

## Next Safe Operator Action

Replace only the response path with a real manually saved JSON response when ready, then rerun the exporter and inspect the local result artifacts.
