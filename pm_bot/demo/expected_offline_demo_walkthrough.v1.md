# PMBOT Offline Demo Walkthrough

Deterministic local PMBOT walkthrough for Monday presentation.

## Boundary

- Offline only: true
- Paper only: true
- Execution allowed: false
- Trading allowed: false
- Network used: false
- API used: false
- Wallet used: false

## Run Summary

- pass: `python pm_bot/demo/run_operator_review_demo.py`
- pass: `python pm_bot/export/build_review_export_package.py`
- pass: `python pm_bot/demo/run_paper_research_demo.py`
- pass: `python pm_bot/replay/run_adversarial_replay.py`
- pass: `python pm_bot/raw_artifacts/build_ingestion_manifest.py`
- pass: `python pm_bot/audit/static_safety_audit_v7.py`
- pass: `python pm_bot/reports/rejection_summary_report.py`
- pass: `python pm_bot/paper/simulate_paper_plan.py pm_bot/paper/paper_plan_fixture.v1.json`
- pass: `python pm_bot/accounting/calculate_fee_slippage.py pm_bot/accounting/accounting_fixture.v1.json`
- pass: `python pm_bot/risk/evaluate_risk_limits.py pm_bot/risk/risk_fixture.v1.json`

## Presentation Highlights

- Accepted paper candidates: 4
- Watchlist candidates: 5
- Review table rows: 12
- Paper demo market: pm_fixture_2026_us_recession_q3
- Paper recommendation type: research_only
- Paper simulation gross PnL: 17.45
- Accounting total cost: 0.2125
- Risk approved: false
- Risk breaches: max_total_notional
- Adversarial replay: 12/12 passed
- False positives: 0
- Raw artifacts accepted: 3
- Raw artifacts quarantined: 9
- Rejection count: 13
- Static audit passed: true
- Static audit blocking findings: 0

## Limitations

- No live bot.
- No live fetcher.
- No normalization implementation.
- No wallet, credentials, private keys, or signing.
- No real orders or live trading.
- No runtime wiring.

Next: `PMBOT-BATCH-013-DEMO-PACKET-POLISH`
