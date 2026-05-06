# PMBOT OpenRouter 006 Structured Critic Schema Redesign

Task: `PMBOT-OPENROUTER-006-STRUCTURED-CRITIC-SCHEMA-REDESIGN`

## Purpose

The OpenRouter critic now returns a strict machine-readable JSON contract instead of free-text review notes.

This removes the false-positive loop where safe negative attestations such as "does not select Yes/No" or "no EV or edge" were scanned as forbidden critic output. The critic safety gate now relies on explicit booleans and enum verdicts.

## Structured Critic Contract

Live critic responses must use:

```text
pmbot_openrouter_critic_response.v1
```

Required top-level fields:

- `contract_version`
- `json_validity`
- `schema_review`
- `safety_boundary_review`
- `operator_readiness`
- `issues`
- `verdict`

Required safety booleans:

- `has_trading_recommendation`
- `has_side_selection`
- `has_probability_estimate`
- `has_ev_or_edge_or_scoring`
- `has_order_instruction`
- `has_wallet_or_credential_instruction`
- `has_market_decision`
- `has_runtime_or_dispatcher_instruction`
- `has_external_data_claim`

All required `has_*` fields must be booleans. Any `true` value fails critic validation.

Operator readiness remains manual-only:

- `ready_for_operator_review` may be `true`
- `ready_for_resolution` is represented as a boolean status
- `ready_for_trading_action=true` fails validation

## Prompt Change

`CRITIC_SYSTEM_PROMPT` now asks GPT-5.5 for raw JSON only in the v1 structured shape. It explicitly forbids prose safety attestations, `review_notes`, explanatory text, trading recommendations, side selection, probabilities, EV/edge/scoring, execution instructions, wallet instructions, external data, and extra fields.

When uncertain, the critic must use `issues[]` with neutral enum values and `message_code` strings instead of prose review notes.

## Validator Change

Sonnet candidate validation is unchanged:

- Strict raw JSON object validation.
- Optional full-response JSON fence repair.
- Forbidden field scans remain enabled.
- Forbidden phrase scans remain enabled for candidate output.

Critic validation is separate:

- Strict raw JSON object validation and optional fence repair still apply.
- The v1 critic contract is required; old free-text critic shapes fail.
- Required fields and nested fields must exist.
- Enum fields must be valid.
- Safety booleans must be booleans.
- Any `safety_boundary_review.has_* = true` fails validation.
- `operator_readiness.ready_for_trading_action = true` fails validation.
- `verdict = fail`, reported candidate JSON invalidity, or `schema_review.status = fail` fails the critic gate.
- Free-text phrase scanning is no longer the primary critic safety gate.
- The validator still blocks explicit forbidden instruction text if it appears in critic string fields.

## Artifacts

Critic raw, content, and validation artifacts are still written.

Accepted structured critic content artifacts now wrap the parsed object:

```json
{
  "content_status": "accepted",
  "status": "accepted",
  "parsed_content": {}
}
```

Rejected parsed critic JSON continues to store `parsed_content`, `raw_content`, `validation_errors`, and `validation_warnings`.

Summary artifacts now include:

- `critic_schema_valid`
- `critic_safety_booleans_passed`
- `critic_verdict`
- `critic_valid`

## Backward Compatibility

Old critic artifacts with free-text review notes may be used only as regression examples. They are not accepted as final structured critic output because they do not implement `pmbot_openrouter_critic_response.v1`.

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
- No runtime or dispatcher wiring.
- No automatic LLM loops.
- No secrets in git, logs, artifacts, stdout, or stderr.
