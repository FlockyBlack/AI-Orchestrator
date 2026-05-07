# PMBOT OpenRouter 010 Manual Network Adapter Proposal

Task: `PMBOT-OPENROUTER-010-MANUAL-NETWORK-ADAPTER-PROPOSAL`

## A. Purpose

This proposal defines a future manually invoked network adapter path from the current dry-run shell to a controlled OpenRouter call.

This task is proposal-only. It does not implement the network adapter, does not add network code, does not call OpenRouter, does not read an API key, and does not wire model output into PMBOT runtime, workbench, dispatcher, review queue import, wallet, order, or trading paths.

The proposed future adapter remains analysis-only, manual-review-only, operator-gated, validator-gated, and deterministic/local-first where possible.

## B. Current Baseline

Committed OpenRouter pieces:

- Manual smoke harness: `pm_bot/llm/run_openrouter_prompt_test.py`
- Design-only adapter contract: `pm_bot/llm/openrouter_adapter_contract.v1.json`
- Dry-run adapter shell: `pm_bot/llm/run_openrouter_adapter.py`
- Design plan: `docs/PMBOT_OPENROUTER_008_DESIGN_ONLY_GATED_ADAPTER_PLAN.md`
- Dry-run shell notes: `docs/PMBOT_OPENROUTER_009_DRY_RUN_ADAPTER_SHELL.md`

Verified prior real smoke:

- Final real OpenRouter smoke passed for market_id `563650`.
- Sonnet candidate was called.
- Sonnet JSON fence recovery was used.
- Structured GPT-5.5 critic was called.
- `critic_schema_valid` was `true`.
- `critic_safety_booleans_passed` was `true`.
- `safety_boundary_passed` was `true`.

Structured critic contract:

```text
pmbot_openrouter_critic_response.v1
```

Runtime artifact paths are ignored by git:

```text
pm_bot/llm/openrouter_test_artifacts/
pm_bot/llm/openrouter_adapter_dry_runs/
```

## C. Explicit Non-Goals

This task explicitly excludes:

- No implementation in this task.
- No OpenRouter API calls.
- No API key read.
- No runtime wiring.
- No dispatcher integration.
- No wallet, private key, or credential access.
- No orders.
- No trading recommendations.
- No side selection.
- No probability, EV, edge, or scoring.
- No buy, sell, hold, enter, or exit language.
- No automatic loops.
- No batch queue automation.
- No auto-import into a review queue.
- No browser or web UI automation.
- No prompt automation against web UIs.
- No workbench changes.
- No runtime changes.

## D. Proposed Future Manual-Network Command Shape

Design only, not implemented in this task:

```powershell
python pm_bot/llm/run_openrouter_adapter.py --market-id 563650 --manual-confirm-network --model-profile sonnet_gpt55_critic --max-cost-usd 0.10 --max-prompt-tokens 20000 --max-completion-tokens 4000 --allow-local-json-fence-repair
```

Alternative explicit prompt and packet path form:

```powershell
python pm_bot/llm/run_openrouter_adapter.py --prompt-path <path> --packet-path <path> --manual-confirm-network --model-profile sonnet_gpt55_critic
```

The future command should process exactly one selected prompt per invocation. A packet may be supplied or inferred for audit context, but it must not cause automatic queue consumption or downstream import.

## E. Required Explicit Gates For Future Implementation

A future implementation must require all of these gates before any network call:

- `--manual-confirm-network` must be present.
- `--dry-run` must not be present.
- `OPENROUTER_API_KEY` must be present only in the process environment.
- `max-cost-usd` must be supplied or defaulted conservatively.
- Max prompt token and completion token caps must be enforced.
- Exactly one prompt may be processed per invocation.
- The selected prompt must exist.
- The selected prompt must be under the approved PMBOT LLM batch path unless `--prompt-path` override is explicitly provided.
- The selected packet is optional, but its resolved path or absence must be logged.
- Runtime artifacts must be written only under ignored paths.
- A staged secret scan command must be documented and run before commit.
- Structured critic schema validation must pass.
- Candidate safety validation must pass.
- Human/operator review must still be required.
- No downstream import may happen unless a separate explicit operator command exists.

The future implementation must also fail closed if any runtime, workbench, dispatcher, wallet, order, trading, queue automation, or browser automation boundary is crossed.

## F. Block Conditions

Future terminal statuses should include:

- `blocked_missing_manual_confirm_network`
- `blocked_dry_run_network_conflict`
- `blocked_missing_api_key`
- `blocked_invalid_model_profile`
- `blocked_cost_cap_missing`
- `blocked_cost_cap_exceeded`
- `blocked_token_cap_exceeded`
- `blocked_missing_prompt`
- `blocked_runtime_boundary`
- `blocked_secret_scan_required`
- `candidate_call_failed`
- `candidate_validation_failed`
- `critic_call_failed`
- `critic_schema_failed`
- `critic_safety_failed`
- `completed_for_operator_review`

Status meanings:

- `blocked_missing_manual_confirm_network`: Network mode was requested without the explicit manual confirmation flag.
- `blocked_dry_run_network_conflict`: `--dry-run` and manual network mode were both requested.
- `blocked_missing_api_key`: The required environment-only key was absent.
- `blocked_invalid_model_profile`: The requested model profile is unknown or does not match the approved profile contract.
- `blocked_cost_cap_missing`: No cost cap was supplied or available through a conservative default.
- `blocked_cost_cap_exceeded`: Estimated or reported cost crossed the cap.
- `blocked_token_cap_exceeded`: Prompt or completion token cap was exceeded or could not be bounded.
- `blocked_missing_prompt`: The selected prompt path was missing.
- `blocked_runtime_boundary`: Runtime, workbench, dispatcher, wallet, order, trading, queue, or browser automation boundary was crossed.
- `blocked_secret_scan_required`: Required local secret scan was missing, failed, or could not prove artifacts were clean enough to proceed.
- `candidate_call_failed`: The candidate model call failed before accepted content was available.
- `candidate_validation_failed`: Candidate output failed JSON, schema, repair, or safety validation.
- `critic_call_failed`: The critic model call failed before accepted content was available.
- `critic_schema_failed`: Critic output failed `pmbot_openrouter_critic_response.v1`.
- `critic_safety_failed`: Critic schema passed, but one or more safety booleans failed.
- `completed_for_operator_review`: Candidate and critic validations passed, and the output is ready only for manual operator review.

## G. Future Network Adapter Flow

Proposed flow:

1. Parse CLI arguments.
2. Refuse if `--manual-confirm-network` is absent.
3. Refuse if `--dry-run` conflicts with network mode.
4. Resolve prompt and packet paths.
5. Estimate or bound token and cost caps before any call.
6. Read `OPENROUTER_API_KEY` from the environment only.
7. Call the candidate model exactly once.
8. Save raw candidate artifact.
9. Validate raw or repaired candidate JSON.
10. If the candidate is valid, call the critic model exactly once.
11. Validate the structured critic response.
12. Write a summary and `operator_next_action`.
13. Exit with pass/fail status.
14. Do not import into the PMBOT review queue.
15. Do not call any runtime, workbench, or dispatcher path.

The future implementation must not perform automatic retries that create loops. A failed call should produce an explicit terminal status for operator review.

## H. Future Artifact Contract

Proposed ignored runtime artifact names:

- `adapter_network_run_summary_<market_id_or_timestamp>.v1.json`
- `candidate_raw_<id>.json`
- `candidate_content_<id>.json`
- `candidate_validation_<id>.json`
- `critic_raw_<id>.json`
- `critic_content_<id>.json`
- `critic_validation_<id>.json`
- `operator_next_action_<id>.md`

The summary fields must include:

- `artifact_type`
- `status`
- `network_calls_made`
- `api_key_source`
- `api_key_logged` with value `false`
- `requested_model`
- `returned_model`
- `provider`
- `usage`
- `cost`
- `response_id`
- `timestamp_utc`
- `prompt_path`
- `packet_path`
- `model_profile`
- `candidate_valid`
- `critic_valid`
- `critic_schema_valid`
- `critic_safety_booleans_passed`
- `safety_boundary_passed`
- `manual_review_required` with value `true`
- `no_runtime_wiring` with value `true`
- `no_dispatcher_integration` with value `true`
- `no_wallet_or_orders` with value `true`
- `no_trading_decision` with value `true`

`operator_next_action_<id>.md` may say whether the operator should review, retry, or stop. It must not suggest a trade, side, probability, EV, edge, score, wallet action, order, or market decision.

## I. Proposed Model Profile

Use the existing model profile:

```text
sonnet_gpt55_critic
```

Profile details:

- Candidate: `anthropic/claude-sonnet-4.5`
- Critic: `openai/gpt-5.5`
- Critic contract: `pmbot_openrouter_critic_response.v1`

The model profile remains a manually selected adapter profile, not runtime authority.

## J. Cost And Token Controls

Recommended defaults for the first future network adapter:

- `max-cost-usd`: `0.10`
- `max-prompt-tokens`: `20000`
- `max-completion-tokens`: `4000`

The proposed default cost cap is `0.10` because the first network adapter should prove the gated path with the lowest practical spend. The existing dry-run shell default of `0.25` is acceptable as a planning placeholder, but a first real network implementation should prefer `0.10` unless the operator separately approves a higher cap for a specific run.

Controls:

- Cost cap must be supplied or defaulted conservatively.
- Prompt and completion token caps must be enforced before calls where possible.
- If usage or cost is missing from the provider response, fail closed unless an explicitly named operator flag later allows missing usage metadata.
- No multi-prompt batching in the first network adapter.
- No automatic retry loop.
- No background polling.

## K. Security

Required future security rules:

- The API key source is environment-only: `OPENROUTER_API_KEY`.
- The key is never logged.
- The key is never stored.
- Authorization header content must be redacted in any debug object.
- Raw provider responses must be sanitized or redacted before write if needed.
- Runtime artifacts must remain ignored by git.
- No encrypted provider blobs may be committed.
- A staged secret scan is required before commit.
- No wallet files, private keys, credential stores, browser profiles, auth files, or `.env` files may be read or touched.

Required staged secret scan command, documented without embedding the disallowed tokens as contiguous scan hits:

```powershell
$patterns = @(
  "sk" + "-or-",
  "Bearer" + " ",
  "Authorization" + ":",
  "OPENROUTER_API_KEY" + "="
)
Select-String -Path ".\docs\*.json",".\docs\*.md",".\pm_bot\llm\*.json",".\.gitignore" `
  -Pattern $patterns `
  -CaseSensitive:$false
```

Expected result:

- `OPENROUTER_API_KEY` may appear only as an environment variable name.
- No real key.
- No credential header implementation in new docs or specs.
- No runtime artifact blobs tracked by git.

## L. Testing Plan For Future Implementation

Future implementation tests should include:

- Network mode fails without `--manual-confirm-network`.
- Dry-run never reads the key.
- Network mode fails without the environment key.
- Key redaction.
- One prompt per invocation.
- Prompt selection by `market_id`.
- Prompt override path.
- Missing prompt blocks.
- Cost cap blocks.
- Token cap blocks.
- Candidate JSON fence recovery.
- Candidate safety failure blocks critic.
- Critic structured schema is required.
- Any critic `has_*` safety boolean set to `true` fails.
- Artifact writing avoids the key.
- Runtime, workbench, and dispatcher modules are not imported.
- Wallet and order modules are not imported.

These tests must use fake local fixtures and mocks. They must not call OpenRouter and must not read a real API key unless a separate operator-approved smoke task explicitly permits it.

## M. Approval Checklist For Future Implementation

Before coding a future network adapter implementation:

- Operator explicitly approves network implementation.
- Tests are green.
- Git is clean before change.
- Result JSON is created for the implementation task.
- No runtime artifacts are tracked.
- Secret scan is clean.
- No runtime wiring is added.
- No dispatcher changes are made.
- No wallet, order, or trading code is added.

Approval for this proposal does not approve network implementation.

## N. Recommended Next Task

Recommended next task:

```text
PMBOT-OPENROUTER-011-MANUAL-NETWORK-ADAPTER-GATED-IMPLEMENTATION
```

This requires separate operator approval before coding. The next task must still preserve manual invocation, one prompt per run, validator gating, human review, ignored runtime artifacts, no dispatcher integration, no wallet/order/trading behavior, no automatic queue processing, and no browser or web UI automation.
