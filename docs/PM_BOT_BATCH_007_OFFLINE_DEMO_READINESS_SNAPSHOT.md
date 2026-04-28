# PMBOT Batch 007 Offline Demo Readiness Snapshot

Task ID: `PMBOT-BATCH-007-OFFLINE-DEMO-READINESS-SNAPSHOT`

Status: `completed_ready_for_review`

Scope: offline-only, paper-only, local-only, deterministic, review-only.

## Root Confirmed

- PMBOT root: `C:\Users\OpenC\Documents\AI-Orchestrator`
- PMBOT tree: `pm_bot/**`
- Canonical root used: `C:\Users\OpenC\Documents\AI-Orchestrator`
- Codex copy roots: not used

## Latest Accepted Local State

The latest local batch result files run through `PM_BOT_BATCH_010_RESULT.json`.

Current state is strongest as a demoable offline package when presented as:

- deterministic operator review and export bundle from `PMBOT-BATCH-006`;
- deterministic paper research demo from `PMBOT-BATCH-002` and later compatibility repairs;
- deterministic adversarial replay and safety validation from `PMBOT-BATCH-005`;
- deterministic design-only live/read-only boundary and fetcher planning from `PMBOT-BATCH-007` and `PMBOT-BATCH-008`;
- deterministic raw artifact validation and ingestion/quarantine manifest from `PMBOT-BATCH-010`.

No latest batch result claims live fetcher implementation, normalization implementation, network/API access, credentials, wallet use, real orders, trading, or runtime wiring.

## Demo Readiness Decision

Demo readiness: `ready_to_demo_now`

The current PMBOT tree can support a Monday demo as an offline/paper review package. It should be presented as a deterministic local review/demo, not as a live bot and not as production trading.

## Recommended Demo Package

### Primary Demo Commands

Run from `C:\Users\OpenC\Documents\AI-Orchestrator`:

```powershell
python pm_bot\demo\run_operator_review_demo.py
python pm_bot\export\build_review_export_package.py
python pm_bot\demo\run_paper_research_demo.py
python pm_bot\replay\run_adversarial_replay.py
python pm_bot\raw_artifacts\build_ingestion_manifest.py
python pm_bot\audit\static_safety_audit_v7.py
```

### Supporting Component Commands

```powershell
python pm_bot\paper\simulate_paper_plan.py pm_bot\paper\paper_plan_fixture.v1.json
python pm_bot\accounting\calculate_fee_slippage.py pm_bot\accounting\accounting_fixture.v1.json
python pm_bot\risk\evaluate_risk_limits.py pm_bot\risk\risk_fixture.v1.json
python pm_bot\reports\rejection_summary_report.py
```

### Verification Command

```powershell
python -m pytest pm_bot\operator\tests pm_bot\export\tests pm_bot\audit\tests pm_bot\demo\tests pm_bot\replay\tests pm_bot\reports\tests pm_bot\paper\tests pm_bot\accounting\tests pm_bot\risk\tests -q
```

Observed result: `121 passed`.

## Available Inputs

- `pm_bot/demo/demo_market_bundle.v1.json`
- `pm_bot/paper/paper_plan_fixture.v1.json`
- `pm_bot/accounting/accounting_fixture.v1.json`
- `pm_bot/risk/risk_fixture.v1.json`
- `pm_bot/adversarial/adversarial_replay_cases.v1.json`
- `pm_bot/raw_artifacts/fixtures/`
- `pm_bot/fixtures/`

## Available Output And Review Artifacts

- `pm_bot/demo/expected_operator_review_demo.v1.json`
- `pm_bot/demo/expected_operator_review_demo.v1.md`
- `pm_bot/demo/expected_paper_research_demo.v1.json`
- `pm_bot/demo/expected_paper_research_demo.v1.md`
- `pm_bot/export/expected_review_export_package.v1.json`
- `pm_bot/export/expected_review_export_package.v1.md`
- `pm_bot/operator/expected_operator_review_bundle.v1.json`
- `pm_bot/operator/expected_paper_candidate_review_table.v1.json`
- `pm_bot/operator/expected_watchlist_policy_report.v1.json`
- `pm_bot/operator/expected_risk_audit_summary.v1.json`
- `pm_bot/replay/expected_adversarial_replay_report.v1.json`
- `pm_bot/reports/expected_rejection_summary_report.v1.json`
- `pm_bot/raw_artifacts/expected_ingestion_manifest.v1.json`
- `pm_bot/audit/expected_static_safety_audit.v7.json`

## What The Demo Shows

- 4 accepted paper candidates in the operator bundle.
- 5 watchlist candidates, all no-action or review-only.
- 5 rejected candidates and excluded/rejected adversarial cases with explicit reasons.
- Paper simulation, accounting, and risk components are fixture-driven and execution-disabled.
- Adversarial replay passes 12 of 12 cases with 0 false positives.
- Raw artifact ingestion accepts 3 local fixtures and quarantines 9 invalid fixtures.
- Static safety audit v7 passes with 0 blocking findings.

## Safety Boundary

- No network/API calls.
- No live Polymarket API.
- No credentials.
- No wallet/private key/signing.
- No real orders.
- No real trading.
- No autonomous trading.
- No dispatcher/runtime integration.
- No OpenClaw runtime/task queue mutation.
- No Codex copy root edits.

## Limitations

- This is not a live bot demo.
- The operator checklist remains pending human review.
- Watchlist items cannot become accepted/live/order/trade candidates without separate future approval.
- Live/read-only fetcher work is still design-only; no live fetcher or normalization implementation exists in the latest result.
- The most practical Monday demo is a local CLI walkthrough plus expected JSON/Markdown artifacts, not an interactive dashboard.

## Recommended Next Task

`PMBOT-BATCH-011-DEMO-WALKTHROUGH-BUNDLE`

Create one deterministic, review-only walkthrough command or markdown bundle that assembles the existing demo outputs into a concise Monday presentation artifact. It must remain offline-only, paper-only, local-only, and must not implement live fetchers, network/API, credentials, wallet, orders, trading, runtime wiring, dispatcher/run_codex, or prompt automation.
