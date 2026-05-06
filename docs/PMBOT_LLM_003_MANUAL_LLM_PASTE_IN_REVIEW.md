# PMBOT-LLM-003 Manual LLM Paste-In Review

## Scope

PMBOT-LLM-003 adds a deterministic local manual paste-in review loop on top of PMBOT-LLM-001 and PMBOT-LLM-002:

`safe LLM analysis packet JSON -> Markdown prompt for manual paste -> manually saved LLM response JSON -> PMBOT-LLM-001 validator -> accepted/rejected review JSON -> Markdown operator summary`

This is an offline-only operator workflow. PMBOT writes a prompt file, the operator manually pastes it into an LLM UI, and the operator manually saves the returned JSON as a local file before PMBOT validates it.

## How It Differs From The Offline Stub

PMBOT-LLM-002 validates a local fixture or mock response JSON and exports a deterministic review stub. It proves the validator and accepted/rejected artifact shape.

PMBOT-LLM-003 adds the missing manual handoff surface:

- `pm_bot/llm/export_manual_llm_prompt.py` writes a deterministic Markdown prompt from a validated safe packet.
- `pm_bot/llm/validate_manual_llm_paste_in_review.py` validates the manually saved response JSON and writes manual review artifacts.
- The response is still validated by `pm_bot/llm/validate_llm_analysis_artifacts.py`.
- The flow remains local file IO only.

## Operator Steps

1. Export the manual prompt:

```powershell
python pm_bot\llm\export_manual_llm_prompt.py `
  --packet pm_bot\llm\example_llm_analysis_packet.v1.json `
  --out-md pm_bot\llm\manual_llm_prompt.v1.md
```

2. Manually open `pm_bot/llm/manual_llm_prompt.v1.md`.

3. Manually paste the full Markdown prompt into an LLM UI.

4. In the LLM UI, request only strict JSON matching `llm_analysis_response_schema.v1.json`.

5. Manually save the returned JSON to a local response file, for example:

```text
pm_bot/llm/manual_llm_paste_in_response_example_valid.v1.json
```

6. Validate and export the manual review result:

```powershell
python pm_bot\llm\validate_manual_llm_paste_in_review.py `
  --packet pm_bot\llm\example_llm_analysis_packet.v1.json `
  --response pm_bot\llm\manual_llm_paste_in_response_example_valid.v1.json `
  --out-json pm_bot\llm\manual_llm_paste_in_review.v1.json `
  --out-md pm_bot\llm\manual_llm_paste_in_review.v1.md
```

The validator exits with `0` for accepted output and `1` for rejected output after writing the JSON and Markdown review artifacts.

## Why API Is Not Added

No LLM API is added in this task because the boundary being tested is manual operator control, deterministic local validation, and safe artifact review. Adding an API would introduce authentication, network behavior, provider-specific request shaping, prompt automation risk, retry behavior, logging questions, and runtime integration decisions that are explicitly outside PMBOT-LLM-003.

The current flow intentionally avoids:

- Live API or network calls.
- LLM API calls.
- Browser automation.
- Prompt automation.
- Credentials, wallet material, private keys, signing, or trading endpoint access.
- Real orders, live trading, or autonomous paper orders.
- Runtime wiring, dispatcher changes, run_codex changes, or workbench entrypoint integration.

## Validation Behavior

The prompt exporter loads the packet and validates it with the PMBOT-LLM-001 packet schema and safety checks. Invalid packets are rejected and no prompt is written.

The manual paste-in validator loads the packet and manually saved response JSON, then validates both through the PMBOT-LLM-001 validator behavior:

- A valid packet plus valid manual response is accepted.
- A response with forbidden fields such as `recommended_side` is rejected.
- A response with forbidden phrases such as `place order` is rejected.
- Malformed response JSON is rejected.
- Missing required response sections are reported.
- Forbidden findings are surfaced in JSON and Markdown outputs.

An accepted result means only that the local artifacts passed deterministic validation. It does not mean the response is correct, fresh, complete, useful, or safe for any trading decision.

## Forbidden Outputs

Manual LLM responses must not include:

- Probability estimates.
- EV.
- Edge.
- Scoring.
- Recommended side.
- Bet recommendations.
- Order size.
- Price target.
- Execution instruction.
- Wallet, private-key, or credential handling.
- Certainty claims.
- Market decisions.
- Side selection.
- Trade instructions.
- Autonomous actions.

If any of these appear as fields or forbidden language patterns caught by PMBOT-LLM-001, the manual review result is rejected.

## Outputs

PMBOT-LLM-003 writes these local artifacts:

- `pm_bot/llm/manual_llm_prompt.v1.md`
- `pm_bot/llm/manual_llm_paste_in_response_example_valid.v1.json`
- `pm_bot/llm/manual_llm_paste_in_response_example_invalid.v1.json`
- `pm_bot/llm/manual_llm_paste_in_review.v1.json`
- `pm_bot/llm/manual_llm_paste_in_review.v1.md`
- `pm_bot/llm/expected_manual_llm_paste_in_review.v1.json`

## Next Safe Task

`PMBOT-LLM-004-MANUAL-LLM-REVIEW-WORKBENCH-SURFACE`

The next task should keep the same safety boundary and only surface these manual review artifacts passively in the operator workbench if explicitly approved.
