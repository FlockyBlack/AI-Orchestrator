# PM Bot Demo Runbook V5

## Purpose

PMBOT-BATCH-006 adds a local-only operator review package that consolidates prior paper and validation artifacts into a human-review bundle.

## New BATCH-006 Commands

- `python pm_bot\demo\run_operator_review_demo.py`
- `python pm_bot\export\build_review_export_package.py`
- `python pm_bot\audit\static_safety_audit_v5.py`

## Operator Review Artifacts

- operator review bundle: `pm_bot/operator/expected_operator_review_bundle.v1.json` and `.md`
- paper candidate review table: `pm_bot/operator/expected_paper_candidate_review_table.v1.json` and `.md`
- watchlist policy report: `pm_bot/operator/expected_watchlist_policy_report.v1.json` and `.md`
- rejection summary: `pm_bot/reports/expected_rejection_summary_report.v1.json` and `.md`
- risk and audit summary: `pm_bot/operator/expected_risk_audit_summary.v1.json` and `.md`
- export package: `pm_bot/export/expected_review_export_package.v1.json` and `.md`
- operator checklist: `pm_bot/operator/expected_operator_review_checklist.v1.json` and `.md`
- operator review demo: `pm_bot/demo/expected_operator_review_demo.v1.json` and `.md`

## Scope Boundaries

- fixture-only
- paper-only
- local-only
- deterministic
- offline-testable
- operator-review-only
- no network or API
- no wallet or private key
- no real orders or trading
- no runtime wiring or orchestration mutation

## Out Of Scope

- live fetcher implementation
- live Polymarket API integration
- wallet/signing work
- real order execution
- autonomous trading
- dispatcher, runtime, run_codex, state, result, freeze, checkpoint, or governance changes

## Future Approval Boundary

Any live fetcher, live API, wallet, signing, real-order, or runtime-wiring work requires a separate future approval task after Flocky validation.