# PMBOT-LLM-008 Real Local Market Packet Trial

## What This Is

PMBOT-LLM-008 creates the first deterministic offline/manual LLM trial packet from an existing local PMBOT market/research artifact, rather than from the PMBOT-LLM example packet.

The flow selects a safe local market artifact, builds an LLM-safe packet, exports a manual paste-in prompt, validates a saved example response, runs the manual review validator, runs the manual review quality gate, and writes local JSON/Markdown trial outputs.

## Real Local Market Source

- Source artifact: `pm_bot/research/selected_ingest_final_dossier_drafts.v1.json`
- Source type: `selected_ingest_final_dossier_draft`
- Market ID: `824952`
- Market title: `MicroStrategy sells any Bitcoin by December 31, 2026?`
- Trial packet source type: `real_local_market_artifact`

The exporter inspects `pm_bot/workbench/operator_review_pack.v1.json` first because that is the preferred source class. It does not select that pack because the pack contains local market IDs but not enough standalone title/question and resolution context for the LLM packet schema. The selected-ingest final dossier draft is then selected because it contains a market ID, market question, local resolution-context excerpt, evidence/source coverage notes, uncertainty notes, and human-review notes.

## Why This Is Stronger Than PMBOT-LLM-007

PMBOT-LLM-007 proved the manual LLM trial infrastructure but labeled its packet source as `example_packet_trial_not_live_market`.

PMBOT-LLM-008 keeps the same offline/manual safety model while replacing the example packet source with a real local PMBOT market/research artifact. The packet is still sanitized and schema-limited, but it now exercises the operator flow against real local market context.

## Why This Still Does Not Call An LLM API

The exporter only reads and writes local files. It calls existing local PMBOT helpers:

- `pm_bot/llm/validate_llm_analysis_artifacts.py`
- `pm_bot/llm/export_manual_llm_prompt.py`
- `pm_bot/llm/validate_manual_llm_paste_in_review.py`
- `pm_bot/llm/evaluate_manual_llm_review_quality_gate.py`

There is no LLM API call, browser automation, prompt automation, network call, runtime service, credential access, wallet access, trading endpoint, real order, live trading, or autonomous paper order.

## Manual Operator Flow

1. Open `pm_bot/llm/real_local_market_llm_trial_prompt.v1.md`.
2. Paste into ChatGPT, Claude, or Gemini manually.
3. Ask for strict JSON only, with no Markdown wrapper or extra prose.
4. Save the response to a local JSON file matching `pm_bot/llm/llm_analysis_response_schema.v1.json`.
5. Rerun `python pm_bot/llm/export_real_local_market_llm_trial.py --response path/to/manual_response.json`.
6. Review accepted/rejected and quality gate status in the JSON, Markdown, or workbench surface.

## Validation And Quality Gate

The trial packet must pass the PMBOT-LLM-001 packet schema and forbidden-content validator.

The saved response must pass the PMBOT-LLM-001 response schema and forbidden-content validator.

The manual review flow from PMBOT-LLM-003 reports accepted/rejected status and surfaces missing sections, accepted sections, errors, warnings, forbidden findings, source artifacts, and next safe operator action.

The quality gate from PMBOT-LLM-005 checks deterministic usefulness and safety. A usable response should finish as `quality_passed` or `quality_passed_with_warnings`; low-quality, malformed, missing, unsafe certainty, or forbidden recommendation responses fail safely.

## Result Meaning

`accepted` means only that the local packet, prompt export, saved response JSON, manual review validator, and deterministic quality gate all passed the offline contracts.

It does not mean the response is true, current, profitable, useful for trading, or suitable for automated action.

## Hard Boundary

This trial is not trading advice and does not add:

- API or network calls
- LLM API calls
- Browser automation
- Prompt automation
- Runtime integration
- Credential, wallet, or private-key access
- Real orders or live trading
- Autonomous paper orders
- Outcome estimates, EV, edge, scoring, or value metrics for market decisions
- Side recommendations
- Market decision logic
- Truth evaluation
- Dispatcher or `run_codex` changes

## Still Missing Before API Or Autonomous Trading

Before any API integration exists, PMBOT still needs explicit separate approval, a reviewed runtime design, dedicated safety gates, credential isolation, audit logging, operator authorization, failure-mode handling, and tests that prove no decision, order, or wallet action can occur without approved authority.

Before autonomous trading exists, PMBOT would need a separate strategy specification, risk model, operator approval model, compliance review, wallet/key controls, live-data validation, irreversible-action controls, and a task that explicitly approves those capabilities. None of that is included here.

## Next Recommended Task

`PMBOT-LLM-009-REAL-MANUAL-LLM-TRIAL-OPERATOR-ACCEPTANCE`
