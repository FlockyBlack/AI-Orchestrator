# PMBOT Batch 011 Demo Walkthrough Bundle

Task ID: `PMBOT-BATCH-011-DEMO-WALKTHROUGH-BUNDLE`

Status: `completed_ready_for_review`

Mode: offline-only, paper-only, local-only, deterministic, review-only.

## What Can Be Shown Monday

PMBOT is demo-ready as a local CLI walkthrough and artifact review package.

The demo can show:

- local operator review summary with paper candidates, watchlist cases, and checklist status;
- full review export package with candidate table, rejection summary, watchlist policy, risk/audit summary, and no-execution statement;
- paper research demo with fixture market, paper simulation, accounting, risk, dashboard, and postmortem summaries;
- adversarial replay proving hostile fixtures stay rejected/watchlisted/excluded with 0 false positives;
- raw artifact ingestion/quarantine manifest with accepted fixtures and blocked invalid artifacts;
- static safety audit v7 with 0 blocking findings.

This is not a live trading demo, not a live fetcher demo, and not a production automation demo.

## Exact Safe Commands

Run from:

```powershell
C:\Users\OpenC\Documents\AI-Orchestrator
```

Primary walkthrough:

```powershell
python pm_bot\demo\run_operator_review_demo.py
python pm_bot\export\build_review_export_package.py
python pm_bot\demo\run_paper_research_demo.py
python pm_bot\replay\run_adversarial_replay.py
python pm_bot\raw_artifacts\build_ingestion_manifest.py
python pm_bot\audit\static_safety_audit_v7.py
```

Supporting components:

```powershell
python pm_bot\paper\simulate_paper_plan.py pm_bot\paper\paper_plan_fixture.v1.json
python pm_bot\accounting\calculate_fee_slippage.py pm_bot\accounting\accounting_fixture.v1.json
python pm_bot\risk\evaluate_risk_limits.py pm_bot\risk\risk_fixture.v1.json
python pm_bot\reports\rejection_summary_report.py
```

Verification:

```powershell
python -m pytest pm_bot\operator\tests pm_bot\export\tests pm_bot\audit\tests pm_bot\demo\tests pm_bot\replay\tests pm_bot\reports\tests pm_bot\paper\tests pm_bot\accounting\tests pm_bot\risk\tests -q
```

Last observed result from the readiness snapshot: `121 passed`.

## Expected Outputs And Artifacts

Operator review:

- `pm_bot/demo/expected_operator_review_demo.v1.json`
- `pm_bot/operator/expected_operator_review_bundle.v1.json`
- `pm_bot/operator/expected_paper_candidate_review_table.v1.json`
- `pm_bot/operator/expected_watchlist_policy_report.v1.json`
- `pm_bot/operator/expected_operator_review_checklist.v1.json`

Review export:

- `pm_bot/export/expected_review_export_package.v1.json`
- `pm_bot/export/expected_review_export_package.v1.md`

Paper research:

- `pm_bot/demo/expected_paper_research_demo.v1.json`
- `pm_bot/demo/expected_paper_research_demo.v1.md`
- `pm_bot/paper/expected_paper_simulation.v1.json`
- `pm_bot/accounting/expected_accounting_report.v1.json`
- `pm_bot/risk/expected_risk_report.v1.json`

Replay and reports:

- `pm_bot/replay/expected_adversarial_replay_report.v1.json`
- `pm_bot/reports/expected_rejection_summary_report.v1.json`

Raw artifact gate:

- `pm_bot/raw_artifacts/expected_ingestion_manifest.v1.json`

Safety:

- `pm_bot/audit/expected_static_safety_audit.v7.json`
- `docs/PM_BOT_BATCH_010_RESULT.json`
- `docs/PM_BOT_STAGE_SUMMARY_V11.md`

## Presentation Flow

1. State the boundary first: PMBOT is offline-only, paper-only, local-only, deterministic, and review-only.
2. Run `python pm_bot\demo\run_operator_review_demo.py`.
3. Point out the operator bundle counts: 4 accepted paper candidates and 5 watchlist cases.
4. State that watchlist is no-action and cannot become live/order/trade without separate approval.
5. Run `python pm_bot\export\build_review_export_package.py`.
6. Show that the package contains review bundle, candidate table, watchlist policy, rejection summary, risk/audit summary, and checklist.
7. Run `python pm_bot\demo\run_paper_research_demo.py`.
8. Show fixture-only research, paper simulation, accounting, risk, dashboard, and postmortem summaries.
9. Run `python pm_bot\replay\run_adversarial_replay.py`.
10. Show 12/12 replay cases passed and false positives remain 0.
11. Run `python pm_bot\raw_artifacts\build_ingestion_manifest.py`.
12. Show 3 accepted raw fixtures and 9 quarantined invalid fixtures.
13. Run `python pm_bot\audit\static_safety_audit_v7.py`.
14. Show audit passed with 0 blocking findings.
15. Close with what is not implemented: no live fetcher, no normalization implementation, no live API, no wallet, no orders, no runtime wiring.

## Safety Evidence

- Operator/export package explicitly says no execution instructions, no live orders, no wallet, and no API path.
- Paper research demo reports `execution_allowed=false`, `trading_allowed=false`, `network_used=false`, `api_used=false`, and `wallet_used=false`.
- Adversarial replay reports 12 passed cases, 0 failed cases, and 0 false positives.
- Raw ingestion manifest reports `validation_passed=true`, 3 accepted fixtures, 9 quarantined invalid fixtures, and unsafe safety detections false.
- Static safety audit v7 reports `audit_passed=true` and no blocking findings.
- Batch 010 result reports no live fetcher implementation, no normalization implementation, no network/API, no credentials, no wallet, no real orders, no real trading, and no runtime wiring.

## Not Implemented Yet

- No live fetcher.
- No normalization implementation.
- No live Polymarket API.
- No credentials or wallet handling.
- No real orders or trading.
- No autonomous trading.
- No dispatcher, runtime, or run_codex integration.
- No prompt automation.
- No interactive dashboard for the Monday demo.

## Strongest Next Engineering Step

`PMBOT-BATCH-012-OFFLINE-DEMO-COMMAND`

Create one deterministic CLI command that runs the existing walkthrough commands, captures their key summaries, and emits one stable JSON/Markdown demo packet. It must reuse existing local outputs, stay offline-only and paper-only, and must not add live fetchers, network/API calls, credentials, wallet handling, orders, trading, runtime wiring, dispatcher/run_codex integration, or prompt automation.

