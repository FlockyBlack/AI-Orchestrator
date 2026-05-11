# ORCH PMBOT Trading MVP 029 Live Canary Readiness Dry-Run Gate

Task: `ORCH-PMBOT-TRADING-MVP-029-LIVE-CANARY-READINESS-DRY-RUN-GATE`

This task adds a deterministic local readiness gate for a future tiny live canary review. It does not add real wallet integration, private-key handling, cryptographic signing, authenticated endpoint access, order submission, or live execution.

## What Was Built

- `pm_bot/trading_core/live_canary_readiness.py` defines the live-canary readiness packet contract, dry-run-only operator approval record, forbidden-field scanner, and local dry-run acceptance receipt.
- The builder assembles one logical canary packet from local PMBOT artifacts: paper strategy ledger, source evidence status, risk decision ledger, wallet boundary packet, signing simulator receipt, and run context.
- Missing required inputs produce a blocked packet with explicit reason codes and a missing artifact summary. The builder does not invent missing data, outcomes, or PnL.
- Operator approval supports only `not_requested`, `requested`, `approved_for_dry_run_only`, `rejected`, and `expired`. It has no live execution approval state.
- The dry-run receipt explicitly records that no real wallet, private key, real signature, order, authenticated endpoint, external API call, or live execution was used.
- `pm_bot/operator_runner/paper_daily_loop.py` now writes canary operator approval, readiness packet, and dry-run receipt artifacts and surfaces a canary summary in the paper daily dashboard/report.
- `docs/ORCH_PMBOT_TRADING_MVP_029_LIVE_CANARY_READINESS_DRY_RUN_GATE_NIGHTLY_BATCH_PLAN.example.json` is a static fake-executor nightly lane batch plan example only.

## How To Run The Local Dry-Run Readiness Flow

After existing paper daily artifacts are present, run:

```powershell
python -m pm_bot.trading_core.live_canary_readiness `
  --paper-strategy-ledger pm_bot/operator_runner/artifacts/paper_daily_022/paper_strategy_evaluation_ledger.json `
  --source-evidence-status pm_bot/operator_runner/artifacts/paper_daily_022/public_evidence_refresh_ledger.json `
  --risk-decision-ledger pm_bot/operator_runner/artifacts/paper_daily_022/risk_engine_decision_ledger.json `
  --wallet-boundary-ledger pm_bot/operator_runner/artifacts/paper_daily_022/wallet_boundary_audit_ledger.json `
  --signing-receipts pm_bot/operator_runner/artifacts/paper_daily_022/dry_run_execution_receipts.json
```

With no operator approval record, the output remains blocked or `needs_operator_approval`. To test the acceptance path, provide a local approval artifact whose status is exactly `approved_for_dry_run_only`.

The paper daily loop also writes these artifacts during its normal one-shot local run:

- `live_canary_operator_approval_record.json`
- `live_canary_readiness_packet.json`
- `live_canary_dry_run_acceptance_receipt.json`
- matching Markdown reports

## Still Forbidden

- No real wallet integration.
- No private keys, seed phrases, mnemonic handling, signing material, wallet files, or credential stores.
- No cryptographic signing and no real signatures.
- No real order placement, CLOB order submission, transaction construction, or transaction broadcasting.
- No authenticated Polymarket endpoint or external API call.
- No autonomous live trading, scheduler, daemon, background worker, browser automation, or real Codex invocation.
- No market recommendation, live action instruction, probability, EV, edge, confidence, or side-selection output.
- No invented outcome resolution and no invented PnL.

## Before Any Real Tiny Live Canary

A separate operator-approved task must define and approve all sensitive boundaries before any real live canary exists:

- exact wallet custody and key-handling design;
- exact signing boundary and dual-control confirmation process;
- authenticated endpoint scope, request limits, and audit output;
- order construction and submission boundary;
- real kill-switch behavior and reconciliation;
- rollback and incident handling;
- legal, compliance, and operator review records;
- explicit confirmation that the canary is still tiny, supervised, and auditable.

This repository still contains no real wallet, signing, authenticated endpoint, order execution, or autonomous live trading implementation.
