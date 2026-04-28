# PMBOT INFRA-005 Integration Review Checklist

## Pre-Integration Checklist

- Confirm canonical root is `C:\Users\OpenC\Documents\AI-Orchestrator`.
- Fetch `origin main` read-only before materializing or reviewing integration work.
- Confirm `main` and `origin/main` base commits.
- Confirm integration branch is `integration/pmbot-abc-feature-round001`.
- Confirm CODEX_A, CODEX_B, and CODEX_C branches are fresh real feature branches, not INFRA-004 demo branches.
- Confirm no feature worktree path collision exists.
- Confirm all worktrees are clean before merge review starts.
- Confirm older pilot worktrees remain untouched.

## Per-Lane Result Validation

For each lane result JSON:

- Parse the JSON.
- Validate required fields from `docs/PMBOT_INFRA_005_CODEX_PARALLEL_RESULT_CONTRACT.v1.json`.
- Confirm `status` is `completed_ready_for_integration` or explicitly accepted with warnings.
- Confirm `base_commit` matches the reviewed round base commit unless the integration task explicitly approves a rebase.
- Confirm `branch`, `worktree_path`, and `head_commit`.
- Confirm `files_created` and `files_modified` match Git diff output.
- Confirm `git_status_before` and `git_status_after` are recorded.
- Confirm `pushed` is true only when normal push succeeded.
- Confirm `blockers` is empty for lanes proposed for merge.
- Confirm `next_action` is compatible with integration.

## Conflict Review

- Merge one lane at a time into the integration branch.
- Stop on the first conflict unless the integration prompt explicitly authorizes conflict resolution.
- Record conflicting branch names, files, and the last successful merge.
- Check whether the conflict indicates overlapping write scopes.
- Do not delete one lane's work to resolve a conflict.
- If overlap is material, mark integration blocked and request a serial follow-up.

## Forbidden-Change Scan

Review changed files across all accepted lanes for:

- `.env`, credentials, API keys, tokens, auth files, browser profiles, wallets, or private keys.
- Network/API calls, live fetchers, authenticated endpoints, or external services.
- Trading endpoints, real orders, live trading, order signing, or autonomous paper orders.
- Scoring, probability, EV, edge, recommendation, truth inference, market decision, side selection, or size selection logic.
- Runtime wiring, dispatcher edits, `run_codex` edits, queue/state automation, prompt automation, or background execution.
- Dashboard server/runtime, Telegram runtime, bot token handling, webhooks, polling, or browser automation.
- Completed dossiers, broad refactors, Codex copy roots, or unrelated source edits.

Any finding in this list blocks integration unless a later task explicitly expands the risk boundary.

## Test Checklist

- Parse each lane result JSON.
- Parse every new or modified JSON artifact introduced by accepted lanes.
- Run every focused test command reported by accepted lane results when practical.
- Run `python -m pytest pm_bot\paper\tests -q`.
- If tests fail, identify whether the failure was introduced by a lane.
- Do not merge a failed lane into `main`.
- If an environment-only failure blocks verification, record exact output and stop for operator review unless the prompt explicitly allows warning-level completion.

## Final Merge/Push Checklist

- Confirm integration branch is clean after all accepted merges and tests.
- Confirm no demo branch was merged.
- Confirm no force push is needed.
- Confirm all accepted lane commits are present in the integration branch.
- Confirm forbidden-change scan is clean.
- Confirm final paper tests pass or are honestly reported.
- Push the integration branch normally only after the review is complete.
- Do not merge integration into `main` unless a dedicated reviewed task explicitly authorizes it.

## Rollback and Stop Guidance

- Stop before destructive cleanup.
- Do not delete branches or worktrees during review unless a task explicitly asks for cleanup.
- Do not rewrite history.
- Do not force push.
- If an integration merge has not been pushed and is wrong, record the state and ask for a dedicated recovery task.
- If a pushed branch contains unsafe changes, stop and escalate; do not attempt hidden remediation.

## Flocky/OpenClaw Escalation

Escalate only for risk boundary changes, including:

- live/API/network/auth/wallet/trading behavior
- real orders, live trading, or autonomous paper orders
- scoring, probability, EV, edge, recommendation, truth inference, or market-decision behavior
- runtime wiring, dispatcher changes, `run_codex` changes, prompt automation, or background automation
- broad refactors or changes that alter public interfaces across lanes

Routine deterministic docs, contracts, fixture JSON, and focused tests should remain within the normal Codex integration review path.

