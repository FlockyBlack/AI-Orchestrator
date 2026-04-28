# PMBOT Demo Runbook V4

## Scope

PMBOT-BATCH-005 adds a deterministic adversarial replay and hostile market validation layer on top of the accepted BATCH-003 and BATCH-004 PMBOT stack.

The added layer stays:

- fixture-only
- paper-only
- local-only
- deterministic
- offline-testable

No live fetcher, live Polymarket API, wallet, signing, real orders, autonomous trading, runtime wiring, dispatcher integration, or `run_codex` integration was added.

## What BATCH-005 Adds

- `pm_bot/adversarial/adversarial_replay_cases.v1.json` with hostile replay fixtures and false-positive traps
- `pm_bot/replay/run_adversarial_replay.py` with deterministic replay validation output
- `pm_bot/adversarial/market_shock_scenarios.v1.json` with synthetic market shock sweeps
- `pm_bot/adversarial/run_market_shock_scenarios.py` with deterministic shock validation output
- `pm_bot/validation/false_positive_prevention_report.py` with replay rejection quality summaries
- `pm_bot/validation/replay_safety_scorecard.py` with replay containment scoring
- `pm_bot/demo/run_adversarial_validation_demo.py` with an integrated hostile-condition demo
- `pm_bot/audit/static_safety_audit_v4.py` with static coverage for `pm_bot/replay`, `pm_bot/adversarial`, and `pm_bot/validation`

## Required Test Commands

Run the targeted test groups:

```powershell
python -m pytest pm_bot\adversarial\tests -q
python -m pytest pm_bot\replay\tests -q
python -m pytest pm_bot\validation\tests -q
python -m pytest pm_bot\demo\tests -q
python -m pytest pm_bot\audit\tests -q
```

Run the grouped PMBOT tests:

```powershell
python -m pytest pm_bot\scenarios\tests pm_bot\demo\tests pm_bot\reports\tests pm_bot\audit\tests pm_bot\research\tests pm_bot\explainability\tests pm_bot\quality\tests pm_bot\adversarial\tests pm_bot\replay\tests pm_bot\validation\tests -q
```

## Local Demo Commands

Run the new replay validation runner:

```powershell
python pm_bot\replay\run_adversarial_replay.py
```

Run the new market shock runner:

```powershell
python pm_bot\adversarial\run_market_shock_scenarios.py
```

Run the integrated adversarial validation demo:

```powershell
python pm_bot\demo\run_adversarial_validation_demo.py
```

Run the existing research quality compatibility demo:

```powershell
python pm_bot\demo\run_research_quality_demo.py
```

Run the latest static audit:

```powershell
python pm_bot\audit\static_safety_audit_v4.py
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

This runbook documents local implementation and offline verification only. PMBOT-BATCH-005 remains ready for Flocky validation; it does not claim final Flocky done state.
