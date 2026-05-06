# PMBOT Real Manual LLM Market Packet Trial v1

- Trial status: accepted
- Packet source: example_packet_trial_not_live_market
- Packet path: pm_bot/llm/real_manual_llm_market_packet_trial_packet.v1.json
- Prompt path: pm_bot/llm/real_manual_llm_market_packet_trial_prompt.v1.md
- Response path: pm_bot/llm/real_manual_llm_market_packet_trial_response_example.v1.json
- Manual review status: accepted
- Quality gate status: quality_passed

## Boundary

No API calls, LLM API calls, browser automation, prompt automation, runtime integration, live trading, real orders, autonomous paper orders, trading advice, truth evaluation, outcome estimates, value scoring, advantage claims, side selection, or market decisions.

## Errors

- none

## Warnings

- none

## Manual Operator Steps For A Real Trial

1. Open pm_bot/llm/real_manual_llm_market_packet_trial_prompt.v1.md.
2. Paste the prompt into ChatGPT, Claude, or Gemini manually.
3. Ask for strict JSON only, with no Markdown wrapper or extra prose.
4. Save the response to a local JSON file matching llm_analysis_response_schema.v1.json.
5. Rerun python pm_bot/llm/export_real_manual_llm_market_packet_trial.py --response path/to/manual_response.json.
6. Review accepted/rejected and quality gate status in the JSON and Markdown trial outputs.

## Current Example Response Status

- Packet validation: accepted
- Response validation: accepted
- Manual review: accepted
- Quality gate: quality_passed

## Next Safe Operator Action

Replace only the response path with a real manually saved JSON response when ready, then rerun the exporter and inspect the local result artifacts.

## Source Notes

This trial uses the existing PMBOT-LLM safe example packet source and is labeled `example_packet_trial_not_live_market`. It does not transform live data or create a market decision artifact.
