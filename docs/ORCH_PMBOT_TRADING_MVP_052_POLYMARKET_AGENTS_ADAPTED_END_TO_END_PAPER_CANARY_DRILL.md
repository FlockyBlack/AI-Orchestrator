# ORCH-PMBOT-TRADING-MVP-052 Polymarket Agents Adapted Paper Canary Drill

## Purpose

This task adds a visible end-to-end PMBOT paper canary drill adapted from safe read-only concepts in the public Polymarket agents donor repository.

The workflow is:

1. deterministic Polymarket-style BTC fixture
2. normalized PMBOT market model
3. read-only BTC market snapshot
4. simulated paper order intent
5. readiness, risk, and go/no-go summaries
6. supervised operator approval packet reference
7. evidence/replay-compatible artifact
8. latest status feed for operator UI and Telegram-facing summary

## Operator Command

Run:

```powershell
python -m pm_bot.operator_runner.paper_canary_drill --market BTC --dry-run
```

Expected concise output:

```text
Paper canary drill completed.
Market: BTC fixture
Mode: paper / review-only
Live execution: blocked
Artifact: pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json
```

`PMBOT_ARTIFACT_DIR` may be set to redirect artifacts for validation or operator review.

## Generated Artifacts

Default artifact paths:

- `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_normalized_market_052.json`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_market_snapshot_052.json`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_order_intent_052.json`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_risk_readiness_052.json`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_gonogo_052.json`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_supervised_approval_packet_052.json`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_supervised_approval_packet_052.md`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_operator.md`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/latest_paper_canary_status_052.json`
- `pm_bot/trading_core/artifacts/paper_canary_drill_052/latest_paper_canary_status_052.md`

Artifact lookup uses fixed filenames under the configured artifact directory. It does not recursively scan the repository.

## What It Does

- Creates normalized Polymarket-style market models for PMBOT review workflows.
- Loads a deterministic local BTC fixture by default.
- Converts the normalized market into the existing BTC read-only connector fixture shape.
- Produces a simulated paper order intent that is explicitly not an order submission.
- Builds readiness, live-boundary, risk, and no-go summaries through existing PMBOT safety modules.
- Produces a supervised operator approval packet reference for review discipline.
- Writes a latest paper canary status JSON and Markdown file.
- Exposes the latest status passively to the operator UI panel.
- Adds a Telegram-facing text summary that is review-only and contains no executable trading instruction.

## What It Does Not Do

- It does not enable live trading.
- It does not approve live execution.
- It does not send orders.
- It does not call authenticated Polymarket endpoints.
- It does not make connector network calls by default.
- It does not connect a wallet.
- It does not read private keys, mnemonics, seed phrases, wallet files, browser wallets, API secrets, auth tokens, Telegram tokens, init data, raw operator IDs, or raw credentials.
- It does not perform signing.
- It does not generate signed payloads.
- It does not generate signed orders.
- It does not generate fake signatures, order IDs, transaction hashes, fills, balances, PnL, or execution results.
- It does not add browser automation, a scheduler, a daemon, a background worker, or an autonomous live trading loop.

## Required Paper-Only Flags

The drill result and latest status require:

- `execution_mode: paper`
- `review_only: true`
- `live_execution_approved: false`
- `canary_executable_now: false`
- `real_execution_available: false`
- `order_submission_enabled: false`
- `wallet_signing_enabled: false`
- `signing_enabled: false`
- `signed_payload_generation_enabled: false`
- `signed_order_generation_enabled: false`
- `authenticated_polymarket_enabled: false`
- `live_connector_enabled: false`
- `allowed_for_live: false`
- `resolved_blocker_count: 0`

Any future change that flips one of these flags must be a separate operator-approved live-enabling task.

## Passive Integration Points

- `pm_bot/trading_core/polymarket_market_models.py`
- `pm_bot/trading_core/polymarket_public_market_data.py`
- `pm_bot/trading_core/paper_canary_drill.py`
- `pm_bot/operator_runner/paper_canary_drill.py`
- `pm_bot/operator_runner/operator_ui_panel_v1.py`
- `pm_bot/operator_runner/telegram_operator_control_bot.py`

## Network Mode

This task implements fixture-only behavior. The optional `--network-check` flag records `network_check_requested: true` and `network_check_status: not_implemented_fixture_only`, but still performs no network call.

A future task may add explicit unauthenticated public Gamma metadata checks if approved, but it must remain read-only and must not use API keys, authenticated endpoints, wallets, signing, or order endpoints.

## Live Trading Status

This task does not approve or enable live execution. PMBOT remains paper/dry-run only.
