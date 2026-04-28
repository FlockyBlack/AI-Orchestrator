# PMBOT Demo Runbook V3

## Scope

PMBOT-BATCH-004 adds a local-only explainability and research quality layer on top of the accepted BATCH-003 fixture/demo/report stack.

The added layer stays:

- fixture-only
- paper-only
- local-only
- deterministic
- offline-testable

No live fetcher, live Polymarket API, wallet, signing, real orders, autonomous trading, runtime wiring, dispatcher integration, or `run_codex` integration was added.

## What BATCH-004 Adds

- `pm_bot/research/research_quality_cases.v1.json` with deterministic research review cases
- `pm_bot/explainability/signal_explainer.py` for structured signal explanations
- `pm_bot/quality/confidence_breakdown.py` for component confidence scoring
- `pm_bot/quality/bad_signal_rejection_report.py` for grouped rejection review
- `pm_bot/reports/candidate_comparison_report.py` for cross-candidate ranking and comparison
- `pm_bot/quality/research_quality_scorecard.py` for local MVP quality scoring
- `pm_bot/explainability/reasoning_trace.py` for machine-readable and human-readable traces
- `pm_bot/demo/run_research_quality_demo.py` for an integrated local demo bundle
- `pm_bot/audit/static_safety_audit_v3.py` for expanded static safety coverage

## Required Test Commands

Run the targeted test groups:

```powershell
python -m pytest pm_bot\research\tests -q
python -m pytest pm_bot\explainability\tests -q
python -m pytest pm_bot\quality\tests -q
python -m pytest pm_bot\reports\tests -q
python -m pytest pm_bot\demo\tests -q
python -m pytest pm_bot\audit\tests -q
```

Run the grouped PMBOT tests:

```powershell
python -m pytest pm_bot\scenarios\tests pm_bot\demo\tests pm_bot\reports\tests pm_bot\audit\tests pm_bot\research\tests pm_bot\explainability\tests pm_bot\quality\tests -q
```

## Local Demo Commands

Run the new research quality demo:

```powershell
python pm_bot\demo\run_research_quality_demo.py
```

Run the new static audit:

```powershell
python pm_bot\audit\static_safety_audit_v3.py
```

Re-run the BATCH-003 compatibility scripts:

```powershell
python pm_bot\scenarios\run_demo_scenarios_v3.py
python pm_bot\demo\run_dashboard_summary.py
python pm_bot\audit\static_safety_audit_v2.py
```

## Out Of Scope

- live fetcher implementation
- live Polymarket API usage
- wallet/private key handling
- signing
- real orders
- real trading
- autonomous execution
- runtime wiring
- dispatcher integration
- `run_codex` integration

## Blocked Pending Future Approval

- any live/API integration
- any wallet/private-key material
- any real order path
- any autonomous or runtime-driven trading behavior
- any mutation of dispatcher, runtime, state, results, freezes, checkpoints, codex_auto, or governance surfaces

## Validation Boundary

This runbook documents local implementation and offline verification only. PMBOT-BATCH-004 remains ready for Flocky validation; it does not claim final Flocky done state.
