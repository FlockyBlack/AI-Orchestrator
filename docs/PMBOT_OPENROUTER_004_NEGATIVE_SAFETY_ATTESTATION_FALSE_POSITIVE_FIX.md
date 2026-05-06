# PMBOT OpenRouter 004 Negative Safety Attestation False Positive Fix

Task: `PMBOT-OPENROUTER-004-NEGATIVE-SAFETY-ATTESTATION-FALSE-POSITIVE-FIX`

## Purpose

Fix a critic validation false positive where safety-review prose that says prohibited content is absent was rejected because it named the prohibited categories.

The OpenRouter harness remains local, manual, operator-gated, and validator-gated. This patch does not add runtime wiring, dispatcher wiring, wallet access, order handling, automatic LLM loops, or trading authority.

## Validator Change

Forbidden phrase detection now checks the local sentence context before emitting a safety error.

Allowed only when clearly scoped as negative safety attestation, absence, non-actionability, or avoidance:

- `No side selection, outcome estimate, EV, edge, trade execution, wallet, or order instructions are present.`
- `No EV, edge, wallet, or order instructions are present.`
- `No trading recommendations detected.`
- `No side selection detected.`
- `No wallet instructions detected.`
- `No order instructions detected.`
- `The candidate avoids market-decision language.`
- `The artifact is not ready for market-resolution analysis.`
- `It is not suitable for resolution, market decisioning, or automated workflow progression.`
- `not actionable`
- `do_not_trade`
- `not_actionable`
- `ready_for_resolution_or_action: false`

Still rejected:

- Buy, sell, hold, enter, or exit language.
- Side selection such as selecting YES or NO.
- Recommended sides, outcomes, trades, positions, entries, exits, orders, or market decisions.
- EV, edge, scoring, probability, or outcome-estimate assertions.
- Order placement/submission/creation language.
- Wallet, private-key, seed-phrase, or credential use language.
- Bypass phrasing such as `No reason not to buy YES`, `No downside to selecting YES`, `No problem using wallet credentials`, `No issue placing an order`, or `No need to avoid trading`.

The allowance is intentionally narrow: the matched forbidden term must sit inside a local negative/absence/avoidance scope, and unsafe action context cancels the allowance.

Follow-up `PMBOT-OPENROUTER-005` extends the same local-context rule to negated Yes/No side-selection attestations such as `The text does not select Yes/No or imply an outcome.` Actual side selection, likely Yes/No language, and bad negated bypass phrasing remain rejected.

## Critic Prompt

The critic prompt now asks the critic to prefer fixed boolean safety fields:

- `no_trading_recommendations_detected`
- `no_side_selection_detected`
- `no_ev_or_edge_detected`
- `no_wallet_or_order_instructions_detected`

The validator still handles prose safely because model output may not follow the preferred shape.

## Saved Artifact Regression

The saved critic artifact at `pm_bot/llm/openrouter_test_artifacts/openrouter_critic_563650_content.json` is used as a no-network regression by validating its `raw_content` field. The previously rejected negative attestation now validates as safe JSON while actual market-action language remains blocked.

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
