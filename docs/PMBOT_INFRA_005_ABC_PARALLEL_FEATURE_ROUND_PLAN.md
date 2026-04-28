# PMBOT INFRA-005 ABC Parallel Feature Round Plan

## Purpose

This document defines the planning and contract layer for the first real PMBOT parallel Codex A/B/C feature round. It does not create feature branches, create worktrees, implement feature code, add runtime wiring, or start dashboard/Telegram/live/API behavior.

The next task may materialize these branches and worktrees only after review.

## Base Assumptions

- Canonical root: `C:\Users\OpenC\Documents\AI-Orchestrator`
- Current planning branch: `main`
- Base commit detected for this plan: `f2e9e96e2fb5099146676408a4aba5dcd6d7da67`
- `origin/main` detected for this plan: `f2e9e96e2fb5099146676408a4aba5dcd6d7da67`
- Local `main` was clean before INFRA-005 docs were created.
- Preferred branch names had no detected local or remote-tracking collision during planning.
- Preferred worktree paths had no detected filesystem collision during planning.
- Existing INFRA-004 demo branches are demo-only and must not be used for real feature work.
- Older pilot worktrees from earlier infrastructure work must not be deleted or repurposed by the feature round.

## Fresh Branch Names

Create these branches from current `origin/main` in the later materialization task:

- CODEX_A: `codex/a-paper-accounting-reconciliation-round001`
- CODEX_B: `codex/b-dashboard-state-contract-round001`
- CODEX_C: `codex/c-operator-command-contract-round001`
- Integration: `integration/pmbot-abc-feature-round001`

Do not create these branches from INFRA-004 demo branches, older pilot branches, or local stale commits.

## Fresh Worktree Paths

Create these worktrees in the later materialization task:

- CODEX_A: `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_A_round001_paper_accounting`
- CODEX_B: `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_B_round001_dashboard_state`
- CODEX_C: `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_C_round001_operator_contract`
- Integration: `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\INTEGRATION_round001_pmbot_abc`

If a path exists later, do not delete it. Stop, document the collision, and choose a safe suffixed alternative such as `_v2` only with explicit operator approval in the materialization task.

## CODEX_A Scope

Theme: `PMBOT-PAPER-017-PAPER-ACCOUNTING-RECONCILIATION-OR-LIFECYCLE-AUDIT`

Allowed concept:

- Reconcile existing paper fill, settlement, PnL, accounting ledger, portfolio snapshot, and metrics artifacts.
- Produce deterministic local accounting or lifecycle audit artifacts.
- Add focused tests for the deterministic audit artifacts if implementation is later authorized.
- Preserve the interpretation that the current `+6.00` is accounting-only PnL from operator-manual fixtures, not strategy profitability.

Allowed file/path patterns:

- `pm_bot/paper/*accounting*`
- `pm_bot/paper/*portfolio*`
- `pm_bot/paper/*metrics*`
- `pm_bot/paper/*fill*`
- `pm_bot/paper/*settlement*`
- `pm_bot/paper/*pnl*`
- `pm_bot/paper/*lifecycle*`
- `pm_bot/paper/expected_*`
- `pm_bot/paper/tests/test_*`
- `docs/PMBOT_PAPER_017_*`
- `docs/PMBOT_PAPER_BATCH_017_*`

Forbidden in CODEX_A:

- Any side, size, price, market, probability, EV, edge, score, recommendation, ranking, truth inference, or market-decision logic.
- Any real/live/autonomous paper order creation.
- Any network/API/live fetcher/auth/trading/wallet endpoint.
- Any runtime, dispatcher, queue, prompt automation, or `run_codex` wiring.
- Any dashboard runtime or Telegram runtime.
- Any completed dossier creation.

## CODEX_B Scope

Theme: `PMBOT-DASHBOARD-001-DASHBOARD-STATE-EXPORT-CONTRACT`

Allowed concept:

- Define or export deterministic local dashboard state from existing PMBOT artifacts.
- Contract outputs may be JSON, Markdown, schema-like docs, or focused tests if implementation is later authorized.
- The dashboard state must describe existing artifact state only; it must not make recommendations or infer truth.

Allowed file/path patterns:

- `pm_bot/dashboard_contracts/**`
- `pm_bot/dashboard_state/**`
- `pm_bot/paper/dashboard_*`
- `pm_bot/paper/*dashboard*`
- `pm_bot/paper/expected_*dashboard*`
- `pm_bot/paper/tests/test_*dashboard*`
- `docs/PMBOT_DASHBOARD_001_*`

Forbidden in CODEX_B:

- Dashboard server, web runtime, frontend app, browser automation, websocket, polling loop, or hosted service.
- Any live API, network call, authenticated endpoint, or external data fetcher.
- Any scoring, probability, EV, edge, recommendation, truth inference, side/size selection, or autonomous paper order behavior.
- Any Telegram/operator command execution wiring.
- Any dispatcher or `run_codex` edit.

## CODEX_C Scope

Theme: `PMBOT-OPERATOR-001-MANUAL-COMMAND-CONTRACT`

Allowed concept:

- Define manual operator command envelopes and result contracts.
- Telegram-oriented wording is allowed only as a static contract.
- Contracts may define input/output envelopes, validation expectations, Markdown docs, JSON fixtures, and tests if implementation is later authorized.

Allowed file/path patterns:

- `pm_bot/operator_contracts/**`
- `pm_bot/operator_commands/**`
- `pm_bot/paper/operator_*`
- `pm_bot/paper/manual_*`
- `pm_bot/paper/expected_*operator*`
- `pm_bot/paper/tests/test_*operator*`
- `docs/PMBOT_OPERATOR_001_*`

Forbidden in CODEX_C:

- Telegram runtime, bot token handling, Telegram network calls, webhook/polling loop, background automation, or command execution wiring.
- Any credential, auth, wallet, trading, or external API behavior.
- Any runtime, dispatcher, queue, prompt automation, or `run_codex` edit.
- Any scoring, probability, EV, edge, recommendation, truth inference, market decision, side/size selection, or autonomous paper order behavior.

## Shared Forbidden Files and Paths

No lane may edit these files or path families unless a later task explicitly grants integration/safety authority:

- `.env*`
- credential stores, browser profiles, wallets, keys, token files, or auth files
- `.git/**`
- `.github/**` unless the task is explicitly GitHub workflow maintenance
- `.agents/**`
- `scripts/dispatcher.py`
- `scripts/run_codex.py`
- runtime queue/state directories
- broad project config files such as `pyproject.toml`, lockfiles, package manifests, or global config
- unrelated PMBOT source outside the assigned lane scope
- INFRA-004 demo branch docs as a source of feature work

## Safe Parallel Work

These tasks are safe to run in parallel when each lane is created from the same current `origin/main`, starts clean, and writes only inside its assigned scope:

- CODEX_A deterministic accounting/lifecycle audit artifacts.
- CODEX_B deterministic local dashboard state contract artifacts.
- CODEX_C manual operator command contract artifacts.
- Read-only inspection of shared PMBOT docs and paper artifacts.
- Per-lane focused tests that do not mutate shared state outside the lane worktree.

## Work That Must Not Run in Parallel

Run these as serial integration or safety tasks only:

- Edits to shared runtime, dispatcher, `run_codex`, automation, queue/state, prompts, or global config.
- Edits that require overlapping file paths across lanes.
- Any merge conflict resolution.
- Any branch cleanup, worktree deletion, branch deletion, or history rewrite.
- Any network/API/live fetcher, Telegram runtime, dashboard runtime, wallet/auth/trading, or real/live order work.
- Any feature that changes public contracts shared by another active lane.

## Integration Branch and Review Flow

1. Materialize all feature branches and worktrees from the same reviewed `origin/main` commit.
2. Run CODEX_A, CODEX_B, and CODEX_C in separate worktrees with isolated write scopes.
3. Each lane must produce a result JSON that conforms to `docs/PMBOT_INFRA_005_CODEX_PARALLEL_RESULT_CONTRACT.v1.json`.
4. Each lane must leave its worktree clean after committing its own changes.
5. The integration task creates or uses `integration/pmbot-abc-feature-round001` from the same base commit.
6. Integration validates each lane result before merging.
7. Integration merges only accepted lane branches, one at a time, and reruns tests after each merge when practical.
8. Integration records rejected, blocked, or warning lane results without improvising a fix.

## Merge Order

Recommended merge order:

1. CODEX_A: core paper/accounting audit layer.
2. CODEX_B: dashboard state export contract layer.
3. CODEX_C: operator command contract layer.

If CODEX_B or CODEX_C depends on an artifact name introduced by CODEX_A, merge CODEX_A first and verify that the dependency is contract-only. If any lane requires code from another lane before review, mark the dependent lane blocked instead of merging unreviewed work.

## Push Policy

- Feature branches may be pushed normally only after the lane result is complete, tests are run or honestly reported, and the lane worktree is clean.
- The integration branch may be pushed normally only after accepted merges, forbidden-change scans, and final tests complete.
- Never force push.
- Never push from a dirty worktree.
- Never push demo branches for feature work.
- Never merge feature branches directly into `main` without a dedicated integration review task.

## Required Tests Per Lane

Every lane must run the smallest relevant tests first and record exact commands and outcomes.

Minimum common checks:

- Parse the lane result JSON.
- Check `git status --short --branch` before and after.
- Run a focused test for any added or changed deterministic artifact behavior.
- If any lane touches `pm_bot/paper`, run `python -m pytest pm_bot\paper\tests -q` unless the task explicitly narrows the test requirement and records why.

Lane expectations:

- CODEX_A: focused accounting/audit tests plus `python -m pytest pm_bot\paper\tests -q`.
- CODEX_B: focused dashboard contract/export tests, JSON parse checks, and paper tests if `pm_bot/paper` is touched.
- CODEX_C: focused operator contract tests, JSON parse checks, and paper tests if `pm_bot/paper` is touched.

## Final Integration Tests

Before the integration branch can be considered ready for review:

- Parse all accepted lane result JSON files.
- Parse all new JSON artifacts introduced by the accepted lanes.
- Run `python -m pytest pm_bot\paper\tests -q`.
- Run any focused tests named by lane results.
- Run a forbidden-change scan over changed files for safety-sensitive strings and path families.
- Confirm no real/live/autonomous order counts were introduced.

## Conflict Handling

- Stop on merge conflicts unless the integration prompt explicitly authorizes conflict resolution.
- Record the conflicting files, branches, and last successful merge.
- Do not auto-resolve conflicts by deleting one lane's work.
- If conflicts are caused by overlapping write scopes, mark the integration blocked and request a serial follow-up task.

## Dirty Worktree Handling

- If `main` is dirty before materialization, stop before creating worktrees.
- If a feature worktree is dirty before lane work starts, stop that lane and report blocked.
- If unexpected dirty files appear during a lane, record them and stop unless they are generated by the lane's own commands and are within scope.
- Do not clean unrelated files.
- Do not use `git add .`; stage exact files only.

## Failed Test Handling

- If a focused test fails, the lane may fix only files inside its assigned scope.
- If the full paper test suite fails for unrelated environment reasons, record the exact failure and mark `completed_with_warnings` only if focused tests and safety checks pass.
- If tests fail due to behavior changed by the lane, mark the lane `failed` or `blocked`; do not pass it to integration.
- Integration must not merge a failed lane unless a later task explicitly overrides the policy.

## Unexpected Safety Changes

Immediately mark `blocked` instead of improvising if any task appears to require:

- live fetchers, network/API calls, authenticated endpoints, or external services
- credentials, API keys, bot tokens, wallet/private-key access, or signing
- trading endpoints, real orders, live trading, or autonomous paper orders
- scoring, probability, EV, edge, side/size selection, recommendation, truth inference, or market decision logic
- runtime wiring, dispatcher edits, `run_codex` edits, prompt automation, or background automation
- broad refactors, completed dossiers, or Codex copy roots

Escalate to Flocky/OpenClaw only for explicit risk boundary changes. Do not escalate routine deterministic docs/contracts/test issues.

## Stop Conditions

Any of the following must trigger `blocked` instead of improvising:

- base branch or origin/main cannot be confirmed
- selected branch name already exists and no approved alternative is provided
- selected worktree path exists and no approved alternative is provided
- dirty `main` before branch/worktree materialization
- dirty or mismatched lane worktree before work starts
- overlapping write scopes
- feature work requires a forbidden file or path
- test failure caused by lane behavior
- secrets or high-risk credential shapes appear in changed files
- any safety boundary expansion appears necessary
- push requires force, history rewrite, or branch deletion
- demo branches appear in the real feature path

