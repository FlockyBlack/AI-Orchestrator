# PMBOT Demo Runbook V1

## Purpose

Run the PMBOT local demo as a deterministic fixture-only and paper-only research pipeline.

## Commands

```powershell
python pm_bot\scenarios\run_demo_scenarios.py
python pm_bot\demo\run_paper_research_demo.py
python pm_bot\demo\run_paper_research_demo.py --markdown
```

## Files Read

- `pm_bot/scenarios/scenario_suite.v2.json`
- `pm_bot/demo/demo_market_bundle.v1.json`
- existing PMBOT fixture inputs under `pm_bot/fixtures`, `pm_bot/hedges`, `pm_bot/paper`, `pm_bot/risk`, `pm_bot/accounting`, `pm_bot/reports`, and `pm_bot/postmortem`
- existing expected output contracts under validated PMBOT modules

## Outputs

- scenario JSON report to stdout, with optional `--output` under `pm_bot/scenarios/`
- demo JSON report to stdout
- demo Markdown report to stdout

## Safety Guarantees

- fixture-only
- paper-only
- local-only
- deterministic
- no live API
- no network calls
- no wallet or private key handling
- no real trading
- no runtime wiring

## Forbidden

- live Polymarket API usage
- wallet access
- private key handling
- real orders
- runtime wiring
- dispatcher or `run_codex` changes
