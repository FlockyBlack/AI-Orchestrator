# PMBOT OpenRouter 005 Negated Yes/No Side False Positive Fix

Task: `PMBOT-OPENROUTER-005-NEGATED-YES-NO-SIDE-FALSE-POSITIVE-FIX`

## Purpose

Fix a critic validation false positive where safety-review prose that explicitly says the candidate does not select Yes/No was rejected as side selection.

The harness remains local, analysis-only, manual-review-only, operator-gated, and validator-gated. This patch does not add runtime wiring, dispatcher wiring, wallet access, order handling, automatic LLM loops, or trading authority.

## Validator Change

Forbidden-language validation still scans string values for PMBOT safety boundary terms, but side-selection matches now use the same local sentence context as other negative safety attestations.

Allowed only when the matched side-selection wording is clearly inside an absence, negation, or attestation scope:

- `The text does not select Yes/No or imply an outcome.`
- `Does not select Yes or No.`
- `No Yes/No side is selected.`
- `No Yes or No outcome is selected.`
- `No side is selected.`
- `No side selection detected.`
- `Does not choose a side.`
- `No outcome side is chosen.`
- `The candidate does not imply an outcome.`
- `No outcome estimate is provided.`

Still rejected:

- `Select Yes`
- `Select No`
- `Choose Yes`
- `Choose No`
- `The selected side is Yes`
- `The selected side is No`
- `YES is the side`
- `NO is the side`
- `Outcome is Yes`
- `Outcome is No`
- `I would choose Yes`
- `I would choose No`
- `The market should resolve Yes`
- `The market should resolve No`
- `Likely Yes`
- `Likely No`

Bad negated or bypass phrasing remains rejected, including:

- `No reason not to select Yes`
- `No downside to choosing Yes`
- `No issue selecting No`
- `Do not avoid choosing Yes`
- `Not selecting No would be wrong`

## Saved Artifact Regression

The saved critic content artifact at `pm_bot/llm/openrouter_test_artifacts/openrouter_critic_563650_content.json` is validated locally without network calls. Its raw content now validates with:

- `valid=true`
- `forbidden_language_absent=true`

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
