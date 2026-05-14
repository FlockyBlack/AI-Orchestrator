# ORCH-PMBOT-TELEGRAM-060T Operator Console

Task: `ORCH-PMBOT-TELEGRAM-060T-OPERATOR-CONSOLE-FOR-PMBOT-STATUS-AND-DRY-RUNS`

This update turns the Telegram `/panel` surface into a PMBOT operator console for the accepted 052-060 paper and preflight flows. The console is review-only and exposes only status reads plus existing dry-run/preflight commands.

## Telegram Console Sections

- PMBOT Status
- Paper Runs
- Public Market Evidence
- Decision Ledger
- Live Readiness
- Blockers
- Latest Artifacts
- Safety State

Russian labels are available through the existing Telegram language flow, including:

- Главное меню
- Бумажный прогон
- Публичный рынок
- Журнал решений
- Live-проверка
- Блокеры
- Только review-only
- Live-торговля заблокирована

## Safe Buttons

The operator-console keyboard is shown after an operator selects a language and opens `/panel`. It contains only these run/status controls:

- Run Paper Canary 052
- Run Paper Loop 053
- Run Public Market Paper Loop 054
- Update Decision Ledger 055
- Run Live Connector Preflight 056
- Run Authenticated CLOB Preflight 057/058
- Run No-Order Auth GET Preflight 059
- Run Signer Boundary Preflight 060
- Show Latest Status
- Show Blockers
- Show Readiness %

The run buttons execute the existing module commands with `--dry-run` and no live/auth/signing/order/wallet enabling flags. The signer-boundary button uses `python -m pm_bot.operator_runner.signer_boundary_preflight --market BTC --strategy tiny-momentum --dry-run`. The status buttons only render Telegram-safe summaries.

## Status Registry

New module:

- `pm_bot/operator_runner/telegram_status_registry.py`

The registry reads latest JSON artifacts from:

- `pm_bot/trading_core/artifacts/paper_canary_drill_052/latest_paper_canary_status_052.json`
- `pm_bot/trading_core/artifacts/paper_trading_loop_053/latest_paper_trading_status_053.json`
- `pm_bot/trading_core/artifacts/public_market_paper_loop_054/latest_public_market_paper_status_054.json`
- `pm_bot/trading_core/artifacts/paper_decision_ledger_055/latest_paper_decision_ledger_status_055.json`
- `pm_bot/trading_core/artifacts/live_connector_preflight_056/latest_live_connector_preflight_status_056.json`
- `pm_bot/trading_core/artifacts/authenticated_clob_preflight_057/latest_authenticated_clob_preflight_status_057.json`
- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/latest_clob_l2_marker_preflight_status_058.json`
- `pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/latest_no_order_auth_get_preflight_status_059.json`
- `pm_bot/trading_core/artifacts/signer_boundary_preflight_060/latest_signer_boundary_preflight_status_060.json`

It tolerates missing files, returns concise status cards, and never includes raw Telegram tokens, operator IDs, init data, credential values, wallet data, balances, positions, fills, or PnL.

Generated artifacts:

- `pm_bot/trading_core/artifacts/telegram_operator_console_060t/telegram_operator_console_060t_result.json`
- `pm_bot/trading_core/artifacts/telegram_operator_console_060t/telegram_operator_console_060t_status_registry_snapshot.json`
- `pm_bot/trading_core/artifacts/telegram_operator_console_060t/latest_telegram_operator_console_status_060t.json`

## Readiness Summary

The Telegram readiness summary reports:

- Paper system: ready
- Public market data: ready
- Decision ledger: ready
- Live connector preflight: ready or blocked
- Auth boundary: ready_live_blocked or blocked
- Signer boundary: ready_live_blocked when the 060 latest artifact exists, otherwise not implemented yet
- Order submission: blocked
- Live execution: blocked

Readiness labels:

- `paper_demo_ready`
- `pre_live_boundary_ready`
- `signer_boundary_ready` or `signer_boundary_missing`
- `live_execution_blocked`

## Safety Invariants

The console keeps these flags false:

- `live_execution_approved`
- `order_submission_enabled`
- `wallet_signing_enabled`
- `signing_enabled`
- `signed_payload_generation_enabled`
- `signed_order_generation_enabled`
- `authenticated_polymarket_enabled`
- `live_connector_enabled`
- `allowed_for_live`

It also keeps `resolved_blocker_count=0` and does not add live trading, order submission, signing, wallet connection, balances, positions, fills, PnL, autonomous execution, daemons, schedulers, or browser automation.

## Manual Runtime Check

Safe local smoke command:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke
```

If a token and allowed operator IDs are configured locally, an operator may start the runtime and open `/panel`. The expected result is a review-only PMBOT menu with only dry-run/preflight/status controls and no live execution controls.
