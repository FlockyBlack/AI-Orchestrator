# PMBOT Demo Runbook V2

## Purpose

Run the PMBOT BATCH-003 local demo as a deterministic fixture-only, paper-only, multi-market research workflow.

## Commands

```powershell
python pm_bot\scenarios\run_demo_scenarios_v3.py
python pm_bot\reports\portfolio_paper_report.py
python pm_bot\reports\portfolio_paper_report.py --markdown
python pm_bot\demo\run_dashboard_summary.py
python pm_bot\demo\run_dashboard_summary.py --markdown
python pm_bot\audit\static_safety_audit_v2.py
python -m pytest pm_bot\scenarios\tests\test_run_demo_scenarios_v3.py
python -m pytest pm_bot\reports\tests\test_portfolio_paper_report.py
python -m pytest pm_bot\demo\tests\test_dashboard_summary.py
python -m pytest pm_bot\audit\tests\test_static_safety_audit_v2.py
python -m pytest pm_bot\scenarios\tests pm_bot\demo\tests pm_bot\reports\tests pm_bot\audit\tests
```

## Files Read

- `pm_bot/fixtures/multi_market_fixture_bundle.v1.json`
- `pm_bot/scenarios/scenario_suite.v3.json`
- existing PMBOT fixture and expected report artifacts from BATCH-001 and BATCH-002
- safe PMBOT docs under `docs/PM_BOT_*.md` and `docs/PM_BOT_*.json` for audit context

## Outputs

- V3 scenario JSON report to stdout, with optional `--output` under `pm_bot/scenarios/`
- portfolio JSON report to stdout
- portfolio Markdown report to stdout
- dashboard summary JSON report to stdout
- dashboard summary Markdown report to stdout
- static audit JSON report to stdout

## BATCH-003 Additions

- synthetic multi-market fixture bundle covering liquid, low-liquidity, wide-spread, stale, resolved, missing-notes, concentration, and correlated-exposure cases
- deterministic V3 scenario suite with portfolio-level warnings and paper-only no-action confirmation
- portfolio-level paper report with capital, exposure, warning, and estimated value-delta summaries
- richer local dashboard summary with explicit safety boundary status
- stronger static audit baseline that inspects only safe PMBOT and PMBOT docs paths

## Safety Guarantees

- fixture-only
- paper-only
- local-only
- deterministic
- no network calls
- no live Polymarket API
- no wallet or private key handling
- no real orders
- no real trading
- no autonomous execution
- no runtime wiring
- no dispatcher or `run_codex` changes

## Out Of Scope

- live market fetching
- wallet access
- private key handling
- signing
- order submission
- dispatcher wiring
- `run_codex` integration
- governance or state mutation

## Required Follow-Up

Implementation complete does not claim final acceptance. Queue Flocky validation `PMBOT-BATCH-003-V` for critic review.
