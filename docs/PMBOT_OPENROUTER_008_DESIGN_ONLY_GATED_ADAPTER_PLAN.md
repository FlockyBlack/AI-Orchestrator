# PMBOT OpenRouter 008 Design-Only Gated Adapter Plan

Task: `PMBOT-OPENROUTER-008-DESIGN-ONLY-GATED-ADAPTER-PLAN`

## Purpose

This document defines a future gated OpenRouter adapter boundary for PMBOT. It is design-only. It does not implement runtime integration, does not call OpenRouter, and does not connect LLM calls to the workbench runtime, dispatcher, trading, wallet, orders, or automated loops.

The boundary remains analysis-only, manual-review-only, operator-gated, validator-gated, and deterministic/local-first where possible.

## A. Current State

The committed manual OpenRouter harness is:

```text
pm_bot/llm/run_openrouter_prompt_test.py
```

Verified milestone:

- Manual OpenRouter harness exists and has been committed.
- Final real smoke passed for market_id `563650`.
- Sonnet primary analysis works.
- Sonnet JSON fence recovery works.
- GPT-5.5 structured critic works.
- Critic schema and safety validation work.
- `safety_boundary_passed` was `true`.
- No API key was committed.

Supported model candidates:

- Primary analysis candidate: `anthropic/claude-sonnet-4.5`
- Structured critic candidate: `openai/gpt-5.5`

JSON and validation behavior:

- Candidate responses are expected to be strict JSON.
- Local JSON fence recovery exists as an explicitly controlled repair path.
- Critic responses use the structured contract:

```text
pmbot_openrouter_critic_response.v1
```

Artifact hygiene:

- Runtime artifacts are written under:

```text
pm_bot/llm/openrouter_test_artifacts/
```

- That path is ignored by git and must remain untracked.
- Runtime artifacts must not contain API keys or other secrets.

## B. Proposed Adapter Boundary

The future adapter should be a manually invoked service boundary. It should not be runtime wiring.

The adapter may exist as a CLI entry point that an operator runs explicitly for one selected prompt or packet at a time. It should return a local pass/fail status and write local artifacts for manual inspection.

Allowed future adapter responsibilities:

- Read a selected prompt path or packet path.
- Call an explicitly configured OpenRouter model only when an operator invokes the command.
- Capture `requested_model`, `returned_model`, `provider`, `usage`, `cost`, `response_id`, and `timestamp`.
- Validate raw JSON and, when explicitly enabled, repaired JSON.
- Validate structured critic booleans.
- Write local artifacts under an ignored runtime artifact directory.
- Return pass/fail status to the operator.

Forbidden future adapter responsibilities:

- No market decision.
- No trade recommendation.
- No side selection.
- No probabilities.
- No EV, edge, or scoring.
- No order, wallet, private-key, or credential access.
- No dispatcher integration.
- No automatic queue processing.
- No hidden background loops.
- No live market fetching unless separately approved.
- No auto-writing accepted responses into the PMBOT review queue without explicit operator action.

Boundary rule:

- The adapter may prepare artifacts for human review.
- It must not transform model output into a PMBOT market decision.
- It must not make or imply a trading action.

## C. Proposed Phases

Phase 0: Current manual harness, completed.

- Existing script supports the manual smoke harness.
- Operator controls invocation.
- Artifacts remain local and ignored.

Phase 1: Design-only adapter contract, this task.

- Create this plan.
- Optionally create an inert JSON contract/spec.
- No runtime implementation.
- No OpenRouter call.

Phase 2: Dry-run adapter shell, no network.

- Add a CLI shell that resolves inputs, validates flags, validates boundaries, and writes dry-run summaries.
- It must not require an API key.
- It must not perform network calls.
- It must not import or call dispatcher, wallet, order, or trading code.

Phase 3: Manual network adapter, operator invoked, one prompt at a time.

- Add network capability only behind an explicit operator confirmation flag.
- Use `OPENROUTER_API_KEY` from the environment only.
- Enforce one prompt or packet per invocation unless separately approved.
- Capture model, provider, usage, cost, response id, and timestamp.

Phase 4: Validator-gated import into local review artifacts, still manual.

- Permit a validated result to be imported into local review artifacts only after schema validation and structured critic pass.
- Keep human review mandatory.
- Require explicit operator action for any import.

Phase 5: Possible workbench UI exposure, explicit operator button only.

- If approved later, expose only a manual operator button.
- The UI must not poll, queue, or run hidden loops.
- The UI must not connect LLM output to trading, wallet, orders, or market decisions.

No phase may include automatic trading, wallet integration, order execution, or autonomous market decisions.

## D. Required Gates Before Any Future Implementation

Any future implementation task must pass these gates before network behavior or downstream artifact import is considered:

- Explicit operator approval.
- Tests passing.
- Secret scan passing.
- Dry-run mode passing.
- No runtime artifacts tracked.
- No API key in git, logs, stdout, stderr, or artifacts.
- Clear cost cap and max token cap.
- Single prompt per invocation unless separately approved.
- Schema validation before any downstream artifact import.
- Structured critic pass required.
- Human review still required.

Implementation-specific gates:

- Network calls blocked unless a manual confirmation flag is present.
- Missing `OPENROUTER_API_KEY` blocks network mode.
- Cost cap blocks execution before or during the run when exceeded.
- Runtime boundary checks block imports from dispatchers, wallet modules, order modules, or trading modules.

## E. Adapter Interface Proposal

Design-only CLI shape, not implemented:

```text
python pm_bot/llm/run_openrouter_adapter.py --market-id <id> --dry-run
python pm_bot/llm/run_openrouter_adapter.py --prompt-path <path> --model-profile sonnet_gpt55_critic --manual-confirm-network
```

Proposed inputs:

- `prompt_path`
- `packet_path`
- `market_id`
- `model_profile`
- `dry_run`
- `allow_local_json_fence_repair`
- `max_prompt_tokens`
- `max_completion_tokens`
- `max_cost_usd`
- `out_dir`

Proposed model profile:

- `sonnet_gpt55_critic`
- Candidate model: `anthropic/claude-sonnet-4.5`
- Critic model: `openai/gpt-5.5`
- Critic contract: `pmbot_openrouter_critic_response.v1`

Proposed outputs:

- `adapter_run_summary.v1.json`
- `candidate_raw.json`
- `candidate_content.json`
- `candidate_validation.json`
- `critic_raw.json`
- `critic_content.json`
- `critic_validation.json`
- `operator_next_action.md`

Output rules:

- Raw provider responses are runtime artifacts only and must remain ignored.
- Repaired JSON must be written separately from raw JSON.
- Summary artifacts must include enough metadata for operator review without exposing secrets.
- `operator_next_action.md` may describe whether the operator can review, retry, or stop; it must not suggest a trade or market side.

## F. Safety Status Taxonomy

The adapter should use explicit terminal statuses:

- `dry_run_ready`
- `candidate_call_failed`
- `candidate_validation_failed`
- `candidate_valid_critic_skipped`
- `critic_call_failed`
- `critic_schema_failed`
- `critic_safety_failed`
- `completed_for_operator_review`
- `blocked_missing_api_key`
- `blocked_cost_cap`
- `blocked_secret_scan`
- `blocked_runtime_boundary`

Status meanings:

- `dry_run_ready`: Inputs, config, and boundaries are valid in dry-run mode.
- `candidate_call_failed`: The candidate model call failed before producing accepted content.
- `candidate_validation_failed`: Candidate output failed JSON, schema, or safety validation.
- `candidate_valid_critic_skipped`: Candidate validation passed, but critic call was intentionally skipped.
- `critic_call_failed`: The critic model call failed before producing accepted content.
- `critic_schema_failed`: Critic output did not satisfy `pmbot_openrouter_critic_response.v1`.
- `critic_safety_failed`: Critic schema passed, but one or more safety booleans or readiness fields failed.
- `completed_for_operator_review`: Candidate and critic validations passed; output is ready only for human review.
- `blocked_missing_api_key`: Network mode was requested without `OPENROUTER_API_KEY`.
- `blocked_cost_cap`: The configured cost cap blocked or stopped execution.
- `blocked_secret_scan`: A local secret scan found a disallowed token in candidate artifacts.
- `blocked_runtime_boundary`: Runtime, dispatcher, wallet, order, or trading boundary violation was detected.

## G. Non-Goals

This plan explicitly excludes:

- No autonomous trading bot.
- No Polymarket order execution.
- No wallet integration.
- No buy, sell, hold, enter, or exit recommendations.
- No probability or EV engine.
- No copy-trading.
- No automatic queue consumption.
- No browser automation.
- No prompt automation against web UIs.
- No dispatcher integration.
- No background autonomous operation.

## H. Testing Strategy

Required future tests:

- Dry-run does not require an API key.
- Missing API key blocks network call.
- Fake API key is not logged.
- Model, provider, usage, and cost are captured.
- Raw JSON fence is rejected without the repair flag.
- Repair flag writes repaired artifacts separately.
- Structured critic schema is required.
- Any `has_*` safety boolean set to `true` fails.
- `ready_for_trading_action=true` fails.
- Artifact path remains ignored.
- No runtime or dispatcher imports.
- No wallet or order imports.

Additional boundary tests:

- Network mode requires explicit manual confirmation.
- More than one prompt or packet per invocation is rejected unless separately approved.
- Downstream import is blocked unless candidate validation and critic validation both pass.
- Operator next action text is scanned for trading recommendations, side selection, probabilities, EV, edge, scoring, wallet access, and order instructions.

## I. Security And Git Hygiene

Security rules:

- OpenRouter API key source is env-only: `OPENROUTER_API_KEY`.
- No key may appear in git, logs, stdout, stderr, summaries, validation reports, or artifacts.
- Use a redaction helper for all user-visible and artifact-visible exception text.
- Runtime artifacts must remain ignored.
- Fixtures committed to git must be sanitized.
- No raw provider blobs in git.
- No secrets, wallet files, private keys, credential stores, browser profiles, or auth files may be read or touched.

Required staged secret scan command before commit. The disallowed patterns are deliberately assembled from fragments here so the committed plan does not make the scan match itself:

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

- Only safe mention of `OPENROUTER_API_KEY` as an environment variable name is allowed.
- No real API key.
- No credential header strings.
- No runtime artifact blobs tracked by git.

## J. Final Recommendation

Recommended next implementation task:

```text
PMBOT-OPENROUTER-009-DRY-RUN-ADAPTER-SHELL
```

The next task must be dry-run only and no network. It should implement only a local CLI shell that validates inputs, boundaries, config, and artifact destinations without calling OpenRouter and without importing runtime dispatcher, wallet, order, or trading code.
