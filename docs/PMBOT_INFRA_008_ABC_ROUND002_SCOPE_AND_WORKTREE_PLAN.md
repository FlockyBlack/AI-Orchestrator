# PMBOT INFRA-008 ABC Round002 Scope and Worktree Plan

Task: `PMBOT-INFRA-008-ABC-ROUND002-SCOPE-AND-WORKTREE-MATERIALIZATION`

Status: `completed_ready_for_review`

## Base Confirmation

- Canonical root: `C:\Users\OpenC\Documents\AI-Orchestrator`
- Main branch confirmed: `main`
- Main was clean before INFRA-008 materialization.
- Current base commit: `c3962ed19b3e1e3d453f2569762fc7269378bebe`
- Current `origin/main` commit: `c3962ed19b3e1e3d453f2569762fc7269378bebe`
- Local `main` and `origin/main` were aligned before worktree creation.
- The base commit is the INFRA-007 portability fix commit and a direct safe descendant of the prior round001 integration base.

## Why Round002 Is Product-Focused

Round001 established deterministic offline contracts for paper accounting, dashboard state export, and manual operator commands. INFRA-007 then removed the isolated-worktree fixture and path portability blockers exposed by round001 validation.

Round002 should therefore move back to bounded product-contract work instead of another infrastructure-only round. The work remains offline and deterministic, but each lane now extends a user-facing PMBOT contract:

- CODEX_A expands accounting audit coverage from one lifecycle to a batch or multi-record review.
- CODEX_B extends dashboard state export so product status can point at paper audit summaries and safety warnings.
- CODEX_C extends operator command contracts into an inert local inbox/review queue for batches of manual command records.

This is still not runtime enablement. No lane may add live data fetching, automation, API/network behavior, wallet/auth behavior, trading behavior, autonomous paper orders, scoring, recommendations, probability, EV, edge, truth inference, or market-decision logic.

## Branches and Worktrees

| Lane | Task | Branch | Worktree |
| --- | --- | --- | --- |
| CODEX_A | `PMBOT-PAPER-018-MULTI-RECORD-PAPER-ACCOUNTING-BATCH-AUDIT` | `codex/a-paper-accounting-batch-audit-round002` | `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_A_round002_paper_batch_audit` |
| CODEX_B | `PMBOT-DASHBOARD-002-PORTFOLIO-AUDIT-STATE-EXPORT` | `codex/b-dashboard-portfolio-audit-state-round002` | `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_B_round002_dashboard_portfolio_state` |
| CODEX_C | `PMBOT-OPERATOR-002-MANUAL-COMMAND-INBOX-REVIEW-QUEUE` | `codex/c-operator-command-inbox-round002` | `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_C_round002_operator_command_inbox` |
| INTEGRATION | round002 merge/review only | `integration/pmbot-abc-feature-round002` | `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\INTEGRATION_round002_pmbot_abc` |

Each branch and worktree was created from `origin/main` at `c3962ed19b3e1e3d453f2569762fc7269378bebe`.

## Collision Checks

No preferred round002 branch collisions were detected before materialization:

- `codex/a-paper-accounting-batch-audit-round002`: no local branch, no remote-tracking branch.
- `codex/b-dashboard-portfolio-audit-state-round002`: no local branch, no remote-tracking branch.
- `codex/c-operator-command-inbox-round002`: no local branch, no remote-tracking branch.
- `integration/pmbot-abc-feature-round002`: no local branch, no remote-tracking branch.

No preferred round002 worktree path collisions were detected before materialization:

- `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_A_round002_paper_batch_audit`
- `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_B_round002_dashboard_portfolio_state`
- `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_C_round002_operator_command_inbox`
- `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\INTEGRATION_round002_pmbot_abc`

No suffixed alternatives were required.

## CODEX_A Scope

Task: `PMBOT-PAPER-018-MULTI-RECORD-PAPER-ACCOUNTING-BATCH-AUDIT`

Allowed scope:

- Extend deterministic offline paper/accounting audit coverage from one lifecycle to batch or multi-record accounting review.
- Reconcile multiple local manual paper records when fixtures already exist, or create small deterministic synthetic fixtures when needed.
- Verify record counts, lifecycle links, accounting summaries, artifact pointers, warnings, and safety flags.
- Produce local deterministic artifacts and focused tests inside the assigned lane scope.

Forbidden boundaries:

- No strategy logic.
- No side, size, price, market selection, recommendation, ranking, or market decision.
- No probability, EV, edge, scoring, or truth inference.
- No autonomous paper orders.
- No real orders, live trading, trading endpoints, wallet/private-key access, credentials, authenticated endpoints, or live fetchers.
- No network/API behavior.
- No dispatcher, `run_codex`, runtime queue, prompt automation, dashboard runtime, Telegram runtime, or Codex copy-root changes.

## CODEX_B Scope

Task: `PMBOT-DASHBOARD-002-PORTFOLIO-AUDIT-STATE-EXPORT`

Allowed scope:

- Extend the local dashboard state export contract to include round001 and round002 paper audit summaries.
- Expose product status, artifact pointers, accounting-only metrics, warnings, and safety flags.
- Keep output deterministic and local-file based.
- Produce local deterministic artifacts and focused tests inside the assigned lane scope.

Forbidden boundaries:

- No dashboard server, frontend, browser automation, websocket, polling loop, hosted service, or runtime wiring.
- No live API, network call, authenticated endpoint, external data fetcher, credentials, wallet access, trading endpoint, real order, or live trading behavior.
- No scoring, probability, EV, edge, recommendation, truth inference, side/size selection, autonomous paper order, or market-decision behavior.
- No Telegram/operator command execution wiring.
- No dispatcher or `run_codex` edits.

## CODEX_C Scope

Task: `PMBOT-OPERATOR-002-MANUAL-COMMAND-INBOX-REVIEW-QUEUE`

Allowed scope:

- Build an inert local operator command inbox/review queue contract from manual command records.
- Validate batches of manual command records.
- Classify commands as `accepted`, `rejected`, or `needs_human_review`.
- Keep all records deterministic, local, and non-executing.
- Produce local deterministic artifacts and focused tests inside the assigned lane scope.

Forbidden boundaries:

- No command execution.
- No Telegram runtime, bot token, polling, webhook, background automation, or live operator integration.
- No network/API behavior, credentials, authenticated endpoints, wallet/private-key access, trading endpoints, real orders, or live trading behavior.
- No autonomous paper orders.
- No scoring, probability, EV, edge, recommendation, truth inference, side/size selection, or market-decision behavior.
- No dispatcher, `run_codex`, runtime queue, prompt automation, or Codex copy-root changes.

## Explicit Reuse Warning

Do not reuse round001 branches, round001 worktrees, pilot branches, INFRA-004 demo branches, or demo worktrees for round002 feature work.

Round002 feature work must happen only in the fresh round002 lane worktrees listed in this plan. Round001 and demo branches remain historical context and must not be repurposed.

## Expected Result JSON Fields

Each CODEX_A/B/C lane should produce a result JSON in `docs/` with these fields at minimum:

- `task_id`
- `codex_lane`
- `status`
- `summary`
- `branch`
- `worktree_path`
- `base_commit`
- `head_commit`
- `files_created`
- `files_modified`
- `commands_run`
- `tests`
- `json_parse_checks`
- `git_status_before`
- `git_status_after`
- `pushed`
- `safety_flags`
- `forbidden_changes_detected`
- `warnings`
- `blockers`
- `next_action`

The result JSON must classify any warnings honestly and must not mark a lane ready if tests fail due to lane behavior or if a safety boundary is crossed.

## Required Tests Per Lane

Common requirements for all lanes:

- Confirm correct branch, base commit, and clean worktree before changes.
- Run the smallest relevant focused tests first.
- Parse the lane result JSON.
- Run `git diff --check`.
- Confirm final worktree cleanliness after committing lane work.
- Record exact commands and outcomes.

CODEX_A required tests:

- Focused batch/multi-record accounting audit tests.
- `python -m pytest pm_bot\paper\tests -q`

CODEX_B required tests:

- Focused dashboard export/contract tests.
- JSON parse checks for new dashboard/result artifacts.
- `python -m pytest pm_bot\dashboard\tests -q`
- `python -m pytest pm_bot\paper\tests -q` if PMBOT paper artifacts or paper-derived fixtures are touched.

CODEX_C required tests:

- Focused operator inbox/review queue contract tests.
- JSON parse checks for new operator/result artifacts.
- `python -m pytest pm_bot\operator\tests -q`
- `python -m pytest pm_bot\paper\tests -q` if PMBOT paper artifacts or manual paper records are touched.

Integration required tests after accepted lane merges:

- Parse all accepted lane result JSON files.
- Parse all new JSON artifacts introduced by accepted lanes.
- Run `python -m pytest pm_bot\paper\tests -q`.
- Run `python -m pytest pm_bot\dashboard\tests pm_bot\operator\tests -q`.
- Run any focused tests named by lane results.
- Run forbidden-change and changed-path safety scans.
- Run `git diff --check`.

## Integration Branch Usage

Use `integration/pmbot-abc-feature-round002` only for review and merge orchestration after CODEX_A, CODEX_B, and CODEX_C have each produced committed lane results.

Recommended merge/review flow:

1. Keep feature implementation out of `main`.
2. CODEX_A/B/C work independently in their assigned round002 worktrees.
3. Each lane commits only its assigned artifacts and pushes only when its result is ready.
4. Integration reads each lane result JSON before merging.
5. Integration checks write scope, result status, tests, safety flags, and final cleanliness.
6. Integration merges accepted lanes one at a time, running focused checks after each merge when practical.
7. Integration stops on merge conflicts, overlapping write scopes, missing result JSON, dirty worktrees, failed tests caused by lane behavior, or safety boundary expansion.
8. Integration pushes the integration branch only after accepted merges and validation.
9. Main merge remains a separate explicit review task.

## Stop Conditions

Stop and report blocked if any of these occur:

- Wrong root or wrong branch.
- Dirty `main` before task changes.
- Local `main` and `origin/main` divergence that cannot be resolved by a safe fast-forward.
- Any new worktree is not based on current `origin/main`.
- Any new worktree is dirty immediately after creation.
- Any branch or path collision cannot be handled with a safe suffixed alternative.
- Isolated worktree paper suite fails due to a portability regression.
- Runtime, dispatcher, `run_codex`, prompt automation, or queue/state changes become necessary.
- Network/API, live fetcher, authenticated endpoint, credential, wallet/private-key, trading, real order, live trading, or autonomous paper-order behavior becomes necessary.
- Scoring, probability, EV, edge, recommendation, truth inference, side/size selection, or market-decision behavior becomes necessary.
- A lane starts feature implementation from `main`.
- A lane touches outside its assigned scope.
- Push requires force, history rewrite, destructive cleanup, or branch deletion.
- Any safety boundary change is detected.

## INFRA-008 Validation

Canonical root validation:

- `python -m pytest pm_bot\paper\tests -q`: `310 passed, 39 subtests passed`
- `python -m pytest pm_bot\dashboard\tests pm_bot\operator\tests -q`: `33 passed, 14 subtests passed`

Isolated worktree validation:

- Worktree: `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\CODEX_A_round002_paper_batch_audit`
- Command: `python -m pytest pm_bot\paper\tests -q`
- Result: `309 passed, 1 skipped, 39 subtests passed`

Generated test churn in `docs/PMBOT_PAPER_017_RESULT.json` was restored in both the main checkout and CODEX_A validation worktree. No product/runtime files were changed by INFRA-008.
