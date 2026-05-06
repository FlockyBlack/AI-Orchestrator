# PMBOT OpenRouter 001 Gated API Test Harness

Task: `PMBOT-OPENROUTER-001-GATED-API-TEST-HARNESS`

## Purpose

`pm_bot/llm/run_openrouter_prompt_test.py` is a local, operator-triggered OpenRouter smoke-test harness for the existing PMBOT manual LLM packet batch.

It is not runtime integration, not an automatic LLM cycle, not a trading agent, and not execution authority.

## Safety Boundary

- Analysis only.
- Manual review only.
- Operator gated.
- Validator gated.
- No trading recommendations.
- No side selection.
- No probability estimates.
- No EV, edge, value, or scoring output.
- No buy, sell, hold, enter, or exit instructions.
- No market decisions.
- No wallet, private key, credential, or order handling.
- No dispatcher or runtime wiring.
- No automatic LLM loops.
- No secrets in git, logs, artifacts, stdout, or stderr.

## Prompt Selection

The harness selects prompts in this order:

1. `--prompt-path`, when explicitly provided.
2. `--market-id`, mapped to `pm_bot/llm/manual_packet_batch/<market_id>_prompt.v1.md`.
3. Default search in `pm_bot/llm/manual_packet_batch/*_prompt.v1.md`, preferring manifest items with `waiting_for_operator_pasted_response`.

The legacy prompt `pm_bot/llm/real_local_market_llm_trial_prompt.v1.md` is never auto-selected.

## API Key

Non-dry-run calls read the OpenRouter API key only from `OPENROUTER_API_KEY`.

The key is not printed, saved, committed, or included in artifacts. Missing key exits cleanly with `error_missing_openrouter_api_key`.

## Commands

Dry run:

```bash
python pm_bot/llm/run_openrouter_prompt_test.py --dry-run --market-id 563650
```

Sonnet plus critic:

```bash
python pm_bot/llm/run_openrouter_prompt_test.py --market-id 563650
```

Sonnet only:

```bash
python pm_bot/llm/run_openrouter_prompt_test.py --market-id 563650 --skip-critic
```

## Models

Default Sonnet model:

```text
anthropic/claude-sonnet-4.5
```

Default critic model:

```text
openai/gpt-5.5
```

Both calls use `temperature: 0`.

## Artifacts

Default output directory:

```text
pm_bot/llm/openrouter_test_artifacts
```

Sonnet artifacts:

- `openrouter_sonnet_<market_id_or_timestamp>_raw.json`
- `openrouter_sonnet_<market_id_or_timestamp>_content.json`
- `openrouter_sonnet_<market_id_or_timestamp>_validation.json`

Critic artifacts:

- `openrouter_critic_<market_id_or_timestamp>_raw.json`
- `openrouter_critic_<market_id_or_timestamp>_content.json`
- `openrouter_critic_<market_id_or_timestamp>_validation.json`

Summary artifact:

- `openrouter_test_summary_<market_id_or_timestamp>.json`

Dry run writes only the summary artifact.

## Validation

The harness validates Sonnet candidate content before critic handoff:

- If the full raw response is exactly one Markdown code fence with `json` or no language, the harness strips the fence, records `markdown_fence_recovered`, and validates only the recovered JSON object.
- Prose-wrapped fences, unsupported fence languages, multiple fenced blocks, and recovered content that still contains fences are rejected.
- Raw artifacts preserve the original model content, including any recovered fence.
- Content artifacts and critic handoff use the parsed JSON object after successful recovery.
- Parsed JSON objects rejected by safety validation are written with `content_status: rejected` and `parsed_content`, not mislabeled as `not_valid_json_object`.
- First non-whitespace character of the validated JSON candidate is `{`.
- Last non-whitespace character of the validated JSON candidate is `}`.
- Markdown fences are absent.
- Content parses as JSON.
- Parsed JSON top level is an object.
- Obvious PMBOT forbidden fields are absent.
- Obvious trading, side-selection, probability, EV, edge, scoring, execution, wallet, and certainty language is absent.
- Recommendation language is context-aware: trading, market, side, outcome, position, entry, exit, order, and market-decision recommendations are rejected, while schema/edit/review wording such as `candidate_json_edits`, `suggested_fix`, or "operator review is recommended" is allowed.
- Negative safety attestations are context-aware: absence or avoidance statements such as "No EV, edge, wallet, or order instructions are present" are allowed, while bypass/action wording such as "No reason not to buy YES", "No downside to selecting YES", "No issue placing an order", or "No problem using wallet credentials" is rejected.
- Negated Yes/No side-selection attestations are context-aware: "The text does not select Yes/No or imply an outcome" and "No side is selected" are allowed, while "Select Yes", "The selected side is Yes", "Outcome is Yes", "The market should resolve Yes", and "Likely Yes" remain rejected.

The critic is called only when Sonnet content passes validation and `--skip-critic` is not set.

Critic validation is now separate from Sonnet candidate validation:

- The critic must return `contract_version: pmbot_openrouter_critic_response.v1`.
- Required critic sections are `json_validity`, `schema_review`, `safety_boundary_review`, `operator_readiness`, `issues`, and `verdict`.
- Critic safety validation relies on `safety_boundary_review.has_*` booleans instead of free-text review notes.
- Any `safety_boundary_review.has_* = true` fails critic validation.
- `operator_readiness.ready_for_trading_action = true` fails critic validation.
- `verdict` and `schema_review.status` must be one of `pass`, `pass_with_notes`, or `fail`; `fail` gates the run as failed.
- Old free-text critic shapes with `review_notes` are regression examples only and are not accepted as final live critic output.
- Critic content artifacts store valid parsed critic JSON under `parsed_content`.
- Summary artifacts include `critic_schema_valid`, `critic_safety_booleans_passed`, `critic_verdict`, and `critic_valid`.

## Non-Goals

- No runtime or dispatcher changes.
- No wallet or order logic.
- No automatic batch loop.
- No real trading.
- No OpenRouter call during `--dry-run`.
