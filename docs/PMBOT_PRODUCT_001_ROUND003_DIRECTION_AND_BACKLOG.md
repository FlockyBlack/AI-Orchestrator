# PMBOT PRODUCT-001 Round003 Direction And Backlog

Task: PMBOT-PRODUCT-001-ROUND003-DIRECTION-AND-BACKLOG-SELECTION

Status: completed_ready_for_review

Canonical root: `C:\Users\OpenC\Documents\AI-Orchestrator`

Base reviewed: `bad252594a92cd90f05bf7babb9a6011f1b2ec5e`

## Current Product Status After Round002

Round002 left PMBOT with a safe offline/local/paper/accounting-only baseline:

- PAPER-018 provides deterministic multi-record paper accounting batch audit over three records.
- DASHBOARD-002 and DASHBOARD-002A provide deterministic local dashboard state export and optional artifact presence compatibility.
- OPERATOR-002 provides an inert local manual command inbox/review queue.
- Existing paper surfaces include manual intent, fill/settlement, accounting PnL, portfolio metrics, reconciliation audit, and batch audit artifacts.
- Existing operator surfaces include manual command validation, static review artifacts, and an inert inbox review report.

The product still does not choose a market, side, size, probability, EV, edge, or order by itself. The prior `+6.00` value remains accounting-only fixture/manual PnL, not strategy profitability.

## Current Safety Boundaries

Round003 should remain docs/contracts/artifacts only until a separate implementation task starts. The selected work must stay offline, local, deterministic, inert, and review-only.

Do not add or enable:

- live fetchers, network/API calls, authenticated endpoints, credentials, API keys, wallet/private-key access, signing, trading endpoints, real orders, live trading, or autonomous paper orders
- betting recommendations, truth inference, market scoring, probability estimates, EV calculations, edge calculations, side recommendations, sizing recommendations, market decisions, or autonomous paper decisions
- dashboard server/frontend/runtime, Telegram runtime/token/webhook/polling, command execution, dispatcher edits, `run_codex` edits, prompt automation, Codex copy roots, completed dossiers, or broad refactors

Allowed round003 implementation lanes should only read existing local artifacts, write deterministic local artifacts/contracts/tests inside assigned scopes, and produce result docs.

## Product Gap Analysis

The most important gap after round002 is not more accounting math. It is operator comprehension and artifact readiness.

The current useful state is spread across paper, dashboard, and operator outputs. An operator must know which artifacts matter, whether they parse, whether the dashboard preview is current relative to newly present docs, what the paper/accounting audit status means, and which inert inbox records are waiting for human review. The repo already contains many local artifacts, but there is no single round002-aware review pack that composes them into one deterministic operator-facing artifact-status surface.

This gap matters because PMBOT is intentionally not autonomous. The human operator is the control boundary, so the next product value should make manual review safer, faster, and less ambiguous without adding decisions or runtime.

## Evaluated Round003 Options

1. Operator Workbench / Review Pack v1
   - Verdict: recommended.
   - Reason: directly addresses the operator comprehension gap while staying offline, deterministic, local, and inert.
   - Useful outputs: one JSON/Markdown review pack, artifact pointers, audit status summary, dashboard state summary, inbox summary, stale/missing warnings, and safe manual review actions.
   - Boundary: no recommendations, no market/side/size/probability/EV/edge, no runtime.

2. More paper/accounting expansion
   - Verdict: defer.
   - Reason: PAPER-017 and PAPER-018 already provide single-record reconciliation and multi-record batch audit coverage. More accounting fixtures would add depth but would not solve the immediate problem that existing state is scattered and hard to review.
   - Safe later use: expand after the review pack reveals concrete missing accounting views.

3. Dashboard/server/UI runtime
   - Verdict: reject for round003.
   - Reason: server/frontend/runtime work changes the risk boundary and is unnecessary while the artifact contract is still being consolidated.
   - Required before reconsideration: Flocky/OpenClaw review, explicit runtime scope, and no trading or live/API coupling.

4. Telegram/operator runtime
   - Verdict: reject for round003.
   - Reason: OPERATOR-002 intentionally stopped at an inert local inbox/review queue. Telegram webhook/polling/token/runtime or command execution would cross a high-risk boundary.
   - Safe substitute: static command-to-review-pack contract only.

5. Read-only live refresh loop
   - Verdict: reject for round003.
   - Reason: even read-only live refresh introduces network/API/runtime behavior and risks being mistaken for live market truth. The current need is local artifact health and review composition.
   - Required before reconsideration: explicit live-data boundary review and a separate approved task.

## Recommended Round003 Direction

Build Operator Workbench / Review Pack v1.

Round003 should create one local operator-facing review pack that composes existing PMBOT artifacts and explains their state without creating decisions. The pack should summarize:

- paper accounting reconciliation and batch audit status
- dashboard portfolio/accounting/audit state
- operator inbox/review queue status
- artifact pointers and parse status
- stale or missing artifact warnings
- safe manual operator actions such as review artifact, inspect pointer, rerun local tests, or mark inbox record for human review

The review pack must not say what to trade, what market to choose, what side to take, what size to use, whether a market is true, or whether a trade has positive EV. It should be an operating checklist and artifact map, not a strategist.

## Proposed A/B/C Scopes

### CODEX_A

Task: `PMBOT-WORKBENCH-001-OPERATOR-REVIEW-PACK-EXPORT`

Scope:

- create a deterministic local JSON and Markdown operator review pack
- compose existing dashboard state, paper reconciliation/batch audits, portfolio/accounting metrics, and operator inbox review outputs
- include artifact pointers, parse status, high-level audit status, inbox counts, stale/missing warnings, and safe manual review actions
- write in a new narrow scope such as `pm_bot/workbench/` plus exact result docs

Forbidden:

- no decisions, recommendations, probability, EV, edge, market scoring, truth inference, side/size/market selection, live data, runtime, command execution, or autonomous paper orders

### CODEX_B

Task: `PMBOT-QUALITY-001-ARTIFACT-HEALTH-AND-STALENESS-CHECK`

Scope:

- create a deterministic local artifact health/staleness report
- check required and optional artifacts for existence, JSON parseability, schema/version fields, expected fixture alignment, and embedded pointer freshness where feasible
- explicitly surface stale generated artifacts when current filesystem presence differs from embedded artifact presence/status fields
- write in a new narrow scope such as `pm_bot/quality/` plus exact result docs

Forbidden:

- no live fetch, no scoring, no market decisions, no recommendations, no runtime, no artifact regeneration unless explicitly in scope

### CODEX_C

Task: `PMBOT-OPERATOR-003-REVIEW-PACK-COMMAND-BRIDGE-CONTRACT`

Scope:

- define a static, inert contract mapping existing manual command inbox command types to review-pack sections
- keep commands as records for human review only
- include examples and tests showing that command records can request status summaries, artifact pointers, or human-review markings without execution authority
- write in `pm_bot/operator/` plus exact result docs

Forbidden:

- no Telegram runtime, token handling, webhook, polling, command execution, dispatch wiring, API calls, trading, recommendations, or market decisions

## Dependency Map

- CODEX_A depends on existing round002 artifacts from PAPER-018, DASHBOARD-002/002A, and OPERATOR-002.
- CODEX_B depends on the same existing artifact inventory and can run in parallel with CODEX_A if it writes only its own quality/health files.
- CODEX_A should treat CODEX_B health output as optional if referenced at all, using the DASHBOARD-002A pattern for present/absent compatibility.
- CODEX_C depends on stable review-pack section identifiers. It can define the contract in parallel if CODEX_A reserves section IDs in its contract, but integration should validate CODEX_C after CODEX_A is merged.
- Recommended integration order: CODEX_B, then CODEX_A, then CODEX_C. If CODEX_A does not consume CODEX_B, CODEX_A and CODEX_B may be merged in either order, but both must be rerun after the combined merge.

## Required Validation Per Lane

Common lane checks:

- confirm branch/worktree/root and clean pre-change status
- parse each new result JSON and artifact JSON
- run focused tests for any new deterministic exporter/checker/contract
- run `python -m py_compile` over new Python files
- run `git diff --check`
- confirm no dispatcher, `run_codex`, runtime, secrets, network/API, wallet, trading, scoring, recommendation, or market-decision changes
- stage exact files only; never use `git add .`

CODEX_A checks:

- focused workbench/review-pack tests
- review-pack JSON parse and Markdown deterministic snapshot check
- `python -m pytest pm_bot\paper\tests -q`
- `python -m pytest pm_bot\dashboard\tests pm_bot\operator\tests -q`

CODEX_B checks:

- focused artifact health/staleness tests
- JSON parse checks for health report and expected fixture
- tests proving missing, present, stale, and parse-failed artifacts are classified deterministically
- dashboard/operator/paper suites if the lane imports or reads their helper modules in a way that could change expectations

CODEX_C checks:

- focused review-pack command bridge contract tests
- `python -m pytest pm_bot\operator\tests -q`
- JSON parse checks for contract/examples/result docs
- tests proving all command bridge records remain non-executing and require human review

## Integration And Rehearsal Requirements

Before merging round003 to main:

- read all accepted lane result JSON files
- verify each lane stayed inside its assigned write scope
- confirm no overlapping writes except exact docs/result files approved for each lane
- parse all new JSON artifacts and result docs
- run all focused tests named by lane results
- run `python -m pytest pm_bot\paper\tests -q`
- run `python -m pytest pm_bot\dashboard\tests pm_bot\operator\tests -q`
- run `python -m py_compile` over new Python files
- run `git diff --check`
- run a forbidden-change scan over changed files for live/API/auth/wallet/trading/runtime/scoring/recommendation/decision/dispatcher strings and path families
- confirm any generated artifact churn is either expected lane output or restored before integration commit
- confirm final worktree is clean after commit and push

## Flocky/OpenClaw Escalation Criteria

Flocky/OpenClaw validation is not needed now because the selected direction is local deterministic docs/artifacts only and does not change a risk boundary.

Escalate before implementation if any round003 lane proposes:

- live/API/network behavior, authenticated data, credentials, wallet access, signing, trading, real orders, or autonomous paper orders
- dashboard runtime/server/frontend/browser automation, Telegram runtime/token/webhook/polling, command execution, dispatcher edits, `run_codex` edits, prompt automation, or background automation
- probability, EV, edge, market scoring, side/size/market selection, truth inference, recommendations, or completed dossiers
- broad refactor or shared runtime/config changes

## Do Not Build Yet

- dashboard server, frontend, browser UI, websocket, hosted dashboard, or runtime loop
- Telegram bot runtime, token handling, webhook/polling, or command execution
- read-only live market refresh loop or any network/API fetcher
- wallet/private-key/authenticated endpoint handling
- real orders, live trading, trading endpoints, or autonomous paper orders
- probability estimates, EV calculations, edge calculations, scoring, ranking, recommendation, truth inference, side/size selection, or market selection
- completed dossiers or any artifact that implies PMBOT selected a market to act on
- dispatcher, `run_codex`, prompt automation, or Codex copy root changes
- broad refactors or cross-lane shared code changes

## Recommended Next Task

`PMBOT-INFRA-009-ABC-ROUND003-WORKTREE-MATERIALIZATION`

Purpose:

- prepare round003 branches and worktrees only; do not implement features
- start from current `origin/main` after PRODUCT-001 is reviewed and pushed
- confirm canonical root, `main`, clean status, fetch origin, and no divergence
- create fresh disjoint worktrees for:
  - CODEX_A: `codex/a-workbench-review-pack-round003`
  - CODEX_B: `codex/b-artifact-health-staleness-round003`
  - CODEX_C: `codex/c-review-pack-command-bridge-round003`
  - Integration: `integration/pmbot-abc-feature-round003`
- use preferred paths under `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees`:
  - `CODEX_A_round003_workbench_review_pack`
  - `CODEX_B_round003_artifact_health`
  - `CODEX_C_round003_review_pack_command_bridge`
  - `INTEGRATION_round003_pmbot_abc`
- run baseline paper and dashboard/operator tests after materialization
- document branch/path collision checks and safety flags
